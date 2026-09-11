"""Unit tests for the instrument-metadata builders.

Every rule here was previously re-implemented in each converter, and the two that
matter are server rules with no model-level guard: a `SettingInput` fills exactly one
value slot, and a device carrying no settings should not be recorded at all.
"""

import numpy as np
import pytest

from mikro_next.metadata import device, devices, setting, settings, text


class TestText:
    def test_none_stays_none(self) -> None:
        assert text(None) is None

    def test_an_enum_renders_as_its_value(self) -> None:
        """Without the unwrap this is `"UnitsLength.MICROMETER"` — legal, and wrong
        in a way nothing downstream would flag."""

        class Unit:
            value = "µm"

        assert text(Unit()) == "µm"

    @pytest.mark.parametrize("empty", ["", "   ", b"", b"\x00\x00"])
    def test_nothing_to_say_is_none_not_an_empty_setting(self, empty: object) -> None:
        assert text(empty) is None

    def test_a_nul_padded_byte_field_stops_at_the_first_nul(self) -> None:
        """Fixed-width char fields survive JSON with their padding and show up in
        labels."""
        assert text(b"FLAIR\x00\x00\x00\x00") == "FLAIR"

    def test_a_numpy_byte_scalar_is_decoded_too(self) -> None:
        assert text(np.array(b"T1\x00\x00", dtype="S8")) == "T1"


class TestSetting:
    def test_a_single_slot_is_kept(self) -> None:
        result = setting("magnification", number=60.0)
        assert result is not None
        assert (result.name, result.number) == ("magnification", 60.0)

    def test_no_slot_is_none_so_an_absent_field_costs_nothing(self) -> None:
        assert setting("magnification") is None

    def test_two_slots_are_refused(self) -> None:
        """The model declares four plain optionals and will happily accept two."""
        with pytest.raises(ValueError, match="fills 2 value slots"):
            setting("magnification", number=60.0, string="60x")

    def test_a_quantity_becomes_a_pint_scalar_not_a_string(self) -> None:
        """The wire field is pint-backed; `"50 ms"` reads identically in source but
        is a different type. Both spellings must land on the same JSON."""
        from kanne.scalars import GenericQuantity

        result = setting("exposure", quantity="50 ms")
        assert result is not None
        assert isinstance(result.quantity, GenericQuantity)
        assert result.model_dump_json() == setting(
            "exposure", quantity=GenericQuantity("50 ms")
        ).model_dump_json()

    def test_a_false_flag_is_a_value_not_an_absence(self) -> None:
        """`False` is falsey but is something the file said."""
        assert setting("binned", flag=False) is not None


class TestDevice:
    def test_settings_drops_the_absent_ones(self) -> None:
        kept = settings(setting("a", number=1.0), setting("b"), None)
        assert [s.name for s in kept] == ["a"]

    def test_a_device_with_nothing_to_say_is_none(self) -> None:
        """`DeviceStateInput(label=..., settings=[])` asserts a device was involved
        and then declines to describe it, which is worse than silence."""
        assert device("objective", "OBJECTIVE", setting("magnification")) is None

    def test_a_device_keeps_only_the_settings_that_carry_a_value(self) -> None:
        result = device(
            "objective", "OBJECTIVE", setting("mag", number=60.0), setting("na")
        )
        assert result is not None
        assert (result.label, len(result.settings)) == ("objective", 1)

    def test_devices_drops_the_silent_ones(self) -> None:
        kept = devices(device("a", "OBJECTIVE", setting("x", number=1.0)), None)
        assert [d.label for d in kept] == ["a"]
