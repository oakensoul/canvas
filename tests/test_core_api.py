# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for reactivate_session, stale_sessions, and public API imports."""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from canvas.config import resolve_paths
from canvas.core import reactivate_session, stale_sessions
from canvas.exceptions import CanvasRegistryError, CanvasSessionError
from canvas.models import Session, SessionStatus
from canvas.registry import add_session, load_registry


@pytest.fixture
def paths(canvas_home: Path):
    """Resolve CanvasPaths using the test canvas_home."""
    return resolve_paths(canvas_home=canvas_home)


@pytest.fixture
def populated_registry(paths):
    """Pre-populate registry with a mix of sessions for testing."""
    sessions = [
        Session(
            slug="active-recent",
            org="acme",
            created=datetime.date(2026, 3, 1),
            status=SessionStatus.ACTIVE,
            label="Recent Active",
        ),
        Session(
            slug="active-old",
            org="acme",
            created=datetime.date(2026, 1, 1),
            status=SessionStatus.ACTIVE,
            label="Old Active",
        ),
        Session(
            slug="archived-old",
            org="acme",
            created=datetime.date(2025, 12, 1),
            status=SessionStatus.ARCHIVED,
            label="Old Archived",
            archived_at=datetime.date(2026, 1, 15),
        ),
        Session(
            slug="archived-recent",
            org="globex",
            created=datetime.date(2026, 2, 20),
            status=SessionStatus.ARCHIVED,
            label="Recent Archived",
            archived_at=datetime.date(2026, 3, 1),
        ),
    ]
    for s in sessions:
        add_session(s, paths)
    return sessions


# ── reactivate_session ──


class TestReactivateSession:
    def test_happy_path(self, paths, populated_registry):
        """Archived session becomes active, archived_at cleared."""
        result = reactivate_session("archived-old", paths=paths)
        assert result.status == SessionStatus.ACTIVE
        assert result.archived_at is None
        assert result.slug == "archived-old"
        # Verify persisted
        sessions = load_registry(paths)
        found = next(s for s in sessions if s.slug == "archived-old")
        assert found.status == SessionStatus.ACTIVE
        assert found.archived_at is None

    def test_not_found(self, paths, populated_registry):
        """Raises CanvasSessionError if session not found."""
        with pytest.raises(CanvasSessionError, match="not found"):
            reactivate_session("nonexistent", paths=paths)

    def test_already_active_is_idempotent(self, paths, populated_registry):
        """Already active session returned unchanged."""
        result = reactivate_session("active-recent", paths=paths)
        assert result.status == SessionStatus.ACTIVE
        assert result.slug == "active-recent"
        assert result.label == "Recent Active"

    def test_reactivate_recently_archived(self, paths, populated_registry):
        """Recently archived session can be reactivated."""
        result = reactivate_session("archived-recent", paths=paths)
        assert result.status == SessionStatus.ACTIVE
        assert result.archived_at is None
        assert result.org == "globex"

    def test_not_found_empty_registry(self, paths):
        """Raises CanvasSessionError on empty registry."""
        with pytest.raises(CanvasSessionError, match="not found"):
            reactivate_session("anything", paths=paths)

    def test_generic_exception_wrapped(self, paths, populated_registry):
        """Non-CanvasError exceptions are wrapped in CanvasSessionError."""
        with (
            patch("canvas.core.update_session", side_effect=RuntimeError("disk full")),
            pytest.raises(CanvasSessionError, match="Failed to reactivate session"),
        ):
            reactivate_session("archived-old", paths=paths)

    def test_canvas_error_reraised_directly(self, paths, populated_registry):
        """CanvasError subclasses are re-raised without wrapping."""
        with (
            patch("canvas.core.update_session", side_effect=CanvasRegistryError("corrupt")),
            pytest.raises(CanvasRegistryError, match="corrupt"),
        ):
            reactivate_session("archived-old", paths=paths)


# ── stale_sessions ──


class TestStaleSessions:
    def test_sessions_older_than_30_days(self, paths, populated_registry):
        """Sessions older than 30 days returned with default days."""
        today = datetime.date(2026, 3, 15)
        result = stale_sessions(paths=paths, today=today)
        slugs = [s.slug for s in result]
        assert "active-old" in slugs  # created 2026-01-01, 73 days old
        assert "active-recent" not in slugs  # created 2026-03-01, 14 days old

    def test_recent_sessions_not_returned(self, paths, populated_registry):
        """Recent sessions should not appear as stale."""
        today = datetime.date(2026, 3, 15)
        result = stale_sessions(paths=paths, today=today)
        slugs = [s.slug for s in result]
        assert "active-recent" not in slugs

    def test_empty_registry(self, paths):
        """Empty registry returns empty list."""
        result = stale_sessions(paths=paths, today=datetime.date(2026, 3, 15))
        assert result == []

    def test_custom_today_parameter(self, paths, populated_registry):
        """Custom today parameter shifts the cutoff."""
        # With today far in the future, all active sessions are stale
        far_future = datetime.date(2027, 6, 1)
        result = stale_sessions(paths=paths, today=far_future)
        slugs = [s.slug for s in result]
        assert "active-old" in slugs
        assert "active-recent" in slugs

    def test_only_active_sessions_considered(self, paths, populated_registry):
        """Archived sessions ignored even if old."""
        today = datetime.date(2026, 3, 15)
        result = stale_sessions(paths=paths, today=today)
        slugs = [s.slug for s in result]
        # archived-old is old but archived — should not appear
        assert "archived-old" not in slugs
        assert "archived-recent" not in slugs

    def test_custom_days_parameter(self, paths, populated_registry):
        """Custom days parameter adjusts the threshold."""
        today = datetime.date(2026, 3, 15)
        # With days=10, active-recent (created 2026-03-01, 14 days ago) is stale
        result = stale_sessions(days=10, paths=paths, today=today)
        slugs = [s.slug for s in result]
        assert "active-recent" in slugs
        assert "active-old" in slugs

    def test_boundary_exactly_n_days(self, paths, populated_registry):
        """Session created exactly N days ago IS stale (created <= cutoff)."""
        # active-old created 2026-01-01; set today so cutoff == 2026-01-01
        # cutoff = 2026-01-31 - 30 days = 2026-01-01
        today = datetime.date(2026, 1, 31)
        result = stale_sessions(days=30, paths=paths, today=today)
        slugs = [s.slug for s in result]
        assert "active-old" in slugs


# ── Public API imports ──


class TestPublicAPIImports:
    def test_import_new_session(self):
        """from canvas import new_session works."""
        from canvas import new_session

        assert callable(new_session)

    def test_import_models(self):
        """from canvas import Session, SessionStatus works."""
        from canvas import Session, SessionStatus

        assert Session is not None
        assert SessionStatus is not None

    def test_all_is_complete(self):
        """All names in __all__ are importable."""
        import canvas

        for name in canvas.__all__:
            assert hasattr(canvas, name), f"canvas.{name} not importable"

    def test_dir_includes_expected_names(self):
        """dir(canvas) includes all expected names."""
        import canvas

        module_dir = dir(canvas)
        expected = [
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
        for name in expected:
            assert name in module_dir, f"{name} not in dir(canvas)"

    def test_import_reactivate_session(self):
        """from canvas import reactivate_session works."""
        from canvas import reactivate_session

        assert callable(reactivate_session)

    def test_import_stale_sessions(self):
        """from canvas import stale_sessions works."""
        from canvas import stale_sessions

        assert callable(stale_sessions)

    def test_import_exceptions(self):
        """from canvas import exception classes works."""
        from canvas import (
            CanvasConfigError,
            CanvasError,
            CanvasRegistryError,
            CanvasSessionError,
            CanvasTemplateError,
        )

        assert issubclass(CanvasConfigError, CanvasError)
        assert issubclass(CanvasRegistryError, CanvasError)
        assert issubclass(CanvasSessionError, CanvasError)
        assert issubclass(CanvasTemplateError, CanvasError)
