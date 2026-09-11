"""Builders for a layer's colour and filter pickers.

`render.py` is the builder for an image layer's render graph and says so in its own
`ChannelSpec` docstring: *"There is deliberately no `categorical` here. A transfer function
maps a continuous intensity to a colour; mapping discrete object ids to distinct colours is
a different thing entirely, and it lives on a label layer."* This module is that other half.

A **colour picker** is a list of readings a layer publishes and a person at the screen
switches between, and `activeColorBy` is an index into it. Each entry names a table and one
of its columns, reached through the FIELD edge that keys the mask's pixels (or a mesh
collection's ids) into record-land -- and, past one hop, a `joinPath` of `references`.

Three things the server refuses that nothing in the generated models checks, all mirrored
here so a bad picker fails before the round trip rather than after it:

1. **Which sort of colormap applies follows from the column's declared *role*, not from a
   choice here:** MEASURE columns (COORDINATE, ATTRIBUTE) take a continuous one and a
   `min`/`max` window, CATEGORICAL ones (ID, TRACK_ID, LABEL, COLOR) take a qualitative
   palette. Naming the wrong sort is refused at the mutation boundary; so is a `min`/`max`
   on a categorical column, which has no range to window.
2. **A colouring names one colormap, and the column decides which sort.** MEASURE columns take
   a continuous one and CATEGORICAL ones a qualitative palette; naming the wrong sort is
   refused. There used to be a second field here -- `classColors`, an explicit value-to-RGBA
   map -- on the grounds that a colormap imposes an order. True of a ramp and not of a
   palette, so the map is gone and the palette is a colormap like any other.
3. **Two entries that render identically are refused**, because "a picker whose two rows
   render identically is a bug wearing two labels". A distinct `label` does not make a
   duplicate legal -- the caption is not what distinguishes two entries.

Set `min`/`max` yourself whenever you can. The server does not serve column statistics (a
picker wanting a range "reads them from the parquet it already has an accessGrant for"), so
an omitted window leaves the viewer to stretch the map over whatever it happens to read --
and a gene maxing at 3 sharing an inherited range with one maxing at 400 renders black.

Not exported from the package root, for the same reason `render` is not: this imports the
generated schema at module level. Reach for ``from mikro_next.picker import ...``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from mikro_next.api.schema import (
    UNSET,
    AxisPositionInput,
    ColorMap,
    ColorSourceKind,
    ColumnColorByInput,
    GraphColorByInput,
    GraphTarget,
    LabelColorByInput,
    LabelFilterByInput,
    LabelRenderInput,
    MeshColorByInput,
    MeshFilterByInput,
    NetworkColorByInput,
    NetworkFilterByInput,
    SparseColorByInput,
    UnsetType,
)

__all__ = [
    "QUALITATIVE_COLORMAPS",
    "categorical_color_by",
    "categorical_filter_by",
    "graph_color_by",
    "graph_filter_by",
    "join_path_of",
    "label_render",
    "measure_color_by",
    "measure_filter_by",
    "mesh_color_by",
    "mesh_filter_by",
    "network_color_by",
    "network_filter_by",
    "sparse_color_by",
]


def join_path_of(option) -> tuple[dict, ...]:
    """The `joinPath` of a `ColorByOption`, in the shape a `colorBys` entry takes.

    An option carries whole `TableDataset` and `TableDatasetColumn` objects; the input takes
    ``{table: ID, column: String}``. The server says to "pass it back verbatim", which is
    true of the *path*, not of its Python type -- this is the one line of mapping between
    the two, so no caller has to remember which side is which.
    """
    return tuple({"table": step.table.id, "column": step.column.name} for step in option.join_path)


#: The colormaps that colour by a value's rank rather than by its place on a ramp. A
#: categorical column takes one of these and a measure column one of the others; which
#: applies follows from the column's declared role and is enforced server-side.
QUALITATIVE_COLORMAPS = (ColorMap.HUES, ColorMap.DISTINCT, ColorMap.PASTEL, ColorMap.VIVID)


def _measure(cls, table, column, colormap, min, max, label, join_path):
    # `min > max`, not `not max > min`: the server refuses an *inverted* window only
    # (`ColorByInputModel._window_is_a_range`), and a degenerate one where both ends are the
    # same value is legal there. A client that fronts a rule must not be stricter than it.
    if min is not None and max is not None and min > max:
        raise ValueError(f"the colormap window on '{column}' is inverted: min={min} is above max={max}. `min` is the value mapped to the bottom of the colormap and `max` the value mapped to its top.")
    del cls  # the member type is the same for both layer kinds now
    return ColumnColorByInput(
        kind=ColorSourceKind.COLUMN,
        table=table,
        column=column,
        colormap=colormap,
        min=min,
        max=max,
        label=label,
        join_path=list(join_path),
    )


def measure_color_by(
    table,
    column: str,
    *,
    colormap: ColorMap = ColorMap.VIRIDIS,
    min: float | None = None,
    max: float | None = None,
    label: str | None = None,
    join_path: Iterable[Mapping[str, object]] = (),
) -> LabelColorByInput:
    """Colour a mask's objects by a measured column -- a count, an area, an intensity.

    For a COORDINATE or ATTRIBUTE column. Pass `min`/`max`: see the module docstring.
    """
    return _measure(LabelColorByInput, table, column, colormap, min, max, label, join_path)


def categorical_color_by(
    table,
    column: str,
    *,
    colormap: ColorMap = ColorMap.HUES,
    label: str | None = None,
    join_path: Iterable[Mapping[str, object]] = (),
) -> LabelColorByInput:
    """Colour a mask's objects by a column that names things rather than measuring them.

    For an ID, TRACK_ID, LABEL or COLOR column, where a *continuous* colormap would impose an
    order the values do not have. A qualitative one does not: it scatters a colour per distinct
    value, so the picture separates classes without ranking them.

    This used to take an explicit `class_colors` map of value to RGBA, which every caller built
    by evenly spacing hues -- which is what a qualitative colormap is. Naming one instead means
    the client sends a word rather than a table of colours, nothing caps how many classes are
    covered, and a colour a class genuinely owns can live in a `COLOR` column of the table,
    where it is a per-row fact rather than a copy on every picker entry.
    """
    if colormap not in QUALITATIVE_COLORMAPS:
        raise ValueError(
            f"'{colormap.value}' is a continuous colormap, and a categorical column has no order for a ramp to follow. "
            f"Name a qualitative one: {', '.join(member.value for member in QUALITATIVE_COLORMAPS)}."
        )
    return ColumnColorByInput(
        kind=ColorSourceKind.COLUMN,
        table=table,
        column=column,
        colormap=colormap,
        label=label,
        join_path=list(join_path),
    )


def sparse_color_by(
    dataset,
    at: Mapping[str, int],
    *,
    colormap: ColorMap = ColorMap.MAGMA,
    min: float | None = None,
    max: float | None = None,
    label: str | None = None,
) -> LabelColorByInput:
    """Colour a mask's objects by one slice of a sparse matrix.

    The other way a set of ids reaches a number. Where a column colouring names a table and a
    column, this names a matrix and a *position* -- and the slice at that position is a value
    per object, which is what a colouring is.

    ``at`` maps axis name to position, e.g. ``{"gene": 4711}``. The position is a row of the
    table that axis references, so finding it is a query against that table rather than
    anything the server enumerates: a matrix with 19 059 features offers one picker entry, not
    19 059.

    **Always measured**, so a qualitative colormap is refused here: a slice is a value per
    object and nothing stores categories sparsely -- the zeros would be a category too. Pass `min`/`max`
    for the same reason a column colouring wants them, which is that the server serves no
    statistics; `SparseReader.maxima()` computes the whole set in one pass at ingest.

    The server refuses a colouring along an axis no stored layout indexes, because reading one
    slice from the wrong layout is a scan of every byte rather than a contiguous range. If that
    refusal fires, upload the transposed matrix and register it on the same dataset.
    """
    if not at:
        raise ValueError("a sparse colouring reads one slice, so it needs a position: `at={'<axis>': <index>}`")
    _check_slice(dataset, at)
    # The window and the colormap are checked by `SparseColorByInputTrait`, on the input
    # itself, because `label_render` also accepts entries built without coming through here.
    return SparseColorByInput(
        kind=ColorSourceKind.SPARSE,
        dataset=dataset if isinstance(dataset, str) else getattr(dataset, "id", dataset),
        at=[AxisPositionInput(axis=axis, value=int(value)) for axis, value in at.items()],
        colormap=colormap,
        min=min,
        max=max,
        label=label,
    )


def _check_slice(dataset: object, at: Mapping[str, int]) -> None:
    """Check `at` against the dataset, when the caller handed over the dataset rather than an id.

    The three refusals `create_label_layer` makes about a sparse slice that do not need the
    coordinate graph -- the fourth, that the dataset is reachable from the layer's source by a
    FIELD edge, needs it and stays server-only, which is what keeps this a subset.

    Every field read is already selected by the `SparseDataset` fragment, and `MikroFetchable`
    defines no `__getattr__`, so this costs no round trip.

    **Guarded by field, not by type.** A `ColorByOption` names its dataset with an object
    carrying only `id` and `name`, and round-tripping one back is a thing `join_path_of`
    exists to support -- so anything that cannot answer these questions is passed through, and
    the server asks them instead.
    """
    identified = getattr(dataset, "axis_references", None)
    if identified is None:
        # A `ColorByOption` states the same set directly, under a different name.
        axes = getattr(dataset, "axes", None)
        identified = None if axes is None else [type("_R", (), {"axis": a})() for a in axes]
    if identified is None:
        return

    named, wanted = sorted(at), sorted(reference.axis for reference in identified)
    if named != wanted:
        name = getattr(dataset, "name", None) or getattr(dataset, "id", "the dataset")
        rest = [a for a in (getattr(dataset, "axis_names", None) or ()) if a not in wanted]
        raise ValueError(
            f"`at` names {named}, but {name!r} is selected along {wanted} -- the axes it "
            f"identifies itself. The other axis ({rest}) is the one the layer supplies ids for."
        )

    # Same condition the server guards its own bound check with: a store whose rank disagrees
    # with the declared axes has no extent to compare against.
    axis_names = list(getattr(dataset, "axis_names", None) or ())
    shape = list(getattr(dataset, "shape", None) or ())
    if len(axis_names) == len(shape):
        for axis, value in at.items():
            extent = shape[axis_names.index(axis)]
            if not 0 <= int(value) < int(extent):
                raise ValueError(
                    f"`at` names position {value} along {axis!r}, which runs 0..{int(extent) - 1}. "
                    "A position is a row of the table that axis references, not an id of its own."
                )

    # `any`, not `all`: requiring a layout per named axis would hide legal colourings, and the
    # picker's offer path applies the same rule -- the two must not disagree.
    indexable = getattr(dataset, "indexable_axes", None)
    if indexable is not None and not any(axis in indexable for axis in at):
        raise ValueError(
            f"No layout indexes any of {named}, so reading one slice is a scan of every byte "
            f"rather than a contiguous range -- 1 777 ms against 2.2 ms, measured. It is "
            f"indexed on: {list(indexable)}. Upload the matrix compressed along one of the "
            "axes `at` names and register it on the same dataset."
        )


def graph_color_by(
    attribute: str,
    *,
    target: GraphTarget = GraphTarget.NODE,
    colormap: ColorMap = ColorMap.VIRIDIS,
    min: float | None = None,
    max: float | None = None,
    label: str | None = None,
) -> NetworkColorByInput:
    """Colour a network's nodes -- or its segments -- by a value the collection itself carries.

    The third way a picker entry reaches a number, and the only per-**node** one: where a
    column colouring joins a table and a sparse one slices a matrix, this names an attribute
    the konnektion collection stores beside its geometry. Every current build carries
    ``strahler``, ``degree``, ``depth`` and ``component`` (computed once, on the full level-0
    graph, and only ever subset -- so the value is the same at every level a node survives
    to), plus whatever per-node columns the writer passed on ``Network.attributes``, plus
    ``radius`` when the encoding stores one. `networkColorByOptions` lists exactly this set,
    and the server refuses a name the collection's manifest never declared.

    ``target`` says which of the network's two row sets is painted. An edge has no durable
    identity of its own -- simplification re-links edges between levels -- so a segment takes
    its **start node's** value either way; `EDGE` merely leaves the node glyphs at the
    layer's base colour.

    **Always measured** (`component` included -- one rule, no per-semantics branch), so a
    qualitative palette is refused. Pass `min`/`max` for the reason the module docstring
    gives; the intrinsic metrics make this easy (`strahler` runs 1..max order, `depth` 0..the
    longest path).
    """
    return GraphColorByInput(
        kind=ColorSourceKind.GRAPH,
        attribute=attribute,
        target=target,
        colormap=colormap,
        min=min,
        max=max,
        label=label,
    )


def graph_filter_by(
    attribute: str,
    *,
    target: GraphTarget = GraphTarget.NODE,
    min: float | None = None,
    max: float | None = None,
    exclude: bool = False,
    label: str | None = None,
) -> NetworkFilterByInput:
    """Hide the nodes -- or segments -- whose graph attribute falls outside a bound.

    The one rule that hides *parts* of an object: a COLUMN or SPARSE rule keeps or drops
    whole objects, where ``graph_filter_by("strahler", min=3)`` is "trunk only" on an arbor
    and ``graph_filter_by("depth", max=100)`` is a soma-centred ball. Always bounds -- a
    graph attribute is measured, so a `values` set has nothing to match.

    A hidden node takes its glyphs and its outgoing segments with it; a `target=EDGE` rule
    hides segments only, each tested by its start node's value.
    """
    if min is None and max is None:
        raise ValueError(f"a filter on the graph attribute '{attribute}' states no bound, so it would keep everything. Give a `min`, a `max`, or both.")
    return NetworkFilterByInput(kind=ColorSourceKind.GRAPH, attribute=attribute, target=target, min=min, max=max, exclude=exclude, label=label)


def network_color_by(*args, **kwargs) -> NetworkColorByInput:
    """The one-call form over a network collection, dispatching on what was named.

    ``network_color_by("strahler")`` is a graph colouring; ``network_color_by(table,
    "total_length")`` is a column one, exactly as :func:`mesh_color_by` builds it -- the
    member classes are shared across all three flat unions, so an entry built by any of
    these goes into `createNetworkLayer` unchanged.

    The same column form covers a per-node or per-edge table (one identified by the
    collection's *node* ids, not just its object ids): never send ``target`` for it --
    the server derives NODE or EDGE from the table's shape and stamps it on the stored
    entry, and refuses a caller-sent one.
    """
    if "attribute" in kwargs or (len(args) == 1 and not kwargs.get("table") and isinstance(args[0], str) and "column" not in kwargs):
        return graph_color_by(*args, **kwargs)
    return mesh_color_by(*args, **kwargs)


def network_filter_by(*args, **kwargs) -> NetworkFilterByInput:
    """:func:`graph_filter_by` / :func:`mesh_filter_by` over a network collection.

    As with :func:`network_color_by`, a rule over a per-node or per-edge table is the
    plain column form: the server stamps ``target`` from the table's shape.
    """
    if "attribute" in kwargs or (len(args) == 1 and isinstance(args[0], str) and "column" not in kwargs and "table" not in kwargs):
        return graph_filter_by(*args, **kwargs)
    entry = categorical_filter_by(*args, **kwargs) if "values" in kwargs or (len(args) > 2 and not isinstance(args[2], (int, float))) else measure_filter_by(*args, **kwargs)
    return NetworkFilterByInput(**entry.model_dump(by_alias=True, exclude_none=True))


def measure_filter_by(
    table,
    column: str,
    *,
    min: float | None = None,
    max: float | None = None,
    exclude: bool = False,
    label: str | None = None,
    join_path: Iterable[Mapping[str, object]] = (),
) -> LabelFilterByInput:
    """Draw only the objects whose measured column falls inside a bound.

    The sibling of a colouring over the same FIELD edge -- same table, same column check --
    deciding whether an object is drawn rather than what colour it takes.
    """
    if min is None and max is None:
        raise ValueError(f"a filter on the measure column '{column}' states no bound, so it would keep everything. Give a `min`, a `max`, or both.")
    return LabelFilterByInput(table=table, column=column, min=min, max=max, exclude=exclude, label=label, join_path=list(join_path))


def categorical_filter_by(
    table,
    column: str,
    values: Sequence[str],
    *,
    exclude: bool = False,
    label: str | None = None,
    join_path: Iterable[Mapping[str, object]] = (),
) -> LabelFilterByInput:
    """Draw only the objects whose categorical column is (or, with `exclude`, is not) in `values`."""
    if not values:
        raise ValueError(f"a filter on the categorical column '{column}' names no values, so it would draw {'everything' if exclude else 'nothing'}. Name the classes it keeps.")
    return LabelFilterByInput(table=table, column=column, values=[str(value) for value in values], exclude=exclude, label=label, join_path=list(join_path))


def mesh_color_by(*args, **kwargs) -> MeshColorByInput:
    """:func:`measure_color_by` / :func:`categorical_color_by` over a mesh collection.

    One relation, two names: a collection's ids reach a table exactly as a mask's pixel
    values do, so the shape is identical and only the GraphQL type differs.
    """
    # No conversion any more: `LabelColorByInput` and `MeshColorByInput` are the SAME two
    # member types behind two aliases, so an entry built once goes into either mutation. The
    # `model_dump` round trip this used to do -- and the argument-shape dispatch that went with
    # it -- were both artefacts of two field-for-field identical classes.
    return categorical_color_by(*args, **kwargs) if kwargs.get("colormap") in QUALITATIVE_COLORMAPS else measure_color_by(*args, **kwargs)


def mesh_filter_by(*args, **kwargs) -> MeshFilterByInput:
    """:func:`measure_filter_by` / :func:`categorical_filter_by` over a mesh collection."""
    entry = categorical_filter_by(*args, **kwargs) if "values" in kwargs or (len(args) > 2 and not isinstance(args[2], (int, float))) else measure_filter_by(*args, **kwargs)
    return MeshFilterByInput(**entry.model_dump(by_alias=True, exclude_none=True))


def _fingerprint(entry) -> tuple:
    """What makes two picker entries the same rendering. Everything but the caption.

    `at` is sorted by axis before it is compared, because the server sorts it too before
    keying its own duplicate check. Without that, ``{"gene": 1, "adduct": 0}`` and
    ``{"adduct": 0, "gene": 1}`` are one entry to the server and two here -- so the pair would
    pass this check and then be refused on the far side, which is the wrong way round.

    Conditionally, because this is generic over both variants of an entry and a COLUMN
    colouring has no `at` at all.
    """
    dumped = entry.model_dump(by_alias=True)
    dumped.pop("label", None)
    # A tuple, not a list -- the field is `tuple[AxisPositionInput, ...]` and `model_dump`
    # keeps the container type. Normalised to a list, which is fine because both sides of the
    # comparison go through here.
    at = dumped.get("at")
    if isinstance(at, (list, tuple)):
        dumped["at"] = sorted(at, key=lambda position: str(position.get("axis")))
    return repr(sorted(dumped.items(), key=lambda item: item[0]))


def label_render(
    color_bys: Sequence[LabelColorByInput] | UnsetType = UNSET,
    *,
    active: int | None | UnsetType = UNSET,
    filter_bys: Sequence[LabelFilterByInput] | UnsetType = UNSET,
    active_filters: Sequence[int] | UnsetType = UNSET,
    background: int | None = None,
    contour: bool | None = None,
    contour_width: float | None = None,
    opacity: float | None = None,
    seed: int | None = None,
    intensity_axis: str | None = None,
    intensity_index: int | None = None,
) -> LabelRenderInput:
    """A label layer's whole render state: its pickers, and how its ids are drawn.

    `active` is an index into `color_bys`; None means every id is hashed to a colour, which
    is what a segmentation with nothing measured about it wants. Only one entry is drawn at
    a time, so two colourings side by side are two layers over one lens -- cheap, since a
    lens is one round trip and the mask uploads once.

    `background` is the id drawn as transparent. It defaults server-side to 0, which is what
    a segmentation mask means; state it explicitly when the source uses something else.
    """
    published = list(color_bys) if color_bys is not UNSET else None
    filters = list(filter_bys) if filter_bys is not UNSET else None

    if active is not UNSET and active is not None:
        if published is None:
            raise ValueError(f"activeColorBy={active} names an entry of a picker this call does not publish. Pass `color_bys=` alongside it, or leave `active` unset to keep the layer's current choice.")
        if not 0 <= active < len(published):
            raise ValueError(f"activeColorBy={active} is not an index into the {len(published)} colouring(s) published here.")
    if active_filters is not UNSET:
        for index in active_filters:
            if filters is None or not 0 <= index < len(filters):
                raise ValueError(f"activeFilterBys names index {index}, which is not one of the {len(filters or ())} filter(s) published here.")

    seen: dict[str, int] = {}
    for index, entry in enumerate(published or ()):
        mark = _fingerprint(entry)
        if mark in seen:
            raise ValueError(f"colorBys[{index}] renders identically to colorBys[{seen[mark]}] -- same source, colormap and window. The caption is not what distinguishes two entries, so the server refuses this pair; drop one.")
        seen[mark] = index

    # `[]` and "not named" are two different instructions and the server reads them as such:
    # an omitted picker is left alone, an empty one is *cleared*. Coercing `[]` to None -- as
    # this did -- made clearing a picker unreachable through the only helper the client has.
    fields: dict[str, object] = {"background": background}
    if published is not None:
        fields["colorBys"] = published
    if filters is not None:
        fields["filterBys"] = filters
    if active is not UNSET:
        fields["activeColorBy"] = active
    if active_filters is not UNSET:
        fields["activeFilterBys"] = list(active_filters)

    return LabelRenderInput(
        **fields,
        contour=contour,
        contour_width=contour_width,
        opacity=opacity,
        seed=seed,
        intensity_axis=intensity_axis,
        intensity_index=intensity_index,
    )
