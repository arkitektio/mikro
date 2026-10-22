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

from mikro.api.schema import (
    AffineTransformInput,
    ByDimensionTransformInput,
    IdentityTransformInput,
    MapAxisTransformInput,
    RotationTransformInput,
    ScaleTransformInput,
    TranslationTransformInput,
    UnmappableTransformInput,
)
from mikro.traits import _part, _transform_member


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


def test_a_by_dimension_is_its_parts() -> None:
    """Each part names its own axes and carries only its own kind's parameter."""
    pixel = _part("SCALE", ["y", "x"], ["y", "x"], scale=[0.5, 2])
    times = _part("FIELD", ["t"], ["t"], field="9", unit="second", min=0.0, max=7.5)
    member = _transform_member("BY_DIMENSION", parts=[pixel, times])
    assert isinstance(member, ByDimensionTransformInput)
    assert member.parts == (pixel, times)
    assert (pixel.kind, pixel.input_axes, pixel.scale, pixel.translation, pixel.affine, pixel.field) == ("SCALE", ("y", "x"), (0.5, 2.0), None, None, None)
    assert times.field is not None and (times.field.system, times.field.unit, times.field.min, times.field.max) == ("9", "second", 0.0, 7.5)


def test_a_by_dimension_needs_its_parts() -> None:
    with pytest.raises(ValueError, match="BY_DIMENSION transformation needs parts"):
        _transform_member("BY_DIMENSION")


def test_a_by_dimension_takes_no_flat_parameters() -> None:
    """The flat spelling is gone: a scale beside the parts would be a second, unnamed map."""
    with pytest.raises(ValueError, match="takes no scale="):
        _transform_member("BY_DIMENSION", scale=[1.0], parts=[_part("IDENTITY", ["y"], ["y"])])


def test_only_a_by_dimension_takes_parts() -> None:
    with pytest.raises(ValueError, match="takes no parts"):
        _transform_member("SCALE", scale=[1.0], parts=[_part("IDENTITY", ["y"], ["y"])])


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
