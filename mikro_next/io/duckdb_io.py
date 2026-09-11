"""Helpers for reading Mikro parquet objects out-of-core via DuckDB + httpfs.

DuckDB's ``httpfs`` extension lets us query a parquet object directly on S3
without downloading it whole into memory, so table reads stay out-of-core: the
caller gets a lazy :class:`duckdb.DuckDBPyRelation` and only materialises what a
query actually needs.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import duckdb

    from mikro_next.io.obstore import S3UploadGrantLike


def require_duckdb() -> "Any":  # noqa: ANN401
    """Import duckdb lazily, raising a helpful error if the extra is missing.

    DuckDB is only needed for the table (parquet) read path, so it is an optional
    dependency. Install it via ``mikro-next[table]``.
    """
    try:
        import duckdb
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "duckdb is required for out-of-core table reads. "
            "Install it with `pip install mikro-next[table]`."
        ) from e
    return duckdb


def create_duckdb_s3_connection(
    endpoint_url: str, grant: "S3UploadGrantLike"
) -> "duckdb.DuckDBPyConnection":
    """Create a DuckDB connection configured to read from the Mikro S3 endpoint.

    Loads the ``httpfs`` extension and applies the S3 settings derived from the
    grant and endpoint (path-style addressing, matching ``create_s3_store``).
    """
    duckdb = require_duckdb()

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")

    # The endpoint setting must not carry the scheme; the scheme decides TLS.
    use_ssl = endpoint_url.startswith("https://")
    s3_endpoint = endpoint_url.split("://", 1)[-1].rstrip("/")

    con.execute("SET s3_url_style='path';")
    con.execute("SET s3_region='us-east-1';")  # dummy; required by duckdb/httpfs
    con.execute("SET s3_endpoint=?;", [s3_endpoint])
    con.execute("SET s3_use_ssl=?;", [use_ssl])
    con.execute("SET s3_access_key_id=?;", [grant.access_key])
    con.execute("SET s3_secret_access_key=?;", [grant.secret_key])
    if grant.session_token:
        con.execute("SET s3_session_token=?;", [grant.session_token])

    return con


def read_parquet_relation(
    con: "duckdb.DuckDBPyConnection", bucket: str, key: str
) -> "duckdb.DuckDBPyRelation":
    """Return a lazy relation over the parquet object at ``s3://{bucket}/{key}``."""
    return con.sql(f"SELECT * FROM read_parquet('s3://{bucket}/{key}')")
