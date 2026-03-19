# SPDX-FileCopyrightText: 2025 Robert Gunnar Johnson Jr.
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for canvas.models — Session dataclass and SessionStatus."""

import dataclasses
import datetime

import pytest

from canvas.models import Session, SessionStatus

_DATE = datetime.date(2026, 3, 18)
_DATE2 = datetime.date(2026, 1, 1)


class TestSessionStatus:
    def test_is_str_enum(self):
        """SessionStatus values can be used as plain strings."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.ARCHIVED == "archived"

    def test_str_conversion(self):
        assert str(SessionStatus.ACTIVE) == "active"
        assert str(SessionStatus.ARCHIVED) == "archived"

    def test_construct_from_string(self):
        assert SessionStatus("active") is SessionStatus.ACTIVE
        assert SessionStatus("archived") is SessionStatus.ARCHIVED

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            SessionStatus("deleted")


class TestSession:
    def test_creation_and_field_access(self):
        s = Session(
            slug="my-session",
            org="acme",
            created=_DATE,
            status=SessionStatus.ACTIVE,
        )
        assert s.slug == "my-session"
        assert s.org == "acme"
        assert s.created == _DATE
        assert s.status == SessionStatus.ACTIVE

    def test_label_defaults_to_none(self):
        s = Session(slug="test", org="acme", created=_DATE2, status=SessionStatus.ACTIVE)
        assert s.label is None

    def test_label_can_be_set(self):
        s = Session(
            slug="test",
            org="acme",
            created=_DATE2,
            status=SessionStatus.ACTIVE,
            label="My Label",
        )
        assert s.label == "My Label"

    def test_frozen(self):
        s = Session(slug="s", org="o", created=_DATE, status=SessionStatus.ACTIVE)
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.slug = "other"  # type: ignore[misc]

    def test_to_dict(self):
        s = Session(
            slug="my-session",
            org="acme",
            created=_DATE,
            status=SessionStatus.ACTIVE,
            label="test label",
        )
        d = s.to_dict()
        assert d == {
            "slug": "my-session",
            "org": "acme",
            "created": "2026-03-18",
            "label": "test label",
            "archived_at": None,
            "status": "active",
        }

    def test_to_dict_label_none(self):
        s = Session(slug="s", org="o", created=_DATE2, status=SessionStatus.ARCHIVED)
        d = s.to_dict()
        assert d["label"] is None

    def test_from_dict_happy_path(self):
        data = {
            "slug": "my-session",
            "org": "acme",
            "created": "2026-03-18",
            "status": "active",
            "label": "hello",
        }
        s = Session.from_dict(data)
        assert s.slug == "my-session"
        assert s.org == "acme"
        assert s.created == _DATE
        assert s.status == SessionStatus.ACTIVE
        assert s.label == "hello"

    def test_from_dict_without_label(self):
        data = {
            "slug": "s",
            "org": "o",
            "created": "2026-01-01",
            "status": "archived",
        }
        s = Session.from_dict(data)
        assert s.label is None

    def test_from_dict_invalid_date(self):
        data = {
            "slug": "s",
            "org": "o",
            "created": "not-a-date",
            "status": "active",
        }
        with pytest.raises(ValueError, match="Invalid 'created' date"):
            Session.from_dict(data)

    def test_from_dict_missing_created(self):
        data = {"slug": "s", "org": "o", "status": "active"}
        with pytest.raises(ValueError, match="Missing required field 'created'"):
            Session.from_dict(data)

    def test_from_dict_invalid_status(self):
        data = {
            "slug": "s",
            "org": "o",
            "created": "2026-01-01",
            "status": "deleted",
        }
        with pytest.raises(ValueError):
            Session.from_dict(data)

    def test_from_dict_missing_slug(self):
        data = {"org": "o", "created": "2026-01-01", "status": "active"}
        with pytest.raises(ValueError, match="Missing required field 'slug'"):
            Session.from_dict(data)

    def test_from_dict_missing_org(self):
        data = {"slug": "s", "created": "2026-01-01", "status": "active"}
        with pytest.raises(ValueError, match="Missing required field 'org'"):
            Session.from_dict(data)

    def test_from_dict_extra_unknown_fields_preserved(self):
        data = {
            "slug": "s",
            "org": "o",
            "created": "2026-01-01",
            "status": "active",
            "label": None,
            "unknown_field": "should be preserved",
            "another": 42,
        }
        s = Session.from_dict(data)
        assert s.slug == "s"
        assert s.extra == {"unknown_field": "should be preserved", "another": 42}

    def test_extra_fields_round_trip(self):
        """Unknown fields survive a to_dict -> from_dict round trip."""
        data = {
            "slug": "s",
            "org": "o",
            "created": "2026-01-01",
            "status": "active",
            "custom_key": "custom_value",
        }
        s = Session.from_dict(data)
        d = s.to_dict()
        assert d["custom_key"] == "custom_value"
        s2 = Session.from_dict(d)
        assert s2.extra == {"custom_key": "custom_value"}
        assert s2 == s

    def test_known_fields_take_precedence_over_extra(self):
        """Known fields overwrite any conflicting extra keys in to_dict."""
        s = Session(
            slug="s",
            org="o",
            created=_DATE,
            status=SessionStatus.ACTIVE,
            extra={"slug": "should-be-overwritten"},
        )
        d = s.to_dict()
        assert d["slug"] == "s"

    def test_extra_defaults_to_empty_dict(self):
        s = Session(slug="s", org="o", created=_DATE, status=SessionStatus.ACTIVE)
        assert s.extra == {}

    def test_equality(self):
        a = Session(slug="s", org="o", created=_DATE, status=SessionStatus.ACTIVE)
        b = Session(slug="s", org="o", created=_DATE, status=SessionStatus.ACTIVE)
        assert a == b

    def test_inequality(self):
        a = Session(slug="s", org="o", created=_DATE, status=SessionStatus.ACTIVE)
        b = Session(slug="s", org="o", created=_DATE, status=SessionStatus.ARCHIVED)
        assert a != b

    def test_round_trip(self):
        """Session -> to_dict -> from_dict produces equal session."""
        original = Session(
            slug="round-trip",
            org="acme",
            created=datetime.date(2026, 6, 15),
            status=SessionStatus.ACTIVE,
            label="roundtrip test",
        )
        reconstructed = Session.from_dict(original.to_dict())
        assert reconstructed == original

    def test_from_dict_slug_not_string_raises(self):
        data = {"slug": 123, "org": "o", "created": "2026-01-01", "status": "active"}
        with pytest.raises(ValueError, match="Field 'slug' must be a string, got int"):
            Session.from_dict(data)

    def test_from_dict_slug_none_raises(self):
        data = {"slug": None, "org": "o", "created": "2026-01-01", "status": "active"}
        with pytest.raises(ValueError, match="Field 'slug' must be a string, got NoneType"):
            Session.from_dict(data)

    def test_from_dict_org_not_string_raises(self):
        data = {"slug": "s", "org": 456, "created": "2026-01-01", "status": "active"}
        with pytest.raises(ValueError, match="Field 'org' must be a string, got int"):
            Session.from_dict(data)

    def test_from_dict_org_none_raises(self):
        data = {"slug": "s", "org": None, "created": "2026-01-01", "status": "active"}
        with pytest.raises(ValueError, match="Field 'org' must be a string, got NoneType"):
            Session.from_dict(data)

    def test_from_dict_invalid_archived_at(self):
        data = {
            "slug": "test",
            "org": "acme",
            "created": "2026-01-01",
            "status": "active",
            "archived_at": "not-a-date",
        }
        with pytest.raises(ValueError, match="archived_at"):
            Session.from_dict(data)

    def test_round_trip_with_archived_at(self):
        session = Session(
            slug="2026-01-15-archived-test",
            org="acme",
            created=datetime.date(2026, 1, 15),
            status=SessionStatus.ARCHIVED,
            label="Archived Test",
            archived_at=datetime.date(2026, 2, 1),
        )
        d = session.to_dict()
        restored = Session.from_dict(d)
        assert restored == session
        assert restored.archived_at == datetime.date(2026, 2, 1)
