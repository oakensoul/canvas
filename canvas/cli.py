# SPDX-FileCopyrightText: 2025 Oakensoul Studios LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click CLI for canvas — commands: new, list, archive, nuke, rename, open."""

import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from canvas import core
from canvas.config import resolve_paths
from canvas.exceptions import CanvasError, CanvasSessionError


@click.group()
def cli() -> None:
    """Manage ephemeral org-aware Claude Code workspaces."""


@cli.command()
@click.argument("label", required=False)
@click.option("--org", default=None, help="Organization (overrides config).")
def new(label: str | None, org: str | None) -> None:
    """Create a new canvas session."""
    try:
        session = core.new_session(label=label, org=org)
        console = Console(stderr=True)
        console.print(Panel(
            f"[bold]{session.slug}[/bold]\n"
            f"org: {session.org}  created: {session.created}",
            title="Canvas Session Created",
        ))
        session_dir = str(resolve_paths().sessions_dir / session.slug)
        os.chdir(session_dir)
        os.execvp("claude", ["claude"])
    except CanvasError as e:
        raise click.ClickException(str(e))


@cli.command("list")
@click.option("--status", type=click.Choice(["active", "archived"]), default=None)
@click.option("--org", default=None)
@click.option("--all", "show_all", is_flag=True, help="Show all sessions (active + archived).")
def list_sessions(status: str | None, org: str | None, show_all: bool) -> None:
    """List canvas sessions."""
    try:
        if status is not None and show_all:
            raise click.UsageError("--status and --all are mutually exclusive.")
        if not show_all and status is None:
            status = "active"
        sessions = core.list_sessions(status=status, org=org)
        console = Console(stderr=True)
        if not sessions:
            console.print("[dim]No sessions found.[/dim]")
            return
        table = Table(title="Canvas Sessions")
        table.add_column("Slug", style="bold")
        table.add_column("Org")
        table.add_column("Created")
        table.add_column("Label")
        table.add_column("Status")
        for s in sessions:
            table.add_row(
                s.slug,
                s.org,
                str(s.created),
                s.label or "",
                str(s.status),
            )
        console.print(table)
    except CanvasError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("slug")
def archive(slug: str) -> None:
    """Archive a canvas session."""
    try:
        session = core.archive_session(slug)
        console = Console(stderr=True)
        console.print(f"Archived [bold]{session.slug}[/bold].")
    except CanvasError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("slug")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def nuke(slug: str, yes: bool) -> None:
    """Permanently destroy a canvas session."""
    try:
        if not yes:
            click.confirm(f"Permanently destroy session '{slug}'?", abort=True)
        core.nuke_session(slug)
        console = Console(stderr=True)
        console.print(f"Nuked [bold]{slug}[/bold].")
    except CanvasError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("slug")
@click.argument("label")
def rename(slug: str, label: str) -> None:
    """Rename a canvas session."""
    try:
        session = core.rename_session(slug, label)
        console = Console(stderr=True)
        console.print(f"Renamed [bold]{session.slug}[/bold] → {session.label}")
    except CanvasError as e:
        raise click.ClickException(str(e))


@cli.command("open")
@click.argument("slug")
def open_session(slug: str) -> None:
    """Re-open an existing canvas session and launch claude."""
    try:
        from canvas.registry import find_session
        session = find_session(slug)
        if session is None:
            raise CanvasSessionError(f"Session '{slug}' not found.")
        session_dir = resolve_paths().sessions_dir / session.slug
        if not session_dir.is_dir():
            raise CanvasSessionError(f"Session directory missing: {session_dir}")
        os.chdir(str(session_dir))
        os.execvp("claude", ["claude"])
    except CanvasError as e:
        raise click.ClickException(str(e))
