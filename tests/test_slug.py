"""Tests for canvas.slug module."""

from __future__ import annotations

import datetime
import re

from canvas.slug import _ADJECTIVES, _NOUNS, generate_slug


class TestWordLists:
    def test_adjectives_minimum_count(self) -> None:
        assert len(_ADJECTIVES) >= 80

    def test_nouns_minimum_count(self) -> None:
        assert len(_NOUNS) >= 80


class TestGenerateSlugNoLabel:
    def test_format_matches_pattern(self) -> None:
        slug = generate_slug()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z]+-[a-z]+", slug)

    def test_date_prefix_is_today(self) -> None:
        slug = generate_slug()
        today = datetime.date.today().isoformat()
        assert slug.startswith(today)

    def test_multiple_calls_produce_variation(self) -> None:
        slugs = {generate_slug() for _ in range(50)}
        assert len(slugs) > 1, "50 calls all produced the same slug"


class TestGenerateSlugWithLabel:
    def test_label_simple(self) -> None:
        slug = generate_slug("OKR Planning")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-okr-planning"

    def test_label_extra_spaces(self) -> None:
        slug = generate_slug("  extra   spaces  ")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-extra-spaces"

    def test_label_special_chars(self) -> None:
        slug = generate_slug("special!@#chars")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-specialchars"

    def test_label_date_prefix_is_today(self) -> None:
        slug = generate_slug("hello")
        today = datetime.date.today().isoformat()
        assert slug.startswith(today)
