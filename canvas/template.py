"""CLAUDE.md rendering from org template."""

from __future__ import annotations

import datetime
from pathlib import Path

import jinja2

from canvas.config import CanvasPaths, resolve_paths
from canvas.exceptions import CanvasTemplateError


def render_claude_md(
    org: str,
    slug: str,
    label: str | None = None,
    paths: CanvasPaths | None = None,
) -> str:
    """Render a CLAUDE.md file from the org's Jinja2 template.

    Template location: paths.template_base / org / "CLAUDE.md.tmpl"

    Available template variables:
        {{ org }}   - org name
        {{ date }}  - today's date (ISO 8601)
        {{ slug }}  - session slug
        {{ label }} - session label (may be None)

    Returns rendered string.
    Raises CanvasTemplateError if template missing or has syntax errors.
    """
    if paths is None:
        paths = resolve_paths()

    template_path = paths.template_base / org / "CLAUDE.md.tmpl"

    if not template_path.exists():
        raise CanvasTemplateError(
            f"No template found for org '{org}' at {template_path}"
        )

    try:
        template_text = template_path.read_text()
        template = jinja2.Template(template_text)
    except jinja2.TemplateSyntaxError as e:
        raise CanvasTemplateError(
            f"Syntax error in template for org '{org}': {e}"
        ) from e

    return template.render(
        org=org,
        date=datetime.date.today().isoformat(),
        slug=slug,
        label=label,
    )
