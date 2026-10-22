"""Integration tests for the coordinate-system workflow.

The integration counterpart to ``test_coordinate_traits.py``, which stubs every
mutation and so never touches a server. This walks the same path a real
acquisition takes -- a shared physical space, datasets registered into it, a
scene staged over it, a lens on a dataset, an ROI drawn on the lens, and a
segmentation hung off that lens by an identity derivation -- one test per step,
on synthetic volumes small enough to upload in a moment.

What a registration edge is, as verified against this backend rather than assumed:
`register` authors a BY_DIMENSION edge, which carries its own `scale` /
`translation` / `affine` over the `inputAxes` it names. These tests assert those
stored numbers directly; composing a path across such an edge by axis name
(``axis_map_to``, ``transform_points_to(axes=)``) is unit-tested in
``test_coordinate_traits.py``.
"""

import json
from typing import Any, NamedTuple, cast

import numpy as np
import pytest
import xarray as xr

from mikro.mikro import Mikro
from mikro import canonical, create_space, dataset_arrays, space_3d
from mikro.api.schema import (
    AnnotationKind,
    ArrayDataset,
    AxisAnchorInput,
    AxisType,
    BootstrapLayerKind,
    CoordinateAnchorInput,
    CoordinateSystem,
    GetCoordinateGraphQueryCoordinateGraph,
    LayerFilter,
    OmeMetadataInput,
    ScenePolicyInput,
    TransformKind,
    ValueRelation,
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


def _upload(mikro: Mikro, data: xr.DataArray, name: str) -> ArrayDataset:
    """A two-level dataset with one contrast window per channel.

    ``dataset_arrays`` returns level 0 and the coarser levels already split the
    way the mutation takes them -- ``data`` *is* level 0, so listing it in
    ``scales`` as well would upload it twice.
    """
    pyramid, scales = dataset_arrays(data, levels=2, method="mean")
    return mikro.create_array_dataset(
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
def registered_dataset(mikro: Mikro, deployed_app: DeployedMikro) -> Placed:
    """One world, one dataset in it -- uploaded once for the tests below."""
    world = space_3d(deployed_app.mikro, "registered world (micrometers)", unit="micrometer")
    data = _volume(seed=0)
    dataset = _upload(mikro, data, "coordsys_registered")
    world.register(dataset, scale={d: VOXEL_UM for d in ("z", "y", "x")})
    return Placed(world=world, dataset=dataset, data=data)


@pytest.fixture(scope="module")
def derived_dataset(mikro: Mikro, registered_dataset: Placed) -> tuple[ArrayDataset, ArrayDataset]:
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
    derived = mikro.create_array_dataset(
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
    world = space_3d(deployed_app.mikro, "a micrometer world", unit="micrometer")

    assert world.id, "Space should have an ID"
    assert world.name == "a micrometer world"
    assert world.axis_names == ["z", "y", "x"]
    assert {str(axis.unit) for axis in world.axes} == {"micrometer"}
    assert {axis.type for axis in world.axes} == {AxisType.SPACE}


@pytest.mark.integration
def test_register_places_a_dataset_in_the_world(mikro: Mikro, deployed_app: DeployedMikro) -> None:
    """`register` authors one BY_DIMENSION edge over the axes the spaces share.

    The channel axis is deliberately not claimed: it is not a position, and a
    physical space has no business naming it.
    """
    world = space_3d(deployed_app.mikro, "placement world (micrometers)", unit="micrometer")
    dataset = _upload(mikro, _volume(seed=1), "coordsys_placed")

    world.register(dataset, scale={d: VOXEL_UM for d in ("z", "y", "x")})

    graph = deployed_app.mikro.get_coordinate_graph(coordinate_system=world.id)
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

    # A BY_DIMENSION carries its map on itself: the voxel size handed to `register`
    # comes back as the edge's own scale, over the axes it names.
    assert tuple(edge.scale) == (0.2, 0.2, 0.2)


@pytest.mark.integration
def test_register_reads_an_uneven_time_axis_from_a_field(mikro: Mikro, deployed_app: DeployedMikro) -> None:
    """An event-triggered movie: y,x scaled, t read from the instants its frames were taken at.

    One edge says both. The looked-up axis is not among the named ones -- the array, not a
    factor, is its map -- and the range comes back as the values the client read and declared.
    """
    from kanne.scalars import Unit

    instants = np.array([0.0, 0.1, 0.15, 2.0, 2.05, 7.5])
    world = create_space(
        deployed_app.mikro,
        "event world",
        {"t": Unit("second"), "y": Unit("micrometer"), "x": Unit("micrometer")},
    )
    movie = mikro.create_array_dataset(
        data=xr.DataArray(np.zeros((len(instants), 16, 16), dtype="float32"), dims=("t", "y", "x")),
        scales=[],
        name="coordsys_event_movie",
        axes=["t", "y", "x"],
    )
    times = mikro.create_array_dataset(
        data=xr.DataArray(instants, dims=("t",)),
        scales=[],
        name="coordsys_event_times",
        axes=["t"],
    )

    world.register(movie, scale={"y": 0.5, "x": 0.5}, field={"t": times})

    graph = deployed_app.mikro.get_coordinate_graph(coordinate_system=world.id)
    edge = _edge(graph, movie.intrinsic_system.id, world.id)
    assert edge.kind == TransformKind.BY_DIMENSION
    assert tuple(edge.input_axes) == ("y", "x"), "only the scaled axes are named"
    assert tuple(edge.scale) == (0.5, 0.5)
    assert edge.lookup is not None
    assert (edge.lookup.axis, edge.lookup.output_axis, edge.lookup.unit) == ("t", "t", "second")
    assert (edge.lookup.min, edge.lookup.max) == (0.0, 7.5)
    assert str(edge.lookup.field.id) == str(times.intrinsic_system.id)


@pytest.mark.integration
def test_a_field_that_does_not_increase_is_refused_before_the_server(mikro: Mikro, deployed_app: DeployedMikro) -> None:
    """The server never reads the array, so the client is where 'strictly increasing' is checked."""
    from kanne.scalars import Unit

    world = create_space(deployed_app.mikro, "bad event world", {"t": Unit("second"), "y": Unit("micrometer"), "x": Unit("micrometer")})
    movie = mikro.create_array_dataset(
        data=xr.DataArray(np.zeros((3, 8, 8), dtype="float32"), dims=("t", "y", "x")), scales=[], name="coordsys_bad_movie", axes=["t", "y", "x"]
    )
    times = mikro.create_array_dataset(data=xr.DataArray(np.array([0.0, 2.0, 1.0]), dims=("t",)), scales=[], name="coordsys_bad_times", axes=["t"])

    with pytest.raises(ValueError, match="strictly increase"):
        world.register(movie, field={"t": times})


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

    dataset = deployed_app.mikro.create_array_dataset(
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
def test_stage_composes_registered_datasets(mikro: Mikro, deployed_app: DeployedMikro) -> None:
    """A scene composes over a space; what can be drawn was decided by `register`.

    Both datasets are registered before staging -- staging in between would
    simply miss the second one.
    """
    world = space_3d(deployed_app.mikro, "staged world (micrometers)", unit="micrometer")
    for index in (4, 5):
        dataset = _upload(mikro, _volume(seed=index), f"coordsys_staged_{index}")
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
    assert str(deployed_app.mikro.get_scene(id=scene.id).id) == str(scene.id), "Scene should round-trip"


@pytest.mark.integration
def test_the_multiscale_edge_parses_with_its_steps(
    mikro: Mikro,
    registered_dataset: Placed,
) -> None:
    """Every edge in the graph resolves to its concrete type, and a sequence carries its map.

    The pyramid's own downscale edge is a SEQUENCE -- a scale, then the half-voxel
    translation -- and its steps are fields of the edge itself, not edges of their
    own. An arm the fragment fails to select degrades the whole edge to a fieldless
    CatchAll, which is what the first assertion guards.
    """
    graph = mikro.get_coordinate_graph(coordinate_system=registered_dataset.world.id)
    # Typed loosely on purpose: these are heterogeneous unions whose useful
    # fields live on the variants, exactly as in ``_edge`` above.
    edges: list[Any] = list(graph.transformations)

    assert not [t for t in edges if type(t).__name__.endswith("CatchAll")], (
        f"No edge should degrade to a CatchAll: {[type(t).__name__ for t in edges]}"
    )

    sequences = [t for t in edges if t.kind == TransformKind.SEQUENCE]
    assert len(sequences) == 1, "One coarser level means one downscale edge"

    steps: dict[Any, Any] = {step.kind: step for step in sequences[0].steps}
    assert set(steps) == {TransformKind.SCALE, TransformKind.TRANSLATION}

    # A step's parameters are in the axis order of the sequence's input.
    # ``dataset_arrays`` halves the spatial axes only; the channel axis keeps
    # its extent at every level, so it scales by one.
    assert tuple(steps[TransformKind.SCALE].scale) == (1.0, 2.0, 2.0, 2.0)


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
def test_a_selection_is_one_lens_however_often_it_is_asked_for(mikro: Mikro, registered_dataset: Placed) -> None:
    """A lens is a row per dataset and selection, and the whole one is read, not made."""
    dataset = registered_dataset.dataset

    whole = dataset.lens()
    assert whole.id == dataset.lens().id
    assert whole.id == mikro.create_lens(dataset=dataset.id, slices=[]).id
    assert not whole.slices, "The whole lens cuts nothing out"
    # A selection that keeps every position is the whole lens, spelled differently.
    assert dataset.lens(c=0).id == whole.id

    crop = dataset.lens(z=(0, 2), x=(0, 8))
    assert crop.id != whole.id
    assert crop.id == dataset.lens(x=slice(0, 8), z=(0, 2)).id
    # Read back in the server's one spelling: dataset axis order, a step always there.
    assert [(s.axis, s.start, s.stop, s.step) for s in crop.slices] == [("z", 0, 2, 1), ("x", 0, 8, 1)]
    assert tuple(crop.shape) == (1, 2, registered_dataset.data.shape[2], 8)
    assert np.array_equal(
        crop.data.compute().to_numpy(),
        registered_dataset.data.isel(z=slice(0, 2), x=slice(0, 8)).to_numpy(),
    )

    last = dataset.lens(z=-1)
    assert tuple(last.shape)[1] == 1
    assert [(s.axis, s.start) for s in last.slices] == [("z", registered_dataset.data.shape[1] - 1)]


@pytest.mark.integration
def test_a_lens_fetched_by_id_comes_back_as_its_kind(mikro: Mikro, registered_dataset: Placed) -> None:
    """`lens(id)` answers with any kind; an array lens is one you can read pixels off."""
    from mikro.api.schema import ArrayLens, LensKind

    crop = registered_dataset.dataset.lens(z=(0, 2))
    fetched = mikro.get_lens(crop.id)

    assert isinstance(fetched, ArrayLens)
    assert fetched.kind == LensKind.ARRAY
    assert tuple(fetched.data.shape) == tuple(crop.shape)


@pytest.mark.integration
def test_a_scene_is_staged_from_a_lens_and_its_layers_say_how_they_face_the_screen(
    mikro: Mikro, registered_dataset: Placed
) -> None:
    """A crop is staged from the lens, and `render_axes` is the layer's, not the lens'."""
    crop = registered_dataset.dataset.lens(z=(0, 2))
    scene = mikro.create_scene_from_lens(lens=crop.id, nominate=False, name="a staged crop")

    layers = mikro.layers(filters=LayerFilter(scene=scene.id))
    assert layers, "One layer per channel"
    for layer in layers:
        assert str(layer.lens.id) == str(crop.id), "Every layer draws through the staged lens"
        assert (layer.render_axes.y, layer.render_axes.x) == ("y", "x")
    assert not hasattr(crop, "render_axes")


@pytest.mark.integration
def test_draw_annotates_the_lens(mikro: Mikro, registered_dataset: Placed) -> None:
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

    edge = _edge(mikro.get_coordinate_graph(coordinate_system=drawing.id), drawing.id, surface.id)
    assert edge.kind == TransformKind.IDENTITY, (
        "Same axes, same voxels: the drawing sits exactly on the surface"
    )


@pytest.mark.integration
def test_a_path_drawn_on_a_scene_maps_onto_the_voxels_of_a_crop(mikro: Mikro, registered_dataset: Placed) -> None:
    """A shape drawn on a scene is in the world's units, and the graph carries it onto a lens.

    The scene's drawing space copies the world's space axes and is registered
    into it; the dataset reaches the same world by its own registration, and the
    crop is one more edge away. Two of those three edges are BY_DIMENSION, so
    this is the path `transform_points_to` could not walk -- and the channel is
    an axis of the crop the path says nothing about, which is what `axes=` is for.
    """
    scene = registered_dataset.world.stage(name="a scene to draw on")
    in_um = np.array([[0.4, 1.0, 1.2], [0.6, 1.6, 2.0]])
    annotation = mikro.create_annotation(kind=AnnotationKind.PATH, vectors=in_um, scene=scene.id, name="a path")

    drawing = annotation.coordinate_system
    assert drawing is not None
    assert [axis.name for axis in drawing.axes] == ["z", "y", "x"], "A scene is drawn on in space"

    crop = registered_dataset.dataset.lens(z=(1, 4), y=(2, 16), x=(4, 16))
    surface = crop.coordinate_system
    assert surface is not None

    on_crop = drawing.transform_points_to(surface, in_um, axes=("z", "y", "x"))
    assert np.allclose(on_crop, in_um / VOXEL_UM - np.array([1.0, 2.0, 4.0]))

    with pytest.raises(ValueError, match="'c'"):
        drawing.matrix_to(surface)

    # And back: a voxel of the crop, with or without its channel, is a place in the drawing.
    mapped = surface.axis_map_to(drawing)
    assert np.allclose(mapped.apply(on_crop, input_axes=("z", "y", "x")), in_um)


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
