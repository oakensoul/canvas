import dataclasses
import json

import pytest
from pathlib import Path

from canvas.config import CanvasPaths, resolve_paths


@pytest.fixture
def canvas_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up isolated canvas directory structure for testing."""
    home = tmp_path / ".canvas"
    home.mkdir()
    sessions = home / "sessions"
    sessions.mkdir()
    monkeypatch.setenv("CANVAS_HOME", str(home))
    monkeypatch.delenv("CANVAS_TEMPLATE_BASE", raising=False)
    return home


def setup_config(canvas_home: Path, org: str = "acme") -> None:
    """Write a valid config file."""
    (canvas_home / "config.json").write_text(json.dumps({"org": org}), encoding="utf-8")


def setup_template(template_base: Path, org: str = "acme") -> None:
    """Write a minimal CLAUDE.md template."""
    org_dir = template_base / org
    org_dir.mkdir(parents=True, exist_ok=True)
    (org_dir / "CLAUDE.md.tmpl").write_text(
        "# {{ org }} / {{ slug }}\nLabel: {{ label }}\nDate: {{ date }}",
        encoding="utf-8",
    )


def make_paths(canvas_home: Path, template_base: Path) -> CanvasPaths:
    """Create CanvasPaths with a custom template_base for testing."""
    base = resolve_paths(canvas_home)
    return dataclasses.replace(base, template_base=template_base)
