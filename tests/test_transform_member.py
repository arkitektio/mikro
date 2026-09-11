"""``_transform_member`` builds the right member of the ``TransformInput`` union.

The schema publishes ``TransformInput`` as a tagged union whose members are each
``extra='forbid'`` — the strict truth about which fields a kind reads. This is
where the flat parameter surface of the sugar methods narrows to one of them, so
what needs pinning is that every kind reaches its own member with its own fields
and nothing else.

There is a second reason these exist. Several of those members declare their
fields with a pydantic ``alias`` (``inputAxes`` for ``input_axes``), and pyright
synthesizes ``__init__`` from the alias without honouring ``populate_by_name``.
It therefore reports "No parameter named input_axes" on exactly the lines below.
Those reports are false: ``populate_by_name=True`` is set on every one of these
models, and the assertions here are what says so.
"""

import pytest

from mikro_next.api.schema import (
    AffineTransformInput,
    ByDimensionTransformInput,
    FieldTransformInput,
    IdentityTransformInput,
    MapAxisTransformInput,
    RotationTransformInput,
    ScaleTransformInput,
    TranslationTransformInput,
    UnmappableTransformInput,
)
from mikro_next.traits import _transform_member


def test_identity_carries_only_its_discriminator() -> None:
    """Omitting the transform is not how you say "same grid" — it is how the
    schema says UNMAPPABLE. The two are opposites."""
    member = _transform_member("IDENTITY")
    assert isinstance(member, IdentityTransformInput)
    assert member.kind == "IDENTITY"


def test_identity_refuses_parameters() -> None:
    with pytest.raises(ValueError, match="IDENTITY transformation takes no parameters"):
        _transform_member("IDENTITY", scale=[1.0])


def test_scale() -> None:
    member = _transform_member("SCALE", scale=[0.5, 2])
    assert isinstance(member, ScaleTransformInput)
    assert member.scale == (0.5, 2.0)


def test_translation() -> None:
    member = _transform_member("TRANSLATION", translation=[10, -5])
    assert isinstance(member, TranslationTransformInput)
    assert member.translation == (10.0, -5.0)


def test_affine() -> None:
    member = _transform_member("AFFINE", affine=[[2, 0, 1], [0, 3, -1]])
    assert isinstance(member, AffineTransformInput)
    assert member.affine == ((2.0, 0.0, 1.0), (0.0, 3.0, -1.0))


def test_rotation() -> None:
    member = _transform_member("ROTATION", affine=[[0, -1], [1, 0]])
    assert isinstance(member, RotationTransformInput)
    assert member.affine == ((0.0, -1.0), (1.0, 0.0))


def test_map_axis_takes_its_axes_by_field_name() -> None:
    """`input_axes`/`output_axes` are aliased to `inputAxes`/`outputAxes`, and
    `populate_by_name=True` is what makes the snake_case spelling work."""
    member = _transform_member("MAP_AXIS", input_axes=["y", "x"], output_axes=["x", "y"])
    assert isinstance(member, MapAxisTransformInput)
    assert member.input_axes == ("y", "x")
    assert member.output_axes == ("x", "y")


def test_by_dimension_carries_only_the_parameters_it_was_given() -> None:
    """The optional three used to be assembled in an untyped dict and splatted
    in; an omitted one must still arrive as None, not as a missing key."""
    member = _transform_member(
        "BY_DIMENSION",
        input_axes=["z", "y"],
        output_axes=["z", "y"],
        scale=[1.0, 0.2],
    )
    assert isinstance(member, ByDimensionTransformInput)
    assert member.input_axes == ("z", "y")
    assert member.scale == (1.0, 0.2)
    assert member.translation is None
    assert member.affine is None


def test_by_dimension_takes_all_three_optionals() -> None:
    member = _transform_member(
        "BY_DIMENSION",
        input_axes=["y", "x"],
        output_axes=["y", "x"],
        scale=[1, 2],
        translation=[3, 4],
        affine=[[1, 0], [0, 1]],
    )
    assert member.scale == (1.0, 2.0)
    assert member.translation == (3.0, 4.0)
    assert member.affine == ((1.0, 0.0), (0.0, 1.0))


def test_by_dimension_needs_its_axes() -> None:
    with pytest.raises(ValueError, match="BY_DIMENSION transformation needs input_axes"):
        _transform_member("BY_DIMENSION", scale=[1.0])


def test_field() -> None:
    member = _transform_member(
        "FIELD", field="17", input_axes=["y", "x"], output_axes=["row"]
    )
    assert isinstance(member, FieldTransformInput)
    assert member.field == "17"
    assert member.input_axes == ("y", "x")
    assert member.output_axes == ("row",)


def test_unmappable_with_and_without_a_reason() -> None:
    assert isinstance(_transform_member("UNMAPPABLE"), UnmappableTransformInput)
    member = _transform_member("UNMAPPABLE", reason="the stage was moved by hand")
    assert member.reason == "the stage was moved by hand"


def test_a_reason_belongs_only_to_an_unmappable_edge() -> None:
    """The coordinate graph reads nothing else from it, so recording one
    elsewhere would be a note nobody ever sees."""
    with pytest.raises(ValueError, match="only recorded on an UNMAPPABLE edge"):
        _transform_member("SCALE", scale=[1.0], reason="because")


def test_a_resolved_kind_is_refused() -> None:
    """SEQUENCE is produced by composing edges; it can come back from a query
    but there is no member of the input union to build for it."""
    with pytest.raises(ValueError, match="Unknown transformation kind 'SEQUENCE'"):
        _transform_member("SEQUENCE")  # type: ignore[arg-type]
