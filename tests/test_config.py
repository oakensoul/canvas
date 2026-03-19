"""Tests for canvas.config module."""

import dataclasses
import json
from pathlib import Path

import pytest

from canvas.config import CanvasPaths, load_config, resolve_paths
from canvas.exceptions import CanvasConfigError


class TestResolvePaths:
    """Tests for resolve_paths()."""

    def test_explicit_canvas_home(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Explicit canvas_home param is used directly."""
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        custom = tmp_path / "custom"
        paths = resolve_paths(canvas_home=custom)
        assert paths.home == custom
        assert paths.config == custom / "config"
        assert paths.registry == custom / "registry.json"
        assert paths.sessions_dir == custom / "sessions"

    def test_env_var_fallback(self, canvas_home: Path) -> None:
        """CANVAS_HOME env var is used when no explicit param given."""
        paths = resolve_paths()
        assert paths.home == canvas_home
        assert paths.config == canvas_home / "config"
        assert paths.registry == canvas_home / "registry.json"
        assert paths.sessions_dir == canvas_home / "sessions"

    def test_default_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Falls back to ~/.canvas when no param and no env var."""
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        paths = resolve_paths()
        expected = Path.home() / ".canvas"
        assert paths.home == expected

    def test_explicit_overrides_env_var(self, canvas_home: Path, tmp_path: Path) -> None:
        """Explicit canvas_home takes priority over CANVAS_HOME env var."""
        custom = tmp_path / "override"
        paths = resolve_paths(canvas_home=custom)
        assert paths.home == custom
        assert paths.home != canvas_home

    def test_template_base_is_global(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """template_base always resolves relative to user home, not canvas_home."""
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        paths = resolve_paths(canvas_home=tmp_path)
        assert paths.template_base == Path.home() / ".dotfiles-private" / "canvas" / "orgs"


class TestLoadConfig:
    """Tests for load_config()."""

    def test_happy_path(self, canvas_home: Path) -> None:
        """Valid config file is read and returned as dict."""
        config_data = {"org": "acme", "extra": "value"}
        (canvas_home / "config").write_text(json.dumps(config_data))
        paths = resolve_paths()
        result = load_config(paths)
        assert result == config_data

    def test_missing_file_raises(self, canvas_home: Path) -> None:
        """Missing config file raises CanvasConfigError."""
        paths = resolve_paths()
        with pytest.raises(CanvasConfigError, match="Config not found"):
            load_config(paths)

    def test_malformed_json_raises(self, canvas_home: Path) -> None:
        """Malformed JSON raises CanvasConfigError."""
        (canvas_home / "config").write_text("{not valid json")
        paths = resolve_paths()
        with pytest.raises(CanvasConfigError, match="Malformed config"):
            load_config(paths)

    def test_missing_org_field_raises(self, canvas_home: Path) -> None:
        """Config without 'org' field raises CanvasConfigError."""
        (canvas_home / "config").write_text(json.dumps({"name": "test"}))
        paths = resolve_paths()
        with pytest.raises(CanvasConfigError, match="missing required 'org' field"):
            load_config(paths)

    def test_with_explicit_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """load_config accepts an explicit paths parameter."""
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        home = tmp_path / "explicit"
        home.mkdir()
        config_data = {"org": "explicit-org"}
        (home / "config").write_text(json.dumps(config_data))
        paths = resolve_paths(canvas_home=home)
        result = load_config(paths)
        assert result == config_data


class TestResolvePathsTemplateBase:
    """Tests for template_base resolution in resolve_paths()."""

    def test_explicit_template_base(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        monkeypatch.delenv("CANVAS_TEMPLATE_BASE", raising=False)
        custom = tmp_path / "my-templates"
        paths = resolve_paths(canvas_home=tmp_path, template_base=custom)
        assert paths.template_base == custom

    def test_template_base_env_var(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        env_path = tmp_path / "env-templates"
        monkeypatch.setenv("CANVAS_TEMPLATE_BASE", str(env_path))
        paths = resolve_paths(canvas_home=tmp_path)
        assert paths.template_base == env_path

    def test_explicit_template_base_overrides_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        env_path = tmp_path / "env-templates"
        monkeypatch.setenv("CANVAS_TEMPLATE_BASE", str(env_path))
        explicit = tmp_path / "explicit-templates"
        paths = resolve_paths(canvas_home=tmp_path, template_base=explicit)
        assert paths.template_base == explicit


class TestCanvasPathsFrozen:
    """Tests for CanvasPaths immutability."""

    def test_frozen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CanvasPaths instances are immutable."""
        monkeypatch.delenv("CANVAS_HOME", raising=False)
        paths = resolve_paths(canvas_home=Path("/tmp/test"))
        with pytest.raises(dataclasses.FrozenInstanceError):
            paths.home = Path("/tmp/other")  # type: ignore[misc]
