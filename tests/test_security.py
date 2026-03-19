# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Security-focused tests — path traversal, directory permissions, symlink safety."""

from __future__ import annotations

import dataclasses
import json
import stat
from pathlib import Path

import pytest

from canvas.config import resolve_paths
from canvas.core import new_session, nuke_session
from canvas.exceptions import CanvasSessionError
from canvas.models import Session, SessionStatus
from canvas.registry import add_session
from canvas.slug import validate_org, validate_slug

# ---------------------------------------------------------------------------
# Org name validation
# ---------------------------------------------------------------------------


class TestValidateOrg:
    """validate_org rejects path-traversal characters."""

    def test_rejects_dot_dot(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_org("../evil")

    def test_rejects_forward_slash(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_org("evil/org")

    def test_rejects_backslash(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_org("evil\\org")

    def test_rejects_null_byte(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_org("evil\x00org")

    def test_accepts_valid_org(self) -> None:
        validate_org("acme")
        validate_org("my-org")
        validate_org("org.name")


# ---------------------------------------------------------------------------
# Slug validation
# ---------------------------------------------------------------------------


class TestValidateSlug:
    """validate_slug rejects path-traversal characters."""

    def test_rejects_dot_dot(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_slug("2026-01-01-../evil")

    def test_rejects_forward_slash(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_slug("2026-01-01-evil/slug")

    def test_rejects_backslash(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_slug("2026-01-01-evil\\slug")

    def test_rejects_null_byte(self) -> None:
        with pytest.raises(CanvasSessionError, match="invalid characters"):
            validate_slug("2026-01-01-evil\x00slug")

    def test_accepts_valid_slug(self) -> None:
        validate_slug("2026-01-01-my-session")
        validate_slug("2026-03-19-bold-falcon")


# ---------------------------------------------------------------------------
# Session directory permissions
# ---------------------------------------------------------------------------


class TestSessionDirPermissions:
    """new_session creates directories with mode 0o700."""

    def test_session_dir_mode(self, canvas_home: Path, tmp_path: Path) -> None:
        template_base = tmp_path / "templates"
        template_base.mkdir()
        org_dir = template_base / "acme"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text("# {{ org }} / {{ slug }}", encoding="utf-8")
        (canvas_home / "config.json").write_text(json.dumps({"org": "acme"}), encoding="utf-8")
        base = resolve_paths(canvas_home)
        paths = dataclasses.replace(base, template_base=template_base)

        session = new_session(label="perms-test", paths=paths)
        session_dir = paths.sessions_dir / session.slug
        mode = stat.S_IMODE(session_dir.stat().st_mode)
        assert mode == 0o700


# ---------------------------------------------------------------------------
# Symlink safety in nuke_session
# ---------------------------------------------------------------------------


class TestNukeSessionSymlinkSafety:
    """nuke_session refuses to delete directories that resolve outside sessions_dir."""

    def test_rejects_symlink_outside_sessions_dir(self, canvas_home: Path, tmp_path: Path) -> None:
        base = resolve_paths(canvas_home)
        # Create a target directory outside sessions_dir
        outside = tmp_path / "outside-target"
        outside.mkdir()
        (outside / "precious.txt").write_text("do not delete", encoding="utf-8")

        slug = "2026-01-01-symlink-escape"
        # Create a symlink inside sessions_dir pointing outside
        symlink = base.sessions_dir / slug
        symlink.symlink_to(outside)

        # Register the session so nuke_session finds it
        session = Session(
            slug=slug,
            org="acme",
            created=__import__("datetime").date(2026, 1, 1),
            status=SessionStatus.ACTIVE,
        )
        add_session(session, paths=base)

        with pytest.raises(CanvasSessionError, match="resolves outside.*refusing"):
            nuke_session(slug, paths=base)

        # Verify the outside directory was NOT deleted
        assert outside.exists()
        assert (outside / "precious.txt").read_text(encoding="utf-8") == "do not delete"
