"""What a Parquet may be compressed with, and why this client has an opinion at all.

The server has none: its only read of an uploaded Parquet is a DuckDB ``DESCRIBE`` of the
footer to record the column types, and it stores whatever arrives. So a file the viewer
cannot decode uploads cleanly, describes cleanly and then renders nothing, with no error
anywhere to attach the cause to. These tests pin the two readable sets, that the library's
own writes state their codec rather than inheriting pyarrow's, and that a caller-written
file is checked from its footer alone.
"""


import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mikro_next.compression import (
    DEFAULT_COMPRESSION,
    MESH_CODECS,
    TABLE_CODECS,
    UnreadableCodecError,
    codecs_of,
    refuse_unreadable_codec,
)
from mikro_next.io.upload import _parquet_payload


@pytest.fixture
def table() -> pa.Table:
    return pa.table({"object_id": [1, 2, 3], "area": [1.5, 2.5, 3.5]})


@pytest.mark.parametrize(
    "written, recorded",
    [
        ("none", "UNCOMPRESSED"),
        ("snappy", "SNAPPY"),
        ("gzip", "GZIP"),
        ("zstd", "ZSTD"),
        ("brotli", "BROTLI"),
        # Measured on pyarrow 24: the footer says `LZ4` for both spellings, so the two
        # cannot be told apart from the metadata. Both are in TABLE_CODECS for that reason
        # and there is nothing to tighten here later.
        ("lz4", "LZ4"),
        ("lz4_raw", "LZ4"),
    ],
)
def test_the_codec_is_read_off_the_footer(table, written, recorded, tmp_path):
    path = tmp_path / "t.parquet"
    pq.write_table(table, path, compression=written)
    assert codecs_of(path) == {recorded}


def test_every_column_chunk_is_asked_not_one(table, tmp_path):
    """Parquet records compression per column chunk, not per file, so a file can hold more
    than one codec -- and one unreadable chunk is an unreadable file."""
    path = tmp_path / "mixed.parquet"
    pq.write_table(table, path, compression={"object_id": "zstd", "area": "gzip"})
    assert codecs_of(path) == {"ZSTD", "GZIP"}

    with pytest.raises(UnreadableCodecError, match="GZIP"):
        refuse_unreadable_codec(path, readable=MESH_CODECS)


def test_a_readable_codec_passes_and_an_unreadable_one_says_whose_limit_it_is(table, tmp_path):
    readable = tmp_path / "ok.parquet"
    pq.write_table(table, readable, compression="zstd")
    refuse_unreadable_codec(readable)  # the table reader decodes zstd

    unreadable = tmp_path / "no.parquet"
    pq.write_table(table, unreadable, compression="gzip")
    refuse_unreadable_codec(unreadable)  # ...and so does the table reader, for gzip

    with pytest.raises(UnreadableCodecError) as raised:
        refuse_unreadable_codec(unreadable, readable=MESH_CODECS, reader="the mesh viewer")
    message = str(raised.value)
    assert "GZIP" in message and "the mesh viewer" in message
    assert "validates no codec at all" in message, "the contract is named as this client's"
    assert DEFAULT_COMPRESSION in message, "and the fix is stated"


def test_the_footer_is_read_without_the_rows(table, tmp_path, monkeypatch):
    """The whole reason a path is streamed to the object store rather than loaded: a 4 GB
    table must not enter the process to have its codec checked."""
    path = tmp_path / "t.parquet"
    pq.write_table(table, path, compression="zstd")

    def refuse_to_read(*args, **kwargs):
        raise AssertionError("the rows were read")

    monkeypatch.setattr(pq, "read_table", refuse_to_read)
    monkeypatch.setattr(pq.ParquetFile, "read", refuse_to_read)
    refuse_unreadable_codec(path)


def test_the_two_readable_sets_are_the_two_readers():
    """A table is read with DuckDB-WASM, which decodes everything but LZO. A mesh collection
    is read with hyparquet, whose built-ins are UNCOMPRESSED and SNAPPY plus the ZSTD the
    viewer registers by hand -- `hyparquet-compressors` is not installed there."""
    assert MESH_CODECS < TABLE_CODECS
    assert MESH_CODECS == {"UNCOMPRESSED", "SNAPPY", "ZSTD"}
    assert {"GZIP", "BROTLI", "LZ4"} <= TABLE_CODECS
    assert "LZO" not in TABLE_CODECS
    assert DEFAULT_COMPRESSION.upper() in TABLE_CODECS and DEFAULT_COMPRESSION.upper() in MESH_CODECS


@pytest.mark.parametrize("kind", ["table", "reader", "dataframe"])
def test_the_library_states_the_codec_it_writes_with(table, kind):
    """All three branches, because pyarrow's default is SNAPPY and until now that was the
    codec every upload got without anyone choosing it."""
    value = {
        "table": table,
        "reader": pa.RecordBatchReader.from_batches(table.schema, table.to_batches()),
        "dataframe": table.to_pandas(),
    }[kind]

    payload, scratch = _parquet_payload(value)
    try:
        source = scratch if scratch is not None else payload
        if scratch is None:
            source.seek(0)
        assert codecs_of(source) == {DEFAULT_COMPRESSION.upper()}
    finally:
        if scratch is not None:
            scratch.unlink(missing_ok=True)


def test_a_path_is_streamed_with_whatever_codec_it_was_written_with(table, tmp_path):
    """Which is why it is checked instead: those bytes are the object in the store."""
    path = tmp_path / "theirs.parquet"
    pq.write_table(table, path, compression="brotli")

    payload, scratch = _parquet_payload(path)
    assert payload == path and scratch is None
    assert codecs_of(path) == {"BROTLI"}
