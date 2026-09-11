from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import obstore  # Imported to access direct streaming capabilities
from koil import unkoil
from rath.scalars import ID
from zarr.storage import StorePath

from mikro_next.api.schema import (
    BigFileAccessGrant,
    ParquetAccessGrant,
    ZarrAccessGrant,
    arequest_bigfile_access,
    arequest_parquet_access,
    arequest_zarr_access,
)
from mikro_next.datalayer import DataLayer, current_next_datalayer
from mikro_next.io.obstore import (
    ParquetDatasetViaObstore,
    create_s3_store,
    create_zarr_store_path,
)

if TYPE_CHECKING:
    from duckdb import DuckDBPyConnection, DuckDBPyRelation


async def aget_zarr_credentials_and_endpoint(
    store: str,
) -> tuple[ZarrAccessGrant, str]:
    """Fetch zarr access credentials and the datalayer endpoint URL."""
    datalayer = current_next_datalayer.get()
    if not datalayer:
        raise ValueError("Datalayer is not set")
    credentials = await arequest_zarr_access(ID.validate(store))

    endpoint_url = await datalayer.get_endpoint_url()
    return credentials, endpoint_url


async def aget_table_credentials_and_endpoint(
    store: str,
) -> tuple[ParquetAccessGrant, str]:
    """Fetch parquet access credentials and the datalayer endpoint URL."""
    datalayer = current_next_datalayer.get()
    if not datalayer:
        raise ValueError("Datalayer is not set")

    credentials = await arequest_parquet_access(ID.validate(store))
    endpoint_url = await datalayer.get_endpoint_url()
    return credentials, endpoint_url


async def aget_bigfile_credentials_and_endpoint(
    store: str,
) -> tuple[BigFileAccessGrant, str]:
    """Fetch big-file access credentials and the datalayer endpoint URL."""
    datalayer = current_next_datalayer.get()
    if not datalayer:
        raise ValueError("Datalayer is not set")

    credentials = await arequest_bigfile_access(ID.validate(store))
    endpoint_url = await datalayer.get_endpoint_url()
    return credentials, endpoint_url


async def aopen_zarr_store(store_id: str, cache: int = 2**30) -> StorePath:
    """Open a zarr store for the given store ID asynchronously."""
    credentials, endpoint_url = await aget_zarr_credentials_and_endpoint(store_id)
    return create_zarr_store_path(endpoint_url, credentials)


def open_zarr_store(store_id: str, cache: int = 2**30) -> StorePath:
    """Open a zarr store for the given store ID synchronously."""
    credentials, endpoint_url = unkoil(aget_zarr_credentials_and_endpoint, store_id)
    return create_zarr_store_path(endpoint_url, credentials)


async def aopen_parquet_filesytem(store_id: str) -> ParquetDatasetViaObstore:
    """Open a parquet dataset for the given store ID asynchronously."""
    try:
        import pyarrow.parquet as pq  # type: ignore # noqa: F401
    except ImportError as e:
        raise ImportError("You need to install pyarrow to use this function") from e
    credentials, endpoint_url = await aget_table_credentials_and_endpoint(store_id)
    return ParquetDatasetViaObstore(
        create_s3_store(endpoint_url, credentials), credentials.key
    )


def open_parquet_filesystem(store_id: str) -> ParquetDatasetViaObstore:
    """Open a parquet dataset for the given store ID synchronously."""
    try:
        import pyarrow.parquet as pq  # type: ignore # noqa: F401
    except ImportError as e:
        raise ImportError("You need to install pyarrow to use this function") from e
    credentials, endpoint_url = unkoil(aget_table_credentials_and_endpoint, store_id)
    return ParquetDatasetViaObstore(
        create_s3_store(endpoint_url, credentials), credentials.key
    )


async def aopen_parquet_duckdb(
    store_id: str,
) -> tuple["DuckDBPyConnection", "DuckDBPyRelation"]:
    """Open a lazy DuckDB relation over the parquet object asynchronously.

    Returns ``(connection, relation)``. The connection is returned alongside the
    relation because the relation is only valid while its connection is alive, so
    the caller must keep a reference to it.
    """
    from mikro_next.io.duckdb_io import (
        create_duckdb_s3_connection,
        read_parquet_relation,
    )

    credentials, endpoint_url = await aget_table_credentials_and_endpoint(store_id)
    con = create_duckdb_s3_connection(endpoint_url, credentials)
    relation = read_parquet_relation(con, credentials.bucket, credentials.key)
    return con, relation


def open_parquet_duckdb(
    store_id: str,
) -> tuple["DuckDBPyConnection", "DuckDBPyRelation"]:
    """Open a lazy DuckDB relation over the parquet object synchronously.

    Returns ``(connection, relation)``; keep a reference to the connection for as
    long as the relation is used (the relation is bound to it).
    """
    return unkoil(aopen_parquet_duckdb, store_id)


def _ensure_parent_directory(file_name: str) -> None:
    """Create parent directories for file_name if they do not exist."""
    parent = Path(file_name).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


async def adownload_presigned_file(
    presigned_url: str,
    file_name: str,
    datalayer: DataLayer | None = None,
) -> str:
    """Download a file from a presigned URL and save it to file_name asynchronously.

    Args:
        presigned_url: The presigned URL path (appended to the endpoint URL).
        file_name: Local path to write the downloaded file to.
        datalayer: Optional DataLayer override; falls back to the active context instance.

    Returns:
        The local path where the file was saved.
    """
    datalayer = datalayer or current_next_datalayer.get()
    if not datalayer:
        raise ValueError("Datalayer is not set")

    endpoint_url = await datalayer.get_endpoint_url()
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


def download_presigned_file(
    presigned_url: str, file_name: str, datalayer: DataLayer | None = None
) -> str:
    """Download a file from a presigned URL and save it to file_name synchronously.

    Args:
        presigned_url: The presigned URL path (appended to the endpoint URL).
        file_name: Local path to write the downloaded file to.
        datalayer: Optional DataLayer override; falls back to the active context instance.

    Returns:
        The local path where the file was saved.
    """
    return unkoil(
        adownload_presigned_file,
        presigned_url,
        file_name=file_name,
        datalayer=datalayer,
    )


async def adownload_file(
    store_id: str,
    file_name: str,
    datalayer: DataLayer | None = None,
) -> str:
    """Download a big file from the store and save it to file_name asynchronously.

    Args:
        store_id: The ID of the big-file store to download from.
        file_name: Local path to write the downloaded file to.
        datalayer: Optional DataLayer override; uses the active context instance otherwise.

    Returns:
        The local path where the file was saved.
    """
    if datalayer is not None:
        token = current_next_datalayer.set(datalayer)
    else:
        token = None

    try:
        credentials, endpoint_url = await aget_bigfile_credentials_and_endpoint(
            store_id
        )
    finally:
        if token is not None:
            current_next_datalayer.reset(token)

    _ensure_parent_directory(file_name)
    store = create_s3_store(endpoint_url, credentials)

    # Stream the file asynchronously directly into the file object
    response = await obstore.get_async(store, credentials.key)
    with open(file_name, "wb") as file:
        async for chunk in response.stream():
            file.write(chunk)

    return file_name


def download_file(store_id: str, file_name: str, datalayer: DataLayer | None = None) -> str:
    """Download a big file from the store and save it to file_name synchronously.

    Args:
        store_id: The ID of the big-file store to download from.
        file_name: Local path to write the downloaded file to.
        datalayer: Optional DataLayer override; uses the active context instance otherwise.

    Returns:
        The local path where the file was saved.
    """
    credentials, endpoint_url = unkoil(aget_bigfile_credentials_and_endpoint, store_id)

    _ensure_parent_directory(file_name)
    store = create_s3_store(endpoint_url, credentials)

    # Stream the file synchronously directly into the file object
    response = obstore.get(store, credentials.key)
    with open(file_name, "wb") as file:
        file.writelines(response.stream())

    return file_name
