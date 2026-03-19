# SPDX-FileCopyrightText: 2025 Oakensoul Studios LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for canvas.slug module."""

from __future__ import annotations

import datetime
import re

import pytest

from canvas.exceptions import CanvasSessionError
from canvas.slug import _ADJECTIVES, _NOUNS, generate_slug, validate_label

FIXED_DATE = datetime.date(2025, 7, 15)
FIXED_ISO = FIXED_DATE.isoformat()  # "2025-07-15"


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
        slug = generate_slug(date=FIXED_DATE)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z]+-[a-z]+", slug)

    def test_date_prefix_matches_injected_date(self) -> None:
        slug = generate_slug(date=FIXED_DATE)
        assert slug.startswith(FIXED_ISO)

    def test_defaults_to_today_when_no_date(self) -> None:
        slug = generate_slug()
        today = datetime.date.today().isoformat()
        assert slug.startswith(today)

    def test_multiple_calls_produce_variation(self) -> None:
        slugs = {generate_slug(date=FIXED_DATE) for _ in range(50)}
        assert len(slugs) > 1, "50 calls all produced the same slug"

    def test_words_come_from_word_lists(self) -> None:
        for _ in range(20):
            slug = generate_slug(date=FIXED_DATE)
            parts = slug.split("-", 3)  # date has 3 parts: YYYY-MM-DD
            words = parts[3]  # everything after the date
            adj, noun = words.split("-")
            assert adj in _ADJECTIVES, f"{adj!r} not in _ADJECTIVES"
            assert noun in _NOUNS, f"{noun!r} not in _NOUNS"


class TestGenerateSlugWithLabel:
    def test_label_simple(self) -> None:
        slug = generate_slug("OKR Planning", date=FIXED_DATE)
        assert slug == f"{FIXED_ISO}-okr-planning"

    def test_label_extra_spaces(self) -> None:
        slug = generate_slug("  extra   spaces  ", date=FIXED_DATE)
        assert slug == f"{FIXED_ISO}-extra-spaces"

    def test_label_special_chars_become_boundaries(self) -> None:
        slug = generate_slug("hello!!!world", date=FIXED_DATE)
        assert slug == f"{FIXED_ISO}-hello-world"

    def test_label_mixed_special_chars(self) -> None:
        slug = generate_slug("a!b@c#d", date=FIXED_DATE)
        assert slug == f"{FIXED_ISO}-a-b-c-d"

    def test_label_date_prefix_matches_injected_date(self) -> None:
        slug = generate_slug("hello", date=FIXED_DATE)
        assert slug.startswith(FIXED_ISO)

    def test_label_leading_trailing_hyphens_stripped(self) -> None:
        slug = generate_slug("-hello-", date=FIXED_DATE)
        assert slug == f"{FIXED_ISO}-hello"

    def test_label_consecutive_hyphens_collapsed(self) -> None:
        slug = generate_slug("a---b", date=FIXED_DATE)
        assert slug == f"{FIXED_ISO}-a-b"

    def test_empty_label_raises(self) -> None:
        with pytest.raises(CanvasSessionError, match="alphanumeric"):
            generate_slug("")

    def test_whitespace_only_label_raises(self) -> None:
        with pytest.raises(CanvasSessionError, match="alphanumeric"):
            generate_slug("   ")

    def test_all_punctuation_label_raises(self) -> None:
        with pytest.raises(CanvasSessionError, match="alphanumeric"):
            generate_slug("!@#$%")

    def test_all_hyphens_label_raises(self) -> None:
        with pytest.raises(CanvasSessionError, match="alphanumeric"):
            generate_slug("---")

    def test_unicode_label_stripped(self) -> None:
        slug = generate_slug("café plan", date=FIXED_DATE)
        assert slug == f"{FIXED_ISO}-caf-plan"

    def test_label_truncated_at_60_chars(self) -> None:
        long_label = "a" * 100
        slug = generate_slug(long_label, date=FIXED_DATE)
        # The kebab part (after the date prefix) should be at most 60 chars
        kebab_part = slug[len(FIXED_ISO) + 1 :]
        assert len(kebab_part) <= 60

    def test_label_truncation_strips_trailing_hyphen(self) -> None:
        # Build a label that will have a hyphen at position 60
        # "a-" repeated = positions 0:a 1:- 2:a 3:- ...
        # At position 59 we want a hyphen so truncation at 60 leaves trailing hyphen
        label = "a-" * 40  # 80 chars, kebab will be "a-a-a-a-..."
        slug = generate_slug(label, date=FIXED_DATE)
        kebab_part = slug[len(FIXED_ISO) + 1 :]
        assert len(kebab_part) <= 60
        assert not kebab_part.endswith("-")

    def test_label_exactly_60_chars_not_truncated(self) -> None:
        label = "a" * 60
        slug = generate_slug(label, date=FIXED_DATE)
        kebab_part = slug[len(FIXED_ISO) + 1 :]
        assert kebab_part == "a" * 60


class TestValidateLabel:
    def test_valid_label_does_not_raise(self) -> None:
        validate_label("hello world")  # should not raise

    def test_empty_label_raises(self) -> None:
        with pytest.raises(CanvasSessionError, match="alphanumeric"):
            validate_label("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(CanvasSessionError, match="alphanumeric"):
            validate_label("   ")

    def test_all_punctuation_raises(self) -> None:
        with pytest.raises(CanvasSessionError, match="alphanumeric"):
            validate_label("!@#$%")

    def test_single_alphanumeric_passes(self) -> None:
        validate_label("a")  # should not raise

    def test_mixed_valid_content_passes(self) -> None:
        validate_label("hello 123!")  # should not raise
