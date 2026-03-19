"""Tests for canvas CLI commands."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import click.testing
import pytest

from canvas.cli import cli
from canvas.exceptions import CanvasSessionError
from canvas.models import Session, SessionStatus


def _make_session(
    slug: str = "2026-03-18-test",
    org: str = "acme",
    label: str | None = None,
    status: SessionStatus = SessionStatus.ACTIVE,
) -> Session:
    return Session(
        slug=slug,
        org=org,
        created=datetime.date(2026, 3, 18),
        status=status,
        label=label,
    )


@pytest.fixture
def runner() -> click.testing.CliRunner:
    return click.testing.CliRunner()


# ── canvas new ──────────────────────────────────────────────────────


class TestNew:
    def test_happy_path(self, runner: click.testing.CliRunner, tmp_path):
        session = _make_session()
        session_dir = tmp_path / "sessions" / session.slug
        session_dir.mkdir(parents=True)

        with (
            patch("canvas.cli.core.new_session", return_value=session) as mock_new,
            patch("canvas.cli.resolve_paths") as mock_paths,
            patch("canvas.cli.os.chdir") as mock_chdir,
            patch("canvas.cli.os.execvp") as mock_execvp,
        ):
            mock_paths.return_value = MagicMock(sessions_dir=tmp_path / "sessions")
            result = runner.invoke(cli, ["new"])

        assert result.exit_code == 0
        mock_new.assert_called_once_with(label=None, org=None)
        mock_chdir.assert_called_once_with(str(session_dir))
        mock_execvp.assert_called_once_with("claude", ["claude"])
        assert "Canvas Session Created" in result.stderr

    def test_label_passed_through(self, runner: click.testing.CliRunner, tmp_path):
        session = _make_session(label="my label")
        session_dir = tmp_path / "sessions" / session.slug
        session_dir.mkdir(parents=True)

        with (
            patch("canvas.cli.core.new_session", return_value=session) as mock_new,
            patch("canvas.cli.resolve_paths") as mock_paths,
            patch("canvas.cli.os.chdir"),
            patch("canvas.cli.os.execvp"),
        ):
            mock_paths.return_value = MagicMock(sessions_dir=tmp_path / "sessions")
            result = runner.invoke(cli, ["new", "my label"])

        assert result.exit_code == 0
        mock_new.assert_called_once_with(label="my label", org=None)

    def test_org_passed_through(self, runner: click.testing.CliRunner, tmp_path):
        session = _make_session()
        session_dir = tmp_path / "sessions" / session.slug
        session_dir.mkdir(parents=True)

        with (
            patch("canvas.cli.core.new_session", return_value=session) as mock_new,
            patch("canvas.cli.resolve_paths") as mock_paths,
            patch("canvas.cli.os.chdir"),
            patch("canvas.cli.os.execvp"),
        ):
            mock_paths.return_value = MagicMock(sessions_dir=tmp_path / "sessions")
            result = runner.invoke(cli, ["new", "--org", "myorg"])

        assert result.exit_code == 0
        mock_new.assert_called_once_with(label=None, org="myorg")

    def test_canvas_error_exits_1(self, runner: click.testing.CliRunner):
        with patch(
            "canvas.cli.core.new_session",
            side_effect=CanvasSessionError("boom"),
        ):
            result = runner.invoke(cli, ["new"])

        assert result.exit_code == 1
        assert "boom" in result.stderr


# ── canvas list ─────────────────────────────────────────────────────


class TestList:
    def test_happy_path_with_sessions(self, runner: click.testing.CliRunner):
        sessions = [
            _make_session(slug="2026-03-18-alpha", org="acme", label="alpha"),
            _make_session(slug="2026-03-18-beta", org="acme"),
        ]

        with patch("canvas.cli.core.list_sessions", return_value=sessions) as mock_list:
            result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(status="active", org=None)
        assert "Canvas Sessions" in result.stderr
        assert "2026-03-18-alpha" in result.stderr
        assert "2026-03-18-beta" in result.stderr

    def test_empty_list(self, runner: click.testing.CliRunner):
        with patch("canvas.cli.core.list_sessions", return_value=[]):
            result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "No sessions found" in result.stderr

    def test_status_archived_filter(self, runner: click.testing.CliRunner):
        with patch("canvas.cli.core.list_sessions", return_value=[]) as mock_list:
            result = runner.invoke(cli, ["list", "--status", "archived"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(status="archived", org=None)

    def test_show_all_no_default_status(self, runner: click.testing.CliRunner):
        with patch("canvas.cli.core.list_sessions", return_value=[]) as mock_list:
            result = runner.invoke(cli, ["list", "--all"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(status=None, org=None)

    def test_status_and_all_mutually_exclusive(self, runner: click.testing.CliRunner):
        result = runner.invoke(cli, ["list", "--status", "active", "--all"])
        assert result.exit_code != 0
        assert "mutually exclusive" in result.stderr.lower()

    def test_org_filter(self, runner: click.testing.CliRunner):
        with patch("canvas.cli.core.list_sessions", return_value=[]) as mock_list:
            result = runner.invoke(cli, ["list", "--org", "acme"])

        assert result.exit_code == 0
        mock_list.assert_called_once_with(status="active", org="acme")


# ── canvas archive ──────────────────────────────────────────────────


class TestArchive:
    def test_happy_path(self, runner: click.testing.CliRunner):
        session = _make_session(status=SessionStatus.ARCHIVED)

        with patch("canvas.cli.core.archive_session", return_value=session) as mock_archive:
            result = runner.invoke(cli, ["archive", "2026-03-18-test"])

        assert result.exit_code == 0
        mock_archive.assert_called_once_with("2026-03-18-test")
        assert "Archived" in result.stderr
        assert "2026-03-18-test" in result.stderr

    def test_not_found_error(self, runner: click.testing.CliRunner):
        with patch(
            "canvas.cli.core.archive_session",
            side_effect=CanvasSessionError("Session 'nope' not found."),
        ):
            result = runner.invoke(cli, ["archive", "nope"])

        assert result.exit_code == 1
        assert "not found" in result.stderr


# ── canvas nuke ─────────────────────────────────────────────────────


class TestNuke:
    def test_happy_path_with_yes(self, runner: click.testing.CliRunner):
        with patch("canvas.cli.core.nuke_session") as mock_nuke:
            result = runner.invoke(cli, ["nuke", "2026-03-18-test", "--yes"])

        assert result.exit_code == 0
        mock_nuke.assert_called_once_with("2026-03-18-test")
        assert "Nuked" in result.stderr

    def test_confirmation_prompt(self, runner: click.testing.CliRunner):
        with patch("canvas.cli.core.nuke_session") as mock_nuke:
            result = runner.invoke(cli, ["nuke", "2026-03-18-test"], input="y\n")

        assert result.exit_code == 0
        mock_nuke.assert_called_once_with("2026-03-18-test")

    def test_confirmation_declined(self, runner: click.testing.CliRunner):
        with patch("canvas.cli.core.nuke_session") as mock_nuke:
            result = runner.invoke(cli, ["nuke", "2026-03-18-test"], input="n\n")

        assert result.exit_code == 1
        mock_nuke.assert_not_called()

    def test_error_exits_1(self, runner: click.testing.CliRunner):
        with patch(
            "canvas.cli.core.nuke_session",
            side_effect=CanvasSessionError("Session 'nope' not found."),
        ):
            result = runner.invoke(cli, ["nuke", "nope", "--yes"])

        assert result.exit_code == 1
        assert "not found" in result.stderr


# ── canvas rename ───────────────────────────────────────────────────


class TestRename:
    def test_happy_path(self, runner: click.testing.CliRunner):
        session = _make_session(label="new label")

        with patch("canvas.cli.core.rename_session", return_value=session) as mock_rename:
            result = runner.invoke(cli, ["rename", "2026-03-18-test", "new label"])

        assert result.exit_code == 0
        mock_rename.assert_called_once_with("2026-03-18-test", "new label")
        assert "Renamed" in result.stderr
        assert "new label" in result.stderr

    def test_error_exits_1(self, runner: click.testing.CliRunner):
        with patch(
            "canvas.cli.core.rename_session",
            side_effect=CanvasSessionError("Session 'nope' not found."),
        ):
            result = runner.invoke(cli, ["rename", "nope", "whatever"])

        assert result.exit_code == 1
        assert "not found" in result.stderr


# ── canvas open ─────────────────────────────────────────────────────


class TestOpen:
    def test_happy_path(self, runner: click.testing.CliRunner, tmp_path):
        session = _make_session()
        session_dir = tmp_path / "sessions" / session.slug
        session_dir.mkdir(parents=True)

        with (
            patch("canvas.registry.find_session", return_value=session),
            patch("canvas.cli.resolve_paths") as mock_paths,
            patch("canvas.cli.os.chdir") as mock_chdir,
            patch("canvas.cli.os.execvp") as mock_execvp,
        ):
            mock_paths.return_value = MagicMock(sessions_dir=tmp_path / "sessions")
            result = runner.invoke(cli, ["open", "2026-03-18-test"])

        assert result.exit_code == 0
        mock_chdir.assert_called_once_with(str(session_dir))
        mock_execvp.assert_called_once_with("claude", ["claude"])

    def test_not_found_exits_1(self, runner: click.testing.CliRunner):
        with patch("canvas.registry.find_session", return_value=None):
            result = runner.invoke(cli, ["open", "nope"])

        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_directory_missing_exits_1(self, runner: click.testing.CliRunner, tmp_path):
        session = _make_session()

        with (
            patch("canvas.registry.find_session", return_value=session),
            patch("canvas.cli.resolve_paths") as mock_paths,
        ):
            mock_paths.return_value = MagicMock(sessions_dir=tmp_path / "sessions")
            result = runner.invoke(cli, ["open", "2026-03-18-test"])

        assert result.exit_code == 1
        assert "directory missing" in result.stderr.lower()
