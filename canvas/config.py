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

    home: Path              # ~/.canvas (or CANVAS_HOME)
    config: Path            # home / "config"
    registry: Path          # home / "registry.json"
    sessions_dir: Path      # home / "sessions"
    template_base: Path     # ~/.dotfiles-private/canvas/orgs


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
        if env:
            canvas_home = Path(env)
        else:
            canvas_home = Path.home() / ".canvas"

    if template_base is None:
        env = os.environ.get("CANVAS_TEMPLATE_BASE")
        if env:
            template_base = Path(env)
        else:
            template_base = Path.home() / ".dotfiles-private" / "canvas" / "orgs"

    return CanvasPaths(
        home=canvas_home,
        config=canvas_home / "config",
        registry=canvas_home / "registry.json",
        sessions_dir=canvas_home / "sessions",
        template_base=template_base,
    )


def load_config(paths: CanvasPaths | None = None) -> dict:
    """Load canvas config from disk.

    Returns dict with at minimum {"org": "..."}.
    Raises CanvasConfigError if file missing or malformed.
    """
    if paths is None:
        paths = resolve_paths()

    if not paths.config.exists():
        raise CanvasConfigError(
            f"Config not found at {paths.config}. Run `loadout init` to set up."
        )

    try:
        data = json.loads(paths.config.read_text())
    except json.JSONDecodeError as e:
        raise CanvasConfigError(
            f"Malformed config at {paths.config}: {e}"
        ) from e

    if "org" not in data:
        raise CanvasConfigError(
            f"Config at {paths.config} missing required 'org' field."
        )

    return data
