# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Date + random word slug generation (e.g. 2026-03-13-electric-penguin)."""

from __future__ import annotations

import datetime
import random
import re

from canvas.exceptions import CanvasSessionError

_PATH_TRAVERSAL_PATTERN = re.compile(r"[/\\]|\.\.|[\x00]")

_ADJECTIVES = (
    "alpine",
    "amber",
    "arctic",
    "azure",
    "bold",
    "brave",
    "bright",
    "brisk",
    "calm",
    "clear",
    "clever",
    "coral",
    "cosmic",
    "crisp",
    "dapper",
    "deep",
    "deft",
    "dusky",
    "eager",
    "early",
    "earthy",
    "electric",
    "fair",
    "firm",
    "focal",
    "fresh",
    "gentle",
    "golden",
    "grand",
    "hardy",
    "hazel",
    "hearty",
    "ivory",
    "jade",
    "keen",
    "kind",
    "lapis",
    "leafy",
    "light",
    "lively",
    "lucid",
    "lunar",
    "mellow",
    "mild",
    "mint",
    "mossy",
    "neat",
    "nimble",
    "noble",
    "oaken",
    "olive",
    "open",
    "outer",
    "placid",
    "polar",
    "prime",
    "quiet",
    "rapid",
    "regal",
    "robust",
    "rustic",
    "sandy",
    "serene",
    "sharp",
    "silver",
    "sleek",
    "solar",
    "steady",
    "still",
    "sturdy",
    "sunny",
    "tidal",
    "topaz",
    "vast",
    "vivid",
    "warm",
    "wide",
    "windy",
    "wise",
    "zonal",
)

_NOUNS = (
    "anchor",
    "atlas",
    "basin",
    "beacon",
    "birch",
    "bridge",
    "brook",
    "canopy",
    "canyon",
    "cedar",
    "cliff",
    "coast",
    "compass",
    "cove",
    "crane",
    "crest",
    "delta",
    "dune",
    "falcon",
    "fern",
    "field",
    "fjord",
    "flint",
    "forge",
    "frost",
    "glade",
    "grove",
    "harbor",
    "haven",
    "hawk",
    "heath",
    "heron",
    "hill",
    "horizon",
    "inlet",
    "isle",
    "jasper",
    "juniper",
    "kite",
    "lagoon",
    "lark",
    "laurel",
    "ledge",
    "linden",
    "lodge",
    "marsh",
    "meadow",
    "mesa",
    "mist",
    "oasis",
    "orchid",
    "otter",
    "pebble",
    "pelican",
    "penguin",
    "pier",
    "pine",
    "pond",
    "prism",
    "quartz",
    "raven",
    "reef",
    "ridge",
    "river",
    "robin",
    "sage",
    "shore",
    "sierra",
    "slate",
    "spruce",
    "stone",
    "summit",
    "thicket",
    "timber",
    "trail",
    "trellis",
    "valley",
    "vista",
    "willow",
    "wren",
)


_LABEL_MAX_LENGTH = 60


def validate_org(org: str) -> None:
    """Validate that an org name contains no path-traversal characters.

    Rejects ``/``, ``\\``, ``..``, and null bytes.
    Raises :class:`~canvas.exceptions.CanvasSessionError` on violation.
    """
    if _PATH_TRAVERSAL_PATTERN.search(org):
        raise CanvasSessionError(f"Org name contains invalid characters: {org!r}")


def validate_slug(slug: str) -> None:
    """Validate that a slug contains no path-traversal characters.

    Rejects ``/``, ``\\``, ``..``, and null bytes.
    Raises :class:`~canvas.exceptions.CanvasSessionError` on violation.
    """
    if _PATH_TRAVERSAL_PATTERN.search(slug):
        raise CanvasSessionError(f"Slug contains invalid characters: {slug!r}")


def _to_kebab(label: str) -> str:
    """Convert a label to kebab-case, stripping non-alphanumeric characters."""
    kebab = label.lower().strip()
    kebab = re.sub(r"\s+", "-", kebab)
    kebab = re.sub(r"[^a-z0-9-]", "-", kebab)
    kebab = re.sub(r"-+", "-", kebab)
    return kebab.strip("-")


def validate_label(label: str) -> None:
    """Validate that a label contains at least one alphanumeric character.

    Raises :class:`~canvas.exceptions.CanvasSessionError` if the label is
    empty, whitespace-only, or all punctuation.
    """
    if not _to_kebab(label):
        raise CanvasSessionError("Label must contain at least one alphanumeric character")


def generate_slug(label: str | None = None, date: datetime.date | None = None) -> str:
    """Generate a dated slug for a new session.

    No label: YYYY-MM-DD-adj-noun (random)
    With label: YYYY-MM-DD-kebab-cased-label

    If *date* is ``None``, defaults to today.
    The kebab-cased label is truncated to 60 characters before stripping
    trailing hyphens.
    """
    date_str = (date or datetime.date.today()).isoformat()

    if label is not None:
        validate_label(label)
        kebab = _to_kebab(label)
        kebab = kebab[:_LABEL_MAX_LENGTH].strip("-")
        return f"{date_str}-{kebab}"

    adj = random.choice(_ADJECTIVES)  # noqa: S311 — not cryptographic
    noun = random.choice(_NOUNS)  # noqa: S311
    return f"{date_str}-{adj}-{noun}"
