"""Spec types: what a lens structurally is, as types to put in a signature.

An action that convolves a z-stack does not take "a lens", it takes a volume::

    from mikro.arkitekt.specs import Volume

    @app.action
    def deconvolve(image: Volume) -> Volume: ...

Each spec is a :class:`~mikro.api.schema.Lens` annotated with rekuest's own
``Requires`` and ``Provides``, nothing more. Both are written out because a port
keeps only its side: an argument the ``Requires`` (the UI offers only lenses that
fit), a return the ``Provides`` (what the action says it made). A run tests them on
every lens that crosses the port, using :func:`lens_descriptors`: a lens that does
not fit fails the task, saying which constraint it broke.

Write your own the same way, as a plain assignment
(``from arkitekt import DescriptorOperator, Provides, Requires``)::

    DualColorVolume = Annotated[
        Lens,
        Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
        Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
        Requires(key=N_CHANNELS, operator=DescriptorOperator.EQUALS, value=2),
        Provides(key=N_CHANNELS, operator=DescriptorOperator.EQUALS, value=2),
    ]

Three things to know:

- Never a PEP 695 ``type`` statement: it wraps the ``Annotated`` so that the
  markers are dropped, without an error.
- The specs here carry no ``Description`` (a port takes only one). Add yours at
  the use: ``Annotated[Volume, Description("...")]``.
- "One channel" is ``n_channels <= 1``, an extent, never "no channel axis": a
  lens can pin a channel of a multichannel dataset, it cannot remove the axis.
  Action code must tolerate a channel axis of length one.
"""

from __future__ import annotations

from collections import Counter
from typing import Annotated, Any

from arkitekt_spec.actions import DescriptorOperator
from arkitekt_spec.declare.annotations import Provides, Requires

from mikro.api.schema import Lens
from mikro.traits import AxisSource, axis_table

# --- The descriptor keys --------------------------------------------------------
# The same keys the mikro server declares for a lens and an array dataset.

N_SPACE_AXES = "@mikro/n_space_axes"
"""How many of its axes are SPACE axes."""
N_TIME_AXES = "@mikro/n_time_axes"
"""How many of its axes are TIME axes."""
N_CHANNEL_AXES = "@mikro/n_channel_axes"
"""How many of its axes are CHANNEL axes."""
N_SPECTRUM_AXES = "@mikro/n_spectrum_axes"
"""How many of its axes are SPECTRUM axes."""
N_MICROTIME_AXES = "@mikro/n_microtime_axes"
"""How many of its axes are MICROTIME axes."""
N_CHANNELS = "@mikro/n_channels"
"""Its total extent along its CHANNEL axes."""
N_TIMEPOINTS = "@mikro/n_timepoints"
"""Its total extent along its TIME axes."""
VALUE_KIND = "@mikro/value_kind"
"""What its values mean. Provenance: stated by whoever made the data, never computed."""


def lens_descriptors(lens: AxisSource) -> dict[str, Any]:
    """The descriptors of a lens (or an array dataset), computed from its axes.

    One count per axis type, zero included, and the total extent along the
    channel and the time axes. ``VALUE_KIND`` is not in it: nothing about the
    axes tells a label mask from an image, so a constraint on it is the
    producer's word and is not tested.

    Args:
        lens: The lens or dataset to describe.

    Returns:
        Its descriptors, by key.
    """
    table = axis_table(lens)
    counts = Counter(axis_type for _, axis_type, _ in table)
    return {
        N_SPACE_AXES: counts["SPACE"],
        N_TIME_AXES: counts["TIME"],
        N_CHANNEL_AXES: counts["CHANNEL"],
        N_SPECTRUM_AXES: counts["SPECTRUM"],
        N_MICROTIME_AXES: counts["MICROTIME"],
        N_CHANNELS: sum(extent for _, axis_type, extent in table if axis_type == "CHANNEL"),
        N_TIMEPOINTS: sum(extent for _, axis_type, extent in table if axis_type == "TIME"),
    }


# --- By spatial rank: exactly one of these holds for any lens -------------------

Scalar = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=0),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=0),
]
"""No spatial axis at all."""

Profile = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=1),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=1),
]
"""One spatial axis: a line profile, a depth trace."""

Image = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
]
"""Two spatial axes: a plane."""

Volume = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
]
"""Three spatial axes: a stack, even one whose z holds a single plane."""

Hypervolume = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.GTE, value=4),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.GTE, value=4),
]
"""Four or more spatial axes."""

# --- By what else it carries: any of these may hold beside a spatial rank ------

Timeseries = Annotated[
    Lens,
    Requires(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a TIME axis, of any length."""

Multichannel = Annotated[
    Lens,
    Requires(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a CHANNEL axis, of any length."""

Spectral = Annotated[
    Lens,
    Requires(key=N_SPECTRUM_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_SPECTRUM_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a SPECTRUM axis: a spectrally resolved acquisition."""

Flim = Annotated[
    Lens,
    Requires(key=N_MICROTIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_MICROTIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a MICROTIME axis: fluorescence-lifetime arrival-time bins."""

Still = Annotated[
    Lens,
    Requires(key=N_TIMEPOINTS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_TIMEPOINTS, operator=DescriptorOperator.LTE, value=1),
]
"""At most one timepoint: no time axis, or one pinned to a single frame."""

SingleChannel = Annotated[
    Lens,
    Requires(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
]
"""At most one channel: no channel axis, or one pinned to a single channel."""

# --- The common combinations ----------------------------------------------------

TimelapseImage = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A plane over time."""

TimelapseVolume = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Requires(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A stack over time."""

MultichannelImage = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A plane with a channel axis."""

MultichannelVolume = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Requires(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A stack with a channel axis."""

SingleChannelImage = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
]
"""A plane with at most one channel."""

SingleChannelVolume = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Requires(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
]
"""A stack with at most one channel."""

RGBImage = Annotated[
    Lens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_CHANNEL_AXES, operator=DescriptorOperator.EQUALS, value=1),
    Provides(key=N_CHANNEL_AXES, operator=DescriptorOperator.EQUALS, value=1),
    Requires(key=N_CHANNELS, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_CHANNELS, operator=DescriptorOperator.EQUALS, value=3),
]
"""A plane whose one channel axis has exactly three positions: a photograph, a
brightfield slide."""

# --- By what the values mean ----------------------------------------------------

LabelMask = Annotated[
    Lens,
    Requires(key=VALUE_KIND, operator=DescriptorOperator.EQUALS, value="categorical"),
    Provides(key=VALUE_KIND, operator=DescriptorOperator.EQUALS, value="categorical"),
]
"""A lens whose values are object ids, not intensities. Provenance, so never
tested on the lens: an action that returns one says it made labels, and only an
action that takes one is offered them."""


__all__ = [
    "N_CHANNELS",
    "N_CHANNEL_AXES",
    "N_MICROTIME_AXES",
    "N_SPACE_AXES",
    "N_SPECTRUM_AXES",
    "N_TIMEPOINTS",
    "N_TIME_AXES",
    "VALUE_KIND",
    "Flim",
    "Hypervolume",
    "Image",
    "LabelMask",
    "Multichannel",
    "MultichannelImage",
    "MultichannelVolume",
    "Profile",
    "RGBImage",
    "Scalar",
    "SingleChannel",
    "SingleChannelImage",
    "SingleChannelVolume",
    "Spectral",
    "Still",
    "TimelapseImage",
    "TimelapseVolume",
    "Timeseries",
    "Volume",
    "lens_descriptors",
]
