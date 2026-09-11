"""Unit tests for the coordinate system and transformation traits.

These construct the generated fragment models directly — no server needed.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from kanne.scalars import Unit

from mikro_next.api.schema import (
    UNSET,
    Axis,
    CoordinateSystem,
    TransformationAffineTransformation,
    TransformationIdentityTransformation,
    TransformationMapAxisTransformation,
    TransformationRotationTransformation,
    TransformationScaleTransformation,
    TransformationSequenceTransformation,
    TransformationTranslationTransformation,
    TransformationUnmappableTransformation,
)
from mikro_next.traits import (
    PathStep,
    _bfs_path,
    _compose_steps,
    _infer_transform_kind,
)
from mikro_next.vocabulary import Calibration


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


def scale_t(id="t-scale", input=PIX, output=UM, scale=(0.5, 2.0)):
    return TransformationScaleTransformation(
        id=id, kind="SCALE", version=0, input=input, output=output, scale=scale
    )


def translation_t(id="t-trans", input=UM, output=STAGE, translation=(10.0, -5.0)):
    return TransformationTranslationTransformation(
        id=id,
        kind="TRANSLATION",
        version=0,
        input=input,
        output=output,
        translation=translation,
    )


class TestTransformationMatrix:
    def test_scale_matrix_and_apply(self):
        t = scale_t()
        expected = np.diag([0.5, 2.0, 1.0])
        assert np.allclose(t.as_matrix(), expected)
        assert np.allclose(t.apply([[2.0, 3.0], [4.0, 1.0]]), [[1.0, 6.0], [2.0, 2.0]])
        # single point keeps its shape
        assert np.allclose(t.apply([2.0, 3.0]), [1.0, 6.0])

    def test_translation_matrix(self):
        t = translation_t()
        assert np.allclose(t.apply([1.0, 1.0]), [11.0, -4.0])

    def test_affine_matrix_with_translation_column(self):
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

    def test_rotation_square_matrix_heuristic(self):
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

    def test_identity_needs_a_system(self):
        t = TransformationIdentityTransformation(
            id="t-id", kind="IDENTITY", version=0, input=None, output=PIX
        )
        assert np.allclose(t.as_matrix(), np.eye(3))
        bare = TransformationIdentityTransformation(
            id="t-id2", kind="IDENTITY", version=0, input=None, output=None
        )
        with pytest.raises(ValueError, match="dimensionality"):
            bare.as_matrix()

    def test_inverse_round_trip(self):
        t = scale_t()
        point = np.array([3.0, 7.0])
        assert np.allclose(t.apply_inverse(t.apply(point)), point)

    def test_non_square_inverse_raises(self):
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

    def test_map_axis_permutation(self):
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

    def test_map_axis_needs_systems(self):
        t = TransformationMapAxisTransformation(
            id="t-map2",
            kind="MAP_AXIS",
            version=0,
            input=None,
            output=None,
            inputAxes=("y", "x"),
            outputAxes=("y", "x"),
        )
        with pytest.raises(ValueError, match="coordinate systems"):
            t.as_matrix()

    def test_sequence_and_unmappable_have_no_matrix(self):
        seq = TransformationSequenceTransformation(
            id="t-seq",
            kind="SEQUENCE",
            version=0,
            input=PIX,
            output=UM,
            sequenceChildren=(),
        )
        with pytest.raises(NotImplementedError, match="resolve_matrix"):
            seq.as_matrix()
        unmappable = TransformationUnmappableTransformation(
            id="t-un", kind="UNMAPPABLE", version=0, input=PIX, output=UM
        )
        with pytest.raises(NotImplementedError, match="no matrix"):
            unmappable.as_matrix()

    def test_wrong_point_dimension(self):
        with pytest.raises(ValueError, match="dimension"):
            scale_t().apply([1.0, 2.0, 3.0])


class TestCoordinateSystemHelpers:
    def test_axis_helpers(self):
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
    def make_dataset(self, intrinsic):
        from mikro_next.api.schema import ArrayDataset

        return ArrayDataset(
            id="d1",
            name="ds",
            axisNames=("y", "x"),
            shape=(10, 10),
            multiscale=False,
            intrinsicSystem=intrinsic,
            dataArrays=(),
        )

    def test_requires_intrinsic_system(self):
        with pytest.raises(ValueError, match="intrinsic"):
            self.make_dataset(None).calibrate(
                {"y": Calibration(0.1, Unit("µm")), "x": Calibration(0.1, Unit("µm"))}
            )

    def test_mapping_must_cover_every_axis(self):
        with pytest.raises(ValueError, match="every intrinsic axis"):
            self.make_dataset(PIX).calibrate({"y": Calibration(0.1, Unit("µm"))})

    def test_list_form_needs_exactly_one_of_scale_or_affine(self):
        with pytest.raises(ValueError, match="exactly"):
            self.make_dataset(PIX).calibrate([])


class TestInferTransformKind:
    def test_each_parameter_maps_to_its_kind(self):
        assert _infer_transform_kind(None, None, [[1.0, 0.0]], None)[0] == "AFFINE"
        assert _infer_transform_kind([1.0], None, None, None)[0] == "SCALE"
        assert _infer_transform_kind(None, [1.0], None, None)[0] == "TRANSLATION"
        assert _infer_transform_kind(None, None, None, ["x"])[0] == "MAP_AXIS"
        assert _infer_transform_kind(None, None, None, None)[0] == "IDENTITY"

    def test_scale_and_translation_fold_into_affine(self):
        kind, scale, translation, affine = _infer_transform_kind(
            [2.0, 3.0], [1.0, -1.0], None, None
        )
        assert kind == "AFFINE" and scale is None and translation is None
        assert np.allclose(affine, [[2.0, 0.0, 1.0], [0.0, 3.0, -1.0]])

    def test_affine_conflicts_with_scale(self):
        with pytest.raises(ValueError, match="not both"):
            _infer_transform_kind([1.0], None, [[1.0]], None)


class TestPathComposition:
    def test_path_with_inverted_edge(self):
        # PIX -> UM (scale), STAGE -> UM (translation): the path PIX -> STAGE
        # must traverse the second edge inverted.
        edges = [scale_t(), translation_t(input=STAGE, output=UM)]
        steps = _bfs_path(edges, "1", "3")
        assert [(s.transformation.id, s.inverted) for s in steps] == [
            ("t-scale", False),
            ("t-trans", True),
        ]
        matrix = _compose_steps(steps)
        expected = np.linalg.inv(edges[1].as_matrix()) @ edges[0].as_matrix()
        assert np.allclose(matrix, expected)

    def test_path_via_trait_with_prefetched_graph(self):
        graph = SimpleNamespace(
            transformations=[scale_t(), translation_t(input=UM, output=STAGE)]
        )
        matrix = PIX.matrix_to(STAGE, graph=graph)
        # y=2,x=4 pixels -> scale (1, 8) -> translate (11, 3)
        assert np.allclose(
            PIX.transform_points_to(STAGE, [2.0, 4.0], graph=graph), [11.0, 3.0]
        )
        assert np.allclose(matrix @ [2.0, 4.0, 1.0], [11.0, 3.0, 1.0])

    def test_self_path_is_identity(self):
        graph = SimpleNamespace(transformations=[])
        assert PIX.path_to(PIX, graph=graph) == []
        assert np.allclose(PIX.matrix_to(PIX, graph=graph), np.eye(3))

    def test_unwalkable_edges_are_excluded(self):
        far = make_system("9", "far", ["y", "x"])
        unmappable = TransformationUnmappableTransformation(
            id="t-un", kind="UNMAPPABLE", version=0, input=PIX, output=far
        )
        with pytest.raises(ValueError, match="No composable transformation path"):
            _bfs_path([unmappable], "1", "9")

    def test_sequence_only_walkable_with_allow_fetch(self):
        seq = TransformationSequenceTransformation(
            id="t-seq",
            kind="SEQUENCE",
            version=0,
            input=PIX,
            output=UM,
            sequenceChildren=(),
        )
        with pytest.raises(ValueError, match="No composable"):
            _bfs_path([seq], "1", "2")
        steps = _bfs_path([seq], "1", "2", allow_fetch=True)
        assert len(steps) == 1

    def test_dimension_mismatch_names_the_edge(self):
        zyx = make_system("8", "zyx", ["z", "y", "x"])
        bad = scale_t(id="t-bad", input=UM, output=zyx, scale=(1.0, 1.0, 1.0))
        steps = [PathStep(scale_t(), False), PathStep(bad, False)]
        with pytest.raises(ValueError, match="t-bad"):
            _compose_steps(steps)


def make_dataset(axis_names):
    from mikro_next.api.schema import ArrayDataset

    return ArrayDataset(
        id="d",
        name="ds",
        axisNames=tuple(axis_names),
        shape=tuple(8 for _ in axis_names),
        multiscale=False,
        intrinsicSystem=make_system("i", "ds/intrinsic", list(axis_names)),
        dataArrays=(),
    )


def make_scene(world_axes=("t", "z", "y", "x")):
    from mikro_next.api.schema import Scene

    return Scene(
        id="s",
        name="scene",
        preferredView="AUTO",
        backgroundColor=None,
        worldCoordinateSystem=make_system("w", "world", list(world_axes)),
    )


class TestRegister:
    """A registration must name the axes the two spaces share.

    A default world is (t, z, y, x) and a photograph is (c, y, x). A square edge
    sized to the dataset passes the server's rank check — the vector length is
    right — but is then read positionally, mapping c onto t and y onto z. Only a
    BY_DIMENSION naming the shared axes says what is actually true.

    The edge lands in the *space*, not in a scene, so `register` is asked of the
    coordinate system.
    """

    def register(self, source, world_axes=("t", "z", "y", "x"), **offsets):
        from unittest.mock import patch

        seen = {}

        def fake(**kwargs):
            seen.update(kwargs)
            return "edge"

        with patch("mikro_next.api.schema.create_transformation", fake):
            make_system("w", "world", list(world_axes)).register(source, **offsets)
        return seen

    def place(self, dataset_axes, world_axes=("t", "z", "y", "x"), **offsets):
        return self.register(make_dataset(dataset_axes), world_axes, **offsets)

    def test_channel_axis_is_not_placed_in_the_world(self):
        transform = self.place(["c", "y", "x"])["transform"]
        assert transform.kind == "BY_DIMENSION"
        assert transform.input_axes == ("y", "x")
        assert transform.output_axes == ("y", "x")
        assert transform.translation == (0.0, 0.0)

    def test_offsets_are_positional_against_the_named_axes(self):
        transform = self.place(["z", "y", "x"], x=288.0, y=144.0)["transform"]
        assert transform.input_axes == ("z", "y", "x")
        assert transform.translation == (0.0, 144.0, 288.0)

    def test_matching_axes_name_all_of_them(self):
        transform = self.place(["t", "z", "y", "x"])["transform"]
        assert transform.input_axes == ("t", "z", "y", "x")
        assert len(transform.translation) == 4

    def test_no_shared_axes_is_refused(self):
        with pytest.raises(ValueError, match="share"):
            self.place(["y", "x"], world_axes=("a", "b"))

    def test_offset_along_an_unshared_axis_is_refused(self):
        with pytest.raises(ValueError, match="nowhere to land"):
            self.place(["c", "y", "x"], c=1.0)

    def test_the_edge_sets_out_from_the_source_space_into_this_one(self):
        seen = self.place(["z", "y", "x"])
        assert seen["input"] == "i"
        assert seen["output"] == "w"

    def test_a_source_that_names_its_space_coordinate_system(self):
        """A table dataset, a mesh collection and an annotation collection call
        their space `coordinate_system`, not `intrinsic_system`."""
        table = SimpleNamespace(
            name="localizations",
            coordinate_system=make_system("tbl", "tbl/space", ["y", "x"]),
        )
        seen = self.register(table)
        assert seen["input"] == "tbl"
        assert seen["transform"].input_axes == ("y", "x")

    def test_a_coordinate_system_registers_directly(self):
        seen = self.register(make_system("stage", "stage", ["y", "x"]))
        assert seen["input"] == "stage"

    def test_a_source_with_no_space_is_refused(self):
        with pytest.raises(ValueError, match="no coordinate system"):
            self.register(SimpleNamespace(name="nowhere"))


class TestRegisterScale:
    """A pixel size is a property of the *edge*: the source's grid is in unitless
    indices, the space is in whatever its axes carry, and the factor between them
    is the claim. Both vectors are positional against the shared axes, so the one
    thing worth pinning down is that they stay aligned with each other."""

    def register(self, world_axes=("z", "y", "x"), dataset_axes=("c", "z", "y", "x"), **kw):
        from unittest.mock import patch

        seen = {}

        def fake(**kwargs):
            seen.update(kwargs)
            return "edge"

        with patch("mikro_next.api.schema.create_transformation", fake):
            make_system("w", "world", list(world_axes)).register(
                make_dataset(dataset_axes), **kw
            )
        return seen["transform"]

    def test_scale_and_translation_line_up_with_the_named_axes(self):
        transform = self.register(scale={"z": 1.0, "y": 0.2, "x": 0.2}, x=10.0)
        assert transform.kind == "BY_DIMENSION"
        assert transform.input_axes == ("z", "y", "x")
        assert transform.scale == (1.0, 0.2, 0.2)
        assert transform.translation == (0.0, 0.0, 10.0)
        assert len(transform.scale) == len(transform.input_axes)
        assert len(transform.translation) == len(transform.input_axes)

    def test_an_unnamed_axis_scales_by_one(self):
        assert self.register(scale={"x": 0.2}).scale == (1.0, 1.0, 0.2)

    def test_a_sequence_is_positional_against_the_shared_axes(self):
        assert self.register(scale=[1.0, 0.2, 0.2]).scale == (1.0, 0.2, 0.2)

    def test_a_sequence_of_the_wrong_length_is_refused(self):
        # Sized to the dataset's four axes, but the edge acts on the three shared
        # ones — the mistake a rank check against the source would wave through.
        with pytest.raises(ValueError, match="shared axes"):
            self.register(scale=[1.0, 1.0, 0.2, 0.2])

    def test_scaling_an_unshared_axis_is_refused(self):
        with pytest.raises(ValueError, match="nowhere to land"):
            self.register(scale={"c": 2.0})

    def test_the_channel_axis_is_simply_not_claimed(self):
        """A physical world has no business naming a channel axis, and
        BY_DIMENSION is what lets it stay silent about one."""
        transform = self.register(scale={"z": 1.0, "y": 0.2, "x": 0.2})
        assert "c" not in transform.input_axes
        assert "c" not in transform.output_axes


class TestSpaceHelpers:
    """The helpers only build the space. Where data sits in it is a separate
    edge, authored by `register`."""

    def create(self, fn, *args, **kwargs):
        from unittest.mock import patch

        seen = {}

        def fake(**call):
            seen.update(call)
            return "space"

        with patch("mikro_next.api.schema.create_coordinate_system", fake):
            fn(*args, **kwargs)
        return seen

    def test_space_3d_is_zyx_in_one_length_unit(self):
        from mikro_next import space_3d

        axes = self.create(space_3d, "stage", unit=Unit("micrometer"))["axes"]
        assert [a.name for a in axes] == ["z", "y", "x"]
        assert {str(a.unit) for a in axes} == {"micrometer"}
        assert {str(a.type) for a in axes} == {"SPACE"}

    def test_space_2d_is_yx(self):
        from mikro_next import space_2d

        axes = self.create(space_2d, "slide")["axes"]
        assert [a.name for a in axes] == ["y", "x"]

    def test_a_time_axis_sorts_ahead_of_the_spatial_ones(self):
        """RFC-5 orders axes by type, and the array's dimension order IS that
        order — a space whose axes disagree describes a different array."""
        from mikro_next import timelapse_3d

        seen = self.create(timelapse_3d, "movie", time_unit=Unit("second"))
        axes = seen["axes"]
        assert [a.name for a in axes] == ["t", "z", "y", "x"]
        assert str(axes[0].type) == "TIME"
        assert str(axes[0].unit) == "second"
        # No epoch given: the clock is unanchored, not anchored to null. UNSET is
        # how the generated layer spells "omitted" — it never reaches the wire.
        assert seen["epoch"] is UNSET

    def test_create_space_infers_the_axis_type_from_the_name(self):
        from mikro_next import create_space

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

    def test_a_space_needs_at_least_one_axis(self):
        from mikro_next import create_space

        with pytest.raises(ValueError, match="at least one axis"):
            create_space("empty", {})


class TestSceneIsNotASpace:
    """A scene composes; it does not place. The edge belongs to the world."""

    def test_place_points_at_the_world(self):
        with pytest.raises(AttributeError, match=r"scene\.world\.register"):
            make_scene().place(make_dataset(["z", "y", "x"]))

    def test_grid_cell_points_at_the_world(self):
        with pytest.raises(AttributeError, match=r"scene\.world\.grid_cell"):
            make_scene().grid_cell(make_dataset(["z", "y", "x"]), 0, 2, 8.0)

    def test_the_world_is_read_straight_off_the_scene(self):
        assert make_scene().world.name == "world"


class TestStage:
    """A scene is obtained *from* a space: it adopts the system as its world and
    authors no edges."""

    def stage(self, **kwargs):
        from unittest.mock import patch

        seen = {}

        def fake(**call):
            seen.update(call)
            return "scene"

        with patch("mikro_next.api.schema.create_scene_from_coordinate_system", fake):
            make_system("w", "world", ["y", "x"]).stage(**kwargs)
        return seen

    def test_the_space_is_the_scenes_world(self):
        assert self.stage()["coordinate_system"] == "w"

    def test_an_omitted_policy_leaves_every_choice_to_the_server(self):
        """Nothing set means nothing serialized, so the server applies its own
        defaults rather than a client-side copy of them going stale.

        Asserted at the wire boundary, not on the input model: `nchildren` is
        `Int!`, so an explicit null here would be rejected outright, and whether
        `exclude_unset` survives validation into `Arguments` is exactly what
        decides that.
        """
        from mikro_next.api.schema import (
            CreateSceneFromCoordinateSystemMutation,
            ScenePolicyInput,
        )

        policy = self.stage()["policy"]
        assert isinstance(policy, ScenePolicyInput)

        variables = CreateSceneFromCoordinateSystemMutation.Arguments(
            input={"coordinateSystem": "w", "policy": policy}
        ).model_dump(by_alias=True, exclude_unset=True)
        assert variables == {"input": {"coordinateSystem": "w", "policy": {}}}

    def test_an_omitted_name_is_not_sent_as_null(self):
        assert self.stage()["name"] is UNSET
        assert self.stage(name="overview")["name"] == "overview"


class TestUnregister:
    """The kind of the source is named, never inferred: the models carry no
    __typename, so a guess could be silently wrong."""

    def test_naming_no_source_is_refused(self):
        with pytest.raises(ValueError, match="exactly one source"):
            make_system("w", "world", ["y", "x"]).unregister()

    def test_naming_two_sources_is_refused(self):
        with pytest.raises(ValueError, match="exactly one source"):
            make_system("w", "world", ["y", "x"]).unregister(
                dataset="d", table_dataset="t"
            )

    def test_the_named_source_is_passed_with_this_space_as_the_world(self):
        from unittest.mock import patch

        seen = {}

        def fake(**kwargs):
            seen.update(kwargs)
            return ()

        with patch("mikro_next.api.schema.delete_registration", fake):
            make_system("w", "world", ["y", "x"]).unregister(mesh_collection="m")
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
        from mikro_next.traits import _as_calibration
        from mikro_next.vocabulary import Calibration, Unit

        value = Calibration(0.5, Unit("micrometer"))
        assert _as_calibration("z", value) is value

    def test_a_factor_unit_pair_is_accepted(self) -> None:
        from mikro_next.traits import _as_calibration

        calibration = _as_calibration("x", (0.2, "micrometer"))
        assert (float(calibration.factor), str(calibration.unit)) == (0.2, "micrometer")

    def test_the_reversed_spelling_is_refused_not_repaired(self) -> None:
        """`Calibration`'s docstring is explicit that only one ordering works."""
        from mikro_next.traits import _as_calibration

        with pytest.raises(TypeError, match="wrong way round"):
            _as_calibration("x", ("micrometer", 0.2))

    @pytest.mark.parametrize("bad", [(0.5, 1.0), "micrometer", (0.5,), None, 0.5])
    def test_anything_that_is_not_a_factor_and_a_unit_is_refused(self, bad: object) -> None:
        from mikro_next.traits import _as_calibration

        with pytest.raises(TypeError, match="axis 'z'"):
            _as_calibration("z", bad)

    def test_a_bool_is_not_a_factor(self) -> None:
        """``bool`` is an ``int`` subclass, so it would otherwise sail through."""
        from mikro_next.traits import _as_calibration

        with pytest.raises(TypeError):
            _as_calibration("z", (True, "micrometer"))
