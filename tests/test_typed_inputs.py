"""The inputs an app hands mikro take what its data libraries produce.

xarray types a dim as ``Hashable``, and a value relation reads most naturally as its
name; both used to be refused by the type checker while working at runtime.
"""

from enum import Enum
from typing import get_args

import pytest

from mikro.api.schema import AxisInput, AxisType, ValueRelation
from mikro.traits import DatasetTrait, HasNamedAxes, Lensable, ValueRelationName


class Dim(str, Enum):
    """A hashable dim that is not a plain ``str`` (xarray allows any hashable)."""

    Z = "z"


def test_a_bare_axis_name_may_be_any_hashable() -> None:
    """A str, a str-valued enum member, or an AxisInput itself."""
    assert AxisInput.model_validate("t").type == AxisType.TIME
    assert AxisInput.model_validate(Dim.Z).name == "z"
    assert AxisInput.model_validate(AxisInput(name="c", type=AxisType.CHANNEL)).name == "c"


class Source(HasNamedAxes):
    """Axes as a fetched lens reports them."""

    @property
    def axis_table(self):  # noqa: ANN201 -- the trait's own return type
        """Two axes: z in space, c a channel."""
        return (("z", "SPACE", 4), ("c", "CHANNEL", 2))


def test_carried_axes_take_the_dims_xarray_reports() -> None:
    """Known dims keep their source type; a new one falls back to its name."""
    axes = Source().carried_axes(("c", Dim.Z, "t"))
    assert [(a.name, a.type) for a in axes] == [
        ("c", AxisType.CHANNEL),
        ("z", AxisType.SPACE),
        ("t", AxisType.TIME),
    ]


class Lens(Lensable):
    """The least a lens is to derive from: an id."""

    id = "lens-1"


def test_a_value_relation_may_be_given_by_its_value() -> None:
    """`"TRANSFORMED"` means ValueRelation.TRANSFORMED."""
    edge = Lens().derive_identity(value_relation="TRANSFORMED")
    assert edge.value_relation == ValueRelation.TRANSFORMED


def test_the_value_relation_names_are_the_enum_values() -> None:
    """The Literal mirrors the generated enum; a regen that adds a member fails here."""
    assert set(get_args(ValueRelationName)) == {member.value for member in ValueRelation}


def test_staging_a_dataset_fetched_without_its_grid_says_why() -> None:
    """``dataset.stage()`` refuses clearly instead of failing on ``None``."""

    class Dataset(DatasetTrait):
        """Fetched without its intrinsic system."""

        intrinsic_system = None

    with pytest.raises(ValueError, match="select intrinsicSystem"):
        Dataset().stage(name="Default")
