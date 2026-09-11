"""Checking a table's declaration against the frame it is made of, before anything moves.

``create_table_dataset`` takes the generated ``ColumnInput`` directly, and a column is
declared ONCE: a non-null ``axisType`` makes it an axis of the table's own space, and
``identifiedBy`` is the one spelling of every "values here identify things there" claim --
for axes (a mask keying an INDEX axis) and data columns (a foreign key into another table)
alike. There is no second ``axes`` list, so nothing exists for a column to disagree with
itself across; and the table's **axis order is the axis-typed columns in the file's column
order** -- a table has no byte order, its consumers address axes by name, and an edge
wanting a different order states its own axis lists.

The file supplies every column's name and DuckDB type, so a caller declares only what the
file cannot say -- which columns are axes and of what kind, what a column measures, what it
means::

    create_table_dataset(
        name="cells",
        data={"object_id": ids, "volume_um3": volumes},
        columns=[
            ColumnInput(name="object_id", axis_type=AxisType.INDEX, long_name="instance id",
                        identified_by=[DatasetIdentifiesInput(kind="DATASET", dataset=mask.id)]),
            ColumnInput(name="volume_um3", unit="micrometer**3"),
        ],
    )

``columns`` is **partial**: a subset, in any order, and ``dtype`` omitted is the ordinary case.
:func:`resolve_columns` merges it onto the file's own list, in the file's order, which is what
the server requires -- and the checks below run on the way, here, where the frame is, rather
than on the far side of an upload. Three things they catch that a hand-written declaration got
right only by accident, each measured:

* **A type the server will not be able to describe.** A float16 column reads back as ``FLOAT``
  on DuckDB 1.5 and as ``BLOB`` on the 1.2 the server runs; an all-null column has no type for
  Parquet to record at all. See :func:`mikro_next.vocabulary.duckdb_type`, which maps only what
  was measured to agree on both and refuses the rest.
* **An index the upload would mangle.** A ``RangeIndex`` is stored as start/stop/step metadata
  rather than as data -- and on pandas 3 *any evenly spaced integer index* is inferred to be
  one, which is what object ids running 1..N are, so ``frame.set_index("object_id")`` writes a
  Parquet with no ``object_id`` column at all. An unnamed non-range index has the opposite
  problem: it gains the file a ``__index_level_0__`` column that exists in no frame.
* **A space in the wrong order.** x is the *last* spatial axis and y the one before it, by
  position and never by name -- and the axis order is the file's column order, so a frame
  whose centroid columns run ``x, y, z`` renders transposed rather than failing. The server
  cannot catch this -- a table's axis names are free-form, so nothing there knows which order
  was meant. A name that follows the convention does, and the frame is in hand here to fix.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from difflib import get_close_matches
from pathlib import Path
from typing import TYPE_CHECKING, Final

from mikro_next.vocabulary import duckdb_type

if TYPE_CHECKING:
    import pyarrow as pa

    from mikro_next.api.schema import ColumnInput


#: The axis types a table's coordinate column may have. A table's axes are its
#: own space: positions, instants, or an enumeration. The array-only types
#: (CHANNEL, SPECTRUM, ...) are not positions a row can hold.
TABLE_AXIS_TYPES: Final[frozenset[str]] = frozenset({"SPACE", "TIME", "INDEX"})

#: The width past which the object is a matrix rather than a table. Mirrors the server's
#: ``_MAX_TABLE_COLUMNS``; refused here so a caller meets it before the bytes move. See
#: :func:`_too_wide` for the argument, which is about shape rather than size.
MAX_COLUMNS: Final[int] = 3000

#: The roles a column may carry a unit in, mirroring the server's `_UNIT_BEARING_ROLES`
#: (`core/mutations/table_dataset.py`). The server refuses the rest: an id, a label or a
#: colour is not measured, so a unit on one names a metric that does not exist.
#:
#: COORDINATE is in the set and unreachable through this check -- a coordinate column is
#: declared with `axisType` rather than a role, and a SPACE/TIME axis' unit is checked on its
#: own terms. It is kept here anyway so the constant states the server's rule rather than the
#: subset this path happens to see.
UNIT_BEARING_ROLES: Final[frozenset[str]] = frozenset({"COORDINATE", "ATTRIBUTE"})

#: The column ``pyarrow`` invents for a frame whose index is neither a
#: ``RangeIndex`` nor named. It is in the file and in no frame.
_ANONYMOUS_INDEX = "__index_level_0__"


class TableDeclarationError(ValueError):
    """Raised when a declaration cannot describe the frame it is made for."""


def arrow_schema_of(frame: object) -> pa.Schema:
    """The Arrow schema of anything ``ParquetLike`` accepts.

    This is the same conversion :func:`mikro_next.io.upload._parquet_payload`
    performs on the way to the object store, which is the point: the schema
    returned here is the schema of the file that will exist, not of the object
    in hand. For a ``DataFrame`` the two differ in ways that matter -- index
    placement, categoricals, nullable extension dtypes.

    A ``Table``, ``Schema`` or ``RecordBatchReader`` is read for its schema
    without being converted, so passing one of those costs nothing; a path is
    read from its Parquet footer, without the rows.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    if isinstance(frame, pa.Schema):
        return frame
    if isinstance(frame, (pa.Table, pa.RecordBatchReader)):
        return frame.schema
    if isinstance(frame, (str, Path)):
        return pq.read_schema(Path(frame))

    from mikro_next.scalars import ParquetLike

    if isinstance(frame, ParquetLike):
        return arrow_schema_of(frame.value)

    # A dict of columns, which `ParquetLike` coerces the same way. Kept here for a direct
    # caller; the trait never reaches it, because the coercion happens at validation.
    if isinstance(frame, Mapping):
        return pa.table(dict(frame)).schema

    # A DataFrame -- and the only branch that converts. `from_pandas` is what
    # the uploader calls, so its answer is the file's answer.
    return pa.Table.from_pandas(frame).schema


def file_columns_of(frame: object) -> list[tuple[str, str]]:
    """``(name, duckdb type)`` per column of the file, in the file's order."""
    fields = list(arrow_schema_of(frame))
    names = [field.name for field in fields]

    if _ANONYMOUS_INDEX in names:
        raise TableDeclarationError(
            f"This frame's index is neither a RangeIndex nor named, so the upload would "
            f"write it as a column called {_ANONYMOUS_INDEX!r} -- a column that exists in "
            "the file and in no frame, and that no declaration can sensibly describe. "
            "Name the index (`frame.index.name = ...`) to declare it, or drop it "
            "(`frame.reset_index(drop=True)`)."
        )

    _refuse_a_dropped_index(frame, names)

    resolved = []
    for field in fields:
        try:
            resolved.append((field.name, duckdb_type(field.type)))
        except ValueError as error:
            raise TableDeclarationError(f"Column {field.name!r}: {error}") from error
    return resolved


def _refuse_a_dropped_index(frame: object, names: Sequence[str]) -> None:
    """Refuse a frame whose index will not survive the upload.

    ``Table.from_pandas`` writes a ``RangeIndex`` as *metadata* rather than as a
    column -- start, stop and step, which is all a range is -- so a column moved
    into the index can vanish from the Parquet entirely. On pandas 3 that is not
    the corner it sounds like: any evenly spaced integer index is inferred to be
    a ``RangeIndex``, and object ids run 1..N::

        frame.set_index("object_id")   # index is RangeIndex(1, N + 1)
                                       # -> `object_id` is not in the file

    Measured: dropped for [1, 2, 3], [5, 10, 15] and [10, 20, 30, 40] on pandas
    3.0.3; kept, and appended after the data columns, on pandas 2.3.3. So the
    same script writes two different files depending on the pandas installed,
    and neither the frame nor the declaration shows it.
    """
    index = getattr(frame, "index", None)
    if index is None or not hasattr(frame, "reset_index"):
        return

    missing = [name for name in index.names if name is not None and name not in names]
    if missing:
        raise TableDeclarationError(
            f"{', '.join(repr(name) for name in missing)} "
            f"{'is' if len(missing) == 1 else 'are'} in this frame's index, and the index "
            "is a RangeIndex -- which pandas stores as start/stop/step metadata rather than "
            f"as data, so {'it' if len(missing) == 1 else 'they'} would not be in the "
            "uploaded file at all. Move it back into the frame: "
            "`frame.reset_index()`."
        )


def resolve_columns(
    file_columns: Sequence[tuple[str, str]],
    declared: Sequence[ColumnInput],
) -> tuple[ColumnInput, ...]:
    """Every column of the file, in the file's order, with the caller's overrides merged on.

    The server checks the declaration against the Parquet's own account of itself -- same
    names, same order, same types -- so the list it wants is complete and ordered. That is a
    fact about the file, which is why it is derived here rather than asked for. What the caller
    passes is only what the file cannot say, for the columns it is true of, in any order.

    ``dtype`` is filled from the frame's **Arrow** schema, never ``frame.dtypes``, because Arrow
    is what the upload writes. The two disagree where it matters: a ``category`` is a
    ``VARCHAR``, a nullable ``Int64`` is a ``BIGINT``. A caller who states one anyway is held to
    it -- an assertion about the data is worth checking, and this is the cheap side to check it.
    """
    from mikro_next.api.schema import ColumnInput

    present = {name for name, _ in file_columns}
    by_name = {column.name: column for column in declared}
    _check_declarations(declared, by_name, present)

    if len(file_columns) > MAX_COLUMNS:
        raise TableDeclarationError(_too_wide(len(file_columns)))

    _check_role_counts(declared)

    resolved: list[ColumnInput] = []
    for name, dtype in file_columns:
        given = by_name.get(name)
        if given is None:
            resolved.append(ColumnInput(name=name, dtype=dtype))
            continue
        if given.dtype is not None and given.dtype != dtype:
            raise TableDeclarationError(
                f"Column {name!r} is declared {given.dtype} and this frame writes {dtype}. "
                "`dtype` is a **DuckDB** type name -- what the Parquet is read back as -- not a "
                "pandas one: a float64 is a DOUBLE and a float32 is a FLOAT. Leave it out and "
                "the file's own answer is used."
            )
        resolved.append(given.model_copy(update={"dtype": dtype}))

    # On the resolved list rather than the caller's: `declared` is partial and in any order,
    # and the axis order is the *file's* -- which is exactly what is being checked.
    _check_axis_order(resolved)
    return tuple(resolved)


def _too_wide(count: int) -> str:
    """Why a frame this wide is not a table, and where it belongs instead.

    The same argument the server makes, made here so the caller meets it before the upload
    rather than after it. Long on purpose: the refusal is about shape, not size, and a caller
    who hits it has a real object that needs somewhere to go.
    """
    return (
        f"This file has {count:,} columns, past the {MAX_COLUMNS:,} at which it stops being a table.\n"
        "\n"
        "The limit is about shape, not size. A table's columns are distinct measurements -- an area, a marker "
        "level, a label -- so each one earns a column row, an entry in every picker, and a term in every hover "
        f"plan's SELECT. {count:,} of those means a {count:,}-column SELECT every time a viewer hovers a pixel.\n"
        "\n"
        "A file this wide is almost always a *matrix*: expression over genes, intensity over metabolites, a "
        "feature matrix over channels. Its columns are not different measurements -- they are the same "
        "measurement at different positions along an axis, and gene 4,711 differs from gene 4,712 only in where "
        "it sits.\n"
        "\n"
        "Use `create_sparse_dataset` instead. Upload the matrix as a sparse store, then declare its two axes -- "
        "the objects and the features -- and say what identifies each: a label mask whose pixel values are the "
        "object ids, and a table whose rows are the features. The features become **one axis with one picker "
        "entry**, not one entry per feature, and a colouring names a position along it. The per-feature metadata "
        "that would have been column names goes in an ordinary narrow table, keyed to that axis.\n"
        "\n"
        f"If the columns really are distinct measurements and there really are more than {MAX_COLUMNS:,} of "
        "them, split the file."
    )


def _enum_value(value: object) -> str:
    """An enum-valued field's value, however it is spelled.

    The generated models set ``use_enum_values=True``, so a model constructed with an enum
    member holds the plain string -- measured, not assumed. The normalizer stays because a
    field can also be read off a model built some other way, and the cost of being wrong here
    is a check that silently passes.
    """
    return getattr(value, "value", value) or ""


def _check_declarations(
    columns: Sequence[ColumnInput],
    by_name: dict,
    present: set,
) -> None:
    """Refuse a declaration that cannot describe this file, before anything moves.

    Every check here is one the server would also make -- but it would make it
    on the far side of an upload, which for a table worth uploading is the far
    side of several hundred megabytes.
    """
    if len(by_name) != len(columns):
        raise TableDeclarationError(_duplicates("columns", [column.name for column in columns]))

    for declared in by_name:
        if declared not in present:
            close = get_close_matches(declared, present, n=1)
            suggestion = f" Did you mean {close[0]!r}?" if close else ""
            raise TableDeclarationError(
                f"No column named {declared!r} in this frame.{suggestion} The file's columns "
                f"are: {', '.join(sorted(present))}"
            )

    for column in columns:
        axis_type = _enum_value(column.axis_type) if column.axis_type is not None else None
        role = _enum_value(column.role)

        if axis_type is not None:
            if role:
                raise TableDeclarationError(
                    f"Column {column.name!r} declares both `axis_type` and `role`. An axis "
                    "column is a COORDINATE by that fact; a role beside it would be the same "
                    "question answered twice. Drop `role`."
                )
            if axis_type not in TABLE_AXIS_TYPES:
                raise TableDeclarationError(
                    f"Column {column.name!r} is a {axis_type} axis, but a table's axes are "
                    f"{', '.join(sorted(TABLE_AXIS_TYPES))} -- a row holds a position, an instant "
                    "or an enumeration, and nothing else is one of those."
                )
            if axis_type == "INDEX" and column.unit is not None:
                raise TableDeclarationError(
                    f"Column {column.name!r} is an INDEX axis, which enumerates -- the distance "
                    "between object 3 and object 4 is not a small number, it is not a number -- "
                    "so it has no metric to state a unit in. Drop `unit`."
                )
        elif role == "COORDINATE":
            raise TableDeclarationError(
                f"Column {column.name!r} is declared COORDINATE, but a coordinate column is an "
                "axis: say so with `axis_type` (SPACE, TIME or INDEX), which is what makes it "
                "one. The server refuses this too."
            )
        # An empty role is an *undeclared* one, which the server fills in as ATTRIBUTE -- so a
        # unit on it is fine, and the check is only for a role that was actually stated.
        elif column.unit is not None and role != "" and role not in UNIT_BEARING_ROLES:
            raise TableDeclarationError(
                f"Column {column.name!r} is a {role} column and carries a unit. A unit says "
                "what the values are measured in, and an id, a label or a colour is not "
                "measured. Drop the unit, or the role."
            )

        # The server refuses these too. Raised here so a caller meets them before the bytes
        # move, which for a table worth uploading is several hundred megabytes earlier.
        # TABLE and NETWORK_COLLECTION_NODES are the two no-edge kinds: both state what a
        # column's values *are* (rows of a table, nodes of a collection) rather than
        # authoring a FIELD edge. TABLE is legal on an INDEX axis (the product-space case)
        # and on a plain data column (a foreign key -- what `references` used to spell);
        # NODES only on an INDEX axis, its scoping being an axis convention. Both count
        # toward one-answer-per-column.
        no_edge = [
            entry
            for entry in (column.identified_by or ())
            if _enum_value(getattr(entry, "kind", None)) in ("TABLE", "NETWORK_COLLECTION_NODES")
        ]
        if axis_type in ("SPACE", "TIME") and no_edge:
            raise TableDeclarationError(
                f"Column {column.name!r} is a {axis_type} axis, so its values are positions "
                "rather than ids: it places the row in this table's own space and cannot "
                "also identify rows elsewhere. Declare the reference on a data column, or -- "
                "if its values really are ids -- declare the column an INDEX axis."
            )
        if axis_type is None and any(
            _enum_value(getattr(entry, "kind", None)) == "NETWORK_COLLECTION_NODES" for entry in no_edge
        ):
            raise TableDeclarationError(
                f"Column {column.name!r} is identified by a network collection's nodes but is "
                "not an axis. A node id is scoped by the sibling object axis, which is an axis "
                "convention -- declare the column `axis_type=AxisType.INDEX` so the "
                "(object, node) pair is the row's key."
            )
        if len(no_edge) > 1:
            raise TableDeclarationError(
                f"Column {column.name!r} is identified by more than one enumeration. A column "
                "enumerates one thing: two answers would be two different claims about what a "
                "value in it is. Fan-in is only meaningful for the kinds that author an "
                "edge -- two masks may key one axis, because each edge stands on its own."
            )


def _check_axis_order(resolved: Sequence[ColumnInput]) -> None:
    """Refuse a space in an order the render will silently transpose.

    A table's axis order is the axis-typed columns in the file's column order -- there is no
    list to reorder it with, deliberately, since nothing strides a table by position. What is
    still worth checking is the one thing position decides and nothing guards:
    ``resolve_render_axes`` takes the last spatial axis as x, the one before it as y, the one
    before that as z, entirely by position and never by name. A frame whose centroid columns
    run ``x, y, z`` yields ``x=z, z=x``, fully transposed, with no error on either side.

    So this refuses only the case that is almost certainly a mistake: spatial axes named
    ``x``/``y``/``z`` in ascending column order rather than the ``(z, y, x)`` array
    convention. It is a convention and this is the only place that says so out loud -- the
    server cannot, since a table's axis names are free-form. The fix is the frame's column
    order, which is in hand here: ``frame[["z", "y", "x", ...]]``.
    """
    spatial = [
        column.name.lower()
        for column in resolved
        if column.axis_type is not None and _enum_value(column.axis_type) == "SPACE"
    ]
    conventional = [name for name in ("z", "y", "x") if name in spatial]
    if len(conventional) >= 2 and spatial == list(reversed(conventional)):
        raise TableDeclarationError(
            f"The spatial axes run {', '.join(spatial)} in this frame's column order, which is "
            "the reverse of the array convention -- and the axis order IS the column order. "
            "x is the *last* spatial axis, y the one before it and z the one before that, by "
            "position and never by name, so this table renders transposed rather than failing. "
            f"Reorder the frame's columns to {', '.join(conventional)} first. "
            "(Nothing on the server can catch this: a table's axis names are free-form, so "
            "only a name that follows the convention says which order was meant.)"
        )


def _check_role_counts(columns: Sequence[ColumnInput]) -> None:
    """Refuse the roles a table may hold only one of.

    Cheap here and expensive later: the server refuses these too, after the Parquet has been
    uploaded and the store row written.
    """
    for role in ("ID", "TRACK_ID"):
        named = [column.name for column in columns if _enum_value(column.role) == role]
        if len(named) > 1:
            raise TableDeclarationError(
                f"A table has at most one {role} column, but {len(named)} were declared: "
                f"{', '.join(named)}."
            )


def _duplicates(where: str, names: Sequence[str]) -> str:
    """The message for a column declared twice in the same list."""
    repeated = sorted({name for name in names if names.count(name) > 1})
    return (
        f"{', '.join(repeated)} appear{'s' if len(repeated) == 1 else ''} more than once in "
        f"`{where}`. Each column is declared once."
    )


__all__ = [
    "MAX_COLUMNS",
    "TABLE_AXIS_TYPES",
    "UNIT_BEARING_ROLES",
    "TableDeclarationError",
    "arrow_schema_of",
    "file_columns_of",
    "resolve_columns",
]
