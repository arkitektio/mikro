"""Charts: mikro's second composition, data laid out along one metric axis.

A chart adopts a one-axis world and places nothing: what lays a source along it is
the edge registered into that world. So every test here authors the edge first and
then reads back what the server derived from it -- `along_axis`, `series_axis`,
`coordinate_column` -- none of which the client ever sends.
"""

import numpy as np
import pytest
import xarray as xr

from mikro import Unit, create_space
from mikro.api.schema import (
    AnnotationKind,
    AutoVisualizeMutation,
    AxisInput,
    AxisType,
    Chart,
    ChartLayerKind,
    ChartMark,
    ChartPolicyInput,
    ColumnInput,
    ColumnRole,
    CreateChartFromCoordinateSystemMutation,
    CreateChartMutation,
    CreateTraceChartLayerMutation,
    PhysicalAxisInput,
    Scene,
)
from mikro.mikro import Mikro

SAMPLES = 64
DT = 0.05

SECONDS = PhysicalAxisInput(name="t", type=AxisType.TIME, unit=Unit("second"))


def test_a_chart_is_created_over_an_axis_or_a_space_and_the_wire_says_which() -> None:
    """`axis` and `coordinate_system` are alternatives; the one not given is not sent."""
    minted = CreateChartMutation.Arguments(input={"name": "profile", "axis": SECONDS})
    sent = minted.model_dump(by_alias=True, exclude_unset=True)["input"]
    assert sent["axis"]["type"] == "TIME" and "coordinateSystem" not in sent

    adopted = CreateChartMutation.Arguments(input={"name": "profile", "coordinate_system": "7"})
    assert adopted.model_dump(by_alias=True, exclude_unset=True)["input"] == {"name": "profile", "coordinateSystem": "7"}


def test_a_trace_layer_sends_the_style_it_was_given_and_nothing_else() -> None:
    """An omitted setting stays off the wire, so the server's default is the default."""
    variables = CreateTraceChartLayerMutation.Arguments(input={"chart": "1", "lens": "2", "mark": ChartMark.STEPS})
    assert variables.model_dump(by_alias=True, exclude_unset=True)["input"] == {"chart": "1", "lens": "2", "mark": "STEPS"}


def test_bootstrapping_a_chart_from_a_space_sends_a_policy() -> None:
    """`space.chart()` always states a policy, the argument being required; an empty one leaves `nchildren` to the server."""
    variables = CreateChartFromCoordinateSystemMutation.Arguments(input={"coordinate_system": "3", "policy": ChartPolicyInput()})
    assert variables.model_dump(by_alias=True, exclude_unset=True)["input"] == {"coordinateSystem": "3", "policy": {}}


def test_auto_visualize_names_a_space_or_a_lens_and_sends_only_that_one() -> None:
    """`coordinate_system` and `lens` are alternatives; the one not given is not sent."""
    of_a_lens = AutoVisualizeMutation.Arguments(input={"lens": "2"})
    assert of_a_lens.model_dump(by_alias=True, exclude_unset=True)["input"] == {"lens": "2"}

    of_a_space = AutoVisualizeMutation.Arguments(input={"coordinate_system": "7"})
    assert of_a_space.model_dump(by_alias=True, exclude_unset=True)["input"] == {"coordinateSystem": "7"}


def _traces(mikro: Mikro, name: str, cells: int = 3):  # noqa: ANN202 - the generated dataset class
    """A `(cell, t)` array: one row per object, one column per sample."""
    data = np.random.default_rng(5).random((cells, SAMPLES)).astype("float32")
    return mikro.create_array_dataset(
        data=xr.DataArray(data, dims=("cell", "t")),
        scales=[],
        name=name,
        axes=[AxisInput(name="cell", type=AxisType.INDEX), "t"],
    )


@pytest.mark.integration
def test_an_array_is_charted_one_line_per_object(mikro: Mikro) -> None:
    """`t` runs along the chart because the edge says so; `cell` is what is left free."""
    chart = mikro.create_chart(name="traces over time", axis=SECONDS)
    assert isinstance(chart, Chart)
    assert (chart.axis.name, chart.axis.type, str(chart.axis.unit)) == ("t", AxisType.TIME, "second")
    assert chart.world.id == chart.world_coordinate_system.id and chart.layers == ()

    traces = _traces(mikro, "chart_traces")
    chart.world.register(traces, scale={"t": DT})

    layer = mikro.create_trace_chart_layer(chart=chart.id, lens=traces.lens().id, name="per cell", mark=ChartMark.LINE_MARKERS)
    assert layer.kind == ChartLayerKind.TRACE and layer.mark == ChartMark.LINE_MARKERS
    assert layer.along_axis == "t" and layer.series_axis == "cell"
    assert layer.placement == "PLACED"
    assert layer.as_affine is not None and layer.as_affine.input_axes == ("cell", "t")
    assert layer.as_affine.matrix == ((0.0, DT, 0.0),)
    assert layer.lens.dataset.id == traces.id

    restyled = mikro.update_chart_layer(id=layer.id, mark=ChartMark.STEPS, opacity=0.5)
    assert restyled.typename == "TraceChartLayer" and restyled.mark == ChartMark.STEPS and restyled.opacity == 0.5

    assert [read.id for read in mikro.get_chart(chart.id).layers] == [layer.id]
    assert mikro.get_chart_layer(layer.id).typename == "TraceChartLayer"

    mikro.delete_chart_layer(id=layer.id)
    assert mikro.get_chart(chart.id).layers == ()


@pytest.mark.integration
def test_a_source_nothing_lays_along_the_axis_is_refused(mikro: Mikro) -> None:
    """A layer mutation writes no edge, so an unregistered source has no place in the chart."""
    chart = mikro.create_chart(name="empty", axis=SECONDS)
    with pytest.raises(Exception, match="(?i)regist"):
        mikro.create_trace_chart_layer(chart=chart.id, lens=_traces(mikro, "chart_unregistered").lens().id)


@pytest.mark.integration
def test_a_table_and_marks_are_drawn_beside_a_trace(mikro: Mikro) -> None:
    """A SERIES reads a value column against the column the edge lays along the chart."""
    chart = mikro.create_chart(name="series and marks", axis=SECONDS)

    table = mikro.create_table_dataset(
        name="chart_mean",
        data={"t": np.arange(SAMPLES) * DT, "mean": np.linspace(0.0, 1.0, SAMPLES)},
        columns=[
            ColumnInput(name="t", axis_type=AxisType.TIME, unit=Unit("second")),
            ColumnInput(name="mean", role=ColumnRole.ATTRIBUTE),
        ],
    )
    chart.world.register(table)

    series = mikro.create_series_chart_layer(chart=chart.id, lens=table.lens().id)
    assert series.kind == ChartLayerKind.SERIES
    assert (series.value_column, series.coordinate_column, series.along_axis) == ("mean", "t", "t")

    # No collection named: the chart makes a drawing surface over (t, value).
    marks = mikro.create_annotation_chart_layer(chart=chart.id, name="peaks")
    assert marks.kind == ChartLayerKind.ANNOTATION and marks.along_axis == "t"
    mikro.create_annotation(kind=AnnotationKind.POINT, vectors=[[1.5, 0.75]], collection=marks.annotation_collection.id, name="peak")

    read = mikro.get_chart(chart.id)
    assert [layer.typename for layer in read.layers] == ["SeriesChartLayer", "AnnotationChartLayer"]

    world = read.world
    read.delete()
    assert mikro.get_coordinate_system(world.id).id == world.id, "deleting a chart never deletes its world"


@pytest.mark.integration
def test_a_space_charts_what_is_already_laid_along_it(mikro: Mikro) -> None:
    """`space.chart()` is `space.stage()`'s sibling: it composes, and authors no edge."""
    clock = create_space(mikro, "chart clock", [SECONDS])
    traces = _traces(mikro, "chart_bootstrapped")
    clock.register(traces, scale={"t": DT})

    chart = clock.chart(name="bootstrapped")
    assert chart.world.id == clock.id
    (layer,) = chart.layers
    assert layer.typename == "TraceChartLayer" and layer.name == "chart_bootstrapped" and layer.series_axis == "cell"


@pytest.mark.integration
def test_a_lens_is_shown_as_a_chart_or_a_scene_by_the_space_it_selects_in(mikro: Mikro) -> None:
    """One metric axis is a chart with the lens as its one layer; an image plane is a scene."""
    table = mikro.create_table_dataset(
        name="auto_series",
        data={"t": np.arange(SAMPLES) * DT, "mean": np.linspace(0.0, 1.0, SAMPLES)},
        columns=[
            ColumnInput(name="t", axis_type=AxisType.TIME, unit=Unit("second")),
            ColumnInput(name="mean", role=ColumnRole.ATTRIBUTE),
        ],
    )
    window = table.lens()
    charted = mikro.auto_visualize(lens=window.id)
    assert isinstance(charted, Chart)
    (layer,) = charted.layers
    assert layer.typename == "SeriesChartLayer" and layer.table_lens.id == window.id

    image = mikro.create_array_dataset(
        data=xr.DataArray(np.zeros((32, 32), dtype="uint8"), dims=("y", "x")),
        scales=[],
        name="auto_plane",
        axes=["y", "x"],
    )
    staged = mikro.auto_visualize(lens=image.lens().id, name="auto plane")
    assert isinstance(staged, Scene) and staged.name == "auto plane"
