"""Tests for canvas.core — new_session orchestration and slug collision retry."""

from __future__ import annotations

import dataclasses
import datetime
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from canvas.config import CanvasPaths, resolve_paths
from canvas.core import new_session
from canvas.exceptions import CanvasConfigError, CanvasSessionError, CanvasTemplateError
from canvas.models import SessionStatus
from canvas.registry import add_session, find_session
from canvas.models import Session


def _setup_config(canvas_home: Path, org: str = "acme") -> None:
    """Write a valid config file."""
    (canvas_home / "config").write_text(json.dumps({"org": org}))


def _setup_template(template_base: Path, org: str = "acme") -> None:
    """Write a minimal CLAUDE.md template."""
    org_dir = template_base / org
    org_dir.mkdir(parents=True, exist_ok=True)
    (org_dir / "CLAUDE.md.tmpl").write_text(
        "# {{ org }} / {{ slug }}\nLabel: {{ label }}\nDate: {{ date }}"
    )


def _make_paths(canvas_home: Path, template_base: Path) -> CanvasPaths:
    """Create CanvasPaths with a custom template_base for testing."""
    base = resolve_paths(canvas_home)
    return dataclasses.replace(base, template_base=template_base)


@pytest.fixture
def full_env(canvas_home: Path, tmp_path: Path):
    """Set up config, template, and return paths for a complete test environment."""
    template_base = tmp_path / "templates"
    template_base.mkdir()
    paths = _make_paths(canvas_home, template_base)
    _setup_config(canvas_home, "acme")
    _setup_template(template_base, "acme")
    return paths


class TestNewSessionEndToEnd:
    """End-to-end: config + template exist -> session created correctly."""

    def test_session_created_with_all_artifacts(self, full_env: CanvasPaths):
        paths = full_env
        session = new_session(paths=paths)

        # Session object returned with correct fields
        assert session.org == "acme"
        assert session.status == SessionStatus.ACTIVE
        assert session.created == datetime.date.today()
        assert session.label is None

        # Directory created
        session_dir = paths.sessions_dir / session.slug
        assert session_dir.is_dir()

        # CLAUDE.md written
        claude_md = (session_dir / "CLAUDE.md").read_text()
        assert "acme" in claude_md
        assert session.slug in claude_md

        # Registry updated
        found = find_session(session.slug, paths=paths)
        assert found is not None
        assert found.slug == session.slug
        assert found.org == "acme"


class TestNewSessionMissingConfig:
    """Missing config raises CanvasConfigError."""

    def test_no_config_raises(self, canvas_home: Path, tmp_path: Path):
        template_base = tmp_path / "templates"
        template_base.mkdir()
        paths = _make_paths(canvas_home, template_base)
        # No config file written

        with pytest.raises(CanvasConfigError, match="Config not found"):
            new_session(paths=paths)


class TestNewSessionMissingTemplate:
    """Missing template raises CanvasTemplateError."""

    def test_no_template_raises(self, canvas_home: Path, tmp_path: Path):
        template_base = tmp_path / "templates"
        template_base.mkdir()
        paths = _make_paths(canvas_home, template_base)
        _setup_config(canvas_home, "acme")
        # No template written

        with pytest.raises(CanvasTemplateError, match="No template found"):
            new_session(paths=paths)


class TestSlugCollisionLabelRegistry:
    """Slug collision (registry) with label raises CanvasSessionError immediately."""

    def test_label_collision_in_registry_raises(self, full_env: CanvasPaths):
        paths = full_env
        # Create a first session with a label
        s1 = new_session(label="my feature", paths=paths)

        # Same label on the same day -> same slug -> collision
        with pytest.raises(CanvasSessionError, match="already exists"):
            new_session(label="my feature", paths=paths)


class TestSlugCollisionLabelDisk:
    """Slug collision (directory on disk but not in registry) raises CanvasSessionError."""

    def test_label_collision_on_disk_raises(self, full_env: CanvasPaths):
        paths = full_env
        # Create a directory that looks like a session slug but isn't in registry
        today = datetime.date.today().isoformat()
        slug = f"{today}-disk-only"
        (paths.sessions_dir / slug).mkdir(parents=True)

        with pytest.raises(CanvasSessionError, match="already exists"):
            new_session(label="disk only", paths=paths)


class TestRandomSlugCollisionRetry:
    """Random slug collision retries succeed when generate_slug eventually returns unique."""

    def test_retry_succeeds_after_collisions(self, full_env: CanvasPaths):
        paths = full_env
        today = datetime.date.today().isoformat()
        colliding_slug = f"{today}-bold-anchor"
        unique_slug = f"{today}-calm-brook"

        # Pre-create the colliding slug directory on disk
        (paths.sessions_dir / colliding_slug).mkdir(parents=True)

        call_count = 0

        def mock_generate_slug(label=None):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return colliding_slug
            return unique_slug

        with patch("canvas.core.generate_slug", side_effect=mock_generate_slug):
            session = new_session(paths=paths)

        assert session.slug == unique_slug
        assert call_count == 4  # 3 collisions + 1 success


class TestRandomSlugExhaustsRetries:
    """Random slug exhausts all retries and raises CanvasSessionError."""

    def test_all_retries_exhausted_raises(self, full_env: CanvasPaths):
        paths = full_env
        today = datetime.date.today().isoformat()
        colliding_slug = f"{today}-bold-anchor"

        # Pre-create the colliding slug directory on disk
        (paths.sessions_dir / colliding_slug).mkdir(parents=True)

        def mock_generate_slug(label=None):
            return colliding_slug  # Always collide

        with patch("canvas.core.generate_slug", side_effect=mock_generate_slug):
            with pytest.raises(CanvasSessionError, match="Failed to generate a unique slug"):
                new_session(paths=paths)


class TestOrgParameterOverride:
    """org parameter overrides config file."""

    def test_explicit_org_overrides_config(self, canvas_home: Path, tmp_path: Path):
        template_base = tmp_path / "templates"
        template_base.mkdir()
        paths = _make_paths(canvas_home, template_base)

        # Config says "acme" but we'll pass "other-org"
        _setup_config(canvas_home, "acme")
        _setup_template(template_base, "other-org")

        session = new_session(org="other-org", paths=paths)

        assert session.org == "other-org"

    def test_explicit_org_skips_config_entirely(self, canvas_home: Path, tmp_path: Path):
        """When org is provided, config file is not required."""
        template_base = tmp_path / "templates"
        template_base.mkdir()
        paths = _make_paths(canvas_home, template_base)

        # No config file at all
        _setup_template(template_base, "direct-org")

        session = new_session(org="direct-org", paths=paths)
        assert session.org == "direct-org"


class TestLabelFlowsThrough:
    """Label flows through to slug and registry."""

    def test_label_in_slug_and_registry(self, full_env: CanvasPaths):
        paths = full_env
        session = new_session(label="My Cool Feature", paths=paths)

        today = datetime.date.today().isoformat()
        assert session.slug == f"{today}-my-cool-feature"
        assert session.label == "My Cool Feature"

        # Verify in registry too
        found = find_session(session.slug, paths=paths)
        assert found is not None
        assert found.label == "My Cool Feature"
