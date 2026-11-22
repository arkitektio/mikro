"""Unit tests for the coordinate system and transformation traits.

These construct the generated fragment models directly — no server needed.
"""

from collections.abc import Callable, Sequence
from types import SimpleNamespace
from typing import Any, TypedDict

import numpy as np
import pytest
from kanne.scalars import Unit

from mikro.api.schema import (
    UNSET,
    ArrayDataset,
    Axis,
    ByDimensionTransformInput,
    CoordinateSystem,
    PhysicalAxisInput,
    Scene,
    TransformationAffineTransformation,
    TransformationByDimensionTransformation,
    TransformationIdentityTransformation,
    TransformationMapAxisTransformation,
    TransformationPart,
    TransformationRotationTransformation,
    TransformationScaleTransformation,
    TransformationSequenceTransformation,
    TransformationTranslationTransformation,
    TransformationUnmappableTransformation,
)
from mikro.traits import (
    PathStep,
    Registrable,
    _bfs_path,
    _compose_axis_maps,
    _infer_transform_kind,
)
from mikro.vocabulary import Calibration


def make_system(id: str, name: str, axis_names: list[str]) -> CoordinateSystem:
    return CoordinateSystem(
        id=id,
        name=name,
        axes=tuple(
            Axis(id=f"{id}-{axis}", order=i, name=axis, type="SPACE")
            for i, axis in enumerate(axis_names)
        ),
    )


PIX = make_system("1", "pixels", ["y", "x"])
UM = make_system("2", "microns", ["y", "x"])
STAGE = make_system("3", "stage", ["y", "x"])


def scale_t(
    id: str = "t-scale",
    input: CoordinateSystem = PIX,
    output: CoordinateSystem = UM,
    scale: tuple[float, ...] = (0.5, 2.0),
) -> TransformationScaleTransformation:
    return TransformationScaleTransformation(
        id=id, kind="SCALE", version=0, input=input, output=output, scale=scale
    )


def translation_t(
    id: str = "t-trans",
    input: CoordinateSystem = UM,
    output: CoordinateSystem = STAGE,
    translation: tuple[float, ...] = (10.0, -5.0),
) -> TransformationTranslationTransformation:
    return TransformationTranslationTransformation(
        id=id,
        kind="TRANSLATION",
        version=0,
        input=input,
        output=output,
        translation=translation,
    )


def part(
    kind: str,
    axes: Sequence[str],
    to: Sequence[str] | None = None,
    *,
    scale: tuple[float, ...] = (),
    translation: tuple[float, ...] = (),
    affine: tuple[tuple[float, ...], ...] = (),
    field: dict[str, object] | None = None,
) -> TransformationPart:
    """One part as the wire spells it: every parameter present, the ones its kind does not read empty."""
    return TransformationPart(
        kind=kind,
        inputAxes=tuple(axes),
        outputAxes=tuple(to or axes),
        scale=scale,
        translation=translation,
        affine=affine,
        field=field,
    )


def by_dimension_t(
    input: CoordinateSystem,
    output: CoordinateSystem,
    *parts_: TransformationPart,
    id: str = "t-dim",
) -> TransformationByDimensionTransformation:
    """A BY_DIMENSION of `parts_`, the edge's own axes their concatenation."""
    return TransformationByDimensionTransformation(
        id=id,
        kind="BY_DIMENSION",
        version=0,
        input=input,
        output=output,
        inputAxes=tuple(axis for p in parts_ for axis in p.input_axes),
        outputAxes=tuple(axis for p in parts_ for axis in p.output_axes),
        parts=parts_,
    )


def field_part(
    field: CoordinateSystem,
    consumed: tuple[str, ...] = ("t",),
    produced: tuple[str, ...] = ("t",),
    *,
    dereference: bool = False,
) -> TransformationPart:
    """A FIELD part reading `consumed` from `field`'s array, giving `produced`."""
    return part(
        "FIELD",
        consumed,
        produced,
        field={
            "values": "SCALAR",
            "spatial": False,
            "dereference": dereference,
            "field": {"id": field.id},
        },
    )


def step(
    kind: str,
    scale: tuple[float, ...] = (),
    translation: tuple[float, ...] = (),
    affine: tuple[tuple[float, ...], ...] = (),
) -> dict[str, object]:
    """One step of a SEQUENCE as the wire spells it: every parameter present, the ones
    its kind does not read empty."""
    return {"kind": kind, "scale": scale, "translation": translation, "affine": affine}


def sequence_t(
    *steps: dict[str, object],
    id: str = "t-seq",
    input: CoordinateSystem = PIX,
    output: CoordinateSystem = UM,
) -> TransformationSequenceTransformation:
    return TransformationSequenceTransformation(
        id=id, kind="SEQUENCE", version=0, input=input, output=output, steps=steps
    )


class TestTransformationMatrix:
    def test_scale_matrix_and_apply(self) -> None:
        t = scale_t()
        expected = np.diag([0.5, 2.0, 1.0])
        assert np.allclose(t.as_matrix(), expected)
        assert np.allclose(t.apply([[2.0, 3.0], [4.0, 1.0]]), [[1.0, 6.0], [2.0, 2.0]])
        # single point keeps its shape
        assert np.allclose(t.apply([2.0, 3.0]), [1.0, 6.0])

    def test_translation_matrix(self) -> None:
        t = translation_t()
        assert np.allclose(t.apply([1.0, 1.0]), [11.0, -4.0])

    def test_affine_matrix_with_translation_column(self) -> None:
        t = TransformationAffineTransformation(
            id="t-aff",
            kind="AFFINE",
            version=0,
            input=PIX,
            output=UM,
            affine=((2.0, 0.0, 1.0), (0.0, 3.0, -1.0)),
        )
        matrix = t.as_matrix()
        assert matrix.shape == (3, 3)
        assert np.allclose(t.apply([1.0, 1.0]), [3.0, 2.0])

    def test_rotation_square_matrix_heuristic(self) -> None:
        # a square N x N orthonormal matrix (no translation column) — the
        # input system is selected, so the shape heuristic applies
        t = TransformationRotationTransformation(
            id="t-rot",
            kind="ROTATION",
            version=0,
            input=PIX,
            output=UM,
            affine=((0.0, -1.0), (1.0, 0.0)),
        )
        matrix = t.as_matrix()
        assert matrix.shape == (3, 3)
        assert np.allclose(matrix[:2, 2], [0.0, 0.0])
        assert np.allclose(t.apply([1.0, 0.0]), [0.0, 1.0])

    def test_identity_needs_a_system(self) -> None:
        t = TransformationIdentityTransformation(
            id="t-id", kind="IDENTITY", version=0, input=PIX, output=PIX
        )
        assert np.allclose(t.as_matrix(), np.eye(3))
        # Every edge joins two systems on the wire, so an edge without them is one a
        # narrower selection read: constructed, not parsed.
        bare = TransformationIdentityTransformation.model_construct(
            id="t-id2", kind="IDENTITY", version=0
        )
        with pytest.raises(ValueError, match="dimensionality"):
            bare.as_matrix()

    def test_inverse_round_trip(self) -> None:
        t = scale_t()
        point = np.array([3.0, 7.0])
        assert np.allclose(t.apply_inverse(t.apply(point)), point)

    def test_non_square_inverse_raises(self) -> None:
        t = TransformationAffineTransformation(
            id="t-drop",
            kind="AFFINE",
            version=0,
            input=make_system("4", "zyx", ["z", "y", "x"]),
            output=UM,
            affine=((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0)),  # 3D -> 2D
        )
        with pytest.raises(ValueError, match="3 -> 2"):
            t.inverse_matrix()

    def test_map_axis_permutation(self) -> None:
        yx = make_system("5", "yx", ["y", "x"])
        xy = make_system("6", "xy", ["x", "y"])
        t = TransformationMapAxisTransformation(
            id="t-map",
            kind="MAP_AXIS",
            version=0,
            input=yx,
            output=xy,
            inputAxes=("y", "x"),
            outputAxes=("y", "x"),
        )
        assert np.allclose(t.apply([1.0, 2.0]), [2.0, 1.0])

    def test_map_axis_needs_systems(self) -> None:
        t = TransformationMapAxisTransformation.model_construct(
            id="t-map2",
            kind="MAP_AXIS",
            version=0,
            input_axes=("y", "x"),
            output_axes=("y", "x"),
        )
        with pytest.raises(ValueError, match="coordinate systems"):
            t.as_matrix()

    def test_a_sequence_composes_its_steps_first_to_last(self) -> None:
        """A pyramid level: a scale, then the half-voxel translation. Order matters --
        composed the other way round the offset would be scaled too."""
        seq = sequence_t(
            step("SCALE", scale=(2.0, 2.0)), step("TRANSLATION", translation=(0.5, 0.5))
        )
        assert np.allclose(seq.apply([1.0, 3.0]), [2.5, 6.5])
        assert np.allclose(seq.apply_inverse([2.5, 6.5]), [1.0, 3.0])

    def test_a_sequence_step_may_be_an_affine_or_an_identity(self) -> None:
        seq = sequence_t(
            step("IDENTITY"),
            step("AFFINE", affine=((2.0, 0.0, 1.0), (0.0, 3.0, -1.0))),
        )
        assert np.allclose(seq.apply([1.0, 1.0]), [3.0, 2.0])

    def test_a_sequence_without_steps_has_no_matrix(self) -> None:
        with pytest.raises(ValueError, match="no steps"):
            sequence_t().as_matrix()

    def test_unmappable_has_no_matrix(self) -> None:
        unmappable = TransformationUnmappableTransformation(
            id="t-un", kind="UNMAPPABLE", version=0, input=PIX, output=UM
        )
        with pytest.raises(NotImplementedError, match="no matrix"):
            unmappable.as_matrix()

    def test_wrong_point_dimension(self) -> None:
        with pytest.raises(ValueError, match="dimension"):
            scale_t().apply([1.0, 2.0, 3.0])


class TestCoordinateSystemHelpers:
    def test_axis_helpers(self) -> None:
        system = CoordinateSystem(
            id="7",
            name="sys",
            axes=(
                Axis(id="x", order=1, name="x", type="SPACE", longName="width"),
                Axis(id="y", order=0, name="y", type="SPACE"),
            ),
        )
        assert system.ndim == 2
        assert system.axis_names == ["y", "x"]
        assert list(system.units) == ["y", "x"]
        assert system.get_axis("x").id == "x"
        assert system.get_axis("width").id == "x"
        with pytest.raises(KeyError, match="Available axes"):
            system.get_axis("z")


class TestCalibrateValidation:
    def make_dataset(self, intrinsic: CoordinateSystem | None) -> ArrayDataset:
        from mikro.api.schema import ArrayDataset

        return ArrayDataset(
            descriptors={},
            id="d1",
            name="ds",
            axisNames=("y", "x"),
            shape=(10, 10),
            multiscale=False,
            intrinsicSystem=intrinsic,
            dataArrays=(),
        )

    def test_requires_intrinsic_system(self) -> None:
        with pytest.raises(ValueError, match="intrinsic"):
            self.make_dataset(None).calibrate(
                {"y": Calibration(0.1, Unit("µm")), "x": Calibration(0.1, Unit("µm"))}
            )

    def test_mapping_must_cover_every_axis(self) -> None:
        with pytest.raises(ValueError, match="every intrinsic axis"):
            self.make_dataset(PIX).calibrate({"y": Calibration(0.1, Unit("µm"))})

    def test_list_form_needs_exactly_one_of_scale_or_affine(self) -> None:
        with pytest.raises(ValueError, match="exactly"):
            self.make_dataset(PIX).calibrate([])


class TestInferTransformKind:
    def test_each_parameter_maps_to_its_kind(self) -> None:
        assert _infer_transform_kind(None, None, [[1.0, 0.0]], None)[0] == "AFFINE"
        assert _infer_transform_kind([1.0], None, None, None)[0] == "SCALE"
        assert _infer_transform_kind(None, [1.0], None, None)[0] == "TRANSLATION"
        assert _infer_transform_kind(None, None, None, ["x"])[0] == "MAP_AXIS"
        assert _infer_transform_kind(None, None, None, None)[0] == "IDENTITY"

    def test_scale_and_translation_fold_into_affine(self) -> None:
        kind, scale, translation, affine = _infer_transform_kind(
            [2.0, 3.0], [1.0, -1.0], None, None
        )
        assert kind == "AFFINE" and scale is None and translation is None
        assert np.allclose(affine, [[2.0, 0.0, 1.0], [0.0, 3.0, -1.0]])

    def test_affine_conflicts_with_scale(self) -> None:
        with pytest.raises(ValueError, match="not both"):
            _infer_transform_kind([1.0], None, [[1.0]], None)


class TestPathComposition:
    def test_path_with_inverted_edge(self) -> None:
        # PIX -> UM (scale), STAGE -> UM (translation): the path PIX -> STAGE
        # must traverse the second edge inverted.
        edges = [scale_t(), translation_t(input=STAGE, output=UM)]
        steps = _bfs_path(edges, "1", "3")
        assert [(s.transformation.id, s.inverted) for s in steps] == [
            ("t-scale", False),
            ("t-trans", True),
        ]
        matrix = _compose_axis_maps(steps, PIX.axis_names).matrix
        expected = np.linalg.inv(edges[1].as_matrix()) @ edges[0].as_matrix()
        assert np.allclose(matrix, expected)

    def test_path_via_trait_with_prefetched_graph(self) -> None:
        graph = SimpleNamespace(
            transformations=[scale_t(), translation_t(input=UM, output=STAGE)]
        )
        matrix = PIX.matrix_to(STAGE, graph=graph)
        # y=2,x=4 pixels -> scale (1, 8) -> translate (11, 3)
        assert np.allclose(
            PIX.transform_points_to(STAGE, [2.0, 4.0], graph=graph), [11.0, 3.0]
        )
        assert np.allclose(matrix @ [2.0, 4.0, 1.0], [11.0, 3.0, 1.0])

    def test_self_path_is_identity(self) -> None:
        graph = SimpleNamespace(transformations=[])
        assert PIX.path_to(PIX, graph=graph) == []
        assert np.allclose(PIX.matrix_to(PIX, graph=graph), np.eye(3))

    def test_unwalkable_edges_are_excluded(self) -> None:
        far = make_system("9", "far", ["y", "x"])
        unmappable = TransformationUnmappableTransformation(
            id="t-un", kind="UNMAPPABLE", version=0, input=PIX, output=far
        )
        with pytest.raises(ValueError, match="No composable transformation path"):
            _bfs_path([unmappable], "1", "9")

    def test_a_sequence_is_walkable_when_every_step_has_a_matrix(self) -> None:
        seq = sequence_t(
            step("SCALE", scale=(2.0, 2.0)), step("TRANSLATION", translation=(0.5, 0.5))
        )
        (only,) = _bfs_path([seq], "1", "2")
        assert only.transformation is seq
        graph = SimpleNamespace(transformations=[seq])
        assert np.allclose(
            PIX.transform_points_to(UM, [1.0, 3.0], graph=graph), [2.5, 6.5]
        )

    def test_a_placing_field_is_walked_forwards_and_leaves_its_axes_out(self) -> None:
        """A FIELD timing a movie: t is the array's, y and x pass through -- forwards only."""
        movie = make_system("30", "movie", ["t", "y", "x"])
        world = make_system("31", "world", ["t", "y", "x"])
        times = make_system("32", "times", ["t"])
        timed = by_dimension_t(
            movie, world, part("IDENTITY", ["y", "x"]), field_part(times), id="t-times"
        )

        steps = _bfs_path([timed], "30", "31")
        assert [(s.transformation.id, s.inverted) for s in steps] == [
            ("t-times", False)
        ]
        composed = _compose_axis_maps(steps, movie.axis_names)
        assert composed.output_axes == ("y", "x"), (
            "t is the array's, so the map says nothing about it"
        )

        with pytest.raises(ValueError, match="No composable"):
            _bfs_path([timed], "31", "30")

    def test_a_key_is_never_walked(self) -> None:
        """A mask's ids land on an INDEX axis: a key, which places nothing."""
        mask = make_system("33", "mask", ["y", "x"])
        objects = make_system("34", "objects", ["i"])
        key = by_dimension_t(
            mask,
            objects,
            field_part(mask, ("y", "x"), ("i",), dereference=True),
            id="t-key",
        )
        with pytest.raises(ValueError, match="No composable"):
            _bfs_path([key], "33", "34")

    def test_dimension_mismatch_names_the_edge(self) -> None:
        zyx = make_system("8", "zyx", ["z", "y", "x"])
        bad = scale_t(id="t-bad", input=UM, output=zyx, scale=(1.0, 1.0, 1.0))
        steps = [PathStep(scale_t(), False), PathStep(bad, False)]
        with pytest.raises(ValueError, match="t-bad"):
            _compose_axis_maps(steps, PIX.axis_names)


# A shape drawn on a scene: the drawing space copies the world's space axes and
# is registered into it by name, the image reaches the same world by its
# calibration, and the lens is a crop of the image.
DRAWING = make_system("20", "drawing", ["z", "y", "x"])
WORLD = make_system("21", "world (micrometers)", ["c", "z", "y", "x"])
GRID = make_system("22", "pixels", ["c", "z", "y", "x"])
CROP = make_system("23", "crop", ["c", "z", "y", "x"])


def scene_graph() -> SimpleNamespace:
    return SimpleNamespace(
        transformations=[
            by_dimension_t(
                DRAWING, WORLD, part("IDENTITY", ["z", "y", "x"]), id="t-drawn"
            ),
            scale_t(id="t-cal", input=GRID, output=WORLD, scale=(1.0, 2.0, 0.5, 0.5)),
            translation_t(
                id="t-crop", input=CROP, output=GRID, translation=(0.0, 3.0, 10.0, 20.0)
            ),
        ]
    )


class TestByDimensionComposition:
    def test_a_by_dimension_edge_is_walkable_both_ways(self) -> None:
        edge = by_dimension_t(DRAWING, WORLD, part("IDENTITY", ["z", "y", "x"]))
        assert [
            (s.transformation.id, s.inverted) for s in _bfs_path([edge], "20", "21")
        ] == [("t-dim", False)]
        assert [
            (s.transformation.id, s.inverted) for s in _bfs_path([edge], "21", "20")
        ] == [("t-dim", True)]

    def test_a_shape_drawn_in_a_scene_lands_on_the_voxels_of_a_crop(self) -> None:
        # (z, y, x) = (10, 8, 12) um -> voxel (5, 16, 24) -> (2, 6, 4) of the crop.
        points = [[10.0, 8.0, 12.0], [8.0, 5.0, 10.0]]
        on_crop = DRAWING.transform_points_to(
            CROP, points, axes=("z", "y", "x"), graph=scene_graph()
        )
        assert np.allclose(on_crop, [[2.0, 6.0, 4.0], [1.0, 0.0, 0.0]])
        # ... and in whatever order they are asked for.
        assert np.allclose(
            DRAWING.transform_points_to(
                CROP, points[0], axes=("x", "z"), graph=scene_graph()
            ),
            [4.0, 2.0],
        )

    def test_the_map_states_only_the_axes_the_path_states(self) -> None:
        mapped = DRAWING.axis_map_to(CROP, graph=scene_graph())
        assert mapped.input_axes == ("z", "y", "x")
        assert mapped.output_axes == ("z", "y", "x")
        with pytest.raises(ValueError, match="nothing about \\['c'\\]"):
            mapped.apply([1.0, 2.0, 3.0], output_axes=("c", "z"))

    def test_an_unstated_axis_has_no_matrix(self) -> None:
        with pytest.raises(ValueError, match="'c'"):
            DRAWING.matrix_to(CROP, graph=scene_graph())
        with pytest.raises(ValueError, match="'c'"):
            DRAWING.transform_points_to(CROP, [1.0, 2.0, 3.0], graph=scene_graph())

    def test_walked_the_other_way_the_channel_is_simply_not_read(self) -> None:
        # Crop voxels -> drawing space: every drawing axis is stated, c is let go.
        back = CROP.axis_map_to(DRAWING, graph=scene_graph())
        assert back.output_axes == ("z", "y", "x")
        assert np.allclose(back.apply([0.0, 2.0, 6.0, 4.0]), [10.0, 8.0, 12.0])
        assert np.allclose(
            back.apply([2.0, 6.0, 4.0], input_axes=("z", "y", "x")), [10.0, 8.0, 12.0]
        )
        assert np.allclose(
            CROP.matrix_to(DRAWING, graph=scene_graph()) @ [7.0, 2.0, 6.0, 4.0, 1.0],
            [10.0, 8.0, 12.0, 1.0],
        )

    def test_points_that_lack_an_axis_the_answer_reads_are_refused(self) -> None:
        back = CROP.axis_map_to(DRAWING, graph=scene_graph())
        with pytest.raises(ValueError, match="depend on 'z'"):
            back.apply([6.0, 4.0], input_axes=("y", "x"))
        assert np.allclose(
            back.apply([6.0, 4.0], input_axes=("y", "x"), output_axes=("y", "x")),
            [8.0, 12.0],
        )

    def test_scale_and_translation_apply_to_the_named_axes_in_that_order(self) -> None:
        yx = make_system("30", "plane", ["y", "x"])
        edge = by_dimension_t(
            yx,
            WORLD,
            part("AFFINE", ["y", "x"], affine=((2.0, 0.0, 1.0), (0.0, 4.0, -1.0))),
        )
        graph = SimpleNamespace(transformations=[edge])
        assert np.allclose(
            yx.transform_points_to(WORLD, [3.0, 5.0], axes=("y", "x"), graph=graph),
            [7.0, 19.0],
        )
        back = WORLD.axis_map_to(yx, graph=graph)
        assert np.allclose(back.apply([7.0, 19.0], input_axes=("y", "x")), [3.0, 5.0])

    def test_an_affine_is_written_over_the_named_axes_and_may_rename_them(self) -> None:
        uv = make_system("31", "sheared", ["u", "v"])
        edge = by_dimension_t(
            uv,
            WORLD,
            part(
                "AFFINE",
                ["u", "v"],
                ["x", "y"],
                affine=((1.0, 1.0, 2.0), (0.0, 2.0, 0.0)),
            ),
        )
        graph = SimpleNamespace(transformations=[edge])
        # x = u + v + 2, y = 2v
        assert np.allclose(
            uv.transform_points_to(WORLD, [3.0, 4.0], axes=("y", "x"), graph=graph),
            [8.0, 9.0],
        )
        back = WORLD.axis_map_to(uv, graph=graph)
        assert np.allclose(back.apply([8.0, 9.0], input_axes=("y", "x")), [3.0, 4.0])

    def test_an_axis_passed_through_is_converted_between_its_two_units(self) -> None:
        def with_units(id: str, unit: str) -> CoordinateSystem:
            return CoordinateSystem(
                id=id,
                name=id,
                axes=(
                    Axis(id=f"{id}-z", order=0, name="z", type="SPACE", unit=unit),
                    Axis(id=f"{id}-x", order=1, name="x", type="SPACE", unit=unit),
                ),
            )

        nm, um = with_units("40", "nanometer"), with_units("41", "micrometer")
        graph = SimpleNamespace(
            transformations=[
                by_dimension_t(
                    nm, um, part("IDENTITY", ["z"]), part("SCALE", ["x"], scale=(1.0,))
                )
            ]
        )
        # z is an IDENTITY part -- the same position, said twice -- so it is converted; x is a
        # SCALE part, whose numbers are the edge's own.
        assert np.allclose(
            nm.transform_points_to(um, [500.0, 7.0], graph=graph), [0.5, 7.0]
        )
        assert np.allclose(
            um.transform_points_to(nm, [0.5, 7.0], graph=graph), [500.0, 7.0]
        )


def make_dataset(axis_names: Sequence[str]) -> ArrayDataset:
    from mikro.api.schema import ArrayDataset

    return ArrayDataset(
        descriptors={},
        id="d",
        name="ds",
        axisNames=tuple(axis_names),
        shape=tuple(8 for _ in axis_names),
        multiscale=False,
        intrinsicSystem=make_system("i", "ds/intrinsic", list(axis_names)),
        dataArrays=(),
    )


def make_scene(world_axes: Sequence[str] = ("t", "z", "y", "x")) -> Scene:
    from mikro.api.schema import Scene

    return Scene(
        descriptors={},
        id="s",
        name="scene",
        preferredView="AUTO",
        backgroundColor=None,
        worldCoordinateSystem=make_system("w", "world", list(world_axes)),
    )


class _Registration(TypedDict):
    """What `register` sent to `create_transformation`, as far as the tests read it."""

    input: object
    output: object
    transform: ByDimensionTransformInput


class _SpaceCreated(TypedDict):
    """What a space helper sent to `create_coordinate_system`, as far as the tests read it."""

    axes: list[PhysicalAxisInput]
    epoch: object


class TestRegister:
    """A registration must name the axes the two spaces share.

    A default world is (t, z, y, x) and a photograph is (c, y, x). A square edge
    sized to the dataset passes the server's rank check — the vector length is
    right — but is then read positionally, mapping c onto t and y onto z. Only a
    BY_DIMENSION naming the shared axes says what is actually true.

    The edge lands in the *space*, not in a scene, so `register` is asked of the
    coordinate system.
    """

    def register(
        self,
        source: Registrable,
        world_axes: Sequence[str] = ("t", "z", "y", "x"),
        **offsets: Any,
    ) -> _Registration:
        seen: dict[str, object] = {}

        def fake(**kwargs: object) -> str:
            seen.update(kwargs)
            return "edge"

        client = SimpleNamespace(create_transformation=fake)
        make_system("w", "world", list(world_axes)).register(
            source, mikro=client, **offsets
        )
        transform = seen["transform"]
        assert isinstance(transform, ByDimensionTransformInput)
        return {
            "input": seen["input"],
            "output": seen["output"],
            "transform": transform,
        }

    def place(
        self,
        dataset_axes: Sequence[str],
        world_axes: Sequence[str] = ("t", "z", "y", "x"),
        **offsets: float,
    ) -> _Registration:
        return self.register(make_dataset(dataset_axes), world_axes, **offsets)

    def test_channel_axis_is_not_placed_in_the_world(self) -> None:
        transform = self.place(["c", "y", "x"])["transform"]
        assert transform.kind == "BY_DIMENSION"
        (shared,) = transform.parts
        assert (shared.kind, shared.input_axes, shared.output_axes) == (
            "IDENTITY",
            ("y", "x"),
            ("y", "x"),
        ), "no numbers: the same positions, said twice"

    def test_offsets_are_positional_against_the_named_axes(self) -> None:
        (shared,) = self.place(["z", "y", "x"], x=288.0, y=144.0)["transform"].parts
        assert (shared.kind, shared.input_axes) == ("TRANSLATION", ("z", "y", "x"))
        assert shared.translation == (0.0, 144.0, 288.0)

    def test_matching_axes_name_all_of_them(self) -> None:
        (shared,) = self.place(["t", "z", "y", "x"])["transform"].parts
        assert shared.input_axes == ("t", "z", "y", "x")

    def test_no_shared_axes_is_refused(self) -> None:
        with pytest.raises(ValueError, match="share"):
            self.place(["y", "x"], world_axes=("a", "b"))

    def test_offset_along_an_unshared_axis_is_refused(self) -> None:
        with pytest.raises(ValueError, match="nowhere to land"):
            self.place(["c", "y", "x"], c=1.0)

    def test_the_edge_sets_out_from_the_source_space_into_this_one(self) -> None:
        seen = self.place(["z", "y", "x"])
        assert seen["input"] == "i"
        assert seen["output"] == "w"

    def test_a_source_that_names_its_space_coordinate_system(self) -> None:
        """A table dataset, a mesh collection and an annotation collection call
        their space `coordinate_system`, not `intrinsic_system`."""
        table = SimpleNamespace(
            name="localizations",
            coordinate_system=make_system("tbl", "tbl/space", ["y", "x"]),
        )
        seen = self.register(table)
        assert seen["input"] == "tbl"
        assert seen["transform"].parts[0].input_axes == ("y", "x")

    def test_a_coordinate_system_registers_directly(self) -> None:
        seen = self.register(make_system("stage", "stage", ["y", "x"]))
        assert seen["input"] == "stage"

    def test_a_source_with_no_space_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no coordinate system"):
            self.register(SimpleNamespace(name="nowhere"))


class TestRegisterScale:
    """A pixel size is a property of the *edge*: the source's grid is in unitless
    indices, the space is in whatever its axes carry, and the factor between them
    is the claim. Both vectors are positional against the shared axes, so the one
    thing worth pinning down is that they stay aligned with each other."""

    def register(
        self,
        world_axes: Sequence[str] = ("z", "y", "x"),
        dataset_axes: Sequence[str] = ("c", "z", "y", "x"),
        **kw: Any,
    ) -> ByDimensionTransformInput:
        seen: dict[str, object] = {}

        def fake(**kwargs: object) -> str:
            seen.update(kwargs)
            return "edge"

        client = SimpleNamespace(create_transformation=fake)
        make_system("w", "world", list(world_axes)).register(
            make_dataset(dataset_axes), mikro=client, **kw
        )
        transform = seen["transform"]
        assert isinstance(transform, ByDimensionTransformInput)
        return transform

    def test_scale_and_translation_line_up_with_the_named_axes(self) -> None:
        """Both at once are one diagonal AFFINE part: the scale on the diagonal, the offset last."""
        transform = self.register(scale={"z": 1.0, "y": 0.2, "x": 0.2}, x=10.0)
        assert transform.kind == "BY_DIMENSION"
        (shared,) = transform.parts
        assert (shared.kind, shared.input_axes) == ("AFFINE", ("z", "y", "x"))
        assert shared.affine == (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.2, 0.0, 0.0),
            (0.0, 0.0, 0.2, 10.0),
        )

    def test_an_unnamed_axis_scales_by_one(self) -> None:
        (shared,) = self.register(scale={"x": 0.2}).parts
        assert (shared.kind, shared.scale) == ("SCALE", (1.0, 1.0, 0.2))

    def test_a_sequence_is_positional_against_the_shared_axes(self) -> None:
        assert self.register(scale=[1.0, 0.2, 0.2]).parts[0].scale == (1.0, 0.2, 0.2)

    def test_a_sequence_of_the_wrong_length_is_refused(self) -> None:
        # Sized to the dataset's four axes, but the edge acts on the three shared
        # ones — the mistake a rank check against the source would wave through.
        with pytest.raises(ValueError, match="shared axes"):
            self.register(scale=[1.0, 1.0, 0.2, 0.2])

    def test_scaling_an_unshared_axis_is_refused(self) -> None:
        with pytest.raises(ValueError, match="nowhere to land"):
            self.register(scale={"c": 2.0})

    def test_the_channel_axis_is_simply_not_claimed(self) -> None:
        """A physical world has no business naming a channel axis, and
        BY_DIMENSION is what lets it stay silent about one."""
        (shared,) = self.register(scale={"z": 1.0, "y": 0.2, "x": 0.2}).parts
        assert "c" not in shared.input_axes
        assert "c" not in shared.output_axes


class TestSpaceHelpers:
    """The helpers only build the space. Where data sits in it is a separate
    edge, authored by `register`."""

    def create(
        self, fn: Callable[..., object], *args: object, **kwargs: object
    ) -> _SpaceCreated:
        seen: dict[str, object] = {}

        def fake(**call: object) -> str:
            seen.update(call)
            return "space"

        fn(SimpleNamespace(create_coordinate_system=fake), *args, **kwargs)
        axes = seen["axes"]
        assert isinstance(axes, list)
        return {"axes": axes, "epoch": seen["epoch"]}

    def test_space_3d_is_zyx_in_one_length_unit(self) -> None:
        from mikro import space_3d

        axes = self.create(space_3d, "stage", unit=Unit("micrometer"))["axes"]
        assert [a.name for a in axes] == ["z", "y", "x"]
        assert {str(a.unit) for a in axes} == {"micrometer"}
        assert {str(a.type) for a in axes} == {"SPACE"}

    def test_space_2d_is_yx(self) -> None:
        from mikro import space_2d

        axes = self.create(space_2d, "slide")["axes"]
        assert [a.name for a in axes] == ["y", "x"]

    def test_a_time_axis_sorts_ahead_of_the_spatial_ones(self) -> None:
        """RFC-5 orders axes by type, and the array's dimension order IS that
        order — a space whose axes disagree describes a different array."""
        from mikro import timelapse_3d

        seen = self.create(timelapse_3d, "movie", time_unit=Unit("second"))
        axes = seen["axes"]
        assert [a.name for a in axes] == ["t", "z", "y", "x"]
        assert str(axes[0].type) == "TIME"
        assert str(axes[0].unit) == "second"
        # No epoch given: the clock is unanchored, not anchored to null. UNSET is
        # how the generated layer spells "omitted" — it never reaches the wire.
        assert seen["epoch"] is UNSET

    def test_create_space_infers_the_axis_type_from_the_name(self) -> None:
        from mikro import create_space

        axes = self.create(
            create_space,
            "mixed",
            {
                "x": Unit("micrometer"),
                "c": Unit("dimensionless"),
                "t": Unit("second"),
            },
        )["axes"]
        # Sorted into RFC-5 order: time, then categorical, then space.
        assert [a.name for a in axes] == ["t", "c", "x"]
        assert [str(a.type) for a in axes] == ["TIME", "CHANNEL", "SPACE"]

    def test_a_space_needs_at_least_one_axis(self) -> None:
        from mikro import create_space

        with pytest.raises(ValueError, match="at least one axis"):
            create_space(SimpleNamespace(), "empty", {})


class TestSceneIsNotASpace:
    """A scene composes; it does not place. The edge belongs to the world."""

    def test_place_points_at_the_world(self) -> None:
        with pytest.raises(AttributeError, match=r"scene\.world\.register"):
            make_scene().place(make_dataset(["z", "y", "x"]))

    def test_grid_cell_points_at_the_world(self) -> None:
        with pytest.raises(AttributeError, match=r"scene\.world\.grid_cell"):
            make_scene().grid_cell(make_dataset(["z", "y", "x"]), 0, 2, 8.0)

    def test_the_world_is_read_straight_off_the_scene(self) -> None:
        assert make_scene().world.name == "world"


class TestStage:
    """A scene is obtained *from* a space: it adopts the system as its world and
    authors no edges."""

    def stage(self, **kwargs: Any) -> dict[str, object]:
        seen: dict[str, object] = {}

        def fake(**call: object) -> str:
            seen.update(call)
            return "scene"

        client = SimpleNamespace(create_scene_from_coordinate_system=fake)
        make_system("w", "world", ["y", "x"]).stage(mikro=client, **kwargs)
        return seen

    def test_the_space_is_the_scenes_world(self) -> None:
        assert self.stage()["coordinate_system"] == "w"

    def test_an_omitted_policy_leaves_every_choice_to_the_server(self) -> None:
        """Nothing set means nothing serialized, so the server applies its own
        defaults rather than a client-side copy of them going stale.

        Asserted at the wire boundary, not on the input model: `nchildren` is
        `Int!`, so an explicit null here would be rejected outright, and whether
        `exclude_unset` survives validation into `Arguments` is exactly what
        decides that.
        """
        from mikro.api.schema import (
            CreateSceneFromCoordinateSystemMutation,
            ScenePolicyInput,
        )

        policy = self.stage()["policy"]
        assert isinstance(policy, ScenePolicyInput)

        variables = CreateSceneFromCoordinateSystemMutation.Arguments(
            input={"coordinateSystem": "w", "policy": policy}
        ).model_dump(by_alias=True, exclude_unset=True)
        assert variables == {"input": {"coordinateSystem": "w", "policy": {}}}

    def test_an_omitted_name_is_not_sent_as_null(self) -> None:
        assert self.stage()["name"] is UNSET
        assert self.stage(name="overview")["name"] == "overview"


class TestUnregister:
    """The kind of the source is named, never inferred: the models carry no
    __typename, so a guess could be silently wrong."""

    def test_naming_no_source_is_refused(self) -> None:
        with pytest.raises(ValueError, match="exactly one source"):
            make_system("w", "world", ["y", "x"]).unregister()

    def test_naming_two_sources_is_refused(self) -> None:
        with pytest.raises(ValueError, match="exactly one source"):
            make_system("w", "world", ["y", "x"]).unregister(
                dataset="d", table_dataset="t"
            )

    def test_the_named_source_is_passed_with_this_space_as_the_world(self) -> None:
        seen: dict[str, object] = {}

        def fake(**kwargs: object) -> tuple[()]:
            seen.update(kwargs)
            return ()

        client = SimpleNamespace(delete_registration=fake)
        make_system("w", "world", ["y", "x"]).unregister(
            mesh_collection="m", mikro=client
        )
        assert seen["world"] == "w"
        assert seen["mesh_collection"] == "m"
        assert "dataset" not in seen


# ---------------------------------------------------------------------------
# Calibration coercion
# ---------------------------------------------------------------------------


class TestCalibrationCoercion:
    """A bare ``(factor, unit)`` pair is accepted wherever a `Calibration` is.

    `Calibration` is a NamedTuple, so a plain tuple looks interchangeable with one
    right up until `calibrate` reads ``.factor`` off it — and that happens after the
    dataset has uploaded. The pair is read by type rather than by position, so the
    ordering ambiguity `Calibration`'s docstring objects to does not arise.
    """

    def test_a_calibration_passes_through(self) -> None:
        from mikro.traits import _as_calibration
        from mikro.vocabulary import Calibration, Unit

        value = Calibration(0.5, Unit("micrometer"))
        assert _as_calibration("z", value) is value

    def test_a_factor_unit_pair_is_accepted(self) -> None:
        from mikro.traits import _as_calibration

        calibration = _as_calibration("x", (0.2, "micrometer"))
        assert (float(calibration.factor), str(calibration.unit)) == (0.2, "micrometer")

    def test_the_reversed_spelling_is_refused_not_repaired(self) -> None:
        """`Calibration`'s docstring is explicit that only one ordering works."""
        from mikro.traits import _as_calibration

        with pytest.raises(TypeError, match="wrong way round"):
            _as_calibration("x", ("micrometer", 0.2))

    @pytest.mark.parametrize("bad", [(0.5, 1.0), "micrometer", (0.5,), None, 0.5])
    def test_anything_that_is_not_a_factor_and_a_unit_is_refused(
        self, bad: object
    ) -> None:
        from mikro.traits import _as_calibration

        with pytest.raises(TypeError, match="axis 'z'"):
            _as_calibration("z", bad)

    def test_a_bool_is_not_a_factor(self) -> None:
        """``bool`` is an ``int`` subclass, so it would otherwise sail through."""
        from mikro.traits import _as_calibration

        with pytest.raises(TypeError):
            _as_calibration("z", (True, "micrometer"))
