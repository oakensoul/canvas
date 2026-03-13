"""Core library — importable by AIDA plugin."""


def new_session() -> None:
    """Create a new canvas session."""
    raise NotImplementedError


def list_sessions() -> None:
    """List all canvas sessions."""
    raise NotImplementedError
