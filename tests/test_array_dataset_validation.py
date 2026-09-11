"""Unit tests for the ``create_array_dataset`` inputs.

The array-dataset path is what replaced the deprecated ``from_array_like`` /
``Image`` route, and the difference is that the caller supplies an arbitrarily
*labelled* array: the axes are declared rather than forced into a fixed
``ctzyx`` layout. That freedom is only safe because the declaration is checked
before anything uploads -- axes against dims, scale arrays against the base --
and because the anchor helpers build the render metadata from the data itself.
Everything here runs offline.
"""

import numpy as np
import pytest
import xarray as xr
from pydantic import ValidationError

from mikro_next.api.schema import (
    AxisInput,
    AxisType,
    CoordinateAnchorInput,
    CreateArrayDatasetInput,
    ScaleInput,
    ValueHistogramInput,
)


def _data(dims: list[str]) -> xr.DataArray:
    return xr.DataArray(np.zeros((2,) * len(dims), dtype="uint16"), dims=dims)


def _axes(names: list[str]) -> list[AxisInput]:
    return [AxisInput(name=name, type="SPACE") for name in names]


def test_matching_axes_validate() -> None:
    """Axes that cover exactly the array's dims are accepted."""
    model = CreateArrayDatasetInput(
        data=_data(["z", "y", "x", "c"]),
        scales=(),
        name="ds",
        axes=_axes(["z", "y", "x", "c"]),
    )
    assert model.data.value.dims == ("z", "y", "x", "c")


def test_axis_order_is_irrelevant() -> None:
    """Only the set of axis names must match, not their order."""
    CreateArrayDatasetInput(
        data=_data(["z", "y", "x", "c"]),
        scales=(),
        name="ds",
        axes=_axes(["c", "x", "y", "z"]),
    )


def test_missing_axis_raises() -> None:
    """A data dim with no matching axis is rejected."""
    with pytest.raises(ValidationError):
        CreateArrayDatasetInput(
            data=_data(["z", "y", "x", "c"]),
            scales=(),
            name="ds",
            axes=_axes(["z", "y", "x"]),
        )


def test_extra_axis_raises() -> None:
    """An axis that does not correspond to any data dim is rejected."""
    with pytest.raises(ValidationError):
        CreateArrayDatasetInput(
            data=_data(["z", "y", "x"]),
            scales=(),
            name="ds",
            axes=_axes(["z", "y", "x", "c"]),
        )


def test_scale_dims_must_match() -> None:
    """A scale array whose dims differ from the data dims is rejected."""
    with pytest.raises(ValidationError):
        CreateArrayDatasetInput(
            data=_data(["z", "y", "x"]),
            scales=(ScaleInput(level=0, array=_data(["z", "y", "c"])),),
            name="ds",
            axes=_axes(["z", "y", "x"]),
        )


def test_the_labels_of_the_data_array_survive() -> None:
    """Unlike the deprecated image path, nothing is renamed into a fixed
    ``ctzyx`` vocabulary -- an axis called ``m`` stays called ``m``."""
    model = CreateArrayDatasetInput(
        data=_data(["t", "m", "y", "x"]),
        scales=(),
        name="flim",
        axes=[
            AxisInput(name="t", type=AxisType.TIME),
            AxisInput(name="m", type=AxisType.MICROTIME),
            AxisInput(name="y", type=AxisType.SPACE),
            AxisInput(name="x", type=AxisType.SPACE),
        ],
    )
    assert model.data.value.dims == ("t", "m", "y", "x")
    assert [axis.type for axis in model.axes] == ["TIME", "MICROTIME", "SPACE", "SPACE"]


# ---------------------------------------------------------------------------
# Axis declarations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [("t", "TIME"), ("time", "TIME"), ("c", "CHANNEL"), ("channel", "CHANNEL"),
     ("z", "SPACE"), ("y", "SPACE"), ("x", "SPACE")],
)
def test_a_bare_axis_name_infers_its_type(name: str, expected: str) -> None:
    """``axes=["c", "z", "y", "x"]`` is enough for the common case; anything the
    convention gets wrong takes a full ``AxisInput`` instead."""
    axis = AxisInput.model_validate(name)
    assert (axis.name, axis.type) == (name, expected)


@pytest.mark.parametrize("name", ["m", "lambda", "tile", "tau", "row"])
def test_an_unconventional_bare_name_is_refused(name: str) -> None:
    """The convention has no catch-all. It used to call anything it did not
    recognise SPACE, and the pyramid coarsens exactly the SPACE axes — which is
    how a tile index gets halved level by level, 12 tiles quietly becoming 6."""
    with pytest.raises(ValidationError, match="No conventional axis type"):
        AxisInput.model_validate(name)


def test_an_unconventional_axis_is_fine_when_its_type_is_stated() -> None:
    axis = AxisInput(name="tile", type="INDEX")
    assert (axis.name, axis.type) == ("tile", "INDEX")


def test_bare_axis_names_are_accepted_by_the_mutation_input() -> None:
    model = CreateArrayDatasetInput(
        data=_data(["c", "z", "y", "x"]), scales=(), name="ds", axes=["c", "z", "y", "x"]
    )
    assert [axis.type for axis in model.axes] == ["CHANNEL", "SPACE", "SPACE", "SPACE"]


# ---------------------------------------------------------------------------
# Value histograms and coordinate anchors
# ---------------------------------------------------------------------------


def test_a_histogram_covers_every_value_in_the_array() -> None:
    """The bin edges span the actual min and max, so nothing falls outside and
    the counts add up to the number of samples."""
    values = np.linspace(0.0, 10.0, 500)
    histogram = ValueHistogramInput.from_array(values, bins=16)

    assert len(histogram.bins) == 17, "n bins means n+1 edges"
    assert len(histogram.histogram) == 16
    assert sum(histogram.histogram) == values.size
    assert (histogram.min, histogram.max) == (0.0, 10.0)


def test_a_histogram_reports_a_robust_contrast_window() -> None:
    """The percentiles ignore hot and dead pixels, so the default contrast
    sliders land somewhere sensible rather than on a single outlier."""
    values = np.concatenate([np.zeros(998), np.array([-1e6, 1e6])])
    histogram = ValueHistogramInput.from_array(values, bins=8)

    assert histogram.min == -1e6 and histogram.max == 1e6
    assert histogram.p1 == 0.0 and histogram.p99 == 0.0


def test_a_histogram_ignores_non_finite_values() -> None:
    values = np.array([0.0, 1.0, np.nan, np.inf, 2.0])
    histogram = ValueHistogramInput.from_array(values, bins=4)

    assert (histogram.min, histogram.max) == (0.0, 2.0)
    assert sum(histogram.histogram) == 3


def test_a_histogram_of_nothing_finite_is_an_error() -> None:
    with pytest.raises(ValueError, match="no finite values"):
        ValueHistogramInput.from_array(np.full(4, np.nan))


def test_one_anchor_per_channel_each_keyed_by_its_position() -> None:
    """A contrast window is per channel: a nuclear stain and a brightfield
    channel in the same stack share no sensible range, so one histogram over
    both would describe neither."""
    array = xr.DataArray(
        np.stack([np.zeros((4, 4)), np.full((4, 4), 100.0)]), dims=["c", "y", "x"]
    )
    anchors = CoordinateAnchorInput.histogram_anchors(array, bins=4)

    assert len(anchors) == 2
    assert [anchor.axis_anchors[0].axis for anchor in anchors] == ["c", "c"]
    assert [anchor.axis_anchors[0].value for anchor in anchors] == [0, 1]
    assert [anchor.value_histogram.max for anchor in anchors] == [0.0, 100.0]


def test_an_array_with_no_channel_axis_gets_one_anchor_at_the_origin() -> None:
    """So callers do not have to branch on whether the data has channels."""
    array = xr.DataArray(np.random.random((4, 4)), dims=["y", "x"])
    (anchor,) = CoordinateAnchorInput.histogram_anchors(array)

    assert [axis.axis for axis in anchor.axis_anchors] == ["y", "x"]
    assert [axis.value for axis in anchor.axis_anchors] == [0, 0]


def test_an_anchor_can_be_pinned_at_an_explicit_position() -> None:
    array = xr.DataArray(np.random.random((2, 4, 4)), dims=["t", "y", "x"])
    anchor = CoordinateAnchorInput.histogram_anchor(array.isel(t=1), at={"t": 1})

    assert anchor.axis_anchors == (
        type(anchor.axis_anchors[0])(axis="t", value=1),
    )
    assert anchor.value_histogram is not None


def test_an_anchor_needs_dimension_names_it_can_pin() -> None:
    """A bare numpy array carries none, so they have to be spelled out."""
    with pytest.raises(ValueError, match="dims= is required"):
        CoordinateAnchorInput.histogram_anchor(np.random.random((4, 4)))
