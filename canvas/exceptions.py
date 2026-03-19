"""Canvas exception hierarchy.

Core modules raise these domain exceptions.
CLI catches and formats them via click.ClickException.
"""


class CanvasError(Exception):
    """Base exception for all canvas errors."""


class CanvasConfigError(CanvasError):
    """Config file missing, malformed, or invalid."""


class CanvasRegistryError(CanvasError):
    """Registry read/write failures."""


class CanvasTemplateError(CanvasError):
    """Template file missing or Jinja2 rendering error."""


class CanvasSessionError(CanvasError):
    """Session operation failures — slug not found, collision, etc."""
