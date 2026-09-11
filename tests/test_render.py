"""Unit tests for the layer render-graph builders.

A layer's recipe is a small tree -- a blend node over one or more channel nodes,
each with its own transfer function -- and :mod:`mikro_next.render` is what keeps
callers from hand-nesting it. What is worth pinning down offline is the split: a
flat spec mixes channel settings with transfer settings, and the builder has to
sort each field into the right node. Colour completion itself is covered by
``test_rgba_color_validation``.
"""

import pytest
from pydantic import ValidationError

from mikro_next.api.schema import Blending, ColorMap, ProjectionMode
from mikro_next.render import (
    FALLBACK_COLORS,
    ChannelSpec,
    channel_graph,
    color_for_wavelength,
    composite_graph,
    fallback_color,
    hue_ramp,
    rgb_graph,
    rgba,
)


def test_composite_graph_nests_channels_under_a_blend_node() -> None:
    graph = composite_graph(
        [
            ChannelSpec(intensity_index=0, colormap=ColorMap.CYAN),
            ChannelSpec(intensity_index=1),
        ]
    )

    assert graph.root.kind == "blend"
    assert graph.root.children is not None
    assert [child.kind for child in graph.root.children] == ["channel", "channel"]
    assert [child.intensity_index for child in graph.root.children] == [0, 1]


def test_composite_graph_sorts_a_flat_spec_into_the_right_nodes() -> None:
    """Channel fields stay on the node; transfer fields move onto its transfer
    function. A flat spec is the whole point, so the split has to be exact."""
    (node,) = composite_graph(
        [
            ChannelSpec(
                intensity_axis="c",
                intensity_index=2,
                mode=ProjectionMode.MIP,
                label="nuclei",
                visible=False,
                colormap=ColorMap.MAGMA,
                gamma=0.8,
                opacity=0.5,
                clim_min=10.0,
                clim_max=400.0,
                invert=True,
            )
        ]
    ).root.children

    # A spec carrying a `mode` gets a projection node above its channel: the server
    # models a projection as its own node kind, and `ChannelSourceNode` has no `mode`
    # field, so a mode set on the channel is accepted and silently dropped.
    assert node.kind == "projection"
    assert node.mode == ProjectionMode.MIP.value
    (node,) = node.children

    assert node.kind == "channel"
    assert node.mode is None
    assert (node.intensity_axis, node.intensity_index) == ("c", 2)
    assert (node.label, node.visible) == ("nuclei", False)
    assert node.transfer is not None
    assert node.transfer.colormap == ColorMap.MAGMA.value
    assert (node.transfer.gamma, node.transfer.opacity) == (0.8, 0.5)
    assert (node.transfer.clim_min, node.transfer.clim_max) == (10.0, 400.0)
    assert node.transfer.invert is True


def test_composite_graph_defaults_to_the_first_position_of_the_channel_axis() -> None:
    (node,) = composite_graph([ChannelSpec()]).root.children
    assert (node.intensity_axis, node.intensity_index) == ("c", 0)


def test_composite_graph_defaults_to_additive_blending() -> None:
    assert composite_graph([ChannelSpec()]).root.blending == Blending.ADDITIVE.value


def test_composite_graph_takes_an_explicit_blending() -> None:
    graph = composite_graph([ChannelSpec()], blending=Blending.NORMAL)
    assert graph.root.blending == Blending.NORMAL.value


def test_composite_graph_rejects_an_empty_spec_list() -> None:
    with pytest.raises(ValueError, match="at least one channel source"):
        composite_graph([])


def test_channel_spec_rejects_an_unknown_field() -> None:
    """A misspelled field would otherwise be silently dropped, and the layer
    would render without the setting the caller thought they had asked for.
    A type checker now catches this too; the model still refuses it at runtime."""
    with pytest.raises(ValidationError, match="colourmap"):
        ChannelSpec(colourmap=ColorMap.VIRIDIS)


def test_channel_spec_rejects_a_categorical_channel() -> None:
    """Mapping discrete object ids to distinct colours is a label layer's job,
    not a transfer function's -- there is no such field on a channel node."""
    with pytest.raises(ValidationError, match="categorical"):
        ChannelSpec(categorical=True)


def test_channel_graph_is_a_single_channel_composite() -> None:
    graph = channel_graph(colormap=ColorMap.INFERNO, gamma=0.8, intensity_index=1)

    assert graph.root.children is not None
    (node,) = graph.root.children
    assert node.intensity_index == 1
    assert node.transfer is not None
    assert node.transfer.colormap == ColorMap.INFERNO.value
    assert node.transfer.gamma == 0.8


def test_channel_graph_leaves_unset_transfer_settings_unset() -> None:
    """Passing nothing means "the viewer decides", not "explicitly none of it"."""
    (node,) = channel_graph().root.children
    assert node.transfer is not None
    assert node.transfer.colormap is None
    assert node.transfer.color is None
    assert node.transfer.gamma is None


def test_channel_graph_accepts_no_intensity_axis() -> None:
    """Data that is single-valued per rendered plane -- a bare z-stack, a time
    series -- has no axis to composite as separate colours."""
    (node,) = channel_graph(intensity_axis=None).root.children
    assert node.intensity_axis is None


def test_rgb_graph_composites_three_display_channels() -> None:
    graph = rgb_graph()

    assert graph.root.children is not None
    assert len(graph.root.children) == 3
    assert [node.intensity_index for node in graph.root.children] == [0, 1, 2]
    assert [node.transfer.color for node in graph.root.children] == [
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
    ]


def test_rgb_graph_defaults_to_the_full_eight_bit_range() -> None:
    """An RGB image is already display-referred, so stretching it would change
    the colours it was authored with."""
    for node in rgb_graph().root.children:
        assert (node.transfer.clim_min, node.transfer.clim_max) == (0.0, 255.0)


def test_rgb_graph_maps_explicit_channel_positions() -> None:
    graph = rgb_graph(channels=(3, 1, 0))
    assert [node.intensity_index for node in graph.root.children] == [3, 1, 0]


@pytest.mark.parametrize("channels", [(0, 1), (0, 1, 2, 3)])
def test_rgb_graph_rejects_anything_but_three_channels(channels: tuple) -> None:
    with pytest.raises(ValueError, match="exactly three channels"):
        rgb_graph(channels=channels)


def test_a_spec_without_a_mode_gets_no_projection_node() -> None:
    """The flat `blend -> channel` tree is what a 2D image should still produce."""
    (node,) = composite_graph([ChannelSpec(intensity_index=1)]).root.children
    assert node.kind == "channel"
    assert node.intensity_index == 1


def test_each_channel_of_a_composite_projects_independently() -> None:
    children = composite_graph(
        [ChannelSpec(intensity_index=i, mode=ProjectionMode.MIP) for i in range(3)]
    ).root.children
    assert [c.kind for c in children] == ["projection"] * 3
    assert [c.children[0].intensity_index for c in children] == [0, 1, 2]


def test_composite_graph_accepts_mappings() -> None:
    """Callers that build settings programmatically hold a dict; `ChannelSpec(**d)`
    at every call site is noise, and the attribute access used to blow up."""
    (node,) = composite_graph([{"intensity_index": 2, "mode": ProjectionMode.MIP}]).root.children
    assert node.kind == "projection"
    assert node.children[0].intensity_index == 2


def test_rgb_graph_can_project() -> None:
    children = rgb_graph(mode=ProjectionMode.MIP).root.children
    assert [c.kind for c in children] == ["projection"] * 3
    assert rgb_graph().root.children[0].kind == "channel"


# ---------------------------------------------------------------------------
# Colour
# ---------------------------------------------------------------------------


class TestColour:
    def test_a_triple_is_completed_to_rgba(self) -> None:
        """`TransferFunctionInput.color` is a bare `[Int!]`, so nothing in its type
        says how many components it wants — the server rejects three."""
        assert rgba((10, 20, 30)) == (10, 20, 30, 255)

    def test_a_quadruple_keeps_its_alpha_and_ignores_extras(self) -> None:
        assert rgba((10, 20, 30, 40), alpha=40) == (10, 20, 30, 40)

    def test_the_palette_is_used_while_it_lasts(self) -> None:
        assert fallback_color(1, 3) == rgba(FALLBACK_COLORS[1])

    def test_the_offset_rotates_the_palette_between_datasets(self) -> None:
        """Several datasets composited into one scene would otherwise each open on
        the same colour and blend to a wash."""
        assert fallback_color(0, 3, offset=2) == rgba(FALLBACK_COLORS[2])

    def test_more_channels_than_palette_entries_falls_to_a_hue_ramp(self) -> None:
        """Sixteen channels rotating through eight colours gives two the same one,
        which reads as a rendering bug rather than as running out of names."""
        total = len(FALLBACK_COLORS) + 1
        assert fallback_color(0, total) == rgba(hue_ramp(0, total))
        assert len({fallback_color(i, total) for i in range(total)}) == total

    def test_the_hue_ramp_survives_a_zero_total(self) -> None:
        assert hue_ramp(0, 0) == (255, 0, 0)

    def test_a_wavelength_takes_the_first_edge_it_falls_below(self) -> None:
        ramp = ((500.0, (0, 0, 255)), (600.0, (0, 255, 0)))
        assert color_for_wavelength(450.0, ramp, (255, 0, 0)) == (0, 0, 255, 255)
        assert color_for_wavelength(550.0, ramp, (255, 0, 0)) == (0, 255, 0, 255)

    def test_a_wavelength_past_the_last_edge_takes_the_far_colour(self) -> None:
        ramp = ((500.0, (0, 0, 255)),)
        assert color_for_wavelength(700.0, ramp, (255, 70, 70)) == (255, 70, 70, 255)
