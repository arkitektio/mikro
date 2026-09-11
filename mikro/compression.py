"""Which Parquet compression codecs survive the trip to a viewer, and refusing the rest.

**This is a contract this client invents.** The server stores whatever arrives and validates no
codec at all -- its only read of an uploaded Parquet is a DuckDB ``DESCRIBE`` of the footer to
record the column types (``datalayer/datalayer.py``). So a file compressed with something the
viewer cannot decode uploads cleanly, describes cleanly, and then renders as nothing. The
failure has no error attached to it anywhere, which is the argument for putting one here.

Two readers, two sets, because they are different code paths in the frontend:

* **A table** is read with DuckDB-WASM (``read_parquet()`` over s3 httpfs) -- see
  ``lib/duckdb/duckdb.ts``, ``components/tables/useDuckDbTable.ts``,
  ``lib/attributes/lookupEngine.ts`` in orkestrator-next. DuckDB 1.5 decodes everything Parquet
  defines except LZO, so :data:`TABLE_CODECS` is wide and this check will rarely fire --
  pyarrow cannot even *write* LZO. Its standing value is that the readable set is written down
  in one place and that the codec this library writes with is stated rather than inherited.
* **A mesh collection** is read with hyparquet, and ``hyparquet-compressors`` is not installed
  -- ``components/scene/features/meshes/fabriks/parquetPart.ts`` registers ZSTD by hand out of
  ``fzstd`` and nothing else. hyparquet's own built-ins are UNCOMPRESSED and SNAPPY. So
  :data:`MESH_CODECS` has three members, and GZIP, BROTLI and LZ4 -- all three selectable in
  ``fabriks.frames.ParquetCompression`` -- would produce a collection that silently does not
  draw. That is where this check has teeth.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:  # pragma: no cover
    import pyarrow.parquet as pq

__all__ = [
    "DEFAULT_COMPRESSION",
    "MESH_CODECS",
    "TABLE_CODECS",
    "UnreadableCodecError",
    "codecs_of",
    "refuse_unreadable_codec",
]


class UnreadableCodecError(ValueError):
    """Raised for a Parquet compressed with a codec the reader downstream cannot decode."""


#: What a table's reader can decode: DuckDB-WASM 1.33.1-dev45.0, i.e. DuckDB v1.5.1. Everything
#: Parquet defines except LZO. Both LZ4 spellings are here because pyarrow's footer reports
#: ``LZ4`` for ``lz4`` and ``lz4_raw`` alike -- the two cannot be told apart from the metadata,
#: and DuckDB reads both, so there is nothing to tighten here later.
TABLE_CODECS: Final[frozenset[str]] = frozenset(
    {"UNCOMPRESSED", "SNAPPY", "GZIP", "ZSTD", "BROTLI", "LZ4", "LZ4_RAW"}
)

#: What a mesh collection's reader can decode: hyparquet's two built-ins plus the ZSTD the
#: viewer registers out of ``fzstd``. Narrow because ``hyparquet-compressors`` is not a
#: dependency there -- not because these three are special.
MESH_CODECS: Final[frozenset[str]] = frozenset({"UNCOMPRESSED", "SNAPPY", "ZSTD"})

#: What this library writes with, everywhere it writes a Parquet itself. Explicit because
#: pyarrow's default is SNAPPY and an implicit codec is a contract nobody stated. ZSTD is in
#: both readable sets, is what every converter in ``testing/`` already chose by hand, and the
#: upload is network-bound, so bytes are the thing worth spending CPU on.
DEFAULT_COMPRESSION: Final[str] = "zstd"


def codecs_of(source: str | Path | pq.FileMetaData) -> frozenset[str]:
    """Every compression codec named in a Parquet's footer, read **without the rows**.

    Parquet records compression per *column chunk*, not per file, so every chunk of every row
    group is asked rather than one of them. ``pq.ParquetFile`` reads the footer only: a 4 GB
    table stays on disk, which is the whole reason the path branch of the uploader exists.
    """
    import pyarrow.parquet as pq

    metadata = source if hasattr(source, "row_group") else pq.ParquetFile(source).metadata
    return frozenset(
        metadata.row_group(group).column(column).compression
        for group in range(metadata.num_row_groups)
        for column in range(metadata.num_columns)
    )


def refuse_unreadable_codec(
    source: str | Path | pq.FileMetaData,
    *,
    readable: Iterable[str] = TABLE_CODECS,
    reader: str = "the table viewer, which reads Parquet with DuckDB-WASM",
) -> None:
    """Refuse a Parquet whose compression the reader downstream cannot decode.

    Raised before the bytes move, because the alternative is finding out from a table that
    loaded, described and then displayed nothing.
    """
    readable = frozenset(readable)
    unreadable = sorted(codecs_of(source) - readable)
    if not unreadable:
        return

    where = f" ({source})" if isinstance(source, (str, Path)) else ""
    raise UnreadableCodecError(
        f"This Parquet{where} is compressed with {', '.join(unreadable)}, which {reader} "
        f"cannot decode. It reads {', '.join(sorted(readable))}.\n"
        "\n"
        "Nothing on the server will tell you this: it stores whatever arrives and validates no "
        "codec at all, so the upload would succeed, the schema would be recorded, and the "
        "failure would surface as a view that renders nothing. This refusal is the client's, "
        "and it is here because it is the only place the reader's limits are known.\n"
        "\n"
        f"Write the file with `compression={DEFAULT_COMPRESSION!r}` -- or let this library "
        "write it, by handing `data=` the table itself rather than a path."
    )
