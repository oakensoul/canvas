"""Tests for canvas.models — Session dataclass and SessionStatus."""

import pytest

from canvas.models import Session, SessionStatus


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
            created="2026-03-18",
            status=SessionStatus.ACTIVE,
        )
        assert s.slug == "my-session"
        assert s.org == "acme"
        assert s.created == "2026-03-18"
        assert s.status == SessionStatus.ACTIVE

    def test_label_defaults_to_none(self):
        s = Session(
            slug="test", org="acme", created="2026-01-01", status=SessionStatus.ACTIVE
        )
        assert s.label is None

    def test_label_can_be_set(self):
        s = Session(
            slug="test",
            org="acme",
            created="2026-01-01",
            status=SessionStatus.ACTIVE,
            label="My Label",
        )
        assert s.label == "My Label"

    def test_to_dict(self):
        s = Session(
            slug="my-session",
            org="acme",
            created="2026-03-18",
            status=SessionStatus.ACTIVE,
            label="test label",
        )
        d = s.to_dict()
        assert d == {
            "slug": "my-session",
            "org": "acme",
            "created": "2026-03-18",
            "label": "test label",
            "status": "active",
        }

    def test_to_dict_label_none(self):
        s = Session(
            slug="s", org="o", created="2026-01-01", status=SessionStatus.ARCHIVED
        )
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
        assert s.created == "2026-03-18"
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

    def test_from_dict_extra_unknown_fields_ignored(self):
        data = {
            "slug": "s",
            "org": "o",
            "created": "2026-01-01",
            "status": "active",
            "label": None,
            "unknown_field": "should be ignored",
        }
        s = Session.from_dict(data)
        assert s.slug == "s"
        assert not hasattr(s, "unknown_field")

    def test_round_trip(self):
        """Session -> to_dict -> from_dict produces equal session."""
        original = Session(
            slug="round-trip",
            org="acme",
            created="2026-06-15",
            status=SessionStatus.ACTIVE,
            label="roundtrip test",
        )
        reconstructed = Session.from_dict(original.to_dict())
        assert reconstructed == original
