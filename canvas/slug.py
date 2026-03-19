"""Date + random word slug generation (e.g. 2026-03-13-electric-penguin)."""

from __future__ import annotations

import datetime
import random
import re

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


def generate_slug(label: str | None = None, date: datetime.date | None = None) -> str:
    """Generate a dated slug for a new session.

    No label: YYYY-MM-DD-adj-noun (random)
    With label: YYYY-MM-DD-kebab-cased-label

    If *date* is ``None``, defaults to today.
    """
    date_str = (date or datetime.date.today()).isoformat()

    if label is not None:
        kebab = label.lower().strip()
        kebab = re.sub(r"\s+", "-", kebab)
        kebab = re.sub(r"[^a-z0-9-]", "-", kebab)
        kebab = re.sub(r"-+", "-", kebab)
        kebab = kebab.strip("-")
        if not kebab:
            raise ValueError(
                "Label must contain at least one alphanumeric character"
            )
        return f"{date_str}-{kebab}"

    adj = random.choice(_ADJECTIVES)
    noun = random.choice(_NOUNS)
    return f"{date_str}-{adj}-{noun}"
