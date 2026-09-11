"""The closed vocabularies the library speaks, as types rather than strings.

Every name here was a bare ``str`` somewhere else first — an axis type inferred
from a dimension name, a transformation kind dispatched on by equality, a
reduction looked up in a dict. Each of those had a runtime guard and a test
asserting the guard fired, which is the tell: the set of legal values was known
all along, just not written down anywhere a type checker could read it.

This module is a leaf on purpose. It imports nothing from ``mikro_next``, so
:mod:`~mikro_next.traits` (which :mod:`~mikro_next.api.schema` imports at module
level, and which therefore cannot import the schema back) can use it as freely
as anything downstream. That is also why the axis-type and transform-kind
vocabularies are spelled as ``Literal`` unions rather than reusing the generated
enums: the generated models all set ``use_enum_values=True``, so a field read
back off a model holds the plain value, not the enum member. A ``Literal``
describes what is actually there. The enums stay for *construction* sites, where
they are what the model wants.

Because the Literals mirror generated enums that ``turms`` regenerates, they can
drift. ``tests/test_vocabulary.py`` asserts the two stay in step.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Final, Literal, NamedTuple, Union

from kanne.scalars import Unit

# --- Axis types -------------------------------------------------------------

#: The semantic kind of an axis, mirroring ``api.schema.AxisType``.
AxisTypeName = Literal[
    "SPACE",
    "TIME",
    "CHANNEL",
    "COORDINATE",
    "DISPLACEMENT",
    "MICROTIME",
    "SPECTRUM",
    "INDEX",
]

#: The bare-name convention. Every name the convention actually knows is listed;
#: there is deliberately no catch-all. An unrecognised name used to become SPACE,
#: which is silently wrong twice over: the pyramid coarsens exactly the SPACE
#: axes, so a mosaic/tile index defaulted to SPACE gets halved level by level —
#: measured, turning 12 tiles into 6 — and `canonical` orders by type, so it also
#: lands in the wrong position.
_AXIS_TYPE_BY_NAME: Final[Mapping[str, AxisTypeName]] = {
    "t": "TIME",
    "time": "TIME",
    "c": "CHANNEL",
    "channel": "CHANNEL",
    "x": "SPACE",
    "y": "SPACE",
    "z": "SPACE",
}


class UnknownAxisName(ValueError):
    """Raised when the bare-name convention has no entry for an axis name."""


def default_axis_type(name: str) -> AxisTypeName:
    """The conventional axis type for a bare axis name.

    ``t``/``time`` -> TIME, ``c``/``channel`` -> CHANNEL, ``x``/``y``/``z`` ->
    SPACE. Anything else raises: the convention covers five names, and guessing
    at a sixth is how a tile index ends up spatial and gets coarsened away.

    Declare the axis instead of naming it — ``AxisInput(name=..., type=...)`` —
    or, for the pyramid helpers, pass the name in ``types=``.

    Raises:
        UnknownAxisName: if the convention has no entry for ``name``.
    """
    try:
        return _AXIS_TYPE_BY_NAME[name.lower()]
    except KeyError:
        raise UnknownAxisName(
            f"No conventional axis type for {name!r}. The bare-name convention "
            f"covers {sorted(_AXIS_TYPE_BY_NAME)} and nothing else — it used to "
            f"call anything unrecognised SPACE, which the pyramid then coarsens. "
            f"State the type explicitly with AxisInput(name={name!r}, type=...), "
            f"or pass types={{{name!r}: ...}} to the pyramid helpers."
        ) from None


# RFC-5 orders a system's axes by type: time first, then the categorical and
# custom types, then space. The array's dimension order IS this order, so a
# space whose axes disagree describes a different array than the one meant.
AXIS_TYPE_ORDER: Final[Mapping[AxisTypeName, int]] = {
    "TIME": 0,
    "CHANNEL": 1,
    "MICROTIME": 1,
    "SPECTRUM": 1,
    "COORDINATE": 1,
    "DISPLACEMENT": 1,
    "INDEX": 1,
    "SPACE": 2,
}

#: Axis types a pyramid may re-bin. Halving a CHANNEL or INDEX axis would invent
#: a position halfway between two acquisitions — or two object ids — which is
#: not a thing, and the server rejects a pyramid whose categorical axes change
#: extent.
COARSENABLE_AXIS_TYPES: Final[frozenset[AxisTypeName]] = frozenset(
    {"SPACE", "TIME", "MICROTIME"}
)


def axis_type_rank(axis_type: AxisTypeName) -> int:
    """The RFC-5 group an axis sorts into.

    Unknown types sort with the categorical ones, which is where every
    non-space, non-time type belongs.
    """
    return AXIS_TYPE_ORDER.get(axis_type, 1)


# --- Transformation kinds ---------------------------------------------------

#: The kinds a caller can *build* — one per member of the ``TransformInput``
#: tagged union.
TransformKind = Literal[
    "IDENTITY",
    "SCALE",
    "TRANSLATION",
    "AFFINE",
    "ROTATION",
    "MAP_AXIS",
    "BY_DIMENSION",
    "FIELD",
    "UNMAPPABLE",
]

#: The kinds an edge can *be* once the server has resolved it. SEQUENCE is
#: deliberately outside `TransformKind`: it is produced by composing edges, so
#: it can come back from a query but can never be passed to a mutation, and a
#: single union would let `_transform_member` statically accept a value its own
#: dispatch rejects at runtime.
ResolvedTransformKind = Union[TransformKind, Literal["SEQUENCE"]]

#: The kinds with a closed-form homogeneous matrix. SEQUENCE has one too, but
#: only after a network round-trip (`resolve_matrix`); the rest have none.
MATRIX_KINDS: Final[frozenset[ResolvedTransformKind]] = frozenset(
    {"IDENTITY", "SCALE", "TRANSLATION", "AFFINE", "ROTATION", "MAP_AXIS"}
)


# --- Pyramids ---------------------------------------------------------------

#: How a pyramid level reduces the level above it, named as xarray names it.
#: `pyramid._REDUCTIONS` maps these onto the server's `ScaleMethod`.
Reduction = Literal["max", "mean", "sum", "min", "nearest"]


# --- Render graphs ----------------------------------------------------------

#: The discriminator of a `LayerNodeInput`. The generated field is an
#: unconstrained `str` because the server does not enumerate it, so this is the
#: only place the four legal spellings are written down.
LayerNodeKind = Literal["channel", "blend", "phasor", "projection"]


# --- Per-axis selections ----------------------------------------------------

#: One axis' worth of a lens selection: an ``int`` pins a single index, a
#: ``slice`` or a ``(start, stop[, step])`` tuple selects a range. ``None`` in a
#: tuple position is open-ended, exactly as in a slice.
AxisSelection = Union[
    int,
    slice,
    tuple[int | None, int | None],
    tuple[int | None, int | None, int | None],
]

#: The normalized form: ``(start, stop, step)``, any of which may be ``None``.
SliceBounds = tuple[int | None, int | None, int | None]


def normalize_selection(axis: str, selection: AxisSelection) -> SliceBounds:
    """One selection as ``(start, stop, step)``, or a refusal naming the axis.

    The single spelling of the selection contract, shared by
    ``DatasetTrait.lens`` (which turns it into a ``SliceInput``) and
    ``specs._selected_extent`` (which measures what it keeps). Shape only —
    anything needing the axis' extent, including bounds checking, belongs to the
    caller that knows it.

    The ``bool`` rejection is not redundant with the annotation: ``bool`` is a
    subclass of ``int``, so no type can exclude ``dataset.lens(c=True)``, and
    silently reading it as index 1 is worse than refusing it.
    """
    if isinstance(selection, bool):
        raise TypeError(f"Invalid selection for axis {axis!r}: {selection!r}")
    if isinstance(selection, int):
        return (selection, selection + 1, None)
    if isinstance(selection, slice):
        return (selection.start, selection.stop, selection.step)
    if isinstance(selection, (tuple, list)) and 2 <= len(selection) <= 3:
        start, stop = selection[0], selection[1]
        step = selection[2] if len(selection) == 3 else None
        return (start, stop, step)
    raise TypeError(
        f"Invalid selection for axis {axis!r}: {selection!r}. Pass an int, a "
        f"slice(), or a (start, stop[, step]) tuple"
    )


# --- Calibration ------------------------------------------------------------


class Calibration(NamedTuple):
    """How far one pixel step goes along an axis, and in what.

    What ``DatasetTrait.calibrate`` takes per axis. A pair rather than two
    parallel sequences because the factor is meaningless without the unit, and
    a named pair rather than a bare tuple because ``(0.2, "micrometer")`` and
    ``("micrometer", 0.2)`` are equally plausible spellings of the same thought
    and only one of them works.
    """

    factor: float
    unit: Unit


# --- Column types -----------------------------------------------------------

#: What a table column is for, mirroring ``api.schema.ColumnRole``.
ColumnRoleName = Literal[
    "COORDINATE",
    "ATTRIBUTE",
    "ID",
    "TRACK_ID",
    "LABEL",
    "COLOR",
]

#: What DuckDB calls each Arrow type, for the types that survive a Parquet round
#: trip with the same answer on every DuckDB the stack runs.
#:
#: A table column's declared ``dtype`` is a **DuckDB** type name and the frame it
#: is declared for is a **pandas/Arrow** object, so this mapping is the whole of
#: the gap — and it is not the obvious one: a float64 is a ``DOUBLE``, a float32
#: is a ``FLOAT``, a str column is a ``VARCHAR``. Every entry was measured, by
#: writing a one-column Parquet of that type and running ``DESCRIBE`` over it on
#: **both** the DuckDB the client has and the older one the server runs.
#:
#: The keys are ``str(arrow_type)`` — what ``pyarrow`` prints, and what a caller
#: reading a traceback sees. Deliberately partial; see :func:`duckdb_type`.
_DUCKDB_BY_ARROW: Final[Mapping[str, str]] = {
    "int8": "TINYINT",
    "int16": "SMALLINT",
    "int32": "INTEGER",
    "int64": "BIGINT",
    "uint8": "UTINYINT",
    "uint16": "USMALLINT",
    "uint32": "UINTEGER",
    "uint64": "UBIGINT",
    "float": "FLOAT",
    "double": "DOUBLE",
    "bool": "BOOLEAN",
    "string": "VARCHAR",
    "large_string": "VARCHAR",
    "string_view": "VARCHAR",
    "binary": "BLOB",
    "large_binary": "BLOB",
    "binary_view": "BLOB",
    # date64 beside date32 is not a duplicate: Parquet has one date encoding, so
    # a date64 column comes back off the file *as* a date32. Both are DATE
    # either way, which is why they can share a row without the caller caring.
    "date32[day]": "DATE",
    "date64[ms]": "DATE",
    "time32[s]": "TIME",
    "time32[ms]": "TIME",
    "time64[us]": "TIME",
    "time64[ns]": "TIME",
    "timestamp[s]": "TIMESTAMP",
    "timestamp[ms]": "TIMESTAMP",
    "timestamp[us]": "TIMESTAMP",
    "timestamp[ns]": "TIMESTAMP_NS",
}

#: The Arrow types this vocabulary refuses by name, and what to do instead. Each
#: is a case where guessing yields a plausible, wrong, silent answer.
_REFUSED_ARROW_TYPES: Final[Mapping[str, str]] = {
    "halffloat": (
        "a float16 column reads back as FLOAT on DuckDB 1.5 and as BLOB on "
        "DuckDB 1.2, so no single answer is right on both. Cast it: "
        "frame.astype({name: 'float32'})"
    ),
    "null": (
        "an all-null column gives Parquet no type to record and DuckDB reads it "
        "back as INTEGER, so declaring it would claim a type the data does not "
        "have. Give the column a dtype, or drop it"
    ),
}

#: The same, matched by prefix because the types are parameterised.
_REFUSED_ARROW_PREFIXES: Final[Mapping[str, str]] = {
    "duration": (
        "a duration column is stored as a bare integer count of its unit, so "
        "DuckDB reads it back as BIGINT and the unit is gone. Convert it to the "
        "number meant -- frame[name].dt.total_seconds() -- and declare the unit "
        "on the column instead"
    ),
    "decimal256": (
        "a decimal256 reads back as DECIMAL while its precision fits DuckDB's 38 "
        "digits and as DOUBLE beyond that, so its type turns on a number this "
        "cannot see. Use decimal128, or float64"
    ),
    "list": "a nested column is not a table column. Explode or flatten it first",
    "large_list": "a nested column is not a table column. Explode or flatten it first",
    "fixed_size_list": "a nested column is not a table column. Explode or flatten it first",
    "struct": "a nested column is not a table column. Flatten it into one column per field",
    "map": "a nested column is not a table column. Flatten it into one column per key",
}

_DECIMAL128 = re.compile(r"^decimal128\((\d+), (\d+)\)$")
_DICTIONARY_VALUES = re.compile(r"^dictionary<values=(.+), indices=[^,]+, ordered=\d+>$")


class UnknownArrowType(ValueError):
    """Raised when the Arrow -> DuckDB vocabulary has no entry for a type."""


def duckdb_type(arrow_type: object) -> str:
    """What DuckDB will call this Arrow type once it is a Parquet file.

    Takes a ``pyarrow.DataType`` — or anything whose ``str()`` is one, which is
    what a schema field prints as — and returns the DuckDB type name a column of
    that type is declared with::

        duckdb_type(pa.float64())   # 'DOUBLE'

    Deliberately partial, in the same way and for the same reason as
    :func:`default_axis_type`: the listed types are the ones measured to give
    the same answer on every DuckDB in the stack, and there is no catch-all.
    Anything else raises, saying what to do about it — because the alternative
    is a column confidently declared as the wrong thing (a float16 named FLOAT,
    an empty column named INTEGER), which nothing downstream would object to.

    Raises:
        UnknownArrowType: if the type is not in the measured vocabulary.
    """
    name = str(arrow_type)

    known = _DUCKDB_BY_ARROW.get(name)
    if known is not None:
        return known

    # A tz-aware timestamp is TIMESTAMP WITH TIME ZONE whatever its unit --
    # measured for s/us/ns and for a named zone as well as UTC, which is why
    # this is a rule where the naive ones above are a table.
    if name.startswith("timestamp[") and ", tz=" in name:
        return "TIMESTAMP WITH TIME ZONE"

    decimal = _DECIMAL128.match(name)
    if decimal is not None:
        return f"DECIMAL({decimal.group(1)},{decimal.group(2)})"

    # A dictionary column becomes its values type on write: Parquet stores the
    # dictionary as an encoding rather than a type, so only a string dictionary
    # survives as one and the rest come back decoded. Recursing is right for
    # both -- measured for values=string (VARCHAR) and values=int64 (BIGINT).
    dictionary = _DICTIONARY_VALUES.match(name)
    if dictionary is not None:
        return duckdb_type(dictionary.group(1))

    advice = _REFUSED_ARROW_TYPES.get(name)
    if advice is None:
        for prefix, reason in _REFUSED_ARROW_PREFIXES.items():
            if name.startswith(prefix):
                advice = reason
                break

    raise UnknownArrowType(
        f"No DuckDB type is recorded for the Arrow type {name!r}: "
        + (advice or "it is not in the measured vocabulary")
        + ". mikro_next.vocabulary._DUCKDB_BY_ARROW lists what is."
    )


#: The colormaps that assign a colour per distinct value rather than a ramp over a range.
#: Held here as the *values* rather than as ``ColorMap`` members, because this module imports
#: nothing from ``mikro_next`` -- that is what lets :mod:`mikro_next.traits` use it, and an
#: enum tuple would come from :mod:`mikro_next.api.schema`, which imports ``traits`` back.
#: ``use_enum_values=True`` means a field holds the value anyway, so nothing is lost.
#: :data:`mikro_next.picker.QUALITATIVE_COLORMAPS` is the same set as members.
QUALITATIVE_COLORMAP_VALUES: Final[frozenset[str]] = frozenset({"HUES", "DISTINCT", "PASTEL", "VIVID"})


__all__ = [
    "AXIS_TYPE_ORDER",
    "COARSENABLE_AXIS_TYPES",
    "MATRIX_KINDS",
    "QUALITATIVE_COLORMAP_VALUES",
    "AxisSelection",
    "AxisTypeName",
    "Calibration",
    "ColumnRoleName",
    "LayerNodeKind",
    "Reduction",
    "ResolvedTransformKind",
    "SliceBounds",
    "TransformKind",
    "UnknownArrowType",
    "UnknownAxisName",
    "axis_type_rank",
    "default_axis_type",
    "duckdb_type",
    "normalize_selection",
]
