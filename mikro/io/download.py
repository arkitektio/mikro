"""Reading what mikro stores: zarr arrays, parquet tables, big files.

Every function takes the client first (``open_zarr_store(mikro, store_id)``):
the access grant is requested through it, and the datalayer that serves the
bytes is its own. An object's accessors (``dataset.data``, ``file.download()``)
pass the client that fetched the object. Nothing is looked up.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import obstore  # Imported to access direct streaming capabilities
from koil import unkoil
from rath.scalars import ID
from zarr.storage import StorePath

from mikro.api.schema import (
    BigFileAccessGrant,
    ParquetAccessGrant,
    ZarrAccessGrant,
)
from mikro.io.obstore import (
    ParquetDatasetViaObstore,
    create_s3_store,
    create_zarr_store_path,
)

if TYPE_CHECKING:
    from duckdb import DuckDBPyConnection, DuckDBPyRelation

    from mikro.mikro import Mikro


async def aget_zarr_credentials_and_endpoint(
    mikro: "Mikro", store: str
) -> tuple[ZarrAccessGrant, str]:
    """Fetch zarr access credentials and the datalayer endpoint URL."""
    credentials = await mikro.arequest_zarr_access(ID.validate(store))
    return credentials, await mikro.datalayer.get_endpoint_url()


async def aget_table_credentials_and_endpoint(
    mikro: "Mikro", store: str
) -> tuple[ParquetAccessGrant, str]:
    """Fetch parquet access credentials and the datalayer endpoint URL."""
    credentials = await mikro.arequest_parquet_access(ID.validate(store))
    return credentials, await mikro.datalayer.get_endpoint_url()


async def aget_bigfile_credentials_and_endpoint(
    mikro: "Mikro", store: str
) -> tuple[BigFileAccessGrant, str]:
    """Fetch big-file access credentials and the datalayer endpoint URL."""
    credentials = await mikro.arequest_bigfile_access(ID.validate(store))
    return credentials, await mikro.datalayer.get_endpoint_url()


async def aopen_zarr_store(mikro: "Mikro", store_id: str, cache: int = 2**30) -> StorePath:
    """Open a zarr store for the given store ID asynchronously."""
    credentials, endpoint_url = await aget_zarr_credentials_and_endpoint(mikro, store_id)
    return create_zarr_store_path(endpoint_url, credentials)


def open_zarr_store(mikro: "Mikro", store_id: str, cache: int = 2**30) -> StorePath:
    """Open a zarr store for the given store ID synchronously."""
    credentials, endpoint_url = unkoil(aget_zarr_credentials_and_endpoint, mikro, store_id)
    return create_zarr_store_path(endpoint_url, credentials)


def _require_pyarrow() -> None:
    try:
        import pyarrow.parquet as pq  # type: ignore # noqa: F401
    except ImportError as e:
        raise ImportError("You need to install pyarrow to use this function") from e


async def aopen_parquet_filesytem(mikro: "Mikro", store_id: str) -> ParquetDatasetViaObstore:
    """Open a parquet dataset for the given store ID asynchronously."""
    _require_pyarrow()
    credentials, endpoint_url = await aget_table_credentials_and_endpoint(mikro, store_id)
    return ParquetDatasetViaObstore(
        create_s3_store(endpoint_url, credentials), credentials.key
    )


def open_parquet_filesystem(mikro: "Mikro", store_id: str) -> ParquetDatasetViaObstore:
    """Open a parquet dataset for the given store ID synchronously."""
    _require_pyarrow()
    credentials, endpoint_url = unkoil(aget_table_credentials_and_endpoint, mikro, store_id)
    return ParquetDatasetViaObstore(
        create_s3_store(endpoint_url, credentials), credentials.key
    )


async def aopen_parquet_duckdb(
    mikro: "Mikro", store_id: str
) -> tuple["DuckDBPyConnection", "DuckDBPyRelation"]:
    """Open a lazy DuckDB relation over the parquet object asynchronously.

    Returns ``(connection, relation)``. The connection is returned alongside the
    relation because the relation is only valid while its connection is alive, so
    the caller must keep a reference to it.
    """
    from mikro.io.duckdb_io import (
        create_duckdb_s3_connection,
        read_parquet_relation,
    )

    credentials, endpoint_url = await aget_table_credentials_and_endpoint(mikro, store_id)
    con = create_duckdb_s3_connection(endpoint_url, credentials)
    relation = read_parquet_relation(con, credentials.bucket, credentials.key)
    return con, relation


def open_parquet_duckdb(
    mikro: "Mikro", store_id: str
) -> tuple["DuckDBPyConnection", "DuckDBPyRelation"]:
    """Open a lazy DuckDB relation over the parquet object synchronously.

    Returns ``(connection, relation)``; keep a reference to the connection for as
    long as the relation is used (the relation is bound to it).
    """
    return unkoil(aopen_parquet_duckdb, mikro, store_id)


def _ensure_parent_directory(file_name: str) -> None:
    """Create parent directories for file_name if they do not exist."""
    parent = Path(file_name).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


async def adownload_presigned_file(
    mikro: "Mikro", presigned_url: str, file_name: str
) -> str:
    """Download a file from a presigned URL (a path on ``mikro``'s datalayer).

    Returns:
        The local path where the file was saved.
    """
    endpoint_url = await mikro.datalayer.get_endpoint_url()
    _ensure_parent_directory(file_name)

    # Stream the file in 1 MiB chunks to avoid per-read syscall overhead.
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint_url + presigned_url) as response:
            response.raise_for_status()
            with open(file_name, "wb") as file:
                while True:
                    chunk = await response.content.read(1024 * 1024)
                    if not chunk:
                        break
                    file.write(chunk)

    return file_name


def download_presigned_file(mikro: "Mikro", presigned_url: str, file_name: str) -> str:
    """Download a file from a presigned URL synchronously (see the async twin)."""
    return unkoil(adownload_presigned_file, mikro, presigned_url, file_name)


async def adownload_file(mikro: "Mikro", store_id: str, file_name: str) -> str:
    """Download a big file from the store and save it to ``file_name``.

    Returns:
        The local path where the file was saved.
    """
    credentials, endpoint_url = await aget_bigfile_credentials_and_endpoint(mikro, store_id)

    _ensure_parent_directory(file_name)
    store = create_s3_store(endpoint_url, credentials)

    # Stream the file asynchronously directly into the file object
    response = await obstore.get_async(store, credentials.key)
    with open(file_name, "wb") as file:
        async for chunk in response.stream():
            file.write(chunk)

    return file_name


def download_file(mikro: "Mikro", store_id: str, file_name: str) -> str:
    """Download a big file from the store synchronously (see the async twin)."""
    credentials, endpoint_url = unkoil(aget_bigfile_credentials_and_endpoint, mikro, store_id)

    _ensure_parent_directory(file_name)
    store = create_s3_store(endpoint_url, credentials)

    # Stream the file synchronously directly into the file object
    response = obstore.get(store, credentials.key)
    with open(file_name, "wb") as file:
        file.writelines(response.stream())

    return file_name
