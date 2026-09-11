"""Instrument metadata: the settings and device states an ingest records.

A converter reads a pile of loosely-typed header fields and has to turn them into
`SettingInput`s and `DeviceStateInput`s. Two rules govern that, and neither is
enforced by the generated models, so both used to be re-implemented per converter:

* a `SettingInput` fills **exactly one** of its four value slots, and
* a device that carries no settings should not be recorded at all.

`setting` and `device` return ``None`` when there is nothing to say, and `settings`
and `devices` drop the ``None``s — so an absent header field costs the caller
nothing and no device ends up asserting ``model = "None"``.

    devices(
        device("objective", "OBJECTIVE",
               setting("magnification", number=60.0),
               setting("immersion", string="Oil")),
        device("camera", "DETECTOR", setting("exposure", quantity="50 ms")),
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from kanne.scalars import GenericQuantity

if TYPE_CHECKING:
    from mikro_next.api.schema import DeviceStateInput, SettingInput

__all__ = ["device", "devices", "setting", "settings", "text"]


def text(value: object) -> str | None:
    """A None-safe string, unwrapping enums and decoding fixed-width byte fields.

    Three things go wrong otherwise, all of them quiet:

    * an enum serialises as ``"UnitsLength.MICROMETER"`` rather than ``"µm"`` —
      legal, and wrong in a way nothing downstream would flag;
    * a NUL-padded char field out of a binary header yields the text followed by
      sixty NULs, which survives JSON, reaches the server and shows up in a label;
    * an empty or whitespace-only string becomes a setting that says nothing.

    Args:
        value: Anything a header hands back — a string, an enum, ``bytes``, a numpy
            byte scalar, or ``None``.

    Returns:
        The rendered text, or ``None`` if there was nothing to render.
    """
    if value is None:
        return None
    if isinstance(value, np.ndarray) and value.dtype.kind == "S":
        value = value.item()
    if isinstance(value, bytes):
        # Fixed-width char fields are NUL-padded; truncating at the first NUL is
        # what the format means.
        value = value.split(b"\x00")[0].decode("latin-1", "replace")
    rendered = str(getattr(value, "value", value)).strip()
    return rendered or None


def setting(
    name: str,
    *,
    quantity: str | GenericQuantity | None = None,
    number: float | None = None,
    string: str | None = None,
    flag: bool | None = None,
) -> SettingInput | None:
    """One named value, or ``None`` when there is no value to name.

    ``SettingInput`` fills exactly one of its four value slots — but the model
    declares four plain optionals and will happily accept two, so that rule is a
    server rule with no client-side guard. This check is that guard.

    Args:
        name: What the value is called.
        quantity: A pint-backed scalar string, e.g. ``"50 ms"``.
        number: A bare number.
        string: Free text.
        flag: A boolean.

    Returns:
        The setting, or ``None`` if every slot was empty.

    Raises:
        ValueError: If more than one value slot is filled.
    """
    from mikro_next.api.schema import SettingInput

    filled = [v for v in (quantity, number, string, flag) if v is not None]
    if len(filled) > 1:
        raise ValueError(
            f"setting {name!r} fills {len(filled)} value slots, not 1: a SettingInput "
            f"carries exactly one of quantity/number/string/flag"
        )
    if not filled:
        return None
    return SettingInput(
        name=name,
        # A `GenericQuantity` is a pint-backed scalar, not a plain string; the wire
        # rejects the bare `"50 ms"` that reads identically in source.
        quantity=None if quantity is None else GenericQuantity(quantity),
        number=number,
        text=string,
        flag=flag,
    )


def settings(*items: SettingInput | None) -> list[SettingInput]:
    """The settings that actually carry a value.

    Args:
        items: Settings, as returned by `setting` — ``None`` for the absent ones.

    Returns:
        The non-``None`` settings, in the order given.
    """
    return [item for item in items if item is not None]


def device(
    label: str, kind: str, *items: SettingInput | None
) -> DeviceStateInput | None:
    """A device state, or ``None`` when the file said nothing about it.

    A ``DeviceStateInput(label="microscope", settings=[])`` asserts a microscope was
    involved and then declines to say anything about it, which is worse than silence.

    Args:
        label: What to call this device.
        kind: Its `DeviceKind`, as the schema spells it.
        items: Its settings — ``None`` entries are dropped.

    Returns:
        The device state, or ``None`` if no setting carried a value.
    """
    from mikro_next.api.schema import DeviceStateInput

    kept = settings(*items)
    if not kept:
        return None
    return DeviceStateInput(label=label, kind=kind, settings=tuple(kept))


def devices(*items: DeviceStateInput | None) -> list[DeviceStateInput]:
    """The device states that actually say something.

    Args:
        items: Device states, as returned by `device` — ``None`` for the silent ones.

    Returns:
        The non-``None`` device states, in the order given.
    """
    return [item for item in items if item is not None]
