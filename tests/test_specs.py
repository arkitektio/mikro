"""The spec types and the descriptors a lens is tested with.

``mikro.arkitekt.specs`` imports ``rekuest`` at module level, and rekuest is a
dev dependency rather than an install requirement — hence the skip. That is also
why the module is not exported from ``mikro/__init__.py``.

Server-free: a candidate is a stand-in naming axes and a shape, and the
comparison is the one a run applies to a lens crossing a port.
"""

from types import SimpleNamespace

import pytest

# Not `pytest.importorskip`: it imports under `simplefilter("error")`, and
# rekuest emits a DeprecationWarning on import, which would skip the whole
# module on every machine rather than only where rekuest is absent.
try:
    import rekuest  # noqa: F401 — presence is the question
except ImportError:  # pragma: no cover — depends on the install
    pytest.skip("rekuest is an optional dev dependency", allow_module_level=True)

from typing import Any, get_args

from arkitekt_spec.actions import ProvidesInput, RequiresInput
from arkitekt_spec.declare.descriptors import unfulfilled

from mikro.arkitekt import specs
from mikro.arkitekt.specs import (
    VALUE_KIND,
    Image,
    LabelMask,
    RGBImage,
    SingleChannelVolume,
    Volume,
    descriptors_of,
)

# `axis_types` moved onto `mikro.traits` with the lens/dataset traits, which is
# also where `Lens.axis_types` now reads it from. It stays a function as well as
# a property because the candidates below are `SimpleNamespace`, not models.
from mikro.traits import axis_types


def candidate(names, shape, types=None):
    """A stand-in for a Lens: axis names, a shape, and optionally typed axes."""
    system = None
    if types is not None:
        system = SimpleNamespace(
            axes=[
                SimpleNamespace(order=i, name=n, type=t)
                for i, (n, t) in enumerate(zip(names, types))
            ]
        )
    return SimpleNamespace(
        axis_names=names, shape=shape, coordinate_system=system, intrinsic_system=None
    )


VOLUME = candidate(["z", "y", "x"], (10, 20, 30))
MULTICHANNEL = candidate(
    ["c", "z", "y", "x"], (3, 10, 20, 30), ["CHANNEL", "SPACE", "SPACE", "SPACE"]
)


def facts(space: int, channel_axes: int = 0, channels: int = 0) -> dict[str, Any]:
    """Descriptors as the server states them for a lens: every count, zeroes included."""
    return {
        "@mikro/n_space_axes": space,
        "@mikro/n_time_axes": 0,
        "@mikro/n_channel_axes": channel_axes,
        "@mikro/n_spectrum_axes": 0,
        "@mikro/n_microtime_axes": 0,
        "@mikro/n_channels": channels,
        "@mikro/n_timepoints": 0,
    }


# What mikro says of the two, fetched with them (`descriptors` on the fragment).
VOLUME.descriptors = facts(space=3)
MULTICHANNEL.descriptors = facts(space=3, channel_axes=1, channels=3)


class TestDescriptors:
    def test_types_fall_back_to_the_bare_name_convention(self) -> None:
        assert axis_types(VOLUME) == ("SPACE", "SPACE", "SPACE")

    def test_a_typed_system_wins_over_the_convention(self) -> None:
        assert axis_types(MULTICHANNEL)[0] == "CHANNEL"

    def test_an_object_is_described_by_what_was_fetched_with_it(self) -> None:
        """The server's word, never recomputed and never asked for again."""
        assert descriptors_of(VOLUME) == facts(space=3)
        assert descriptors_of(VOLUME) is not VOLUME.descriptors

    def test_an_object_built_by_hand_has_none_so_nothing_is_tested(self) -> None:
        assert descriptors_of(candidate(["y", "x"], (4, 4))) == {}


def requires(spec: Any) -> list[RequiresInput]:
    """What a spec puts on an argument port."""
    return [
        marker for marker in get_args(spec)[1:] if isinstance(marker, RequiresInput)
    ]


def provides(spec: Any) -> list[ProvidesInput]:
    """What a spec puts on a return port."""
    return [
        marker for marker in get_args(spec)[1:] if isinstance(marker, ProvidesInput)
    ]


class TestSpecs:
    def test_a_volume_is_a_Volume_and_not_an_Image(self) -> None:
        described = descriptors_of(VOLUME)
        assert unfulfilled(requires(Volume), described) == ()
        assert unfulfilled(requires(Image), described) == (
            "@mikro/n_space_axes EQUALS 2 (actual 3)",
        )

    def test_every_unmet_constraint_is_reported_not_just_the_first(self) -> None:
        failures = unfulfilled(requires(RGBImage), descriptors_of(VOLUME))
        assert len(failures) == 3
        assert "@mikro/n_channels EQUALS 3" in failures[-1]

    def test_a_multichannel_volume_is_not_single_channel(self) -> None:
        assert unfulfilled(
            requires(SingleChannelVolume), descriptors_of(MULTICHANNEL)
        ) == ("@mikro/n_channels LTE 1 (actual 3)",)

    def test_provenance_is_tested_only_when_stated(self) -> None:
        described = descriptors_of(VOLUME)
        assert unfulfilled(provides(LabelMask), described) == ()
        (failure,) = unfulfilled(
            provides(LabelMask), {**described, VALUE_KIND: "continuous"}
        )
        assert "@mikro/value_kind EQUALS 'categorical' (actual 'continuous')" in failure

    def test_every_spec_says_the_same_on_both_sides_of_a_port(self) -> None:
        """An argument keeps the Requires and a return the Provides, so a spec that
        stated a constraint on one side only would mean something else there."""
        names = [
            name for name in specs.__all__ if name[0].isupper() and not name.isupper()
        ]
        assert len(names) == 20
        for name in names:
            spec = getattr(specs, name)
            asked = [(m.key, m.operator, m.value) for m in requires(spec)]
            made = [(m.key, m.operator, m.value) for m in provides(spec)]
            assert asked and asked == made, name
