"""Checking an array dataset's declaration against the array it is made of.

``create_array_dataset`` takes an arbitrarily-labelled array and one ``AxisInput`` per
dimension. The one thing that can go wrong at the model level is the two disagreeing: a
dimension with no axis, an axis with no dimension, or a scale level whose array carries a
different set of dimensions than level 0. The server refuses the same, after the upload.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class ArrayDeclarationError(ValueError):
    """Raised when the declared axes cannot describe the array they are made for."""


def check_dims_match_axes(data: Any, axes: Iterable[Any], scales: Iterable[Any] | None) -> None:  # noqa: ANN401
    """Refuse axes that do not name the array's dimensions, or scales that do not share them.

    Args:
        data: The level-0 array, or the scalar wrapping it (``.value`` is read if present).
        axes: The declared ``AxisInput`` values; only ``.name`` is read.
        scales: The declared ``ScaleInput`` values, if any; each ``.array.value`` is read.

    Raises:
        ArrayDeclarationError: If the dimension names and the axis names are not the same set,
            or if any scale array's dimension names differ from level 0's.
    """
    array = getattr(data, "value", data)
    array_dims = tuple(str(dim) for dim in array.dims)
    axis_names = tuple(axis.name for axis in axes)

    if set(array_dims) != set(axis_names):
        raise ArrayDeclarationError(
            f"axes {axis_names} do not match the data array dimensions {array_dims}. "
            "Every array dimension must have exactly one matching axis (and vice versa)."
        )

    for scale in scales or ():
        scale_array = getattr(getattr(scale, "array", None), "value", None)
        if scale_array is None:
            continue
        scale_dims = tuple(str(dim) for dim in scale_array.dims)
        if set(scale_dims) != set(array_dims):
            raise ArrayDeclarationError(
                f"Scale level {getattr(scale, 'level', '?')} array dimensions {scale_dims} "
                f"do not match the data array dimensions {array_dims}."
            )
