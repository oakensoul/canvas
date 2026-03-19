import pytest
from canvas.exceptions import (
    CanvasError,
    CanvasConfigError,
    CanvasRegistryError,
    CanvasTemplateError,
    CanvasSessionError,
)

CHILD_EXCEPTIONS = [
    CanvasConfigError,
    CanvasRegistryError,
    CanvasTemplateError,
    CanvasSessionError,
]


@pytest.mark.parametrize("exc_cls", CHILD_EXCEPTIONS)
def test_subclass_of_canvas_error(exc_cls):
    assert issubclass(exc_cls, CanvasError)


@pytest.mark.parametrize("exc_cls", [CanvasError] + CHILD_EXCEPTIONS)
def test_subclass_of_exception(exc_cls):
    assert issubclass(exc_cls, Exception)


@pytest.mark.parametrize("exc_cls", CHILD_EXCEPTIONS)
def test_raise_and_catch_as_canvas_error(exc_cls):
    with pytest.raises(CanvasError):
        raise exc_cls("test")


@pytest.mark.parametrize("exc_cls", [CanvasError] + CHILD_EXCEPTIONS)
def test_message_preserved(exc_cls):
    msg = f"something went wrong in {exc_cls.__name__}"
    exc = exc_cls(msg)
    assert str(exc) == msg
