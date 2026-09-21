"""An array dataset's axes name its dimensions, and every scale level shares them.

The check used to live inline in the trait; it is the same refusal the table and sparse
paths make from `mikro.checks`, so it lives beside them and the trait only calls it.
"""

import numpy as np
import pytest
import xarray as xr

from mikro.checks import ArrayDeclarationError
from mikro.checks.arrays import check_dims_match_axes


class _Axis:
    def __init__(self, name: str) -> None:
        self.name = name


class _Scale:
    def __init__(self, level: int, array: xr.DataArray) -> None:
        self.level = level
        self.array = type("V", (), {"value": array})()


def _cube(*dims: str) -> xr.DataArray:
    return xr.DataArray(np.zeros([2] * len(dims)), dims=dims)


def test_matching_axes_and_scales_pass() -> None:
    """The ordinary case: every dimension named once, every level the same dimensions."""
    check_dims_match_axes(_cube("z", "y", "x"), [_Axis("x"), _Axis("y"), _Axis("z")], [_Scale(1, _cube("z", "y", "x"))])


def test_an_axis_the_array_does_not_have_is_refused() -> None:
    """An axis with no dimension behind it is refused, and the message names both sides."""
    with pytest.raises(ArrayDeclarationError, match="do not match the data array dimensions"):
        check_dims_match_axes(_cube("y", "x"), [_Axis("z"), _Axis("y"), _Axis("x")], None)


def test_a_scale_with_other_dimensions_is_refused() -> None:
    """A coarser level cannot carry a dimension level 0 does not."""
    with pytest.raises(ArrayDeclarationError, match="Scale level 1"):
        check_dims_match_axes(_cube("y", "x"), [_Axis("y"), _Axis("x")], [_Scale(1, _cube("c", "y", "x"))])


def test_the_trait_delegates_here() -> None:
    """The generated input raises the same error, wrapped by pydantic."""
    from pydantic import ValidationError

    from mikro.api.schema import AxisInput, AxisType, CreateArrayDatasetInput

    with pytest.raises(ValidationError, match="do not match the data array dimensions"):
        CreateArrayDatasetInput(name="x", data=_cube("y", "x"), axes=[AxisInput(name="z", type=AxisType.SPACE)], scales=[])
