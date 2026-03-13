"""Click CLI for canvas — commands: new, list, archive, nuke, rename."""

import click


@click.group()
def cli() -> None:
    """Manage ephemeral org-aware Claude Code workspaces."""


@cli.command()
@click.argument("label", required=False)
def new(label: str | None) -> None:
    """Create a new canvas session."""
    raise NotImplementedError


@cli.command("list")
def list_sessions() -> None:
    """List active canvas sessions."""
    raise NotImplementedError


@cli.command()
@click.argument("slug")
def archive(slug: str) -> None:
    """Archive a canvas session."""
    raise NotImplementedError


@cli.command()
@click.argument("slug")
def nuke(slug: str) -> None:
    """Permanently destroy a canvas session."""
    raise NotImplementedError


@cli.command()
@click.argument("slug")
@click.argument("label")
def rename(slug: str, label: str) -> None:
    """Rename a canvas session."""
    raise NotImplementedError
