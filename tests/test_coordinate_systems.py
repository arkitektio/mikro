"""Integration tests for the coordinate-system workflow.

The integration counterpart to ``test_coordinate_traits.py``, which stubs every
mutation and so never touches a server. This walks the same path a real
acquisition takes -- a shared physical space, datasets registered into it, a
scene staged over it, a lens on a dataset, an ROI drawn on the lens, and a
segmentation hung off that lens by an identity derivation -- one test per step,
on synthetic volumes small enough to upload in a moment.

Two things constrain what a registration edge can be asserted about, both
verified against this backend rather than assumed:

* `register` authors a BY_DIMENSION edge, and BY_DIMENSION is absent from
  ``TransformationTrait.MATRIX_KINDS``. ``_bfs_path`` skips any kind not in that
  tuple, so ``matrix_to`` / ``transform_points_to`` raise "No composable
  transformation path" across exactly the edges `register` creates. These tests
  therefore read the stored edge instead of composing a matrix through it.
* Nothing reads a registration's numbers back. ``ByDimensionTransformInput``
  takes `scale` / `translation` / `affine`, but ``ByDimensionTransformation``
  exposes none of them -- only `inputAxes`, `outputAxes` and child
  `transformations`, and the server returns that child list empty. So the voxel
  size handed to `register` is not observable at all, and BY_DIMENSION cannot be
  given a client-side matrix until it is.
"""

import json
from typing import Any, NamedTuple, cast

import numpy as np
import pytest
import xarray as xr

from mikro_next import canonical, dataset_arrays, space_3d
from mikro_next.api.schema import (
    AnnotationKind,
    ArrayDataset,
    AxisAnchorInput,
    AxisType,
    BootstrapLayerKind,
    CoordinateAnchorInput,
    CoordinateSystem,
    GetCoordinateGraphQueryCoordinateGraph,
    OmeMetadataInput,
    ScenePolicyInput,
    TransformKind,
    ValueRelation,
    create_array_dataset,
    get_coordinate_graph,
    get_scene,
)

from .conftest import DeployedMikro

# The dims the server wants: time, then channel, then space. ``canonical`` puts
# them in that order, and the order is load-bearing -- the render axes are
# derived from the *position* of the spatial axes.
_DIMS = ("c", "z", "y", "x")

# The voxel size of this imaginary microscope, in micrometers. It belongs to the
# *edge* that registers a dataset into a physical space, not to either space:
# the dataset's grid is in unitless indices, the world is in micrometers.
VOXEL_UM = 0.2


def _volume(seed: int, channels: int = 1) -> xr.DataArray:
    """A small deterministic (c, z, y, x) volume -- channels x 4 x 32 x 32."""
    rng = np.random.default_rng(seed)
    return canonical(
        xr.DataArray(
            rng.random((channels, 4, 32, 32)).astype("float32"),
            dims=["c", "z", "y", "x"],
        )
    )


def _ome(name: str) -> OmeMetadataInput:
    """Minimal OME metadata for one plane, as the JSON string the input takes."""
    return OmeMetadataInput(
        metadataString=json.dumps(
            {
                "@type": "http://www.openmicroscopy.org/Schemas/OME/2016-06#Image",
                "Name": name,
                "Pixels": {
                    "SizeX": 32,
                    "SizeY": 32,
                    "SizeZ": 4,
                    "SizeC": 1,
                    "SizeT": 1,
                },
            }
        )
    )


def _upload(data: xr.DataArray, name: str) -> ArrayDataset:
    """A two-level dataset with one contrast window per channel.

    ``dataset_arrays`` returns level 0 and the coarser levels already split the
    way the mutation takes them -- ``data`` *is* level 0, so listing it in
    ``scales`` as well would upload it twice.
    """
    pyramid, scales = dataset_arrays(data, levels=2, method="mean")
    return create_array_dataset(
        data=pyramid,
        scales=scales,
        name=name,
        # bare names; the kind is inferred (c -> CHANNEL, z/y/x -> SPACE)
        axes=list(_DIMS),
        anchors=_anchors(data),
    )


def _anchors(data: xr.DataArray) -> list[CoordinateAnchorInput]:
    """One contrast window per channel.

    The cast is a typing wart, not a runtime one: the classmethod is declared on
    ``CoordinateAnchorInputTrait`` and so is typed as returning the trait rather
    than the generated model it is actually mixed into.
    """
    return cast(list[CoordinateAnchorInput], CoordinateAnchorInput.histogram_anchors(data))


def _edge(
    graph: GetCoordinateGraphQueryCoordinateGraph,
    source_id: str,
    target_id: str,
) -> Any:  # noqa: ANN401 - a heterogeneous union; the fields live on the variants
    """The stored edge from `source_id` to `target_id`, in its true direction.

    Edges whose concrete type the client does not recognise come back as a
    ``...CatchAll`` carrying no fields at all, so this reads `input`/`output`
    defensively rather than assuming every edge has them.
    """
    for transformation in graph.transformations:
        source = getattr(transformation, "input", None)
        target = getattr(transformation, "output", None)
        if (
            source is not None
            and target is not None
            and str(source.id) == str(source_id)
            and str(target.id) == str(target_id)
        ):
            return transformation
    raise AssertionError(
        f"No edge from {source_id} to {target_id} in "
        f"{[type(t).__name__ for t in graph.transformations]}"
    )


class Placed(NamedTuple):
    """A physical space with one dataset registered into it."""

    world: CoordinateSystem
    dataset: ArrayDataset
    data: xr.DataArray


@pytest.fixture(scope="module")
def registered_dataset(deployed_app: DeployedMikro) -> Placed:
    """One world, one dataset in it -- uploaded once for the tests below."""
    world = space_3d("registered world (micrometers)", unit="micrometer")
    data = _volume(seed=0)
    dataset = _upload(data, "coordsys_registered")
    world.register(dataset, scale={d: VOXEL_UM for d in ("z", "y", "x")})
    return Placed(world=world, dataset=dataset, data=data)


@pytest.fixture(scope="module")
def derived_dataset(registered_dataset: Placed) -> tuple[ArrayDataset, ArrayDataset]:
    """A thresholded child hung off the source's lens by an identity edge.

    ``isel(c=0)`` drops the singleton channel axis so the threshold walks the
    volume itself. A median split is enough to make the values stop being
    intensities and start being labels, which is what CATEGORIZED says.
    """
    lens = registered_dataset.dataset.lens()
    volume = lens.data.isel(c=0).compute().to_numpy()
    segmented = (volume > np.median(volume)).astype(np.uint16)

    data = canonical(xr.DataArray(segmented, dims=["z", "y", "x"]).expand_dims("c"))

    # Single level: ``data`` is level 0, so ``scales`` is empty -- no pyramid.
    # The segmentation shares the source's grid exactly, so its edge back to the
    # lens is an IDENTITY and it carries no physical space of its own; that is
    # reached by composing this edge with the source's registration.
    derived = create_array_dataset(
        data=data,
        scales=[],
        name="coordsys_thresholded",
        axes=list(_DIMS),
        derived_from=[lens.derive_identity(value_relation=ValueRelation.CATEGORIZED)],
        anchors=[
            CoordinateAnchorInput(
                axisAnchors=(AxisAnchorInput(axis="c", value=0),),
                omeMetadata=_ome("thresholded"),
            )
        ],
    )
    return registered_dataset.dataset, derived


@pytest.mark.integration
def test_space_3d_creates_a_physical_space(deployed_app: DeployedMikro) -> None:
    """A physical space is ordinary and ownerless: (z, y, x) in one length unit."""
    world = space_3d("a micrometer world", unit="micrometer")

    assert world.id, "Space should have an ID"
    assert world.name == "a micrometer world"
    assert world.axis_names == ["z", "y", "x"]
    assert {str(axis.unit) for axis in world.axes} == {"micrometer"}
    assert {axis.type for axis in world.axes} == {AxisType.SPACE}


@pytest.mark.integration
def test_register_places_a_dataset_in_the_world(deployed_app: DeployedMikro) -> None:
    """`register` authors one BY_DIMENSION edge over the axes the spaces share.

    The channel axis is deliberately not claimed: it is not a position, and a
    physical space has no business naming it.
    """
    world = space_3d("placement world (micrometers)", unit="micrometer")
    dataset = _upload(_volume(seed=1), "coordsys_placed")

    world.register(dataset, scale={d: VOXEL_UM for d in ("z", "y", "x")})

    graph = get_coordinate_graph(coordinate_system=world.id)
    intrinsic = dataset.intrinsic_system
    assert intrinsic is not None, "Dataset should carry its own pixel grid"
    assert str(intrinsic.id) in {str(s.id) for s in graph.systems}, (
        "The dataset's grid should be reachable from the world"
    )

    edge = _edge(graph, intrinsic.id, world.id)
    assert edge.kind == TransformKind.BY_DIMENSION, (
        "A registration names the shared axes, so it is BY_DIMENSION"
    )
    # The edge sets out from the dataset's grid and lands in the physical space,
    # which stays three-dimensional.
    assert [axis.name for axis in edge.input.axes] == list(_DIMS)
    assert [axis.name for axis in edge.output.axes] == ["z", "y", "x"]

    # The claim itself names only the shared axes. The channel axis is not a
    # position, so a physical world has no business naming it -- and
    # BY_DIMENSION is exactly what lets the edge stay silent about one.
    assert tuple(edge.input_axes) == ("z", "y", "x")
    assert tuple(edge.output_axes) == ("z", "y", "x")
    assert "c" not in edge.input_axes

    # The backend materialises per-axis children now, so this is the assertion the old
    # pin (`by_dimension_children == ()`) said to become: the voxel size handed to
    # `register` comes back as a SCALE child over the shared spatial axes.
    scales = [child for child in edge.by_dimension_children if child.kind == TransformKind.SCALE]
    assert scales, "the voxel size handed to `register` is materialised as a SCALE child"
    assert tuple(scales[0].scale) == (0.2, 0.2, 0.2)
    assert tuple(scales[0].output_axes) == ("z", "y", "x")


@pytest.mark.integration
def test_histogram_anchors_splits_on_the_channel_axis(
    deployed_app: DeployedMikro,
) -> None:
    """One contrast window per channel -- and one anchor when there is no channel axis.

    A nuclear stain and a brightfield channel share no sensible range, so one
    histogram over both describes neither.
    """
    two_channels = _volume(seed=2, channels=2)
    anchors = _anchors(two_channels)
    assert len(anchors) == 2, "One anchor per channel"
    assert [a.axis_anchors[0].value for a in anchors] == [0, 1]
    assert {a.axis_anchors[0].axis for a in anchors} == {"c"}

    dataset = create_array_dataset(
        data=two_channels,
        scales=[],
        name="coordsys_two_channel",
        axes=list(_DIMS),
        anchors=anchors,
    )
    assert dataset.id
    assert set(dataset.axis_names) == set(_DIMS)

    # No axis to split on -- callers should not have to branch on that.
    flat = xr.DataArray(
        np.random.default_rng(3).random((4, 32, 32)).astype("float32"),
        dims=["z", "y", "x"],
    )
    fallback = _anchors(flat)
    assert len(fallback) == 1, "Falls back to a single anchor covering the whole array"
    assert {a.axis for a in fallback[0].axis_anchors} == {"z", "y", "x"}


@pytest.mark.integration
def test_stage_composes_registered_datasets(deployed_app: DeployedMikro) -> None:
    """A scene composes over a space; what can be drawn was decided by `register`.

    Both datasets are registered before staging -- staging in between would
    simply miss the second one.
    """
    world = space_3d("staged world (micrometers)", unit="micrometer")
    for index in (4, 5):
        dataset = _upload(_volume(seed=index), f"coordsys_staged_{index}")
        world.register(dataset, scale={d: VOXEL_UM for d in ("z", "y", "x")})

    # Z-stacks, so the layer recipe is a max-intensity projection over z.
    scene = world.stage(
        name="staged world",
        policy=ScenePolicyInput(kind=BootstrapLayerKind.VOLUME),
    )

    assert scene.id, "Scene should have an ID"
    assert str(scene.world_coordinate_system.id) == str(world.id), (
        "The scene adopts the space it was staged from as its world"
    )
    assert str(get_scene(id=scene.id).id) == str(scene.id), "Scene should round-trip"


@pytest.mark.integration
def test_the_multiscale_edge_parses_with_its_children(
    registered_dataset: Placed,
) -> None:
    """Every edge in the graph resolves to its concrete type, children included.

    A composite edge's children are a union discriminated on ``__typename``, so
    a child selection omitting it cannot be tagged and takes the whole parent
    down with it -- the pyramid's own downscale edge used to come back as a
    fieldless CatchAll. This is the regression test for that.
    """
    graph = get_coordinate_graph(coordinate_system=registered_dataset.world.id)
    # Typed loosely on purpose: these are heterogeneous unions whose useful
    # fields live on the variants, exactly as in ``_edge`` above.
    edges: list[Any] = list(graph.transformations)

    assert not [t for t in edges if type(t).__name__.endswith("CatchAll")], (
        f"No edge should degrade to a CatchAll: {[type(t).__name__ for t in edges]}"
    )

    sequences = [t for t in edges if t.kind == TransformKind.SEQUENCE]
    assert len(sequences) == 1, "One coarser level means one downscale edge"

    children: dict[Any, Any] = {child.kind: child for child in sequences[0].sequence_children}
    assert set(children) == {TransformKind.SCALE, TransformKind.TRANSLATION}

    scale = children[TransformKind.SCALE]
    assert tuple(scale.input_axes) == _DIMS, "A child carries the axes it acts on"
    # ``dataset_arrays`` halves the spatial axes only; the channel axis keeps
    # its extent at every level, so it scales by one.
    assert tuple(scale.scale) == (1.0, 2.0, 2.0, 2.0)


@pytest.mark.integration
def test_lens_reads_back_the_volume(registered_dataset: Placed) -> None:
    """A lens with no selections frames the whole dataset, and its data round-trips."""
    lens = registered_dataset.dataset.lens()

    assert lens.id, "Lens should have an ID"
    assert tuple(lens.axis_names) == _DIMS
    assert tuple(lens.shape) == registered_dataset.data.shape

    read_back = lens.data.isel(c=0).compute()
    expected = registered_dataset.data.isel(c=0)
    assert read_back.shape == expected.shape
    assert read_back.dtype == expected.dtype
    assert np.allclose(read_back.to_numpy(), expected.to_numpy()), (
        "The uploaded voxels should come back unchanged"
    )


@pytest.mark.integration
def test_draw_annotates_the_lens(registered_dataset: Placed) -> None:
    """Vectors are read in the lens' own coordinate system; the last axis is (z, y, x).

    The drawing is not filed *in* the lens' space -- it gets a space of its own,
    tied to the surface it was drawn on by an IDENTITY edge. That is what lets a
    drawing be moved or reinterpreted without rewriting the data's own grid.
    """
    lens = registered_dataset.dataset.lens()
    surface = lens.coordinate_system
    assert surface is not None, "A lens frames some coordinate system"

    vectors = np.array([[0.0, 0.0, 0.0], [2.0, 8.0, 8.0]])
    annotation = lens.draw(kind=AnnotationKind.RECTANGLE, vectors=vectors, name="a rectangle")

    assert annotation.id, "Annotation should have an ID"
    assert annotation.kind == AnnotationKind.RECTANGLE
    assert np.allclose(np.asarray(annotation.vectors, dtype=float), vectors)

    drawing = annotation.coordinate_system
    assert drawing is not None
    assert str(drawing.id) != str(surface.id), "A drawing gets its own space"
    assert [axis.name for axis in drawing.axes] == list(_DIMS), (
        "The drawing space mirrors the axes of the surface it was drawn on"
    )

    edge = _edge(get_coordinate_graph(coordinate_system=drawing.id), drawing.id, surface.id)
    assert edge.kind == TransformKind.IDENTITY, (
        "Same axes, same voxels: the drawing sits exactly on the surface"
    )


@pytest.mark.integration
def test_derive_identity_creates_a_categorized_child(
    derived_dataset: tuple[ArrayDataset, ArrayDataset],
) -> None:
    """A segmentation shares the source grid exactly, so the edge is an IDENTITY."""
    source, derived = derived_dataset

    assert derived.id, "Derived dataset should have an ID"
    assert derived.name == "coordsys_thresholded"
    assert tuple(derived.axis_names) == _DIMS
    assert tuple(derived.shape) == tuple(source.shape), (
        "An identity derivation keeps the source's axes and voxels"
    )
    assert len(derived.data_arrays) == 1, "Empty scales= means a single level"
    assert derived.data_arrays[0].level == 0

    assert derived.intrinsic_system is not None
    assert source.intrinsic_system is not None
    assert str(derived.intrinsic_system.id) != str(source.intrinsic_system.id), (
        "The child gets its own grid; the edge is what relates the two"
    )


@pytest.mark.integration
def test_intrinsic_system_stages_a_label_scene(
    registered_dataset: Placed,
    derived_dataset: tuple[ArrayDataset, ArrayDataset],
) -> None:
    """The child stages in its own pixel grid, not in the source's physical space.

    A scene over a shared space composes what has been *registered* into it, and
    this dataset reaches physical scale through a derivation edge instead. LABEL
    is stated rather than inferred: nothing about an array distinguishes a label
    map from an image.
    """
    _, derived = derived_dataset
    grid = derived.intrinsic_system
    assert grid is not None

    scene = grid.stage(
        name="thresholded",
        policy=ScenePolicyInput(kind=BootstrapLayerKind.LABEL),
    )

    assert scene.id, "Scene should have an ID"
    assert str(scene.world_coordinate_system.id) == str(grid.id)
    assert str(scene.world_coordinate_system.id) != str(registered_dataset.world.id), (
        "Staging in the child's own grid, not in the micrometer world"
    )
