"""Render graphs: what a layer does with the pixels behind it.

A layer's recipe is a small tree — a blend node over one or more channel nodes,
each with its own transfer function. Written out by hand that is three levels of
nesting for the simplest possible "show this in green", so these builders cover
the shapes that actually recur::

    channel_graph(colormap=ColorMap.INFERNO, gamma=0.8)
    composite_graph([ChannelSpec(intensity_index=0, colormap=ColorMap.CYAN),
                     ChannelSpec(intensity_index=1, colormap=ColorMap.MAGENTA)])
    rgb_graph()

For the common cases you may not need a graph at all: staging a scene from
a coordinate system — ``dataset.intrinsic_system.stage(policy=ScenePolicyInput(...))``
— has the server build the scene, the lens and a default layer for you. Reach for
these when you want something the default recipes do not express — a specific
colormap, a contrast window, a projection mode.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Union

from pydantic import BaseModel, ConfigDict

from mikro_next.api.schema import (
    Blending,
    ColorMap,
    LayerNodeInput,
    LayerRenderGraphInput,
    ProjectionMode,
    TransferFunctionInput,
)
from mikro_next.vocabulary import LayerNodeKind

#: A colour as the wire wants it. Three components are completed to RGBA with a
#: full alpha by `RGBAColorInputTrait`; four are passed through.
RGBAColor = Union[tuple[int, int, int], tuple[int, int, int, int]]


#: Full alpha. `TransferFunctionInput.color` is a bare ``[Int!]``, so nothing in its
#: type says how many components it wants — the server rejects three.
OPAQUE = 255

#: The three additive primaries an implicit-RGB stack is recomposed from, in array
#: order. Not a palette choice: the samples *are* red, green and blue, so anything
#: else would repaint a photograph.
RGB_PRIMARIES: tuple[tuple[int, int, int], ...] = (
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
)

#: The rotation for channels with neither a recorded colour nor a wavelength. Ordered
#: so the first few stay maximally distinguishable when additively blended.
FALLBACK_COLORS: tuple[tuple[int, int, int], ...] = (
    (0, 255, 255),
    (255, 0, 255),
    (255, 255, 0),
    (0, 255, 0),
    (255, 80, 80),
    (80, 130, 255),
    (255, 160, 0),
    (220, 220, 220),
)


def rgba(color: Sequence[int], alpha: int = OPAQUE) -> tuple[int, int, int, int]:
    """An RGB triple completed to the RGBA quadruple the server requires.

    ``TransferFunctionInput.color`` arrives as a bare ``[Int!]``, so nothing in its
    type says how many components it wants; the server rejects three. Send every
    colour out through here and that constraint is satisfied in one place rather than
    remembered at each literal.

    Args:
        color: At least three components; anything past the third is ignored.
        alpha: The alpha component, full by default.

    Returns:
        The colour as ``(r, g, b, a)``.
    """
    r, g, b = (int(c) for c in color[:3])
    return (r, g, b, int(alpha))


def hue_ramp(index: int, total: int) -> tuple[int, int, int]:
    """An evenly spaced hue, for stacks with more channels than the palette has.

    A 16-band spectral or FLIM stack rotating through eight colours gives two channels
    the same one, which reads as a rendering bug rather than as running out of names.

    Args:
        index: Which channel this is.
        total: How many there are, which sets the spacing.

    Returns:
        The colour as an ``(r, g, b)`` triple.
    """
    import colorsys

    r, g, b = colorsys.hsv_to_rgb((index / max(total, 1)) % 1.0, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


def fallback_color(index: int, total: int, offset: int = 0) -> tuple[int, int, int, int]:
    """The colour for a channel the file said nothing useful about.

    The palette while it lasts, an evenly spaced hue once there are more channels than
    palette entries.

    Args:
        index: Which channel this is.
        total: How many there are.
        offset: Rotates the palette *between* datasets. Within one dataset the channel
            index already walks it, but several datasets composited into one shared
            scene would otherwise each open on the same colour and blend to a wash.

    Returns:
        The colour as ``(r, g, b, a)``.
    """
    if total > len(FALLBACK_COLORS):
        return rgba(hue_ramp(index, total))
    return rgba(FALLBACK_COLORS[(index + offset) % len(FALLBACK_COLORS)])


def color_for_wavelength(
    nanometers: float,
    ramp: Sequence[tuple[float, tuple[int, int, int]]],
    beyond: tuple[int, int, int],
) -> tuple[int, int, int, int]:
    """The first colour in ``ramp`` whose edge the wavelength falls below.

    Roughly the colour the eye would have seen down the eyepiece — the one guess about
    a channel a microscopist can check at a glance. The ramp is a parameter because
    what the wavelength *means* differs: an emission wavelength gives the colour the
    dye actually emitted, an excitation wavelength gives the colour the channel is
    called. Same lookup, different claim.

    Args:
        nanometers: The wavelength.
        ramp: ``(edge, colour)`` pairs in ascending edge order.
        beyond: The colour for a wavelength past the last edge.

    Returns:
        The colour as ``(r, g, b, a)``.
    """
    for edge, color in ramp:
        if nanometers < edge:
            return rgba(color)
    return rgba(beyond)


class ChannelSpec(BaseModel):
    """One channel of a composite: which positions to read, and how to colour them.

    Flat on purpose — the split between the channel node and its transfer
    function is a detail of the wire format, not something worth making a caller
    nest for. `_channel_node` sorts these fields into the two nodes.

    There is deliberately no ``categorical`` here. A transfer function maps a
    continuous intensity to a colour; mapping discrete object ids to distinct
    colours is a different thing entirely, and it lives on a label layer
    (`create_label_layer`, `LabelRenderInput`) rather than on a channel node.
    """

    # -- channel-node settings
    intensity_axis: str | None = "c"
    intensity_index: int = 0
    mode: ProjectionMode | None = None
    label: str | None = None
    visible: bool | None = None

    # -- transfer-function settings
    colormap: ColorMap | None = None
    color: RGBAColor | None = None
    clim_min: float | None = None
    clim_max: float | None = None
    gamma: float | None = None
    opacity: float | None = None
    invert: bool | None = None

    # No `alias` on any field: a ChannelSpec is written in Python, never parsed
    # off the wire, and an alias would make type checkers reject the snake_case
    # spelling the caller actually writes.
    model_config = ConfigDict(frozen=True, extra="forbid")


def _channel_node(spec: ChannelSpec) -> LayerNodeInput:
    """One channel node, with its transfer function, from a spec.

    Deliberately carries no ``mode``. A projection is its own node kind
    server-side — ``ChannelSourceNode`` has no ``mode`` field at all, so a mode
    set here is accepted by the mutation and then silently dropped, leaving a
    z-stack rendering one slice. `_project` wraps this node instead.
    """
    kind: LayerNodeKind = "channel"
    return LayerNodeInput(
        kind=kind,
        intensity_axis=spec.intensity_axis,
        intensity_index=spec.intensity_index,
        label=spec.label,
        visible=spec.visible,
        transfer=TransferFunctionInput(
            colormap=spec.colormap,
            color=spec.color,
            clim_min=spec.clim_min,
            clim_max=spec.clim_max,
            gamma=spec.gamma,
            opacity=spec.opacity,
            invert=spec.invert,
        ),
    )


def _as_spec(spec: ChannelSpec | Mapping[str, object]) -> ChannelSpec:
    """Accept a mapping wherever a `ChannelSpec` is wanted.

    Callers that build their channel settings programmatically hold a dict, and
    ``ChannelSpec(**d)`` at every call site is noise. A mapping is validated into
    a spec here, so a bad key is a pydantic error naming the field rather than an
    ``AttributeError`` from deep inside the node builder.
    """
    if isinstance(spec, ChannelSpec):
        return spec
    return ChannelSpec.model_validate(dict(spec))


def _project(node: LayerNodeInput, mode: ProjectionMode | None) -> LayerNodeInput:
    """Wrap a channel node in a projection, or return it untouched.

    The projection sits *above* the channel rather than beside it: it consumes
    the axis it walks and hands the blend node the 2D image that comes out. A
    channel with no ``mode`` is passed straight through, so a plain 2D image
    still produces the flat ``blend -> channel`` tree it always did.
    """
    if mode is None:
        return node
    kind: LayerNodeKind = "projection"
    return LayerNodeInput(kind=kind, mode=mode, children=(node,))


def composite_graph(
    specs: Iterable[ChannelSpec | Mapping[str, object]],
    blending: Blending = Blending.ADDITIVE,
) -> LayerRenderGraphInput:
    """Composite several channels into one layer.

    Each `ChannelSpec` mixes channel settings (``intensity_axis``,
    ``intensity_index``, ``mode``) with transfer settings (``colormap``,
    ``color``, ``clim_min``/``clim_max``, ``gamma``, ``opacity``, ``invert``);
    they are sorted into the right nodes for you.

        composite_graph([
            ChannelSpec(intensity_index=0, colormap=ColorMap.CYAN),
            ChannelSpec(intensity_index=1, colormap=ColorMap.MAGENTA, opacity=0.7),
        ])
    """
    kind: LayerNodeKind = "blend"
    resolved = tuple(_as_spec(spec) for spec in specs)
    children = tuple(_project(_channel_node(spec), spec.mode) for spec in resolved)
    if not children:
        raise ValueError("A render graph needs at least one channel source")
    return LayerRenderGraphInput(
        root=LayerNodeInput(kind=kind, blending=blending, children=children)
    )


def channel_graph(
    colormap: ColorMap | None = None,
    color: RGBAColor | None = None,
    intensity_axis: str | None = "c",
    intensity_index: int = 0,
    clim_min: float | None = None,
    clim_max: float | None = None,
    gamma: float | None = None,
    opacity: float | None = None,
    invert: bool | None = None,
    mode: ProjectionMode | None = None,
    blending: Blending = Blending.ADDITIVE,
) -> LayerRenderGraphInput:
    """A single channel with a fully specified transfer function.

    ``intensity_axis`` names the axis whose positions are composited *together*
    as separate colour channels, so it has to be a CHANNEL axis — the server
    rejects a TIME or SPACE axis outright, and for good reason: pointing it at
    ``t`` stacks every frame of a timelapse on top of each other at once and
    consumes the axis the time slider would have walked.

    Pass ``intensity_axis=None`` for data that is single-valued per rendered
    plane — a bare z-stack, a time series. The projection ``mode`` and the time
    slider already know which axis they walk.
    """
    return composite_graph(
        [
            ChannelSpec(
                intensity_axis=intensity_axis,
                intensity_index=intensity_index,
                mode=mode,
                colormap=colormap,
                color=color,
                clim_min=clim_min,
                clim_max=clim_max,
                gamma=gamma,
                opacity=opacity,
                invert=invert,
            )
        ],
        blending=blending,
    )


def rgb_graph(
    clim_min: float = 0.0,
    clim_max: float = 255.0,
    intensity_axis: str = "c",
    channels: Sequence[int] = (0, 1, 2),
    mode: ProjectionMode | None = None,
) -> LayerRenderGraphInput:
    """Three channels composited as red, green and blue — a photograph, a
    brightfield slide, anything already in display colour.

    The contrast window defaults to a full 8-bit range rather than being read
    off the data: an RGB image is already display-referred, so stretching it
    would change the colours it was authored with.

    ``mode`` projects each channel through the volume, for the RGB z-stack case.
    It is here because without it the only way to get a projection was to
    hand-build the three specs, which is what the converters were doing.
    """
    if len(channels) != 3:
        raise ValueError(f"An RGB graph needs exactly three channels, got {len(channels)}")
    colors: tuple[RGBAColor, RGBAColor, RGBAColor] = (
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
    )
    return composite_graph(
        [
            ChannelSpec(
                intensity_axis=intensity_axis,
                intensity_index=index,
                color=color,
                colormap=ColorMap.INTENSITY,
                clim_min=clim_min,
                clim_max=clim_max,
                mode=mode,
            )
            for index, color in zip(channels, colors)
        ]
    )


__all__ = [
    "FALLBACK_COLORS",
    "OPAQUE",
    "RGB_PRIMARIES",
    "ChannelSpec",
    "RGBAColor",
    "channel_graph",
    "color_for_wavelength",
    "composite_graph",
    "fallback_color",
    "hue_ramp",
    "rgb_graph",
    "rgba",
]
