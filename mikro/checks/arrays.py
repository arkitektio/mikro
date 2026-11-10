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


def name_bare_dims(levels: Iterable[Any], axes: Iterable[Any]) -> None:  # noqa: ANN401
    """Name the dimensions of every bare array (``dims is None``) by the declared axes, in order.

    A numpy or dask array carries no names, so ``axes=["z", "y", "x"]`` is the statement of
    what its dimensions are. An array that brought its own names (an ``xarray.DataArray``)
    is left alone; :func:`check_dims_match_axes` holds it to the axes by name instead.

    Args:
        levels: The ``ArrayLike`` values of one dataset; ``.dims`` and ``.ndim`` are read.
        axes: The declared ``AxisInput`` values; only ``.name`` is read.

    Raises:
        ArrayDeclarationError: If a bare array's rank is not the number of axes.
    """
    axis_names = tuple(axis.name for axis in axes)
    for level in levels:
        if level.dims is not None:
            continue
        if level.ndim != len(axis_names):
            raise ArrayDeclarationError(
                f"An array of shape {level.shape} has {level.ndim} dimensions, but "
                f"{len(axis_names)} axes {axis_names} are declared. A bare numpy or dask "
                "array is named by its axes, in order, so there must be one per dimension."
            )
        level.dims = axis_names


def check_dims_match_axes(data: Any, axes: Iterable[Any], scales: Iterable[Any] | None) -> None:  # noqa: ANN401
    """Refuse axes that do not name the array's dimensions, or scales that do not share them.

    Args:
        data: The level-0 ``ArrayLike``; ``.dims`` is read.
        axes: The declared ``AxisInput`` values; only ``.name`` is read.
        scales: The declared ``ScaleInput`` values, if any; each ``.array.dims`` is read.

    Raises:
        ArrayDeclarationError: If the dimension names and the axis names are not the same set,
            or if any scale array's dimension names differ from level 0's.
    """
    array_dims = tuple(data.dims)
    axis_names = tuple(axis.name for axis in axes)

    if set(array_dims) != set(axis_names):
        raise ArrayDeclarationError(
            f"axes {axis_names} do not match the data array dimensions {array_dims}. "
            "Every array dimension must have exactly one matching axis (and vice versa)."
        )

    for scale in scales or ():
        scale_array = getattr(scale, "array", None)
        if scale_array is None:
            continue
        scale_dims = tuple(scale_array.dims)
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
        levels: The arrays of one dataset, level 0 first; ``.dims`` and ``.layout`` are read.
        axis_types: Axis type name by dimension name.

    Raises:
        ArrayDeclarationError: If a layout does not have its array's rank, or a pinned axis is
            chunked differently on two levels.
    """
    from mikro.io.chunking import AxisRole, roles_for

    pinned: dict[str, int] = {}
    for index, level in enumerate(levels):
        dims = list(level.dims)
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
