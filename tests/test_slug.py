"""Tests for canvas.slug module."""

from __future__ import annotations

import datetime
import re

import pytest

from canvas.slug import _ADJECTIVES, _NOUNS, generate_slug


class TestWordLists:
    def test_adjectives_minimum_count(self) -> None:
        assert len(_ADJECTIVES) >= 80

    def test_nouns_minimum_count(self) -> None:
        assert len(_NOUNS) >= 80

    def test_no_overlap_between_lists(self) -> None:
        overlap = set(_ADJECTIVES) & set(_NOUNS)
        assert overlap == set(), f"Words in both lists: {overlap}"

    def test_all_adjectives_lowercase_alpha(self) -> None:
        for word in _ADJECTIVES:
            assert re.fullmatch(r"[a-z]+", word), f"Bad adjective: {word!r}"

    def test_all_nouns_lowercase_alpha(self) -> None:
        for word in _NOUNS:
            assert re.fullmatch(r"[a-z]+", word), f"Bad noun: {word!r}"


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

    def test_words_come_from_word_lists(self) -> None:
        for _ in range(20):
            slug = generate_slug()
            parts = slug.split("-", 3)  # date has 3 parts: YYYY-MM-DD
            words = parts[3]  # everything after the date
            adj, noun = words.split("-")
            assert adj in _ADJECTIVES, f"{adj!r} not in _ADJECTIVES"
            assert noun in _NOUNS, f"{noun!r} not in _NOUNS"


class TestGenerateSlugWithLabel:
    def test_label_simple(self) -> None:
        slug = generate_slug("OKR Planning")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-okr-planning"

    def test_label_extra_spaces(self) -> None:
        slug = generate_slug("  extra   spaces  ")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-extra-spaces"

    def test_label_special_chars_become_boundaries(self) -> None:
        slug = generate_slug("hello!!!world")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-hello-world"

    def test_label_mixed_special_chars(self) -> None:
        slug = generate_slug("a!b@c#d")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-a-b-c-d"

    def test_label_date_prefix_is_today(self) -> None:
        slug = generate_slug("hello")
        today = datetime.date.today().isoformat()
        assert slug.startswith(today)

    def test_label_leading_trailing_hyphens_stripped(self) -> None:
        slug = generate_slug("-hello-")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-hello"

    def test_label_consecutive_hyphens_collapsed(self) -> None:
        slug = generate_slug("a---b")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-a-b"

    def test_empty_label_raises(self) -> None:
        with pytest.raises(ValueError, match="alphanumeric"):
            generate_slug("")

    def test_whitespace_only_label_raises(self) -> None:
        with pytest.raises(ValueError, match="alphanumeric"):
            generate_slug("   ")

    def test_all_punctuation_label_raises(self) -> None:
        with pytest.raises(ValueError, match="alphanumeric"):
            generate_slug("!@#$%")

    def test_all_hyphens_label_raises(self) -> None:
        with pytest.raises(ValueError, match="alphanumeric"):
            generate_slug("---")

    def test_unicode_label_stripped(self) -> None:
        slug = generate_slug("café plan")
        today = datetime.date.today().isoformat()
        assert slug == f"{today}-caf-plan"
