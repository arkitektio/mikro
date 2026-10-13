"""Unit tests for the client-side helpers that are not tied to one mutation."""

from mikro.errors import MikroError, NoMikroFound


def test_mikro_error_classes() -> None:
    """Every mikro error is catchable as a ``MikroError``."""
    base_error = MikroError("Base error message")
    assert str(base_error) == "Base error message", "Error message should be preserved"
    assert isinstance(base_error, Exception), "Should be an Exception"

    assert isinstance(NoMikroFound("No mikro instance found"), MikroError)
