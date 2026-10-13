"""Chunk and shard shapes for the Zarr arrays this library writes.

The shapes are chosen for the reader, not for the writer. The frontend fetches and decodes
whole inner chunks and repacks them into fixed bricks -- 64 voxels a side in a volume, a
256 x 256 single plane otherwise -- so an inner chunk that is one brick is one request and no
wasted decode, and anything larger is decoded whole for every brick that touches it. A shard
then groups the chunks a view asks for together: every channel of a brick, and its spatial
neighbours, so they coalesce into one ranged GET.

``testing/chunk_layout_probe.py`` models that reader and is where the budgets below were
measured. Used by :mod:`mikro.io.obstore` on the way out.
"""

import math
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Protocol, Self

import xarray as xr

from pydantic import BaseModel, ConfigDict, model_validator

from mikro.vocabulary import UnknownAxisName, default_axis_type

#: The reader's brick edge in a volume. An inner chunk no larger than this on every spatial
#: axis is what lets it refine brick by brick.
BRICK_3D = 64

#: The shallowest stack cut into volume bricks. Below it a stack is a handful of planes and
#: is chunked for the plane viewer. It is well under a brick on purpose: a 46-slice stack
#: opened in 3D as single-plane chunks cost 184 chunks per brick (46 planes x 4 channels);
#: as volume chunks it costs 4. The price is on the other view -- one 2D slice of such a
#: stack decodes its whole depth.
VOLUME_MIN_DEPTH = 16

#: The reader's brick edge on a single plane.
BRICK_2D = 256

#: Ceiling for one inner chunk. Only a profile axis (kept whole, see :class:`AxisRole`) or a
#: trailing-axes fallback ever reaches it; a plain brick is far below.
INNER_CHUNK_BYTES = 2 * 1024**2

#: The plane edge is never shrunk below this to make room for a profile axis.
MIN_PROFILE_EDGE = 32

#: Shard budget: how many uncompressed bytes one S3 object holds. A shard is built whole in
#: memory before its single PUT, so this is also the unit of write memory. Measured by the
#: probe from 4 to 128 MiB: requests for a slide viewport, a volume frustum and a volume
#: slice bottom out here (10, 92 and 166, against 17, 160 and 270 at 4 MiB) and do not improve
#: past it, because the reader caps one coalesced GET at 8 MiB of compressed bytes.
SHARD_BYTES = 16 * 1024**2

#: The reader fetches at most this many channels for one brick, so grouping more in a shard
#: buys nothing.
MAX_SHARD_CHANNELS = 16


class AxisRole(Enum):
    """What the reader does with an axis, which is all that decides its chunk extent."""

    SPACE = "SPACE"
    """Cut into bricks. The last two SPACE axes are the plane, the one before them the depth."""
    CHANNEL = "CHANNEL"
    """Every position is fetched for every brick: one per chunk, all in one shard."""
    PROFILE = "PROFILE"
    """A microtime or spectrum axis, reduced whole by a phasor: kept whole in the chunk."""
    COLLAPSED = "COLLAPSED"
    """Pinned to one position (time, an index): one per chunk, or its extent multiplies every
    decode. The reader pins the chunk coordinate from level 0, so this must hold on every level."""


_ROLE_BY_AXIS_TYPE: Mapping[str, AxisRole] = {
    "SPACE": AxisRole.SPACE,
    "CHANNEL": AxisRole.CHANNEL,
    "MICROTIME": AxisRole.PROFILE,
    "SPECTRUM": AxisRole.PROFILE,
}


class ChunkLayout(BaseModel):
    """The on-disk layout of one array: its inner chunks and the shards that group them.

    Set it on an :class:`~mikro.scalars.ArrayLike` to override what the declaration would have
    chosen. ``shards`` is ``None`` for an unsharded array.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunks: tuple[int, ...]
    shards: tuple[int, ...] | None = None

    @model_validator(mode="after")
    def _shards_group_whole_chunks(self) -> Self:
        if not self.chunks or any(extent < 1 for extent in self.chunks):
            raise ValueError(f"chunks must be positive on every axis, got {self.chunks}.")
        if self.shards is None:
            return self
        if len(self.shards) != len(self.chunks):
            raise ValueError(
                f"shards {self.shards} and chunks {self.chunks} must have the same rank."
            )
        if any(shard % chunk for shard, chunk in zip(self.shards, self.chunks)):
            raise ValueError(
                f"shards {self.shards} must be a whole multiple of chunks {self.chunks} on "
                "every axis; readers refuse anything else."
            )
        return self


def roles_for(
    dims: Sequence[str], axis_types: Mapping[str, str] | None = None
) -> tuple[AxisRole, ...]:
    """The role of every dimension, from its declared axis type or else its conventional name.

    Args:
        dims: The array's dimension names, in store order.
        axis_types: Axis type name by dimension name, where the declaration is at hand. A
            dimension it does not name falls back to the bare-name convention (``x``/``y``/``z``
            are SPACE, ``c`` is CHANNEL); a name the convention does not know is COLLAPSED.
    """
    roles: list[AxisRole] = []
    for dim in dims:
        axis_type = (axis_types or {}).get(dim)
        if axis_type is None:
            try:
                axis_type = default_axis_type(dim)
            except UnknownAxisName:
                axis_type = ""
        roles.append(_ROLE_BY_AXIS_TYPE.get(axis_type, AxisRole.COLLAPSED))
    return tuple(roles)


def _plane_and_depth(roles: Sequence[AxisRole]) -> tuple[list[int], int | None]:
    space = [i for i, role in enumerate(roles) if role is AxisRole.SPACE]
    return space[-2:], space[-3] if len(space) >= 3 else None


def is_volumetric(shape: Sequence[int], roles: Sequence[AxisRole]) -> bool:
    """Whether an array is deep enough to be chunked for the volume renderer.

    Asked of level 0 and applied to the whole pyramid: a coarse level of a deep stack has to
    stay brick-shaped in 3D even once its own depth has dropped under a brick.
    """
    _, depth = _plane_and_depth(roles)
    return depth is not None and shape[depth] >= VOLUME_MIN_DEPTH


def _fill_trailing(shape: Sequence[int], itemsize: int) -> list[int]:
    """Chunks for an array with no image plane: trailing axes whole while the budget lasts."""
    chunk = [1] * len(shape)
    chunk_bytes = itemsize
    for i in reversed(range(len(shape))):
        if chunk_bytes * shape[i] <= INNER_CHUNK_BYTES:
            chunk[i] = shape[i]
            chunk_bytes *= shape[i]
        else:
            chunk[i] = max(1, INNER_CHUNK_BYTES // chunk_bytes)
            break
    return chunk


def chunk_layout(
    shape: Sequence[int],
    roles: Sequence[AxisRole],
    itemsize: int,
    *,
    volumetric: bool | None = None,
    shard_bytes: int = SHARD_BYTES,
) -> ChunkLayout:
    """The layout of one array, from what the reader does with each of its axes.

    Args:
        shape: The array's shape.
        roles: One :class:`AxisRole` per axis, see :func:`roles_for`.
        itemsize: Bytes per element.
        volumetric: Whether to cut 64-cubed bricks rather than 256 x 256 planes. Pass level 0's
            answer (:func:`is_volumetric`) for every level of a pyramid; ``None`` asks this array.
        shard_bytes: The uncompressed size one shard may reach.
    """
    rank = len(shape)
    plane, depth = _plane_and_depth(roles)
    if volumetric is None:
        volumetric = is_volumetric(shape, roles)
    volumetric = volumetric and depth is not None

    if len(plane) < 2:
        chunk = _fill_trailing(shape, itemsize)
        grouped = list(range(rank))
        spatial: list[int] = []
    else:
        profile_bytes = itemsize
        chunk = [1] * rank
        for i, role in enumerate(roles):
            if role is AxisRole.PROFILE:
                chunk[i] = shape[i]
                profile_bytes *= shape[i]
        edge = BRICK_3D if volumetric else BRICK_2D
        while (
            edge > MIN_PROFILE_EDGE
            and profile_bytes * edge * edge * (edge if volumetric else 1) > INNER_CHUNK_BYTES
        ):
            edge //= 2
        for i in plane:
            chunk[i] = min(edge, shape[i])
        if volumetric and depth is not None:
            chunk[depth] = min(edge, shape[depth])
        spatial = [*reversed(plane), *([depth] if depth is not None else [])]
        grouped = [
            i
            for i, role in enumerate(roles)
            if i not in spatial and role in (AxisRole.COLLAPSED, AxisRole.SPACE)
        ]

    counts = [math.ceil(size / extent) for size, extent in zip(shape, chunk)]
    factor = [1] * rank
    shard_size = itemsize * math.prod(chunk)

    def grow(axis: int, to: int) -> bool:
        nonlocal shard_size
        to = min(to, counts[axis])
        if to <= factor[axis] or shard_size // factor[axis] * to > shard_bytes:
            return False
        shard_size = shard_size // factor[axis] * to
        factor[axis] = to
        return True

    # Channels first: they are fetched together for every brick, so they are the one group
    # that always coalesces.
    for i, role in enumerate(roles):
        if role is AxisRole.CHANNEL and len(plane) == 2:
            grow(i, min(MAX_SHARD_CHANNELS, max(1, shard_bytes // shard_size)))
    # Then spatial neighbours, doubling each axis in turn: the writer lays a shard's chunks
    # out in Morton order, which keeps a brick's neighbours adjacent when the counts are
    # powers of two.
    growing = True
    while growing:
        growing = False
        for i in spatial:
            growing = grow(i, factor[i] * 2) or growing
    # Whatever is left goes to time and the other pinned axes, purely to cut object count.
    for i in reversed(grouped):
        grow(i, factor[i] * max(1, shard_bytes // shard_size))

    if all(f == 1 for f in factor):
        return ChunkLayout(chunks=tuple(chunk))
    return ChunkLayout(
        chunks=tuple(chunk), shards=tuple(extent * f for extent, f in zip(chunk, factor))
    )


class LaidOutArray(Protocol):
    """An array on its way to a store, and the layout it will be written with."""

    value: xr.DataArray
    layout: ChunkLayout | None


def lay_out_pyramid(
    levels: Sequence[LaidOutArray], axis_types: Mapping[str, str] | None = None
) -> None:
    """Give every level that has no layout yet the one its declaration implies.

    A level whose caller already chose a layout is left alone.

    Args:
        levels: The arrays of one dataset, level 0 first.
        axis_types: Axis type name by dimension name, see :func:`roles_for`.
    """
    def dims_of(level: LaidOutArray) -> list[str]:
        return [str(dim) for dim in level.value.dims]

    base = levels[0].value
    volumetric = is_volumetric(base.shape, roles_for(dims_of(levels[0]), axis_types))
    for level in levels:
        if level.layout is None:
            # Each level by its own dtype: a mean pyramid is wider than the integers under it.
            level.layout = chunk_layout(
                level.value.shape,
                roles_for(dims_of(level), axis_types),
                level.value.dtype.itemsize,
                volumetric=volumetric,
            )
