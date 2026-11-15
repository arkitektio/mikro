"""Spec types: what a lens structurally is, as types to put in a signature.

An action that convolves a z-stack does not take "a lens", it takes a volume::

    from mikro.arkitekt.specs import Volume

    @app.action
    def deconvolve(image: Volume) -> Volume: ...

Each spec is an :class:`~mikro.api.schema.ArrayLens` annotated with rekuest's own
``Requires`` and ``Provides``, nothing more. Both are written out because a port
keeps only its side: an argument the ``Requires`` (the UI offers only lenses that
fit), a return the ``Provides`` (what the action says it made). A run tests them on
every lens that crosses the port, using the lens's own ``descriptors`` (the server's,
fetched with it; see :func:`descriptors_of`): a lens that does
not fit fails the task, saying which constraint it broke.

Write your own the same way, as a plain assignment
(``from arkitekt import DescriptorOperator, Provides, Requires``)::

    DualColorVolume = Annotated[
        ArrayLens,
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

from typing import Annotated, Any

from arkitekt_spec.actions import DescriptorOperator
from arkitekt_spec.declare.annotations import Provides, Requires

from mikro.api.schema import Annotation, ArrayLens

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
SIZE = "@mikro/size"
"""How many elements it has: the product of its shape."""
DSIZE = "@mikro/dsize"
"""How many bytes one element takes, from its dtype: its uncompressed size in bytes is size * dsize."""
VALUE_KIND = "@mikro/value_kind"
"""What its values mean. Provenance: the server reads it off the data's derivation, never off its axes."""
DTYPE = "@mikro/dtype"
"""The element type of its values, as numpy spells it (uint8, uint16, float32, ...): its level-0 zarr store's."""
ANNOTATION_KIND = "@mikro/annotation_kind"
"""The shape one annotation is drawn as, as the names of ``AnnotationKind``."""
METRIC_KEY = "@mikro/metric_key"
"""What a metric measured, namespaced by who measured it: ``ais_suite.measure_profile/threshold_distance``."""
MAGNITUDE = "@mikro/magnitude"
"""A quantity's number; absent for a code."""
UNIT = "@mikro/unit"
"""A quantity's unit, as the server normalized it; absent for a code."""
METRIC_CODE = "@mikro/metric_code"
"""The category a process emitted; absent for a quantity."""
TARGET_IDENTIFIER = "@mikro/target_identifier"
"""The structure of the object a metric is about: ``@mikro/annotation``, ``@mikro/arraydataset``, ..."""
TARGET_OBJECT = "@mikro/target_object"
"""The id of the object a metric is about."""
EXTENSION = "@mikro/extension"
"""A file's extension, lowercased and without the dot: ``nd2``, ``ome.tif``; empty for none. What an importer is picked by."""


def descriptors_of(obj: Any) -> dict[str, Any]:  # noqa: ANN401 - any fragment that selects `descriptors`
    """What mikro says of an object: its ``descriptors``, as they were fetched with it.

    Every identified mikro type has the field, and every fragment a structure is
    expanded to selects it, so describing an object costs nothing: the facts arrive
    in the query that loads it. They are the server's own, the ones its pickers
    filter by and its signals carry, so what a port tests is what the server matched.

    Never compute them here, and never ask the server for them a second time: a
    describer that makes its own round trip doubles every constrained call. An
    object that was not fetched with its descriptors (one built by hand) has none,
    and a constraint on a key that is absent is not tested.

    Args:
        obj: The object to describe.

    Returns:
        Its descriptors, by key.
    """
    return dict(getattr(obj, "descriptors", None) or {})


#: Extensions of two parts, which name a format the last part alone does not. The server's list, verbatim.
DOUBLE_EXTENSIONS = ("ome.tif", "ome.tiff", "ome.zarr", "ome.btf", "tar.gz", "nii.gz")


def file_extension(name: str) -> str:
    """A file name's extension, lowercased and without the dot: ``ome.tif`` for ``Cells.OME.TIF``, empty for none.

    The server's rule, verbatim: a port's ``requires`` on :data:`EXTENSION` is tested
    against this, and the file picker filters by the server's copy.
    """
    base = name.rsplit("/", 1)[-1].lower()
    for double in DOUBLE_EXTENSIONS:
        if base.endswith(f".{double}"):
            return double
    stem, dot, extension = base.rpartition(".")
    return extension if dot and stem else ""


# --- By spatial rank: exactly one of these holds for any lens -------------------

Scalar = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=0),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=0),
]
"""No spatial axis at all."""

Profile = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=1),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=1),
]
"""One spatial axis: a line profile, a depth trace."""

Image = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
]
"""Two spatial axes: a plane."""

Volume = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
]
"""Three spatial axes: a stack, even one whose z holds a single plane."""

Hypervolume = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.GTE, value=4),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.GTE, value=4),
]
"""Four or more spatial axes."""

# --- By what else it carries: any of these may hold beside a spatial rank ------

Timeseries = Annotated[
    ArrayLens,
    Requires(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a TIME axis, of any length."""

Multichannel = Annotated[
    ArrayLens,
    Requires(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a CHANNEL axis, of any length."""

Spectral = Annotated[
    ArrayLens,
    Requires(key=N_SPECTRUM_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_SPECTRUM_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a SPECTRUM axis: a spectrally resolved acquisition."""

Flim = Annotated[
    ArrayLens,
    Requires(key=N_MICROTIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_MICROTIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""Has a MICROTIME axis: fluorescence-lifetime arrival-time bins."""

Still = Annotated[
    ArrayLens,
    Requires(key=N_TIMEPOINTS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_TIMEPOINTS, operator=DescriptorOperator.LTE, value=1),
]
"""At most one timepoint: no time axis, or one pinned to a single frame."""

SingleChannel = Annotated[
    ArrayLens,
    Requires(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
]
"""At most one channel: no channel axis, or one pinned to a single channel."""

# --- The common combinations ----------------------------------------------------

TimelapseImage = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A plane over time."""

TimelapseVolume = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Requires(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A stack over time."""

MultichannelImage = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A plane with a channel axis."""

MultichannelVolume = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Requires(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
    Provides(key=N_CHANNEL_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A stack with a channel axis."""

SingleChannelImage = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
]
"""A plane with at most one channel."""

SingleChannelVolume = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
    Requires(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
    Provides(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
]
"""A stack with at most one channel."""

RGBImage = Annotated[
    ArrayLens,
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
    ArrayLens,
    Requires(key=VALUE_KIND, operator=DescriptorOperator.EQUALS, value="categorical"),
    Provides(key=VALUE_KIND, operator=DescriptorOperator.EQUALS, value="categorical"),
]
"""A lens whose values are object ids, not intensities. Provenance, so never
tested on the lens: an action that returns one says it made labels, and only an
action that takes one is offered them."""


# --- Annotations, by the shape they are drawn as --------------------------------

PathAnnotation = Annotated[
    Annotation,
    Requires(key=ANNOTATION_KIND, operator=DescriptorOperator.EQUALS, value="PATH"),
    Provides(key=ANNOTATION_KIND, operator=DescriptorOperator.EQUALS, value="PATH"),
]
"""One annotation drawn as a PATH: an open run of vertices, what a tracing or a
centreline is. Named ``PathAnnotation`` rather than ``Path`` so that it does not
shadow ``pathlib.Path`` in the app that imports it."""


__all__ = [
    "ANNOTATION_KIND",
    "DOUBLE_EXTENSIONS",
    "EXTENSION",
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
    "PathAnnotation",
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
    "descriptors_of",
    "file_extension",
]
