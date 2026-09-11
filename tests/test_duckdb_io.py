"""Unit tests for the DuckDB parquet read helpers (no network)."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from mikro_next.io.duckdb_io import (
    create_duckdb_s3_connection,
    require_duckdb,
)


def _grant() -> SimpleNamespace:
    return SimpleNamespace(
        access_key="access",
        secret_key="secret",
        session_token="token",
        bucket="bucket",
        key="tables/example.parquet",
    )


def test_require_duckdb_returns_module() -> None:
    duckdb = require_duckdb()
    assert hasattr(duckdb, "connect")


def test_relation_roundtrips_local_parquet(tmp_path) -> None:
    """A relation over a local parquet file materialises back to the source frame."""
    df = pd.DataFrame(
        {
            "x": np.arange(5, dtype="int64"),
            "value": np.linspace(0.0, 1.0, 5),
        }
    )
    path = tmp_path / "example.parquet"
    pq.write_table(pa.Table.from_pandas(df), path)

    duckdb = require_duckdb()
    con = duckdb.connect()
    relation = con.sql(f"SELECT * FROM read_parquet('{path.as_posix()}')")

    assert relation.df().equals(df), "Materialised relation should match the source"
    # Lazy filtering happens in DuckDB, not by loading everything into pandas first.
    filtered = relation.filter("value > 0.5").df()
    assert (filtered["value"] > 0.5).all()


def test_create_duckdb_s3_connection_applies_settings() -> None:
    """The S3 connection helper configures httpfs path-style settings from the grant."""
    con = create_duckdb_s3_connection("http://minio:9000", _grant())

    url_style = con.execute("SELECT current_setting('s3_url_style')").fetchone()[0]
    endpoint = con.execute("SELECT current_setting('s3_endpoint')").fetchone()[0]
    use_ssl = con.execute("SELECT current_setting('s3_use_ssl')").fetchone()[0]

    assert url_style == "path"
    assert endpoint == "minio:9000"  # scheme stripped
    assert use_ssl is False  # http:// -> no TLS


def test_create_duckdb_s3_connection_uses_ssl_for_https() -> None:
    con = create_duckdb_s3_connection("https://s3.example.com", _grant())
    use_ssl = con.execute("SELECT current_setting('s3_use_ssl')").fetchone()[0]
    endpoint = con.execute("SELECT current_setting('s3_endpoint')").fetchone()[0]
    assert use_ssl is True
    assert endpoint == "s3.example.com"
