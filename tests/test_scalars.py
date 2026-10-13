"""Test cases for the hand-written scalars."""

import numpy as np
import pytest

from mikro.scalars import ThreeDVector


@pytest.mark.parametrize("vertex", [[4.0, 5.0], [1.0, 4.0, 5.0], np.array([4.0, 5.0])])
def test_a_vertex_has_the_space_components_of_its_system(vertex: object) -> None:
    """A shape on a plane is drawn as (y, x), one in a volume as (z, y, x)."""
    assert ThreeDVector.validate(vertex) == list(vertex)


@pytest.mark.parametrize("vertex", [[4.0], [0.0, 1.0, 4.0, 5.0]])
def test_a_vertex_of_another_width_is_refused(vertex: list[float]) -> None:
    """One component is no position in space, and four are more than space has."""
    with pytest.raises(AssertionError, match="two or three"):
        ThreeDVector.validate(vertex)
