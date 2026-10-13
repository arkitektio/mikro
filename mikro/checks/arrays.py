"""Checking an array dataset's declaration against the array it is made of.

``create_array_dataset`` takes an arbitrarily-labelled array and one ``AxisInput`` per
dimension. The one thing that can go wrong at the model level is the two disagreeing: a
dimension with no axis, an axis with no dimension, or a scale level whose array carries a
different set of dimensions than level 0. The server refuses the same, after the upload.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
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


def check_layouts_agree(levels: Sequence[Any], axis_types: Mapping[str, str]) -> None:  # noqa: ANN401
    """Refuse layouts the reader would address wrongly on some level of the pyramid.

    The reader pins a time or index axis to one chunk coordinate, computes it from level 0's
    chunk extent, and uses it on every level. A level chunked differently along such an axis
    is asked for chunks it does not have, which read back as fill.

    Args:
        levels: The arrays of one dataset, level 0 first; ``.value`` and ``.layout`` are read.
        axis_types: Axis type name by dimension name.

    Raises:
        ArrayDeclarationError: If a layout does not have its array's rank, or a pinned axis is
            chunked differently on two levels.
    """
    from mikro.io.chunking import AxisRole, roles_for

    pinned: dict[str, int] = {}
    for index, level in enumerate(levels):
        dims = [str(dim) for dim in level.value.dims]
        chunks = level.layout.chunks
        if len(chunks) != len(dims):
            raise ArrayDeclarationError(
                f"Level {index}: layout chunks {chunks} do not have the array's dimensions {dims}."
            )
        for dim, role, extent in zip(dims, roles_for(dims, axis_types), chunks):
            if role is not AxisRole.COLLAPSED:
                continue
            if pinned.setdefault(dim, extent) != extent:
                raise ArrayDeclarationError(
                    f"Level {index} chunks axis {dim!r} by {extent}, level 0 by {pinned[dim]}. "
                    "A time or index axis must be chunked the same on every level: the viewer "
                    "addresses all of them by level 0's chunk extent."
                )
