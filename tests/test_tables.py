"""Declaring a table dataset, and what the declaration is checked against.

Three things are under test and only one of them is the checking. The second is the
Arrow -> DuckDB vocabulary, which is a claim about what *another process* will say: the
server DESCRIBEs the Parquet with its own DuckDB, and a mapping that is merely plausible
produces a column confidently declared as the wrong thing with nothing anywhere to object.
Every entry in it was measured against a real Parquet round trip on two DuckDB versions.

The third is the shape of the API itself. A caller writes the generated ``ColumnInput`` --
one declaration per column, `axisType` making it an axis, `identifiedBy` saying what its
values are -- and passes them to ``create_table_dataset``; there is no helper in between and
no wrapper type. So the tests construct ``CreateTableDatasetInput``, which is where the
resolution and every refusal now live, and a refusal arrives as pydantic's
``ValidationError`` wrapping ours.
"""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from mikro_next.api.schema import (
    AxisType,
    ColumnInput,
    ColumnRole,
    CreateTableDatasetInput,
    TableIdentifiesInput,
)
from mikro_next.tables import (
    MAX_COLUMNS,
    TableDeclarationError,
    arrow_schema_of,
    file_columns_of,
)
from mikro_next.vocabulary import UnknownArrowType, duckdb_type


@pytest.fixture
def frame() -> pd.DataFrame:
    """The shape of a measurement table: an id, two measurements, a flag."""
    return pd.DataFrame(
        {
            "object_id": [1, 2, 3],
            "volume_um3": [1.5, 2.5, 3.5],
            "label": ["a", "b", "c"],
            "at_edge": [True, False, True],
        }
    )


def declare(data, columns=()) -> CreateTableDatasetInput:
    """The call under test, minus the name nothing here is about."""
    return CreateTableDatasetInput(name="t", data=data, columns=list(columns))


# --- the vocabulary ---------------------------------------------------------


@pytest.mark.parametrize(
    "arrow, duck",
    [
        (pa.int64(), "BIGINT"),
        (pa.int32(), "INTEGER"),
        (pa.float64(), "DOUBLE"),
        (pa.float32(), "FLOAT"),
        (pa.bool_(), "BOOLEAN"),
        (pa.string(), "VARCHAR"),
        (pa.large_string(), "VARCHAR"),
        (pa.decimal128(10, 2), "DECIMAL(10,2)"),
        (pa.dictionary(pa.int8(), pa.string()), "VARCHAR"),
        (pa.timestamp("us"), "TIMESTAMP"),
        (pa.timestamp("us", tz="UTC"), "TIMESTAMP WITH TIME ZONE"),
    ],
)
def test_the_duckdb_name_is_what_duckdb_actually_says(arrow, duck, tmp_path):
    """And it is checked against DuckDB, not against the table it came from.

    The point of the mapping is that it predicts another process's answer, so a
    test that only reads the dict back proves nothing. This writes the Parquet
    and asks.
    """
    assert duckdb_type(arrow) == duck

    duckdb = pytest.importorskip("duckdb")
    path = tmp_path / "probe.parquet"
    pq.write_table(pa.table({"c": pa.array([None, None], type=arrow)}), path)
    described = duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{path}');").fetchall()
    assert described[0][1] == duck


@pytest.mark.parametrize(
    "arrow, because",
    [
        # FLOAT on DuckDB 1.5, BLOB on the 1.2 the server runs -- version-skewed,
        # so there is no answer that is right on both.
        (pa.float16(), "float32"),
        # An all-null column: Parquet records no type and DuckDB reads INTEGER.
        (pa.null(), "drop it"),
        # Stored as a bare integer count, so the unit is silently gone.
        (pa.duration("us"), "total_seconds"),
        (pa.list_(pa.int64()), "Explode or flatten"),
        (pa.struct([("a", pa.int64())]), "Flatten it into one column per field"),
    ],
)
def test_a_type_with_no_stable_answer_is_refused_not_guessed(arrow, because):
    """The refusals are the load-bearing half.

    `default_axis_type` is the precedent: guessing at an unlisted name is how a
    tile index became a spatial axis and got coarsened away. The same shape of
    bug here is a column declared as a type it does not have.
    """
    with pytest.raises(UnknownArrowType) as raised:
        duckdb_type(arrow)
    assert because in str(raised.value)


def test_a_type_the_server_could_not_describe_is_refused_before_the_upload(frame):
    """The vocabulary's job: predict what the server will read back, or refuse to guess.

    A float16 column reads back as FLOAT on DuckDB 1.5 and as BLOB on the 1.2 the server runs,
    and an all-null column has no type for Parquet to record at all. Both are a declaration
    that cannot be right, and both are otherwise found *after* the upload.
    """
    ok = frame.astype({"label": "category"})
    assert [column.dtype for column in declare(ok).columns] == ["BIGINT", "DOUBLE", "VARCHAR", "BOOLEAN"]

    with pytest.raises(ValidationError, match="float32"):
        declare(frame.assign(f16=pd.array([1.0, 2.0, 3.0], dtype="float16")))


# --- what the file supplies -------------------------------------------------


def test_every_column_of_the_file_is_declared_whether_the_caller_names_it_or_not(frame):
    """The server checks the declaration against the Parquet: same names, same order, same
    types. That is a fact about the file, so it is derived rather than asked for -- and a
    column nobody says anything about is an ATTRIBUTE of the type the file records."""
    got = declare(frame, columns=[ColumnInput(name="volume_um3", unit="micrometer**3")])

    assert [(column.name, column.dtype) for column in got.columns] == [
        ("object_id", "BIGINT"),
        ("volume_um3", "DOUBLE"),
        ("label", "VARCHAR"),
        ("at_edge", "BOOLEAN"),
    ]
    assert [column.unit for column in got.columns] == [None, "micrometer**3", None, None]
    assert all(column.role is None for column in got.columns)


def test_the_caller_s_columns_are_a_subset_in_any_order(frame):
    """`columns` is what the file cannot say, for the columns it is true of. It is not the
    file's list and does not have to look like it -- the file's order is imposed here."""
    got = declare(
        frame,
        columns=[
            ColumnInput(name="at_edge", longName="touches the field boundary"),
            ColumnInput(name="object_id", description="the segmentation's instance id"),
        ],
    )

    assert [column.name for column in got.columns] == ["object_id", "volume_um3", "label", "at_edge"]
    assert got.columns[0].description == "the segmentation's instance id"
    assert got.columns[3].long_name == "touches the field boundary"


def test_a_column_may_be_declared_without_its_dtype(frame):
    """Which is the ordinary case. `dtype` is DuckDB's vocabulary and a DataFrame speaks
    pandas', so writing it by hand is transcription with one specific way to be wrong."""
    got = declare(frame, columns=[ColumnInput(name="label", role=ColumnRole.LABEL)])

    assert got.columns[2].dtype == "VARCHAR"
    # And it reaches the wire, rather than being dropped as unset.
    payload = got.model_dump(by_alias=True, exclude_unset=True)
    assert payload["columns"][2] == {"name": "label", "dtype": "VARCHAR", "role": "LABEL"}


def test_a_stated_dtype_is_still_checked(frame):
    """Optional is not unchecked: an assertion about the data is worth checking, and this is
    the cheap side to check it on."""
    with pytest.raises(ValidationError, match="declared BIGINT and this frame writes VARCHAR"):
        declare(frame, columns=[ColumnInput(name="label", dtype="BIGINT")])


def test_a_matrix_wide_file_is_refused_and_told_where_it_belongs():
    """The refusal is about shape rather than size, so it says so at length.

    The same argument the server makes, made here so the caller meets it before the upload.
    A caller who hits this has a real object -- an expression matrix, an intensity matrix --
    and needs to know there is somewhere for it to go and roughly what that looks like.
    """
    wide = pa.table({f"gene_{index}": pa.array([0.0], type=pa.float32()) for index in range(MAX_COLUMNS + 1)})

    with pytest.raises(ValidationError) as raised:
        declare(wide)
    message = str(raised.value)
    assert "3,001 columns" in message and "3,000" in message
    assert "shape, not size" in message
    assert "create_sparse_dataset" in message
    assert "one axis with one picker entry" in message

    narrow = pa.table({f"gene_{index}": pa.array([0.0], type=pa.float32()) for index in range(MAX_COLUMNS)})
    assert len(declare(narrow).columns) == MAX_COLUMNS


def test_an_index_that_would_not_be_written_at_all_is_refused(frame):
    """A `RangeIndex` is start/stop/step metadata rather than data, and on pandas 3 any
    evenly spaced integer index is inferred to be one -- which object ids running 1..N are.
    So `frame.set_index("object_id")` writes a Parquet with no `object_id` column."""
    with pytest.raises(ValidationError, match="reset_index"):
        declare(frame.set_index("object_id"))


def test_an_anonymous_index_is_refused(frame):
    """The opposite problem: it gains the file a `__index_level_0__` column that exists in
    no frame, and that no declaration can sensibly describe."""
    unnamed = frame.set_index(pd.Index([10, 20, 31]))
    with pytest.raises(ValidationError, match="__index_level_0__"):
        declare(unnamed)


@pytest.mark.parametrize("source", ["dict", "dataframe", "arrow_table", "schema", "path"])
def test_every_parquet_like_thing_gives_the_same_answer(frame, source, tmp_path):
    """A `Table` big enough to matter must not be converted twice to describe it -- and a
    dict of columns is the shortest way to say a small table, so it answers the same.

    Compared as *DuckDB* names rather than Arrow ones, because that is what a declaration is
    made of and the Arrow spellings legitimately differ: pandas writes a string column as
    `large_string` and a numpy object array becomes `string`. Both are VARCHAR, which is the
    only thing that reaches the server."""
    table = pa.Table.from_pandas(frame)
    path = tmp_path / "t.parquet"
    pq.write_table(table, path)
    value = {
        "dict": {name: frame[name].to_numpy() for name in frame.columns},
        "dataframe": frame,
        "arrow_table": table,
        "schema": table.schema,
        "path": path,
    }[source]

    assert [(field.name, duckdb_type(field.type)) for field in arrow_schema_of(value)] == [
        (field.name, duckdb_type(field.type)) for field in table.schema
    ]


def test_a_dict_of_columns_needs_no_file_at_all(frame, tmp_path):
    """The point of the dict: nothing is staged, nothing is written, nothing is unlinked."""
    got = declare({"i": [1, 2, 3], "name": ["a", "b", "c"]})

    assert [(column.name, column.dtype) for column in got.columns] == [("i", "BIGINT"), ("name", "VARCHAR")]
    assert list(tmp_path.iterdir()) == []


# --- what the caller declares -----------------------------------------------


def test_a_declared_column_that_is_not_in_the_frame_is_refused_with_the_near_miss(frame):
    with pytest.raises(ValidationError) as raised:
        declare(frame, columns=[ColumnInput(name="volume_um2", unit="micrometer**2")])
    assert "volume_um3" in str(raised.value), "the near miss is named"


def test_an_axis_column_carries_its_own_prose(frame):
    """One declaration: the column that is an axis says everything about itself in one place,
    so there is no second list for a unit or a longName to be silently dropped from."""
    got = declare(frame, columns=[ColumnInput(name="object_id", axis_type=AxisType.INDEX, long_name="instance id")])

    assert [column.name for column in got.columns] == ["object_id", "volume_um3", "label", "at_edge"]
    assert got.columns[0].axis_type == AxisType.INDEX.value
    assert got.columns[0].role is None, "COORDINATE follows from `axisType`, not from a role"
    assert got.columns[0].long_name == "instance id"


def test_a_column_declared_twice_is_refused(frame):
    with pytest.raises(ValidationError, match="more than once"):
        declare(frame, columns=[ColumnInput(name="label"), ColumnInput(name="label", role=ColumnRole.LABEL)])


def test_an_axis_type_beside_a_role_is_refused(frame):
    """An axis column IS a COORDINATE by the fact of `axisType`; a role beside it is the same
    question answered twice, and the old two-list shape silently preferred one answer."""
    with pytest.raises(ValidationError, match="both `axis_type` and `role`"):
        declare(frame, columns=[ColumnInput(name="object_id", axis_type=AxisType.INDEX, role=ColumnRole.ID)])


def test_an_index_axis_carries_no_unit(frame):
    """It enumerates: the distance between object 3 and object 4 is not a small number, it is
    not a number."""
    with pytest.raises(ValidationError, match="no metric to state a unit in"):
        declare(frame, columns=[ColumnInput(name="object_id", axis_type=AxisType.INDEX, unit="micrometer")])


def test_a_space_axis_may_not_say_what_it_enumerates(frame):
    """A position in nanometres and a row id are different things."""
    enumerates = [TableIdentifiesInput(kind="TABLE", table="7")]

    with pytest.raises(ValidationError, match="positions rather than ids"):
        declare(frame, columns=[ColumnInput(name="volume_um3", axis_type=AxisType.SPACE, unit="micrometer**3", identified_by=enumerates)])

    # Accepted -- the product-space case -- and the identification reaches the input intact.
    got = declare(frame, columns=[ColumnInput(name="object_id", axis_type=AxisType.INDEX, identified_by=enumerates)])
    assert got.columns[0].identified_by[0].table == "7"


def test_a_data_column_may_reference_a_table(frame):
    """The retired `references`, spelled the one remaining way: a TABLE identification on a
    plain data column is a foreign key, authors no edge, and makes the column no axis."""
    got = declare(
        frame,
        columns=[ColumnInput(name="object_id", role=ColumnRole.ID, identified_by=[TableIdentifiesInput(kind="TABLE", table="7")])],
    )
    assert got.columns[0].axis_type is None
    assert got.columns[0].identified_by[0].table == "7"


def test_a_column_identified_by_two_tables_is_refused(frame):
    """Fan-in is meaningful only for the kinds that author an edge.

    Two masks keying one axis are two edges, each standing on its own. Two tables would be two
    different answers to what a value in the column is -- and it lands on one column's
    `references`, so only one of them could even be recorded.
    """
    # The prose says "enumeration" now that NETWORK_COLLECTION_NODES counts too.
    with pytest.raises(ValidationError, match="more than one enumeration"):
        declare(
            frame,
            columns=[
                ColumnInput(
                    name="object_id",
                    axis_type=AxisType.INDEX,
                    identified_by=[
                        TableIdentifiesInput(kind="TABLE", table="7"),
                        TableIdentifiesInput(kind="TABLE", table="8"),
                    ],
                )
            ],
        )


def test_the_axis_order_is_the_files_column_order(frame):
    """A table has no byte order, so there is no list to reorder its space with: the axes are
    the axis-typed columns as the file runs, however the caller orders the declaration."""
    spatial = pd.DataFrame({"z": [1.0], "y": [2.0], "x": [3.0], "photons": [4.0]})
    got = declare(
        spatial,
        columns=[
            # Declared x-first on purpose: `columns` is a subset in any order, and the
            # resolution imposes the file's.
            ColumnInput(name=name, axis_type=AxisType.SPACE, unit="nanometer")
            for name in ("x", "y", "z")
        ],
    )
    assert [column.name for column in got.columns if column.axis_type is not None] == ["z", "y", "x"]


def test_spatial_columns_in_ascending_order_are_refused():
    """x is the *last* spatial axis and y the one before it, by position and never by name,
    so a frame whose columns run `(x, y, z)` renders fully transposed rather than failing.
    Nothing on the server can catch it -- a table's axis names are free-form -- so only a
    name that follows the convention says which order was meant. The axis order is the
    column order, so the fix is reordering the frame, and the message says so."""
    spatial = pd.DataFrame({"x": [1.0], "y": [2.0], "z": [3.0]})
    with pytest.raises(ValidationError, match="reverse of the array convention"):
        declare(
            spatial,
            columns=[ColumnInput(name=name, axis_type=AxisType.SPACE, unit="nanometer") for name in ("x", "y", "z")],
        )


def test_a_table_axis_is_a_position_an_instant_or_an_enumeration(frame):
    with pytest.raises(ValidationError, match="a table's axes are"):
        declare(frame, columns=[ColumnInput(name="object_id", axis_type=AxisType.CHANNEL)])


def test_a_coordinate_role_is_spelled_axis_type(frame):
    """The server refuses this too: COORDINATE follows from `axisType`, it is not a role."""
    with pytest.raises(ValidationError, match="say so with `axis_type`"):
        declare(frame, columns=[ColumnInput(name="object_id", role=ColumnRole.COORDINATE)])


def test_a_unit_belongs_on_something_measured(frame):
    """An id, a label or a colour is not measured, so a unit on one says nothing. The server
    refuses it after the upload; this refuses it before."""
    with pytest.raises(ValidationError, match="is not\\s+measured"):
        declare(frame, columns=[ColumnInput(name="label", role=ColumnRole.LABEL, unit="micrometer")])


def test_a_table_holds_at_most_one_id_column(frame):
    with pytest.raises(ValidationError, match="at most one ID column"):
        declare(
            frame,
            columns=[
                ColumnInput(name="object_id", role=ColumnRole.ID),
                ColumnInput(name="label", role=ColumnRole.ID),
            ],
        )


def test_the_frame_s_own_account_is_readable_on_its_own(frame):
    """`file_columns_of` is the seam the trait uses, and is worth being able to ask directly
    -- a caller checking a frame before building a declaration for it."""
    assert file_columns_of(frame) == [
        ("object_id", "BIGINT"),
        ("volume_um3", "DOUBLE"),
        ("label", "VARCHAR"),
        ("at_edge", "BOOLEAN"),
    ]
    with pytest.raises(TableDeclarationError):
        file_columns_of(frame.set_index("object_id"))
