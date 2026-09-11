"""The hand-written vocabularies must not drift from the generated schema.

:mod:`mikro_next.vocabulary` spells the closed vocabularies as ``Literal``
unions rather than reusing the generated enums, because every generated model
sets ``use_enum_values=True`` — a field read back off a model holds the plain
value, not the member, so a ``Literal`` is what is actually there.

The cost of that is two copies, and ``turms`` regenerates one of them. These
tests are the guard: if the schema grows an axis type or a transformation kind,
they fail here rather than silently type-checking a value the library will then
mishandle.
"""

from typing import get_args

import pytest

from mikro_next.api.schema import AxisType, TransformInput
from mikro_next.vocabulary import (
    AXIS_TYPE_ORDER,
    COARSENABLE_AXIS_TYPES,
    MATRIX_KINDS,
    AxisTypeName,
    Calibration,
    ResolvedTransformKind,
    TransformKind,
    default_axis_type,
    normalize_selection,
)


def _literals(alias: object) -> set[str]:
    """Every literal value in an alias, flattening a Union of Literals."""
    values: set[str] = set()
    for arg in get_args(alias):
        values |= _literals(arg) if get_args(arg) else {arg}
    return values


def _transform_input_kinds() -> set[str]:
    """The `kind` discriminator of every member of the TransformInput union."""
    # `TransformInput` is `Annotated[Union[...], Field(discriminator='kind')]`,
    # so the members are the first arg's args.
    members = get_args(get_args(TransformInput)[0])
    return {get_args(member.model_fields["kind"].annotation)[0] for member in members}


def test_axis_type_names_match_the_generated_enum() -> None:
    assert set(get_args(AxisTypeName)) == {member.value for member in AxisType}


def test_every_axis_type_has_a_sort_rank() -> None:
    """`axis_type_rank` defaults unknown types to the categorical group, which
    would silently misplace a genuinely new one."""
    assert set(AXIS_TYPE_ORDER) == set(get_args(AxisTypeName))


def test_coarsenable_axis_types_are_real_axis_types() -> None:
    assert COARSENABLE_AXIS_TYPES <= set(get_args(AxisTypeName))


def test_transform_kinds_match_the_input_union() -> None:
    """One member of `TransformInput` per buildable kind, and no more."""
    assert set(get_args(TransformKind)) == _transform_input_kinds()


def test_sequence_is_resolved_only() -> None:
    """SEQUENCE comes back from a query but can never be passed to a mutation,
    so it must not be in the buildable vocabulary."""
    assert "SEQUENCE" not in _literals(TransformKind)
    assert _literals(ResolvedTransformKind) == _literals(TransformKind) | {"SEQUENCE"}


def test_matrix_kinds_are_all_real_kinds() -> None:
    assert MATRIX_KINDS <= _literals(ResolvedTransformKind)


class TestDefaultAxisType:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [("t", "TIME"), ("Time", "TIME"), ("c", "CHANNEL"), ("z", "SPACE")],
    )
    def test_the_bare_name_convention(self, name: str, expected: str) -> None:
        assert default_axis_type(name) == expected


class TestNormalizeSelection:
    def test_an_int_pins_one_index(self) -> None:
        assert normalize_selection("c", 3) == (3, 4, None)

    def test_a_slice_passes_through(self) -> None:
        assert normalize_selection("x", slice(1, 5, 2)) == (1, 5, 2)

    def test_a_pair_is_a_half_open_range(self) -> None:
        assert normalize_selection("x", (0, 128)) == (0, 128, None)

    def test_an_open_ended_pair_is_allowed(self) -> None:
        assert normalize_selection("x", (None, 128)) == (None, 128, None)

    def test_a_triple_carries_its_step(self) -> None:
        assert normalize_selection("x", (0, 128, 2)) == (0, 128, 2)

    def test_a_bool_is_refused(self) -> None:
        """`bool` is a subclass of `int`, so no annotation excludes it — and
        silently reading `c=True` as index 1 is worse than refusing it."""
        with pytest.raises(TypeError, match="Invalid selection for axis 'c'"):
            normalize_selection("c", True)

    def test_nonsense_is_refused_by_name(self) -> None:
        with pytest.raises(TypeError, match="Invalid selection for axis 'x'"):
            normalize_selection("x", "0:128")  # type: ignore[arg-type]


def test_calibration_names_its_halves() -> None:
    """`(0.2, "micrometer")` and `("micrometer", 0.2)` are equally plausible
    spellings of the same thought; only one of them works."""
    calibration = Calibration(0.2, "micrometer")
    assert calibration.factor == 0.2
    assert calibration.unit == "micrometer"
