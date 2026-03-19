# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Core library — importable by AIDA plugin."""

from __future__ import annotations

import datetime
import shutil
from pathlib import Path

from canvas.config import CanvasPaths, load_config, resolve_paths
from canvas.exceptions import CanvasError, CanvasRegistryError, CanvasSessionError
from canvas.models import Session, SessionStatus
from canvas.registry import (
    add_session,
    find_session,
    load_registry,
    remove_session,
    update_session,
)
from canvas.slug import generate_slug, validate_label, validate_org, validate_slug
from canvas.template import render_claude_md

_MAX_RANDOM_SLUG_ATTEMPTS = 5


def _verify_inside_sessions_dir(session_dir: Path, sessions_dir: Path) -> None:
    """Verify that *session_dir* resolves inside *sessions_dir*.

    Raises CanvasSessionError if the resolved path escapes (e.g. via symlink).
    """
    if not session_dir.resolve().is_relative_to(sessions_dir.resolve()):
        raise CanvasSessionError(
            f"Session directory {session_dir} resolves outside sessions dir — refusing to proceed."
        )


def _slug_exists(slug: str, sessions_dir: Path, paths: CanvasPaths) -> bool:
    """Check for slug collision in both registry and on disk."""
    if find_session(slug, paths=paths) is not None:
        return True
    return bool((sessions_dir / slug).exists())


def new_session(
    label: str | None = None,
    org: str | None = None,
    paths: CanvasPaths | None = None,
) -> Session:
    """Create a new canvas session.

    Orchestration steps:
    1. Resolve CanvasPaths if not provided
    2. If org is None, read from config
    3. Capture today's date (single source of truth for slug, template, session)
    4. Generate slug (with collision retry for random slugs)
    5. Create session directory, render CLAUDE.md, register in registry
       (with cleanup on partial failure)
    6. Return Session object

    .. note:: TOCTOU — The check-then-create sequence (slug collision check →
       mkdir) is not atomic.  This is acceptable because canvas targets
       single-user, local-filesystem usage where concurrent session creation
       is not expected.
    """
    # 1. Resolve paths
    if paths is None:
        paths = resolve_paths()

    # 2. Resolve org from config if not provided
    config_raw: dict[str, object] | None = None
    if org is None:
        config = load_config(paths)
        org = config.org
        config_raw = config.raw

    validate_org(org)

    # 3. Capture today once to avoid date skew across midnight
    today = datetime.date.today()

    # 4. Generate slug with collision handling
    is_random = label is None

    if is_random:
        slug = None
        for _attempt in range(_MAX_RANDOM_SLUG_ATTEMPTS):
            candidate = generate_slug(label, date=today)
            if not _slug_exists(candidate, paths.sessions_dir, paths):
                slug = candidate
                break
        if slug is None:
            raise CanvasSessionError(
                f"Failed to generate a unique slug after {_MAX_RANDOM_SLUG_ATTEMPTS} attempts. "
                "Try again or provide a label."
            )
    else:
        slug = generate_slug(label, date=today)
        if _slug_exists(slug, paths.sessions_dir, paths):
            raise CanvasSessionError(
                f"Session '{slug}' already exists for today. "
                "Choose a different label or try again tomorrow."
            )

    # 5. Create session directory, render CLAUDE.md, register session
    #    Wrap in try/except to clean up partial state on failure.
    session_dir = paths.sessions_dir / slug
    try:
        session_dir.mkdir(parents=True, mode=0o700)
    except OSError as e:
        raise CanvasSessionError(f"Failed to create session directory {session_dir}: {e}") from e

    _verify_inside_sessions_dir(session_dir, paths.sessions_dir)

    try:
        claude_md = render_claude_md(
            org=org,
            slug=slug,
            label=label,
            paths=paths,
            session_path=session_dir,
            date=today,
            config=config_raw,
        )
        if not claude_md.endswith("\n"):
            claude_md += "\n"
        (session_dir / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

        session = Session(
            slug=slug,
            org=org,
            created=today,
            status=SessionStatus.ACTIVE,
            label=label,
        )
        # add_session must remain the last operation in this try block;
        # cleanup only removes the directory, not the registry entry.
        add_session(session, paths=paths)
    except Exception:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise

    return session


def list_sessions(
    status: SessionStatus | str | None = None,
    org: str | None = None,
    paths: CanvasPaths | None = None,
) -> list[Session]:
    """Load registry and return sessions, optionally filtered by status and/or org."""
    if paths is None:
        paths = resolve_paths()

    if status is not None:
        try:
            status = SessionStatus(status)
        except ValueError as e:
            valid = ", ".join(s.value for s in SessionStatus)
            raise CanvasSessionError(f"Invalid status '{status}'. Valid values: {valid}") from e

    sessions = load_registry(paths)

    if status is not None:
        sessions = [s for s in sessions if s.status == status]

    if org is not None:
        sessions = [s for s in sessions if s.org == org]

    return sessions


def archive_session(
    slug: str, paths: CanvasPaths | None = None, date: datetime.date | None = None
) -> Session:
    """Archive a session by setting status to ARCHIVED and archived_at to today.

    Directory is preserved. Raises CanvasSessionError if not found.
    """
    if paths is None:
        paths = resolve_paths()

    validate_slug(slug)

    session = find_session(slug, paths=paths)
    if session is None:
        raise CanvasSessionError(f"Session '{slug}' not found.")

    if session.status == SessionStatus.ARCHIVED:
        return session

    try:
        updated = update_session(
            slug,
            paths=paths,
            status=SessionStatus.ARCHIVED,
            archived_at=date or datetime.date.today(),
        )
    except CanvasError:
        raise
    except Exception as e:
        raise CanvasSessionError(f"Failed to archive session '{slug}': {e}") from e

    return updated


def nuke_session(slug: str, paths: CanvasPaths | None = None) -> None:
    """Delete a session's directory and remove it from the registry.

    If the directory doesn't exist but the registry entry does, clean up the registry.
    Raises CanvasSessionError if not found in registry.
    """
    if paths is None:
        paths = resolve_paths()

    validate_slug(slug)

    try:
        remove_session(slug, paths=paths)
    except CanvasRegistryError as e:
        raise CanvasSessionError(f"Session '{slug}' not found.") from e

    # Remove directory if it exists
    session_dir = paths.sessions_dir / slug
    if session_dir.exists():
        _verify_inside_sessions_dir(session_dir, paths.sessions_dir)
        try:
            shutil.rmtree(session_dir)
        except OSError as e:
            raise CanvasSessionError(
                f"Failed to remove session directory {session_dir}: {e}"
            ) from e


def rename_session(slug: str, label: str, paths: CanvasPaths | None = None) -> Session:
    """Update a session's label in the registry (slug/directory unchanged).

    Raises CanvasSessionError if not found.
    """
    if paths is None:
        paths = resolve_paths()

    validate_slug(slug)
    validate_label(label)

    try:
        updated = update_session(slug, paths=paths, label=label)
    except CanvasRegistryError as e:
        raise CanvasSessionError(f"Session '{slug}' not found.") from e

    return updated


def reactivate_session(slug: str, paths: CanvasPaths | None = None) -> Session:
    """Reactivate an archived session — set status to ACTIVE, clear archived_at.

    Idempotent: if the session is already active, return it unchanged.
    Raises CanvasSessionError if session not found.
    """
    if paths is None:
        paths = resolve_paths()

    validate_slug(slug)

    session = find_session(slug, paths=paths)
    if session is None:
        raise CanvasSessionError(f"Session '{slug}' not found.")

    if session.status == SessionStatus.ACTIVE:
        return session

    try:
        updated = update_session(
            slug,
            paths=paths,
            status=SessionStatus.ACTIVE,
            archived_at=None,
        )
    except CanvasError:
        raise
    except Exception as e:
        raise CanvasSessionError(f"Failed to reactivate session '{slug}': {e}") from e

    return updated


def stale_sessions(
    days: int = 30,
    paths: CanvasPaths | None = None,
    today: datetime.date | None = None,
) -> list[Session]:
    """Return active sessions older than *days* days.

    Only considers sessions with status ACTIVE.
    *today* can be injected for testing; defaults to datetime.date.today().
    """
    if paths is None:
        paths = resolve_paths()

    if today is None:
        today = datetime.date.today()

    cutoff = today - datetime.timedelta(days=days)
    sessions = load_registry(paths)
    return [s for s in sessions if s.status == SessionStatus.ACTIVE and s.created <= cutoff]
