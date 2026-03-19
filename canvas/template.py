"""CLAUDE.md rendering from org template.

Templates are loaded from the user's filesystem (template_base / org / CLAUDE.md.tmpl).
Jinja2 runs unsandboxed since templates are user-controlled local files.
"""

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
    session_path: Path | None = None,
    date: datetime.date | None = None,
    config: dict | None = None,
) -> str:
    """Render a CLAUDE.md file from the org's Jinja2 template.

    Template location: paths.template_base / org / "CLAUDE.md.tmpl"

    Available template variables:
        {{ org }}          - org name
        {{ date }}         - today's date (ISO 8601)
        {{ slug }}         - session slug
        {{ label }}        - session label (empty string if None)
        {{ session_path }} - absolute path to session directory (if provided)
        {{ config }}       - raw config dict (empty dict if not provided)

    If *date* is ``None``, defaults to today.

    Returns rendered string.
    Raises CanvasTemplateError if template missing or has syntax/render errors.
    """
    if paths is None:
        paths = resolve_paths()

    template_path = paths.template_base / org / "CLAUDE.md.tmpl"

    if not template_path.exists():
        raise CanvasTemplateError(
            f"No template found for org '{org}' at {template_path}.\n"
            f"Create it with: mkdir -p {template_path.parent} && touch {template_path}"
        )

    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path.parent), encoding="utf-8"),
            undefined=jinja2.StrictUndefined,
        )
        template = env.get_template(template_path.name)
    except jinja2.TemplateSyntaxError as e:
        raise CanvasTemplateError(
            f"Syntax error in template for org '{org}': {e}"
        ) from e

    try:
        return template.render(
            org=org,
            date=(date or datetime.date.today()).isoformat(),
            slug=slug,
            label=label or "",
            session_path=str(session_path) if session_path else "",
            config=config or {},
        )
    except jinja2.UndefinedError as e:
        raise CanvasTemplateError(
            f"Undefined variable in template for org '{org}': {e}"
        ) from e
    except jinja2.TemplateError as e:
        raise CanvasTemplateError(
            f"Template error for org '{org}': {e}"
        ) from e
