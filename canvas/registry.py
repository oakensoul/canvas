"""Read/write ~/.canvas/registry.json."""

from __future__ import annotations

import json
import os
from pathlib import Path

from canvas.config import CanvasPaths, resolve_paths
from canvas.exceptions import CanvasRegistryError
from canvas.models import Session


def load_registry(paths: CanvasPaths | None = None) -> list[Session]:
    """Load session registry from disk. Returns [] if file missing (first-run bootstrap)."""
    if paths is None:
        paths = resolve_paths()

    if not paths.registry.exists():
        return []

    try:
        data = json.loads(paths.registry.read_text())
        return [Session.from_dict(s) for s in data.get("sessions", [])]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise CanvasRegistryError(f"Corrupt registry at {paths.registry}: {e}") from e


def save_registry(sessions: list[Session], paths: CanvasPaths | None = None) -> None:
    """Persist sessions to registry. Uses atomic write (tmp + os.replace)."""
    if paths is None:
        paths = resolve_paths()

    paths.registry.parent.mkdir(parents=True, exist_ok=True)

    data = {"sessions": [s.to_dict() for s in sessions]}
    tmp = paths.registry.with_suffix(f".tmp.{os.getpid()}")
    try:
        tmp.write_text(json.dumps(data, indent=2) + "\n")
        tmp.replace(paths.registry)
    except OSError as e:
        # Clean up temp file on failure
        tmp.unlink(missing_ok=True)
        raise CanvasRegistryError(f"Failed to write registry: {e}") from e


def add_session(session: Session, paths: CanvasPaths | None = None) -> None:
    """Add a session to the registry."""
    sessions = load_registry(paths)
    sessions.append(session)
    save_registry(sessions, paths)


def find_session(slug: str, paths: CanvasPaths | None = None) -> Session | None:
    """Find a session by slug. Returns None if not found."""
    sessions = load_registry(paths)
    for s in sessions:
        if s.slug == slug:
            return s
    return None


def update_session(slug: str, paths: CanvasPaths | None = None, **fields) -> Session:
    """Update fields on a session. Returns the updated session.

    Raises CanvasRegistryError if slug not found.
    """
    sessions = load_registry(paths)
    for i, s in enumerate(sessions):
        if s.slug == slug:
            for key, value in fields.items():
                if not hasattr(s, key):
                    raise CanvasRegistryError(f"Session has no field '{key}'")
                setattr(s, key, value)
            save_registry(sessions, paths)
            return sessions[i]
    raise CanvasRegistryError(f"Session '{slug}' not found in registry.")


def remove_session(slug: str, paths: CanvasPaths | None = None) -> None:
    """Remove a session from the registry.

    Raises CanvasRegistryError if slug not found.
    """
    sessions = load_registry(paths)
    original_len = len(sessions)
    sessions = [s for s in sessions if s.slug != slug]
    if len(sessions) == original_len:
        raise CanvasRegistryError(f"Session '{slug}' not found in registry.")
    save_registry(sessions, paths)
