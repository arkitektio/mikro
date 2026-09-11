"""The spec vocabulary, the descriptors it matches against, and the composer.

``mikro_next.specs`` imports ``rekuest_next`` at module level, and rekuest is a
dev dependency rather than an install requirement — hence the skip. That is also
why the module is not exported from ``mikro_next/__init__.py``.

Everything here is server-free by construction: `compose` is the reference
implementation a frontend mirrors to decide, for a dropped dataset and a port's
requires, whether to filter it out, pass it through, or offer a picker.
"""

from types import SimpleNamespace

import pytest

# Not `pytest.importorskip`: it imports under `simplefilter("error")`, and
# rekuest emits a DeprecationWarning on import, which would skip the whole
# module on every machine rather than only where rekuest is absent.
try:
    import rekuest_next  # noqa: F401 — presence is the question
except ImportError:  # pragma: no cover — depends on the install
    pytest.skip("rekuest-next is an optional dev dependency", allow_module_level=True)

from mikro_next.specs import (
    N_CHANNELS,
    VALUE_KIND,
    Image,
    LabelMask,
    RGBImage,
    SingleChannelVolume,
    SpecMismatch,
    Volume,
    axis_types,
    compose,
    exactly,
    fulfills,
    lens_descriptors,
    refine,
    selections_for,
    spec_constraints,
    unfulfilled,
)


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


class TestDescriptors:
    def test_types_fall_back_to_the_bare_name_convention(self) -> None:
        assert axis_types(VOLUME) == ("SPACE", "SPACE", "SPACE")

    def test_a_typed_system_wins_over_the_convention(self) -> None:
        assert axis_types(MULTICHANNEL)[0] == "CHANNEL"

    def test_every_count_key_is_emitted_including_the_zeroes(self) -> None:
        """`Still` and `SingleChannel` match on absence, so a missing key and a
        zero count are not the same thing."""
        descriptors = lens_descriptors(VOLUME)
        assert descriptors["@mikro/n_space_axes"] == 3
        assert descriptors["@mikro/n_channel_axes"] == 0

    def test_adjustable_keys_are_total_extents(self) -> None:
        assert lens_descriptors(MULTICHANNEL)["@mikro/n_channels"] == 3

    def test_value_kind_is_never_computed(self) -> None:
        """It is provenance: only a producer that made labels can vouch for it."""
        assert VALUE_KIND not in lens_descriptors(MULTICHANNEL)


class TestFulfilment:
    def test_a_volume_fulfils_Volume(self) -> None:
        assert fulfills(VOLUME, Volume)

    def test_every_unmet_constraint_is_reported_not_just_the_first(self) -> None:
        failures = unfulfilled(VOLUME, RGBImage)
        assert len(failures) == 3
        assert "@mikro/n_channels EQUALS 3" in failures[-1]

    def test_provenance_must_be_declared(self) -> None:
        (failure,) = unfulfilled(VOLUME, LabelMask)
        assert "key absent" in failure
        assert fulfills(VOLUME, LabelMask, {VALUE_KIND: "categorical"})

    def test_refine_stacks_constraints_onto_a_base(self) -> None:
        dual = refine(Volume, *exactly(N_CHANNELS, 2))
        assert len(spec_constraints(dual)) == 2


class TestCompose:
    def test_an_invariant_mismatch_is_a_hard_failure(self) -> None:
        """No lens over a volume ever makes it a plane — extents shrink, axes
        do not vanish."""
        plan = compose(VOLUME, Image)
        assert not plan.satisfiable

    def test_a_fitting_candidate_needs_no_adjustment(self) -> None:
        plan = compose(VOLUME, Volume)
        assert plan.already_fits

    def test_an_adjustable_mismatch_becomes_a_pin(self) -> None:
        """Which channel to keep is exactly the choice to render as a picker."""
        plan = compose(MULTICHANNEL, SingleChannelVolume)
        assert plan.satisfiable and not plan.already_fits
        (pin,) = plan.pins
        assert (pin.axis_type, pin.operator, pin.target) == ("CHANNEL", "LTE", 1)
        assert pin.axes == (("c", 3),)


class TestSelections:
    def test_an_int_pin_satisfies_the_plan(self) -> None:
        plan = compose(MULTICHANNEL, SingleChannelVolume)
        assert selections_for(plan, c=1) == {"c": 1}

    def test_a_size_one_slice_satisfies_it_too(self) -> None:
        plan = compose(MULTICHANNEL, SingleChannelVolume)
        assert selections_for(plan, c=slice(0, 1)) == {"c": slice(0, 1)}

    def test_a_selection_that_keeps_too_much_is_refused(self) -> None:
        plan = compose(MULTICHANNEL, SingleChannelVolume)
        with pytest.raises(ValueError, match="need LTE 1"):
            selections_for(plan, c=(0, 2))

    def test_an_unpinned_pin_is_refused(self) -> None:
        plan = compose(MULTICHANNEL, SingleChannelVolume)
        with pytest.raises(ValueError, match="must be reduced to"):
            selections_for(plan)

    def test_a_choice_no_pin_asked_about_is_refused(self) -> None:
        """It would silently change the data the action was offered."""
        plan = compose(MULTICHANNEL, SingleChannelVolume)
        with pytest.raises(ValueError, match="no pin asked about"):
            selections_for(plan, c=0, z=1)

    def test_an_out_of_range_index_is_refused_by_axis(self) -> None:
        plan = compose(MULTICHANNEL, SingleChannelVolume)
        with pytest.raises(ValueError, match="out of range for axis 'c'"):
            selections_for(plan, c=9)

    def test_an_unsatisfiable_plan_is_refused_outright(self) -> None:
        with pytest.raises(SpecMismatch, match="unsatisfiable"):
            selections_for(compose(VOLUME, Image))
