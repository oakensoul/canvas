"""Tests for canvas.registry — CRUD operations on the session registry."""

import datetime
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from canvas.config import resolve_paths
from canvas.exceptions import CanvasRegistryError
from canvas.models import Session, SessionStatus
from canvas.registry import (
    add_session,
    find_session,
    load_registry,
    remove_session,
    save_registry,
    update_session,
)

_DATE = datetime.date(2026, 3, 18)


def _make_session(slug: str = "test-session", **overrides) -> Session:
    defaults = {
        "slug": slug,
        "org": "acme",
        "created": _DATE,
        "status": SessionStatus.ACTIVE,
        "label": None,
    }
    defaults.update(overrides)
    return Session(**defaults)


class TestLoadRegistry:
    def test_missing_file_returns_empty(self, canvas_home: Path):
        sessions = load_registry()
        assert sessions == []

    def test_valid_registry(self, canvas_home: Path):
        registry_path = canvas_home / "registry.json"
        data = {
            "sessions": [
                {
                    "slug": "s1",
                    "org": "acme",
                    "created": "2026-01-01",
                    "status": "active",
                    "label": None,
                }
            ]
        }
        registry_path.write_text(json.dumps(data), encoding="utf-8")
        sessions = load_registry()
        assert len(sessions) == 1
        assert sessions[0].slug == "s1"
        assert sessions[0].status == SessionStatus.ACTIVE

    def test_corrupt_json_raises(self, canvas_home: Path):
        registry_path = canvas_home / "registry.json"
        registry_path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(CanvasRegistryError, match="Corrupt registry"):
            load_registry()

    def test_invalid_session_data_raises(self, canvas_home: Path):
        registry_path = canvas_home / "registry.json"
        data = {"sessions": [{"slug": "s", "org": "o", "created": "bad", "status": "active"}]}
        registry_path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(CanvasRegistryError, match="Corrupt registry"):
            load_registry()

    def test_empty_sessions_list(self, canvas_home: Path):
        registry_path = canvas_home / "registry.json"
        registry_path.write_text(json.dumps({"sessions": []}), encoding="utf-8")
        sessions = load_registry()
        assert sessions == []


class TestSaveRegistry:
    def test_writes_valid_json(self, canvas_home: Path):
        session = _make_session()
        save_registry([session])
        registry_path = canvas_home / "registry.json"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["slug"] == "test-session"

    def test_can_load_after_save(self, canvas_home: Path):
        original = _make_session(label="my label")
        save_registry([original])
        loaded = load_registry()
        assert len(loaded) == 1
        assert loaded[0] == original

    def test_no_tmp_files_after_write(self, canvas_home: Path):
        save_registry([_make_session()])
        tmp_files = list(canvas_home.glob("registry.json.tmp.*"))
        assert tmp_files == []

    def test_save_empty_list(self, canvas_home: Path):
        save_registry([])
        data = json.loads((canvas_home / "registry.json").read_text(encoding="utf-8"))
        assert data == {"sessions": []}

    def test_creates_parent_dirs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        nested = tmp_path / "deep" / "nested" / ".canvas"
        monkeypatch.setenv("CANVAS_HOME", str(nested))
        save_registry([_make_session()])
        assert (nested / "registry.json").exists()


class TestCRUDCycle:
    def test_add_and_find(self, canvas_home: Path):
        session = _make_session()
        add_session(session)
        found = find_session("test-session")
        assert found is not None
        assert found.slug == "test-session"

    def test_find_returns_none_for_missing(self, canvas_home: Path):
        assert find_session("nonexistent") is None

    def test_update_session(self, canvas_home: Path):
        add_session(_make_session())
        updated = update_session("test-session", label="new label")
        assert updated.label == "new label"
        # Verify persisted
        found = find_session("test-session")
        assert found.label == "new label"

    def test_update_status(self, canvas_home: Path):
        add_session(_make_session())
        updated = update_session("test-session", status=SessionStatus.ARCHIVED)
        assert updated.status == SessionStatus.ARCHIVED

    def test_update_missing_slug_raises(self, canvas_home: Path):
        with pytest.raises(CanvasRegistryError, match="not found"):
            update_session("nonexistent", label="x")

    def test_update_invalid_field_raises(self, canvas_home: Path):
        add_session(_make_session())
        with pytest.raises(CanvasRegistryError, match="not a mutable session field"):
            update_session("test-session", nonexistent_field="x")

    def test_remove_session(self, canvas_home: Path):
        add_session(_make_session())
        remove_session("test-session")
        assert find_session("test-session") is None

    def test_remove_missing_slug_raises(self, canvas_home: Path):
        with pytest.raises(CanvasRegistryError, match="not found"):
            remove_session("nonexistent")

    def test_add_duplicate_slug_raises(self, canvas_home: Path):
        add_session(_make_session(slug="dup"))
        with pytest.raises(CanvasRegistryError, match="already exists"):
            add_session(_make_session(slug="dup"))

    def test_update_immutable_org_raises(self, canvas_home: Path):
        add_session(_make_session())
        with pytest.raises(CanvasRegistryError, match="not a mutable session field"):
            update_session("test-session", org="new-org")

    def test_update_immutable_created_raises(self, canvas_home: Path):
        add_session(_make_session())
        with pytest.raises(CanvasRegistryError, match="not a mutable session field"):
            update_session("test-session", created="2099-01-01")

    def test_update_invalid_status_raises(self, canvas_home: Path):
        add_session(_make_session())
        with pytest.raises(CanvasRegistryError, match="Invalid status value"):
            update_session("test-session", status="bogus")

    def test_update_status_from_string(self, canvas_home: Path):
        """update_session accepts status as a plain string and coerces to SessionStatus."""
        add_session(_make_session(slug="string-status"))
        updated = update_session("string-status", status="archived")
        assert updated.status == SessionStatus.ARCHIVED
        assert isinstance(updated.status, SessionStatus)

    def test_update_archived_at_from_string(self, canvas_home: Path):
        """update_session coerces string archived_at to datetime.date."""
        session = Session(
            slug="date-coerce",
            org="acme",
            created=datetime.date(2026, 1, 1),
            status=SessionStatus.ACTIVE,
            label="Date Coerce",
        )
        add_session(session)
        updated = update_session("date-coerce", archived_at="2026-04-01")
        assert updated.archived_at == datetime.date(2026, 4, 1)
        assert isinstance(updated.archived_at, datetime.date)

    def test_update_archived_at_invalid_string_raises(self, canvas_home: Path):
        """update_session raises CanvasRegistryError for invalid archived_at string."""
        session = Session(
            slug="bad-date",
            org="acme",
            created=datetime.date(2026, 1, 1),
            status=SessionStatus.ACTIVE,
            label="Bad Date",
        )
        add_session(session)
        with pytest.raises(CanvasRegistryError, match="Invalid archived_at"):
            update_session("bad-date", archived_at="not-a-date")

    def test_full_crud_cycle(self, canvas_home: Path):
        """Add -> find -> update -> remove -> verify removed."""
        session = _make_session(slug="lifecycle")
        add_session(session)

        found = find_session("lifecycle")
        assert found is not None
        assert found.slug == "lifecycle"

        update_session("lifecycle", label="updated")
        found = find_session("lifecycle")
        assert found.label == "updated"

        remove_session("lifecycle")
        assert find_session("lifecycle") is None


class TestSaveRegistryErrors:
    def test_oserror_on_replace_cleans_up_tmp(self, canvas_home: Path):
        """OSError during atomic replace raises CanvasRegistryError and cleans up temp file."""
        with patch("os.replace", side_effect=OSError("permission denied")):
            with pytest.raises(CanvasRegistryError, match="Failed to write registry"):
                save_registry([_make_session()])
        # The temp file should have been cleaned up by the except branch
        tmp_files = list(canvas_home.glob("registry.json.tmp.*"))
        assert tmp_files == []


class TestLoadRegistryEdgeCases:
    def test_missing_sessions_key_returns_empty(self, canvas_home: Path):
        """Valid JSON without a 'sessions' key returns empty list."""
        (canvas_home / "registry.json").write_text('{"version": 1}', encoding="utf-8")
        sessions = load_registry()
        assert sessions == []


class TestExplicitPaths:
    def test_load_registry_with_explicit_paths(self, canvas_home: Path):
        paths = resolve_paths(canvas_home=canvas_home)
        registry_path = canvas_home / "registry.json"
        data = {
            "sessions": [
                {"slug": "s1", "org": "acme", "created": "2026-01-01", "status": "active"}
            ]
        }
        registry_path.write_text(json.dumps(data), encoding="utf-8")
        sessions = load_registry(paths=paths)
        assert len(sessions) == 1
        assert sessions[0].slug == "s1"

    def test_add_and_find_with_explicit_paths(self, canvas_home: Path):
        paths = resolve_paths(canvas_home=canvas_home)
        session = _make_session(slug="explicit")
        add_session(session, paths=paths)
        found = find_session("explicit", paths=paths)
        assert found is not None
        assert found.slug == "explicit"


class TestRoundTrip:
    def test_session_to_dict_json_from_dict(self, canvas_home: Path):
        """Session -> to_dict -> JSON -> from_dict produces equal Session."""
        original = _make_session(label="round trip test")
        json_str = json.dumps(original.to_dict())
        reconstructed = Session.from_dict(json.loads(json_str))
        assert reconstructed == original
