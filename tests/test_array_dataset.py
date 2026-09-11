"""Integration tests for the array-dataset path -- ``create_array_dataset``.

This is what replaced the deprecated ``from_array_like`` / ``Image`` route.
Two things are different and both are exercised here: the array keeps its own
*named* axes rather than being forced into a fixed ``ctzyx`` layout, and the
resolution pyramid is stated rather than inferred -- ``data`` is level 0 and
``scales`` carries only what is coarser than it.

The helpers the converters use are used here too (``dataset_arrays``,
``CoordinateAnchorInput.histogram_anchors``) rather than hand-rolled equivalents:
they are the supported way to build these arguments, so they are what should be
under test end to end. Their offline behaviour lives in ``test_pyramid.py`` and
``test_array_dataset_validation.py``.

Axis order is not arbitrary: the server requires axes sorted by type -- time,
then channel and custom types, then space -- and the array's dimension order is
that order.
"""

import tempfile
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import xarray as xr

from mikro_next import dataset_arrays
from mikro_next.api.schema import (
    AxisInput,
    AxisType,
    CoordinateAnchorInput,
    DatasetDerivedFromInput,
    IdentityTransformInput,
    ScaleInput,
    ScaleMethod,
    SourceFileInput,
    create_array_dataset,
    create_folder,
    from_file_like,
    get_array_dataset,
)

from .conftest import DeployedMikro


def _make_volume() -> xr.DataArray:
    """A small labelled (c, z, y, x) volume suitable for fast uploads.

    The server requires axes ordered by type -- time, then channel and custom
    types, then space -- and the array's dimension order *is* that order, so the
    channel axis leads.
    """
    return xr.DataArray(
        np.random.random((2, 4, 64, 64)).astype("float32"),
        dims=["c", "z", "y", "x"],
    )


def _axes() -> list[AxisInput]:
    return [
        AxisInput(name="c", type=AxisType.CHANNEL),
        AxisInput(name="z", type=AxisType.SPACE),
        AxisInput(name="y", type=AxisType.SPACE),
        AxisInput(name="x", type=AxisType.SPACE),
    ]


@pytest.mark.integration
def test_create_array_dataset(deployed_app: DeployedMikro) -> None:
    """Create a dataset from a single arbitrarily-labelled array."""
    data = _make_volume()
    dataset = create_array_dataset(
        data=data,
        # ``data`` *is* level 0; listing it in ``scales`` too would upload it
        # twice, which the server rejects (one_data_array_per_level).
        scales=[],
        name="array_dataset_basic",
        axes=_axes(),
    )
    assert dataset.id, "Dataset should have an ID"
    assert dataset.name == "array_dataset_basic"
    # The axis names come back as given rather than being renamed into a fixed
    # t/c/z/y/x vocabulary. Their *order* is no longer free -- the server
    # requires axes sorted by type -- so only the names are asserted here.
    assert set(dataset.axis_names) == {"z", "y", "x", "c"}


@pytest.mark.integration
def test_create_array_dataset_from_bare_axis_names(deployed_app: DeployedMikro) -> None:
    """The common case needs no ``AxisInput`` at all: a bare name carries its
    own conventional type (``c`` -> CHANNEL, everything spatial -> SPACE)."""
    dataset = create_array_dataset(
        data=_make_volume(),
        scales=[],
        name="array_dataset_bare_axes",
        axes=["c", "z", "y", "x"],
    )
    assert set(dataset.axis_names) == {"c", "z", "y", "x"}


@pytest.mark.integration
def test_create_array_dataset_with_pyramid(deployed_app: DeployedMikro) -> None:
    """Create a dataset with a multiscale pyramid of scale arrays.

    ``dataset_arrays`` returns the two halves already separated -- level 0 as
    ``data``, the coarser levels as ``scales`` -- which is the split the mutation
    takes and the one that silently uploads the base twice if got wrong.
    """
    data, scales = dataset_arrays(_make_volume(), levels=3, method="mean")

    dataset = create_array_dataset(
        data=data,
        scales=scales,
        name="array_dataset_pyramid",
        axes=_axes(),
    )
    assert dataset.id
    assert len(dataset.data_arrays) == len(scales) + 1, "All pyramid levels should be stored"
    assert {arr.level for arr in dataset.data_arrays} == set(range(len(scales) + 1)), (
        "Pyramid levels should be correctly labeled"
    )
    # A pyramid halves the spatial axes only -- a position halfway between two
    # channels is not a thing -- so every level keeps both channels.
    assert all(arr.shape[0] == 2 for arr in dataset.data_arrays)


@pytest.mark.integration
def test_create_array_dataset_with_a_hand_built_scale(deployed_app: DeployedMikro) -> None:
    """``scales`` also takes levels built any other way, as long as they are
    numbered from 1 and share the base's dims."""
    data = _make_volume()
    coarse = data.coarsen(z=2, y=2, x=2, boundary="trim").mean().astype(data.dtype)  # type: ignore[attr-defined]

    dataset = create_array_dataset(
        data=data,
        scales=[ScaleInput(level=1, array=coarse, scaleMethod=ScaleMethod.AREA)],
        name="array_dataset_manual_scale",
        axes=_axes(),
    )
    assert {arr.level for arr in dataset.data_arrays} == {0, 1}


@pytest.mark.integration
def test_create_array_dataset_with_anchors(deployed_app: DeployedMikro) -> None:
    """Create a dataset with per-channel coordinate anchors and histograms.

    ``histogram_anchors`` produces one anchor per channel, each computed from
    that channel's slice alone -- a nuclear stain and a brightfield channel
    share no sensible contrast range, so one histogram over both describes
    neither.
    """
    data = _make_volume()
    dataset = create_array_dataset(
        data=data,
        scales=[],
        name="array_dataset_anchored",
        axes=_axes(),
        anchors=cast(
            list[CoordinateAnchorInput], CoordinateAnchorInput.histogram_anchors(data)
        ),
    )
    assert dataset.id
    assert dataset.name == "array_dataset_anchored"


@pytest.mark.integration
def test_create_array_dataset_in_a_folder(deployed_app: DeployedMikro) -> None:
    """A dataset can be filed at creation rather than moved afterwards."""
    folder = create_folder(name="array_dataset_folder")
    dataset = create_array_dataset(
        data=_make_volume(),
        scales=[],
        name="array_dataset_filed",
        axes=_axes(),
        folder=folder.id,
    )
    assert dataset.id
    assert get_array_dataset(id=dataset.id).id == dataset.id


@pytest.mark.integration
def test_create_array_dataset_recording_the_file_it_came_from(
    deployed_app: DeployedMikro,
) -> None:
    """What every converter does: record the bytes the arrays were read out of.

    A source file is deliberately not a coordinate-graph edge -- a file has no
    space, so there is no map to state and ``derivedFrom`` would be the wrong
    mechanism.
    """
    with tempfile.TemporaryDirectory() as scratch:
        source = Path(scratch) / "acquisition.txt"
        source.write_bytes(b"not really a microscope file, but it is bytes")
        uploaded = from_file_like(file=str(source), file_name=source.name)

    dataset = create_array_dataset(
        data=_make_volume(),
        scales=[],
        name="array_dataset_from_file",
        axes=_axes(),
        source_files=[SourceFileInput(file=uploaded.id, seriesIdentifier="series 0")],
    )
    assert dataset.id


@pytest.mark.integration
def test_a_derived_dataset_records_the_dataset_it_came_from(
    deployed_app: DeployedMikro,
) -> None:
    """A segmentation of a volume shares that volume's grid, so its lineage edge
    is an identity transform: same grid, different values."""
    source = create_array_dataset(
        data=_make_volume(), scales=[], name="array_dataset_lineage_source", axes=_axes()
    )

    derived = create_array_dataset(
        data=xr.DataArray(
            np.zeros((2, 4, 64, 64), dtype="uint16"), dims=["c", "z", "y", "x"]
        ),
        scales=[],
        name="array_dataset_lineage_derived",
        axes=_axes(),
        derived_from=[
            DatasetDerivedFromInput(dataset=source.id, transform=IdentityTransformInput())
        ],
    )
    assert derived.id
    assert derived.id != source.id


@pytest.mark.integration
def test_create_array_dataset_rejects_mismatched_axes(
    deployed_app: DeployedMikro,
) -> None:
    """The model-level trait rejects axes that don't cover the data dims."""
    data = _make_volume()
    with pytest.raises(Exception):
        create_array_dataset(
            data=data,
            scales=[],
            name="array_dataset_bad",
            # Missing the "c" axis -> should fail before any upload.
            axes=[
                AxisInput(name="z", type=AxisType.SPACE),
                AxisInput(name="y", type=AxisType.SPACE),
                AxisInput(name="x", type=AxisType.SPACE),
            ],
        )
