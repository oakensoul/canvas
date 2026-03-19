# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Config and path resolution for canvas."""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

from canvas.exceptions import CanvasConfigError


@dataclasses.dataclass(frozen=True)
class CanvasPaths:
    """Centralized path resolution for all canvas directories and files."""

    home: Path  # ~/.canvas (or CANVAS_HOME)
    config: Path  # home / "config.json"
    registry: Path  # home / "registry.json"
    sessions_dir: Path  # home / "sessions"
    template_base: Path  # ~/.dotfiles-private/canvas/orgs


@dataclasses.dataclass(frozen=True)
class CanvasConfig:
    """Parsed canvas configuration."""

    org: str
    raw: dict[str, object]


def resolve_paths(
    canvas_home: Path | None = None,
    template_base: Path | None = None,
) -> CanvasPaths:
    """Resolve all canvas paths from a root directory.

    Priority for canvas_home: explicit param > CANVAS_HOME env var > ~/.canvas/
    Priority for template_base: explicit param > CANVAS_TEMPLATE_BASE env var > default
    """
    if canvas_home is None:
        env = os.environ.get("CANVAS_HOME")
        canvas_home = Path(env) if env else Path.home() / ".canvas"

    if template_base is None:
        env = os.environ.get("CANVAS_TEMPLATE_BASE")
        template_base = Path(env) if env else Path.home() / ".dotfiles-private" / "canvas" / "orgs"

    return CanvasPaths(
        home=canvas_home,
        config=canvas_home / "config.json",
        registry=canvas_home / "registry.json",
        sessions_dir=canvas_home / "sessions",
        template_base=template_base,
    )


def load_config(paths: CanvasPaths | None = None) -> CanvasConfig:
    """Load canvas config from disk.

    Returns CanvasConfig with at minimum org set.
    Raises CanvasConfigError if file missing or malformed.
    """
    if paths is None:
        paths = resolve_paths()

    # Backward-compat check: legacy config file without .json extension
    legacy_config = paths.home / "config"
    if legacy_config.is_file() and not paths.config.exists():
        raise CanvasConfigError(
            f"Found legacy config file at {legacy_config}. "
            f"Please rename it to config.json: mv {legacy_config} {paths.config}"
        )

    if not paths.config.exists():
        raise CanvasConfigError(
            f"Config not found at {paths.config}.\n"
            f'Create it with: echo \'{{"org": "YOUR_ORG"}}\' > {paths.config}'
        )

    try:
        data = json.loads(paths.config.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CanvasConfigError(f"Malformed config at {paths.config}: {e}") from e

    if "org" not in data:
        raise CanvasConfigError(f"Config at {paths.config} missing required 'org' field.")

    return CanvasConfig(org=data["org"], raw=data)
