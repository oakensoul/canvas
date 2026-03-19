"""Tests for canvas.template — CLAUDE.md rendering from org templates."""

from __future__ import annotations

import dataclasses
import datetime
from pathlib import Path

import pytest

from canvas.config import CanvasPaths, resolve_paths
from canvas.exceptions import CanvasTemplateError
from canvas.template import render_claude_md

FIXED_DATE = datetime.date(2025, 7, 15)
FIXED_ISO = FIXED_DATE.isoformat()  # "2025-07-15"


def make_paths(canvas_home: Path, template_base: Path) -> CanvasPaths:
    """Create CanvasPaths with a custom template_base for testing."""
    base = resolve_paths(canvas_home)
    return dataclasses.replace(base, template_base=template_base)


@pytest.fixture
def template_env(canvas_home: Path, tmp_path: Path):
    """Set up a template directory and return (paths, template_base)."""
    template_base = tmp_path / "templates"
    template_base.mkdir()
    paths = make_paths(canvas_home, template_base)
    return paths, template_base


class TestRenderClaudeMdHappyPath:
    """Happy-path rendering with all variables substituted."""

    def test_all_variables_substituted(self, template_env):
        paths, template_base = template_env
        org_dir = template_base / "acme"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text(
            "Org: {{ org }}\nDate: {{ date }}\nSlug: {{ slug }}\nLabel: {{ label }}"
        )

        result = render_claude_md(
            org="acme", slug="my-session", label="my label", paths=paths,
            date=FIXED_DATE,
        )

        assert "Org: acme" in result
        assert f"Date: {FIXED_ISO}" in result
        assert "Slug: my-session" in result
        assert "Label: my label" in result


class TestRenderClaudeMdMissingTemplate:
    """Missing template raises CanvasTemplateError."""

    def test_missing_template_raises(self, template_env):
        paths, _ = template_env

        with pytest.raises(CanvasTemplateError, match="No template found"):
            render_claude_md(org="nonexistent", slug="s", paths=paths)

    def test_error_mentions_org_and_path(self, template_env):
        paths, template_base = template_env

        with pytest.raises(CanvasTemplateError) as exc_info:
            render_claude_md(org="missing-org", slug="s", paths=paths)

        msg = str(exc_info.value)
        assert "missing-org" in msg
        assert str(template_base) in msg


class TestRenderClaudeMdMalformedTemplate:
    """Malformed Jinja2 templates raise CanvasTemplateError."""

    def test_syntax_error_raises(self, template_env):
        paths, template_base = template_env
        org_dir = template_base / "broken"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text("{{ unclosed")

        with pytest.raises(CanvasTemplateError, match="Syntax error"):
            render_claude_md(org="broken", slug="s", paths=paths)


class TestRenderClaudeMdLabelNone:
    """label=None should not cause an error."""

    def test_label_none_renders(self, template_env):
        paths, template_base = template_env
        org_dir = template_base / "testorg"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text(
            'Label: {{ label or "unlabeled" }}'
        )

        result = render_claude_md(org="testorg", slug="s", label=None, paths=paths)

        assert "Label: unlabeled" in result

    def test_label_none_default_renders_as_empty(self, template_env):
        paths, template_base = template_env
        org_dir = template_base / "testorg2"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text("Label: [{{ label }}]")

        result = render_claude_md(org="testorg2", slug="s", paths=paths)

        assert "Label: []" in result


class TestRenderClaudeMdSessionPath:
    """session_path variable is available in templates."""

    def test_session_path_rendered(self, template_env):
        paths, template_base = template_env
        org_dir = template_base / "pathorg"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text("Path: {{ session_path }}")

        result = render_claude_md(
            org="pathorg", slug="s", paths=paths,
            session_path=Path("/tmp/sessions/my-session"),
        )

        assert "Path: /tmp/sessions/my-session" in result

    def test_session_path_none_renders_empty(self, template_env):
        paths, template_base = template_env
        org_dir = template_base / "pathorg2"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text("Path: [{{ session_path }}]")

        result = render_claude_md(org="pathorg2", slug="s", paths=paths)

        assert "Path: []" in result


class TestRenderClaudeMdUndefinedVariable:
    """Undefined variables in templates raise CanvasTemplateError."""

    def test_undefined_variable_raises(self, template_env):
        """Simple undefined variable raises CanvasTemplateError with StrictUndefined."""
        paths, template_base = template_env
        org_dir = template_base / "undef"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text("{{ nonexistent_var }}")

        with pytest.raises(CanvasTemplateError, match="Undefined variable"):
            render_claude_md(org="undef", slug="s", paths=paths)

    def test_undefined_variable_attribute_raises(self, template_env):
        """Accessing an attribute on an undefined variable raises CanvasTemplateError."""
        paths, template_base = template_env
        org_dir = template_base / "undef2"
        org_dir.mkdir()
        (org_dir / "CLAUDE.md.tmpl").write_text("{{ nonexistent_var.attr }}")

        with pytest.raises(CanvasTemplateError, match="Undefined variable"):
            render_claude_md(org="undef2", slug="s", paths=paths)


class TestRenderClaudeMdMultipleOrgs:
    """Each org renders its own template content."""

    def test_two_orgs_render_independently(self, template_env):
        paths, template_base = template_env

        for name in ("alpha", "beta"):
            org_dir = template_base / name
            org_dir.mkdir()
            (org_dir / "CLAUDE.md.tmpl").write_text(
                f"Welcome to {name}! Org: {{{{ org }}}}"
            )

        result_alpha = render_claude_md(org="alpha", slug="s1", paths=paths)
        result_beta = render_claude_md(org="beta", slug="s2", paths=paths)

        assert "Welcome to alpha!" in result_alpha
        assert "Org: alpha" in result_alpha
        assert "Welcome to beta!" in result_beta
        assert "Org: beta" in result_beta
