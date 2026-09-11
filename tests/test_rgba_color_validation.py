"""Unit tests for the RGBAColorInputTrait colour validation.

``color`` is declared in the schema as a bare ``[Int!]``, so the generated model
says nothing about how many components it wants — but the server takes exactly
four and refuses three. These cover the completion that keeps the obvious
three-component spelling working, and the rejection that turns a wrong length
into a local error instead of a round trip.
"""

import pytest
from pydantic import ValidationError

from mikro_next.api.schema import PhasorCursorInput, TransferFunctionInput
from mikro_next.render import ChannelSpec, channel_graph, composite_graph, rgb_graph


def test_rgb_triple_is_completed_to_opaque_rgba() -> None:
    """Three components mean an opaque colour, which is what the caller meant."""
    assert TransferFunctionInput(color=(0, 255, 255)).color == (0, 255, 255, 255)


def test_rgba_quadruple_is_left_alone() -> None:
    """A stated alpha is a choice and survives untouched."""
    assert TransferFunctionInput(color=(0, 255, 255, 128)).color == (0, 255, 255, 128)


def test_a_list_is_accepted_like_a_tuple() -> None:
    """The completion is about length, not about the container it arrived in."""
    assert TransferFunctionInput(color=[10, 20, 30]).color == (10, 20, 30, 255)


def test_absent_colour_stays_absent() -> None:
    """No colour is not the same as a bad one — the field is optional."""
    assert TransferFunctionInput(colormap="INTENSITY").color is None


@pytest.mark.parametrize("components", [(0, 255), (1,), (1, 2, 3, 4, 5)])
def test_wrong_length_is_rejected_locally(components: tuple[int, ...]) -> None:
    """Anything that is neither RGB nor RGBA fails here, not at the backend."""
    with pytest.raises(ValidationError, match="RGBA colour"):
        TransferFunctionInput(color=components)


def test_the_trait_also_guards_phasor_cursors() -> None:
    """The other input carrying a bare ``[Int!]`` colour gets the same treatment."""
    assert PhasorCursorInput(kind="CIRCLE", color=(1, 2, 3)).color == (1, 2, 3, 255)


def test_render_builders_emit_rgba() -> None:
    """The builders in ``render.py`` pass RGB triples through, so they rely on this."""
    graph = channel_graph(color=(0, 255, 255))
    assert graph.root.children[0].transfer.color == (0, 255, 255, 255)

    assert [node.transfer.color for node in rgb_graph().root.children] == [
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
    ]

    composite = composite_graph([ChannelSpec(intensity_index=0, color=(12, 34, 56))])
    assert composite.root.children[0].transfer.color == (12, 34, 56, 255)
