# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for canvas.core session management functions."""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from canvas.config import resolve_paths
from canvas.core import archive_session, list_sessions, nuke_session, rename_session
from canvas.exceptions import CanvasRegistryError, CanvasSessionError
from canvas.models import Session, SessionStatus
from canvas.registry import add_session, load_registry


@pytest.fixture
def paths(canvas_home: Path):
    """Resolve CanvasPaths using the test canvas_home."""
    return resolve_paths(canvas_home=canvas_home)


@pytest.fixture
def populated_registry(paths):
    """Pre-populate registry with a mix of sessions."""
    sessions = [
        Session(
            slug="alpha",
            org="acme",
            created=datetime.date(2026, 1, 1),
            status=SessionStatus.ACTIVE,
            label="Alpha Session",
        ),
        Session(
            slug="beta",
            org="acme",
            created=datetime.date(2026, 1, 15),
            status=SessionStatus.ARCHIVED,
            label="Beta Session",
            archived_at=datetime.date(2026, 2, 1),
        ),
        Session(
            slug="gamma",
            org="globex",
            created=datetime.date(2026, 2, 1),
            status=SessionStatus.ACTIVE,
            label="Gamma Session",
        ),
        Session(
            slug="delta",
            org="globex",
            created=datetime.date(2026, 3, 1),
            status=SessionStatus.ARCHIVED,
            label=None,
            archived_at=datetime.date(2026, 3, 10),
        ),
    ]
    for s in sessions:
        add_session(s, paths)
    # Create session directories for alpha and gamma
    (paths.sessions_dir / "alpha").mkdir()
    (paths.sessions_dir / "gamma").mkdir()
    return sessions


# ── list_sessions ──


class TestListSessions:
    def test_no_filter(self, paths, populated_registry):
        result = list_sessions(paths=paths)
        assert len(result) == 4

    def test_filter_by_status_active(self, paths, populated_registry):
        result = list_sessions(status="active", paths=paths)
        assert len(result) == 2
        assert all(s.status == SessionStatus.ACTIVE for s in result)

    def test_filter_by_status_archived(self, paths, populated_registry):
        result = list_sessions(status="archived", paths=paths)
        assert len(result) == 2
        assert all(s.status == SessionStatus.ARCHIVED for s in result)

    def test_filter_by_org(self, paths, populated_registry):
        result = list_sessions(org="acme", paths=paths)
        assert len(result) == 2
        assert all(s.org == "acme" for s in result)

    def test_filter_by_both(self, paths, populated_registry):
        result = list_sessions(status="active", org="globex", paths=paths)
        assert len(result) == 1
        assert result[0].slug == "gamma"

    def test_empty_registry(self, paths):
        result = list_sessions(paths=paths)
        assert result == []

    def test_filter_no_matches(self, paths, populated_registry):
        result = list_sessions(status="active", org="nonexistent", paths=paths)
        assert result == []

    def test_invalid_status_raises(self, paths, populated_registry):
        with pytest.raises(CanvasSessionError, match="Invalid status"):
            list_sessions(status="bogus", paths=paths)

    def test_filter_by_status_enum_directly(self, paths, populated_registry):
        """Passing SessionStatus enum directly works (enum-passthrough path)."""
        result = list_sessions(status=SessionStatus.ACTIVE, paths=paths)
        assert len(result) == 2
        assert all(s.status == SessionStatus.ACTIVE for s in result)


# ── archive_session ──


class TestArchiveSession:
    def test_happy_path(self, paths, populated_registry):
        fixed_date = datetime.date(2026, 6, 15)
        result = archive_session("alpha", paths=paths, date=fixed_date)
        assert result.status == SessionStatus.ARCHIVED
        assert result.archived_at == fixed_date
        assert result.slug == "alpha"
        # Verify persisted
        sessions = load_registry(paths)
        alpha = next(s for s in sessions if s.slug == "alpha")
        assert alpha.status == SessionStatus.ARCHIVED
        assert alpha.archived_at == fixed_date

    def test_already_archived_is_idempotent(self, paths, populated_registry):
        result = archive_session("beta", paths=paths)
        assert result.status == SessionStatus.ARCHIVED
        # Original archived_at preserved (not overwritten with today)
        assert result.archived_at == datetime.date(2026, 2, 1)

    def test_not_found(self, paths, populated_registry):
        with pytest.raises(CanvasSessionError, match="not found"):
            archive_session("nonexistent", paths=paths)

    def test_directory_preserved(self, paths, populated_registry):
        session_dir = paths.sessions_dir / "alpha"
        assert session_dir.exists()
        archive_session("alpha", paths=paths)
        assert session_dir.exists()

    def test_generic_exception_wrapped(self, paths, populated_registry):
        """Non-CanvasError exceptions are wrapped in CanvasSessionError."""
        with (
            patch("canvas.core.update_session", side_effect=RuntimeError("disk full")),
            pytest.raises(CanvasSessionError, match="Failed to archive session"),
        ):
            archive_session("alpha", paths=paths)

    def test_canvas_error_reraised_directly(self, paths, populated_registry):
        """CanvasError subclasses are re-raised without wrapping."""
        with (
            patch("canvas.core.update_session", side_effect=CanvasRegistryError("corrupt")),
            pytest.raises(CanvasRegistryError, match="corrupt"),
        ):
            archive_session("alpha", paths=paths)


# ── nuke_session ──


class TestNukeSession:
    def test_happy_path(self, paths, populated_registry):
        session_dir = paths.sessions_dir / "alpha"
        assert session_dir.exists()
        nuke_session("alpha", paths=paths)
        assert not session_dir.exists()
        sessions = load_registry(paths)
        assert not any(s.slug == "alpha" for s in sessions)

    def test_missing_dir_still_cleans_registry(self, paths, populated_registry):
        # beta has no directory but is in the registry
        assert not (paths.sessions_dir / "beta").exists()
        nuke_session("beta", paths=paths)
        sessions = load_registry(paths)
        assert not any(s.slug == "beta" for s in sessions)

    def test_not_found(self, paths, populated_registry):
        with pytest.raises(CanvasSessionError, match="not found"):
            nuke_session("nonexistent", paths=paths)

    def test_rmtree_oserror_raises_session_error(self, paths, populated_registry):
        """OSError during rmtree is wrapped in CanvasSessionError."""
        with (
            patch("canvas.core.shutil.rmtree", side_effect=OSError("Permission denied")),
            pytest.raises(CanvasSessionError, match="Failed to remove session directory"),
        ):
            nuke_session("alpha", paths=paths)


# ── rename_session ──


class TestRenameSession:
    def test_happy_path(self, paths, populated_registry):
        result = rename_session("alpha", "New Alpha Label", paths=paths)
        assert result.label == "New Alpha Label"
        assert result.slug == "alpha"
        # Verify persisted
        sessions = load_registry(paths)
        alpha = next(s for s in sessions if s.slug == "alpha")
        assert alpha.label == "New Alpha Label"

    def test_not_found(self, paths, populated_registry):
        with pytest.raises(CanvasSessionError, match="not found"):
            rename_session("nonexistent", "Whatever", paths=paths)

    def test_slug_unchanged(self, paths, populated_registry):
        result = rename_session("gamma", "Renamed Gamma", paths=paths)
        assert result.slug == "gamma"
        assert result.org == "globex"
