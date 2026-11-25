"""A lens fetched back by id describes itself the way the specs constrain it.

A run tests every lens crossing a port: its descriptors, computed by the structure's
``describe``, against the port's Requires (after expanding the id) and Provides (before
shrinking). The comparison is the runtime's; what is mikro's is that the described lens
is the one the expander returns, with nothing but the id to go on.
"""

import numpy as np
import pytest
import xarray as xr

pytest.importorskip("rekuest")

from typing import get_args  # noqa: E402

from arkitekt_spec.actions import RequiresInput  # noqa: E402
from arkitekt_spec.declare.descriptors import unfulfilled  # noqa: E402
from arkitekt_spec.declare.structures.declare import structure_of  # noqa: E402

from mikro import Mikro  # noqa: E402
from mikro.api.schema import ArrayLens  # noqa: E402
from mikro.arkitekt.specs import LabelMask, SingleChannelImage, Volume  # noqa: E402


def spec_constraints(spec: object) -> list[RequiresInput]:
    """What a spec puts on an argument port."""
    return [
        marker for marker in get_args(spec)[1:] if isinstance(marker, RequiresInput)
    ]


def _described(
    mikro: Mikro, shape: tuple[int, ...], axes: list[str]
) -> dict[str, object]:
    """Store an array, fetch its lens back by id as a port would, and describe it."""
    data = xr.DataArray(np.zeros(shape, dtype="uint8"), dims=axes)
    stored = mikro.create_array_dataset(
        data=data, scales=[], name="described", axes=axes
    )
    lens = mikro.get_lens(stored.lens().id)
    declared = structure_of(ArrayLens)
    assert declared is not None and declared.describe is not None
    describe = declared.describe
    return dict(describe(lens))


@pytest.mark.integration
def test_a_lens_fetched_by_id_is_described_as_the_specs_constrain_it(
    mikro: Mikro,
) -> None:
    """A plane, a two-channel image and a stack each pass and fail the specs they should."""
    plane = _described(mikro, (8, 8), ["y", "x"])
    assert unfulfilled(spec_constraints(SingleChannelImage), plane) == ()
    assert unfulfilled(spec_constraints(Volume), plane) == (
        "@mikro/n_space_axes EQUALS 3 (actual 2)",
    )

    two_channels = _described(mikro, (2, 8, 8), ["c", "y", "x"])
    assert unfulfilled(spec_constraints(SingleChannelImage), two_channels) == (
        "@mikro/n_channels LTE 1 (actual 2)",
    )

    stack = _described(mikro, (4, 8, 8), ["z", "y", "x"])
    assert unfulfilled(spec_constraints(Volume), stack) == ()


@pytest.mark.integration
def test_provenance_is_the_servers_word_too(mikro: Mikro) -> None:
    """The descriptors are mikro's own, so they state what the client could never compute: a
    lens nobody marked as labels is not a ``LabelMask``, and a port that says so is refused."""
    plane = _described(mikro, (8, 8), ["y", "x"])
    assert "@mikro/value_kind" in plane
    assert unfulfilled(spec_constraints(LabelMask), plane) != ()
