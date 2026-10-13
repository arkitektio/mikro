"""Chunk and shard shapes follow what the viewer does with each axis.

The viewer fetches whole inner chunks and cuts them into fixed bricks, so the numbers asserted
here are its numbers: 64 a side in a volume, 256 x 256 on a plane, one channel and one
timepoint per chunk. `testing/chunk_layout_probe.py` is where they are measured.
"""

import numpy as np
import pytest
import xarray as xr
from pydantic import ValidationError

from mikro.checks import ArrayDeclarationError
from mikro.io.chunking import (
    SHARD_BYTES,
    AxisRole,
    ChunkLayout,
    chunk_layout,
    is_volumetric,
    roles_for,
)
from mikro.scalars import ArrayLike


def _layout(dims: str, shape: tuple[int, ...], itemsize: int) -> ChunkLayout:
    return chunk_layout(shape, roles_for(dims), itemsize)


def _by_dim(dims: str, extents: tuple[int, ...] | None) -> dict[str, int]:
    assert extents is not None
    return dict(zip(dims, extents))


def test_a_plane_is_cut_into_plane_bricks_with_its_channels_in_one_shard() -> None:
    """A slide: 256 x 256 chunks, one channel each, all three channels in every shard."""
    layout = _layout("ctzyx", (3, 1, 1, 20000, 20000), 1)

    assert layout.chunks == (1, 1, 1, 256, 256)
    assert _by_dim("ctzyx", layout.shards)["c"] == 3


def test_a_deep_stack_is_cut_into_volume_bricks() -> None:
    """A deep stack is a volume: 64-cubed chunks, both channels in every shard."""
    layout = _layout("ctzyx", (2, 1, 200, 2048, 2048), 2)

    assert layout.chunks == (1, 1, 64, 64, 64)
    assert _by_dim("ctzyx", layout.shards)["c"] == 2


def test_a_shallow_stack_stays_a_pile_of_planes() -> None:
    """A handful of slices is for the plane viewer: one slice per chunk. From 16 up it is a
    volume, with the chunk as deep as the stack until that passes a brick."""
    assert _layout("ctzyx", (1, 1, 15, 2048, 2048), 2).chunks == (1, 1, 1, 256, 256)
    assert _layout("ctzyx", (1, 1, 16, 2048, 2048), 2).chunks == (1, 1, 16, 64, 64)
    assert _layout("ctzyx", (4, 1, 46, 2456, 2456), 1).chunks == (1, 1, 46, 64, 64)
    assert _layout("ctzyx", (1, 1, 200, 2048, 2048), 2).chunks == (1, 1, 64, 64, 64)


@pytest.mark.parametrize(
    ("dims", "shape"),
    [
        ("zyx", (200, 2048, 2048)),
        ("czyx", (3, 200, 2048, 2048)),
        ("zyxc", (200, 2048, 2048, 3)),
        ("tczyx", (5, 3, 200, 2048, 2048)),
    ],
)
def test_the_bricks_do_not_depend_on_which_dimensions_are_present(
    dims: str, shape: tuple[int, ...]
) -> None:
    """Any labelling of a volume gets the same bricks -- not full-width strips."""
    chunks = _by_dim(dims, _layout(dims, shape, 2).chunks)

    assert {dim: chunks[dim] for dim in "zyx"} == {"z": 64, "y": 64, "x": 64}
    assert all(extent == 1 for dim, extent in chunks.items() if dim not in "zyx")


def test_time_is_one_per_chunk_and_absorbs_the_shard() -> None:
    """A frame is one chunk deep in time; the shard groups frames only to cut object count."""
    layout = _layout("ctzyx", (1, 500, 1, 512, 512), 1)

    assert layout.chunks == (1, 1, 1, 256, 256)
    assert layout.shards == (1, 64, 1, 512, 512)


def test_a_profile_axis_is_kept_whole() -> None:
    """A phasor reduces every bin, so the bins stay together and the plane shrinks instead."""
    roles = roles_for(["y", "x", "tau"], {"tau": "MICROTIME"})
    assert roles == (AxisRole.SPACE, AxisRole.SPACE, AxisRole.PROFILE)

    assert chunk_layout((512, 512, 256), roles, 2).chunks == (64, 64, 256)


def test_declared_types_win_over_names_and_unknown_names_are_pinned() -> None:
    """The declaration decides; the bare-name convention only fills what it leaves out."""
    assert roles_for(["a", "b", "tile"], {"a": "SPACE", "b": "SPACE", "tile": "INDEX"}) == (
        AxisRole.SPACE,
        AxisRole.SPACE,
        AxisRole.COLLAPSED,
    )
    assert roles_for("cyx") == (AxisRole.CHANNEL, AxisRole.SPACE, AxisRole.SPACE)
    assert roles_for(["tile", "y", "x"])[0] is AxisRole.COLLAPSED


@pytest.mark.parametrize(
    ("dims", "shape", "itemsize"),
    [
        ("ctzyx", (3, 1, 1, 20000, 20000), 1),
        ("ctzyx", (2, 7, 200, 2048, 2048), 2),
        ("ctzyx", (1, 1, 3, 300, 5000), 2),
        ("zyx", (65, 100, 4097), 4),
        ("yxc", (20000, 20000, 3), 1),
    ],
)
def test_a_shard_is_whole_chunks_inside_the_budget(
    dims: str, shape: tuple[int, ...], itemsize: int
) -> None:
    """Readers refuse a shard that is not a whole multiple; a writer holds one in memory."""
    layout = _layout(dims, shape, itemsize)
    assert layout.shards is not None

    for size, chunk, shard in zip(shape, layout.chunks, layout.shards):
        assert chunk <= size, "an inner chunk never exceeds the array"
        assert shard % chunk == 0
        assert shard - size < chunk, "a shard overhangs the array by less than one chunk"
    assert itemsize * int(np.prod(layout.shards)) <= SHARD_BYTES


def test_an_array_with_no_image_plane_fills_its_trailing_axes() -> None:
    """Nothing to cut bricks from: fall back to a byte budget instead of one-element chunks."""
    layout = chunk_layout((25_000_000, 4), roles_for(["dim_0", "dim_1"]), 4)

    assert layout.chunks == (131072, 4)
    assert layout.shards is not None and layout.shards[0] % 131072 == 0


def test_every_level_is_cut_for_the_view_level_0_decides() -> None:
    """A coarse level of a volume keeps volume bricks even once it is shallower than one."""
    levels = [
        ("ctzyx", (2, 10, 200, 2048, 2048)),
        ("ctzyx", (2, 10, 100, 1024, 1024)),
        ("ctzyx", (2, 10, 25, 256, 256)),
        ("ctzyx", (2, 10, 6, 64, 64)),
    ]
    roles = roles_for(levels[0][0])
    volumetric = is_volumetric(levels[0][1], roles)
    layouts = [chunk_layout(shape, roles_for(dims), 2, volumetric=volumetric) for dims, shape in levels]

    assert [layout.chunks for layout in layouts] == [
        (1, 1, 64, 64, 64),
        (1, 1, 64, 64, 64),
        (1, 1, 25, 64, 64),
        (1, 1, 6, 64, 64),
    ]
    # The viewer addresses time on every level by level 0's chunk extent.
    assert {layout.chunks[1] for layout in layouts} == {1}
    assert all(layout.shards is not None for layout in layouts)


def test_a_layout_must_group_whole_chunks() -> None:
    """The refusal a reader would make, made before anything is written."""
    with pytest.raises(ValidationError, match="whole multiple"):
        ChunkLayout(chunks=(64, 64), shards=(100, 128))
    with pytest.raises(ValidationError, match="same rank"):
        ChunkLayout(chunks=(64, 64), shards=(128,))


def _dataset_input(data: object, scales: tuple[object, ...] = ()):  # noqa: ANN202
    from mikro.api.schema import AxisInput, AxisType, CreateArrayDatasetInput

    axes = tuple(
        AxisInput(name=name, type=kind)
        for name, kind in (
            ("t", AxisType.TIME),
            ("z", AxisType.SPACE),
            ("y", AxisType.SPACE),
            ("x", AxisType.SPACE),
        )
    )
    return CreateArrayDatasetInput(name="stack", data=data, axes=axes, scales=scales)


def _stack(t: int, z: int, yx: int) -> xr.DataArray:
    return xr.DataArray(np.zeros((t, z, yx, yx), dtype="uint8"), dims=list("tzyx"))


def test_the_declaration_lays_out_every_level() -> None:
    """Declaring a dataset is what chooses the layout: it sees the axes and all the levels."""
    from mikro.api.schema import ScaleInput

    declared = _dataset_input(
        _stack(3, 64, 128), scales=(ScaleInput(level=1, array=_stack(3, 32, 64)),)
    )

    assert declared.data.layout.chunks == (1, 64, 64, 64)
    assert declared.scales[0].array.layout.chunks == (1, 32, 64, 64)


def test_a_caller_layout_survives_the_declaration() -> None:
    """An explicit layout is the override: the declaration leaves it alone."""
    mine = ChunkLayout(chunks=(1, 16, 64, 64), shards=(1, 64, 128, 128))

    declared = _dataset_input(ArrayLike(_stack(3, 64, 128), layout=mine))

    assert declared.data.layout is mine


def test_levels_that_chunk_time_differently_are_refused() -> None:
    """The viewer would ask the coarse level for chunks it does not have."""
    from mikro.api.schema import ScaleInput

    coarse = ArrayLike(_stack(3, 32, 64), layout=ChunkLayout(chunks=(3, 32, 64, 64)))

    with pytest.raises(ValidationError, match="chunked the same on every level") as refusal:
        _dataset_input(_stack(3, 64, 128), scales=(ScaleInput(level=1, array=coarse),))
    assert isinstance(refusal.value.errors()[0]["ctx"]["error"], ArrayDeclarationError)


def test_each_level_is_budgeted_by_its_own_dtype() -> None:
    """A mean level is wider than the integers under it; its shards must not be sized for them."""
    from mikro.api.schema import ScaleInput

    def stack(dtype: str, yx: int) -> xr.DataArray:
        return xr.DataArray(np.zeros((1, 1, yx, yx), dtype=dtype), dims=list("tzyx"))

    declared = _dataset_input(
        stack("uint8", 8192), scales=(ScaleInput(level=1, array=stack("float64", 4096)),)
    )

    coarse = declared.scales[0].array.layout
    assert 8 * int(np.prod(coarse.shards)) <= SHARD_BYTES
