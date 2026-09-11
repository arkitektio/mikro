"""Unit tests for the array-dataset pyramid helpers.

``create_array_dataset`` takes level 0 as ``data`` and every coarser level as a
``ScaleInput`` in ``scales``, and :mod:`mikro_next.pyramid` is what produces that
pair. Everything here runs offline -- the split, the reduction, the axis
selection and the ``ScaleMethod`` provenance are all decided client-side, which
is exactly why they are worth pinning down without a server.
"""


import dask.array as da
import numpy as np
import pytest
import xarray as xr

from mikro_next import axes_for, build_pyramid, canonical, dataset_arrays, scales_from
from mikro_next.api.schema import ScaleMethod
from mikro_next.vocabulary import UnknownAxisName


def _volume(dims: list[str] = ["c", "z", "y", "x"], dtype: str = "uint16") -> xr.DataArray:
    """A small labelled volume; every axis is big enough to halve three times."""
    shape = tuple(2 if dim == "c" else 8 for dim in dims)
    data = np.arange(int(np.prod(shape)), dtype=dtype).reshape(shape)
    return xr.DataArray(data, dims=dims)


# ---------------------------------------------------------------------------
# canonical
# ---------------------------------------------------------------------------


def test_canonical_orders_time_then_channel_then_space() -> None:
    """The server's axis order, derived from the names alone.

    Only the *groups* move: the spatial axes keep the relative order they were
    given, so ``(z, y, x)`` arrives after ``t`` and ``c`` still as ``(z, y, x)``.
    """
    scrambled = xr.DataArray(np.zeros((4, 8, 8, 2, 3)), dims=["z", "y", "x", "c", "t"])
    assert canonical(scrambled).dims == ("t", "c", "z", "y", "x")


def test_canonical_keeps_order_within_a_type() -> None:
    """``(z, y, x)`` and ``(x, y, z)`` are different volumes, so neither is
    rewritten into the other -- the sort is stable within a rank."""
    reversed_space = xr.DataArray(np.zeros((8, 8, 4)), dims=["x", "y", "z"])
    assert canonical(reversed_space).dims == ("x", "y", "z")


def test_canonical_is_a_no_op_on_an_already_ordered_array() -> None:
    """No transpose is inserted when there is nothing to reorder."""
    ordered = _volume()
    assert canonical(ordered) is ordered


def test_canonical_takes_explicit_axis_types() -> None:
    """A name the convention gets wrong is corrected by ``types``, not renamed.

    ``m`` would otherwise be guessed SPACE and left after the channel axis;
    declaring it MICROTIME sorts it into the categorical group instead.
    """
    array = xr.DataArray(np.zeros((8, 8, 4, 3)), dims=["y", "x", "m", "t"])
    assert canonical(array, types={"m": "MICROTIME"}).dims == ("t", "m", "y", "x")


def test_canonical_does_not_compute_a_lazy_array() -> None:
    """Reordering is metadata, so a dask-backed array stays dask-backed."""
    lazy = xr.DataArray(da.zeros((8, 8, 2), chunks=(8, 8, 2)), dims=["y", "x", "c"])
    assert hasattr(canonical(lazy).data, "dask")


# ---------------------------------------------------------------------------
# build_pyramid
# ---------------------------------------------------------------------------


def test_build_pyramid_halves_the_spatial_axes_only() -> None:
    """A pyramid is level-of-detail, and a channel is not a resolution: the
    server refuses to downsample a categorical axis, so ``c`` keeps its extent
    while ``z``, ``y`` and ``x`` halve."""
    pyramid = build_pyramid(_volume(), levels=4, method="mean")

    assert [level.shape for level in pyramid] == [
        (2, 8, 8, 8),
        (2, 4, 4, 4),
        (2, 2, 2, 2),
        (2, 1, 1, 1),
    ]
    assert all(level.dims == ("c", "z", "y", "x") for level in pyramid)


def test_build_pyramid_level_zero_is_the_base_itself() -> None:
    """Level 0 is handed back untouched, not a copy or a re-derivation."""
    base = _volume()
    assert build_pyramid(base, levels=3, method="max")[0] is base


def test_build_pyramid_preserves_the_dtype() -> None:
    """``mean`` promotes an integer array to float; a pyramid level that changes
    dtype halfway up is not the same image at a lower resolution."""
    pyramid = build_pyramid(_volume(dtype="uint16"), levels=3, method="mean")
    assert all(level.dtype == np.dtype("uint16") for level in pyramid)


def test_build_pyramid_stops_when_nothing_is_left_to_halve() -> None:
    """Asking for more levels than the data supports returns what exists."""
    tiny = xr.DataArray(np.zeros((2, 2)), dims=["y", "x"])
    pyramid = build_pyramid(tiny, levels=8, method="max")
    assert [level.shape for level in pyramid] == [(2, 2), (1, 1)]


def test_build_pyramid_nearest_subsamples_rather_than_reduces() -> None:
    """``nearest`` is a stride: every value in the level was already in the one
    above it, which is what makes it the only label-safe choice here."""
    base = xr.DataArray(np.arange(8).reshape(1, 8) * np.ones((4, 1), dtype=int), dims=["y", "x"])
    level_one = build_pyramid(base, levels=2, method="nearest")[1]
    assert level_one.to_numpy()[0].tolist() == [0, 2, 4, 6]


def test_build_pyramid_max_keeps_the_bright_pixel() -> None:
    """``max`` is the reduction that keeps a thin bright structure visible."""
    values = np.zeros((4, 4))
    values[0, 0] = 5.0
    pyramid = build_pyramid(xr.DataArray(values, dims=["y", "x"]), levels=2, method="max")
    assert pyramid[1].to_numpy()[0, 0] == 5.0


def test_build_pyramid_coarsens_an_explicitly_named_axis() -> None:
    """``axes`` overrides the spatial default -- here only ``x`` is halved."""
    pyramid = build_pyramid(_volume(), levels=2, method="mean", axes=["x"])
    assert pyramid[1].shape == (2, 8, 8, 4)


@pytest.mark.parametrize("levels", [0, -1])
def test_build_pyramid_rejects_a_level_count_below_one(levels: int) -> None:
    with pytest.raises(ValueError, match="levels must be at least 1"):
        build_pyramid(_volume(), levels=levels)


def test_build_pyramid_rejects_an_unknown_reduction() -> None:
    with pytest.raises(ValueError, match="Unknown reduction"):
        build_pyramid(_volume(), levels=2, method="median")


def test_build_pyramid_rejects_an_axis_the_array_does_not_have() -> None:
    with pytest.raises(ValueError, match="Cannot coarsen along"):
        build_pyramid(_volume(), levels=2, axes=["q"])


def test_build_pyramid_rejects_coarsening_a_categorical_axis() -> None:
    """A position halfway between two channels is not a thing, so the server
    rejects a pyramid whose categorical axes change extent -- caught here first."""
    with pytest.raises(ValueError, match="only continuously sampled axes"):
        build_pyramid(_volume(), levels=2, axes=["c", "x"])


def test_build_pyramid_allows_coarsening_a_continuous_non_spatial_axis() -> None:
    """MICROTIME is continuous, so a pyramid may re-bin it -- but only when the
    caller says the axis is one, since ``m`` reads as SPACE by convention."""
    array = xr.DataArray(np.zeros((8, 8, 8)), dims=["m", "y", "x"])
    pyramid = build_pyramid(
        array, levels=2, method="mean", axes=["m"], types={"m": "MICROTIME"}
    )
    assert pyramid[1].shape == (4, 8, 8)


def test_build_pyramid_materializes_a_lazy_base_once() -> None:
    """Every coarser level is a lazy view chained back to level 0, and dask does
    not cache across separate computations. Without materializing, building N
    levels re-derives the base N times; with it, once.
    """
    calls: list[int] = []

    def _tracked(block: np.ndarray) -> np.ndarray:
        calls.append(1)
        return block

    def _lazy_base() -> xr.DataArray:
        source = da.from_array(np.random.random((8, 8, 8)), chunks=(8, 8, 8))
        return xr.DataArray(source.map_blocks(_tracked, dtype="float64"), dims=["z", "y", "x"])

    for level in build_pyramid(_lazy_base(), levels=4, method="mean", materialize=False):
        np.asarray(level)
    without = len(calls)

    calls.clear()
    for level in build_pyramid(_lazy_base(), levels=4, method="mean"):
        np.asarray(level)
    with_materialize = len(calls)

    assert with_materialize < without, (
        "A materialized base should be derived once, not once per level"
    )


def test_build_pyramid_materialized_levels_match_the_lazy_ones() -> None:
    """The scratch Zarr round trip is an optimisation, not a change of values."""
    values = np.random.random((8, 8, 8))
    lazy = xr.DataArray(da.from_array(values, chunks=(4, 4, 4)), dims=["z", "y", "x"])

    eager = build_pyramid(lazy, levels=3, method="mean", materialize=False)
    materialized = build_pyramid(lazy, levels=3, method="mean", materialize=True)

    for expected, actual in zip(eager, materialized):
        np.testing.assert_allclose(np.asarray(expected), np.asarray(actual))


# ---------------------------------------------------------------------------
# scales_from / dataset_arrays
# ---------------------------------------------------------------------------


def test_scales_from_omits_level_zero() -> None:
    """``data`` *is* level 0, so listing it here as well would upload it twice."""
    pyramid = build_pyramid(_volume(), levels=4, method="mean")
    scales = scales_from(pyramid, "mean")

    assert [scale.level for scale in scales] == [1, 2, 3]
    assert len(scales) == len(pyramid) - 1


def test_scales_from_a_single_level_pyramid_is_empty() -> None:
    assert scales_from(build_pyramid(_volume(), levels=1)) == []


@pytest.mark.parametrize(
    ("reduction", "expected"),
    [
        ("max", ScaleMethod.MAX),
        ("min", ScaleMethod.MIN),
        ("mean", ScaleMethod.AREA),
        ("nearest", ScaleMethod.NEAREST),
    ],
)
def test_scales_from_records_the_reduction_as_a_scale_method(
    reduction: str, expected: ScaleMethod
) -> None:
    """xarray's vocabulary and the server's are not the same list -- ``mean`` is
    ``AREA`` -- and a reduction name that is not translated is rejected outright
    by ``ScaleInput``, so the mapping is the whole of what makes this work.
    """
    pyramid = build_pyramid(_volume(), levels=2, method=reduction)
    assert scales_from(pyramid, reduction)[0].scale_method == expected.value


def test_scales_from_leaves_sum_without_a_scale_method() -> None:
    """Pooling that conserves counts is not one of the server's resampling
    filters, so it travels with no method rather than misreported as one."""
    pyramid = build_pyramid(_volume(dtype="float64"), levels=2, method="sum")
    assert scales_from(pyramid, "sum")[0].scale_method is None


def test_scales_from_rejects_an_unknown_reduction() -> None:
    pyramid = build_pyramid(_volume(), levels=2, method="mean")
    with pytest.raises(ValueError, match="Unknown reduction"):
        scales_from(pyramid, "median")


def test_scales_from_carries_the_level_arrays() -> None:
    """The array on each scale is the level it was built from, unchanged."""
    pyramid = build_pyramid(_volume(), levels=3, method="mean")
    scales = scales_from(pyramid, "mean")
    assert [scale.array.value.shape for scale in scales] == [
        level.shape for level in pyramid[1:]
    ]


def test_dataset_arrays_splits_level_zero_from_the_rest() -> None:
    """The ``(data, scales)`` pair ``create_array_dataset`` wants, already split."""
    base = _volume()
    data, scales = dataset_arrays(base, levels=3, method="mean")

    assert data is base
    assert [scale.level for scale in scales] == [1, 2]
    assert all(scale.scale_method == ScaleMethod.AREA.value for scale in scales)


def test_dataset_arrays_of_a_single_level_has_no_scales() -> None:
    """A dataset with no pyramid is the same call with an empty ``scales``."""
    data, scales = dataset_arrays(_volume(), levels=1)
    assert scales == []
    assert data.shape == (2, 8, 8, 8)


class TestAxesFor:
    """`axes_for` builds the `AxisInput` list an ingest declares."""

    def _data(self, dims: list) -> "xr.DataArray":
        return xr.DataArray(np.zeros((2,) * len(dims), dtype="uint8"), dims=dims)

    def test_the_convention_covers_the_ordinary_dims(self) -> None:
        axes = axes_for(self._data(["t", "c", "z", "y", "x"]))
        assert [a.name for a in axes] == ["t", "c", "z", "y", "x"]
        assert [a.type for a in axes] == [
            "TIME", "CHANNEL", "SPACE", "SPACE", "SPACE",
        ]

    def test_dims_keep_the_arrays_own_order(self) -> None:
        axes = axes_for(self._data(["x", "y", "c"]))
        assert [a.name for a in axes] == ["x", "y", "c"]

    def test_a_declared_type_wins_over_the_convention(self) -> None:
        """A tile index left to the convention would become SPACE, and the pyramid
        coarsens exactly the SPACE axes — 12 tiles quietly becoming 6."""
        axes = axes_for(self._data(["tile", "y", "x"]), types={"tile": "INDEX"})
        assert [a.type for a in axes] == ["INDEX", "SPACE", "SPACE"]

    def test_an_undeclared_unknown_axis_is_refused(self) -> None:
        with pytest.raises(UnknownAxisName):
            axes_for(self._data(["tile", "y", "x"]))

    def test_long_names_default_to_the_axis_name(self) -> None:
        axes = axes_for(self._data(["z"]), long_names={"z": "depth"})
        assert axes[0].long_name == "depth"
        assert axes_for(self._data(["z"]))[0].long_name == "z"
