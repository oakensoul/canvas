"""Read/write ~/.canvas/registry.json."""


def load_registry() -> dict:
    """Load the session registry from disk."""
    raise NotImplementedError


def save_registry(registry: dict) -> None:
    """Persist the session registry to disk."""
    raise NotImplementedError
