"""Light-path graphs: the optical elements a photon passes through.

An element in a `LightpathGraphInput` is joined to its neighbours by *ports* rather
than by position, so even the simplest element — a filter with one thing before it and
one after — needs an explicit input and output port before it can be wired up. These
builders cover that shape, which is nearly every element.

    OpticalElementInput(
        kind=ElementKind.FILTER, id="ex", name="Ex 488/10",
        ports=in_out(SpectrumInput(center=488.0, width=10.0)),
    )

The spectrum rides on the **output** port: it describes what leaves the element, which
is what the next element receives. An input port carries none — what arrives is
whatever the previous element emitted, and stating it twice invites the two to drift.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mikro_next.api.schema import LightPortInput, PortRole, SpectrumInput

__all__ = ["in_out", "port"]


def port(
    port_id: str,
    name: str,
    role: PortRole,
    spectrum: SpectrumInput | None = None,
) -> LightPortInput:
    """One free-space port on an optical element.

    Args:
        port_id: Unique within the element.
        name: Human-readable label.
        role: `PortRole.INPUT` or `PortRole.OUTPUT`.
        spectrum: What leaves through this port; only meaningful on an output.

    Returns:
        The port.
    """
    from mikro_next.api.schema import ChannelKind, LightPortInput

    return LightPortInput(
        id=port_id,
        name=name,
        role=role,
        channel=ChannelKind.FREE_SPACE,
        spectrum=spectrum,
    )


def in_out(spectrum: SpectrumInput | None = None) -> list[LightPortInput]:
    """The ordinary input/output pair for an in-line element.

    Args:
        spectrum: What leaves the element, carried on the output port.

    Returns:
        The two ports, input first.
    """
    from mikro_next.api.schema import PortRole

    return [
        port("in", "input", PortRole.INPUT),
        port("out", "output", PortRole.OUTPUT, spectrum),
    ]
