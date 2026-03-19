"""Core library — importable by AIDA plugin."""

from __future__ import annotations

import datetime
import shutil
from pathlib import Path

from canvas.config import CanvasPaths, load_config, resolve_paths
from canvas.exceptions import CanvasSessionError
from canvas.models import Session, SessionStatus
from canvas.registry import (
    add_session,
    find_session,
    load_registry,
    remove_session,
    save_registry,
    update_session,
)
from canvas.slug import generate_slug
from canvas.template import render_claude_md

_MAX_RANDOM_SLUG_ATTEMPTS = 5


def _slug_exists(slug: str, sessions_dir: Path, paths: CanvasPaths) -> bool:
    """Check for slug collision in both registry and on disk."""
    if find_session(slug, paths=paths) is not None:
        return True
    if (sessions_dir / slug).exists():
        return True
    return False


def new_session(
    label: str | None = None,
    org: str | None = None,
    paths: CanvasPaths | None = None,
) -> Session:
    """Create a new canvas session.

    Orchestration steps:
    1. Resolve CanvasPaths if not provided
    2. If org is None, read from config
    3. Generate slug (with collision retry for random slugs)
    4. Create session directory
    5. Render and write CLAUDE.md
    6. Register session in registry
    7. Return Session object
    """
    # 1. Resolve paths
    if paths is None:
        paths = resolve_paths()

    # 2. Resolve org from config if not provided
    if org is None:
        config = load_config(paths)
        org = config["org"]

    # 3. Generate slug with collision handling
    is_random = label is None

    if is_random:
        slug = None
        for _attempt in range(_MAX_RANDOM_SLUG_ATTEMPTS):
            candidate = generate_slug(label)
            if not _slug_exists(candidate, paths.sessions_dir, paths):
                slug = candidate
                break
        if slug is None:
            raise CanvasSessionError(
                f"Failed to generate a unique slug after {_MAX_RANDOM_SLUG_ATTEMPTS} attempts. "
                "Try again or provide a label."
            )
    else:
        slug = generate_slug(label)
        if _slug_exists(slug, paths.sessions_dir, paths):
            raise CanvasSessionError(
                f"Session '{slug}' already exists. Choose a different label."
            )

    # 4. Create session directory
    session_dir = paths.sessions_dir / slug
    session_dir.mkdir(parents=True)

    # 5. Render CLAUDE.md and write to session directory
    claude_md = render_claude_md(
        org=org,
        slug=slug,
        label=label,
        paths=paths,
        session_path=session_dir,
    )
    (session_dir / "CLAUDE.md").write_text(claude_md)

    # 6. Register session
    session = Session(
        slug=slug,
        org=org,
        created=datetime.date.today(),
        status=SessionStatus.ACTIVE,
        label=label,
    )
    add_session(session, paths=paths)

    # 7. Return session
    return session


def list_sessions(
    status: str | None = None,
    org: str | None = None,
    paths: CanvasPaths | None = None,
) -> list[Session]:
    """Load registry and return sessions, optionally filtered by status and/or org."""
    sessions = load_registry(paths)

    if status is not None:
        sessions = [s for s in sessions if s.status == status]

    if org is not None:
        sessions = [s for s in sessions if s.org == org]

    return sessions


def archive_session(slug: str, paths: CanvasPaths | None = None) -> Session:
    """Archive a session by setting status to ARCHIVED and archived_at to today.

    Directory is preserved. Raises CanvasSessionError if not found.
    """
    if paths is None:
        paths = resolve_paths()

    session = find_session(slug, paths)
    if session is None:
        raise CanvasSessionError(f"Session '{slug}' not found.")

    try:
        updated = update_session(
            slug,
            paths=paths,
            status=SessionStatus.ARCHIVED,
            archived_at=datetime.date.today(),
        )
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

    session = find_session(slug, paths)
    if session is None:
        raise CanvasSessionError(f"Session '{slug}' not found.")

    # Remove directory if it exists
    session_dir = paths.sessions_dir / slug
    if session_dir.exists():
        shutil.rmtree(session_dir)

    # Remove from registry
    remove_session(slug, paths)


def rename_session(slug: str, label: str, paths: CanvasPaths | None = None) -> Session:
    """Update a session's label in the registry (slug/directory unchanged).

    Raises CanvasSessionError if not found.
    """
    if paths is None:
        paths = resolve_paths()

    session = find_session(slug, paths)
    if session is None:
        raise CanvasSessionError(f"Session '{slug}' not found.")

    try:
        updated = update_session(slug, paths=paths, label=label)
    except Exception as e:
        raise CanvasSessionError(f"Failed to rename session '{slug}': {e}") from e

    return updated
