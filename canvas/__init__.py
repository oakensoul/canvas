# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Canvas — ephemeral org-aware Claude Code workspace manager."""

from canvas.config import CanvasPaths, resolve_paths
from canvas.core import (
    archive_session,
    list_sessions,
    new_session,
    nuke_session,
    reactivate_session,
    rename_session,
    stale_sessions,
)
from canvas.exceptions import (
    CanvasConfigError,
    CanvasError,
    CanvasRegistryError,
    CanvasSessionError,
    CanvasTemplateError,
)
from canvas.models import Session, SessionStatus

__all__ = [
    "CanvasConfigError",
    "CanvasError",
    "CanvasPaths",
    "CanvasRegistryError",
    "CanvasSessionError",
    "CanvasTemplateError",
    "Session",
    "SessionStatus",
    "archive_session",
    "list_sessions",
    "new_session",
    "nuke_session",
    "reactivate_session",
    "rename_session",
    "resolve_paths",
    "stale_sessions",
]
