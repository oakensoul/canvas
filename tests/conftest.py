import pytest
from pathlib import Path


@pytest.fixture
def canvas_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up isolated canvas directory structure for testing."""
    home = tmp_path / ".canvas"
    home.mkdir()
    sessions = home / "sessions"
    sessions.mkdir()
    monkeypatch.setenv("CANVAS_HOME", str(home))
    return home
