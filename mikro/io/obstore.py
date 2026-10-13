"""Helpers for reading and writing Mikro S3 objects via obstore."""

import asyncio
import math
import os
from io import BytesIO
from typing import TYPE_CHECKING, Protocol

import numpy as np
import obstore
import xarray as xr
import zarr
from obstore.store import ObjectStore as ObstoreObjectStore
from obstore.store import S3Store
from zarr.storage import ObjectStore as ZarrObjectStore
from zarr.storage import StorePath

from mikro.scalars import is_dask_array
from mikro.io.chunking import ChunkLayout, chunk_layout, roles_for

if TYPE_CHECKING:
    from obstore.store import ClientConfig, RetryConfig
    from pyarrow import Table  # type: ignore

    from mikro.datalayer import DataLayer


class S3UploadGrantLike(Protocol):
    """Protocol for grants that carry S3 credentials and object coordinates."""

    @property
    def access_key(self) -> str: ...  # noqa: D102

    @property
    def secret_key(self) -> str: ...  # noqa: D102

    @property
    def session_token(self) -> str: ...  # noqa: D102

    @property
    def bucket(self) -> str: ...  # noqa: D102

    @property
    def key(self) -> str: ...  # noqa: D102


def create_s3_store(
    endpoint_url: str,
    grant: "S3UploadGrantLike",
    client_options: "ClientConfig | None" = None,
    retry_config: "RetryConfig | None" = None,
    prefix: str | None = None,
    *,
    proxy: str | None = None,
) -> S3Store:
    """Create an obstore S3 client from a Mikro grant and endpoint.

    ``prefix`` roots the store inside the bucket, so every key the caller passes is
    relative to it. Zarr needs this (see :func:`create_zarr_store_path`); the
    single-object paths address their key directly and leave it unset.

    ``proxy`` is the HTTP forward proxy the datalayer is only reachable through
    (see :attr:`DataLayer.proxy`). It is merged into the client options, never
    replacing them -- dropping ``allow_http`` would break every ``http://`` store.
    """
    normalized_client_options: dict[str, object] = dict(client_options or {})
    if endpoint_url.startswith("http://"):
        normalized_client_options.setdefault("allow_http", True)
    if proxy:
        normalized_client_options["proxy_url"] = proxy

    store_kwargs: dict[str, object] = {
        "access_key_id": grant.access_key,
        "secret_access_key": grant.secret_key,
        "endpoint": endpoint_url,
        "virtual_hosted_style_request": False,
        "client_options": normalized_client_options or None,
        "retry_config": retry_config,
    }
    if grant.session_token:
        store_kwargs["session_token"] = grant.session_token
    if prefix:
        store_kwargs["prefix"] = prefix

    return S3Store(
        grant.bucket,
        **store_kwargs,
    )


def create_zarr_store_path(
    endpoint_url: str, grant: "S3UploadGrantLike", *, proxy: str | None = None
) -> StorePath:
    """Create a Zarr store path rooted at the granted S3 prefix.

    The store is rooted at ``grant.key`` and the node sits at the store's root, rather
    than the store being rooted at the bucket with the node at ``grant.key``. The two
    write identical objects, but only this one stays inside the grant: zarr's
    ``init_array`` walks a node's parents to create intermediate groups, and the parent
    of ``grant.key`` in a bucket-rooted store is the *bucket root* -- so that shape
    reads and writes ``<bucket>/zarr.json``, which a prefix-scoped STS grant denies with
    a 403. A node at the root has no parents to walk.
    """
    zarr_store = ZarrObjectStore(
        create_s3_store(endpoint_url, grant, prefix=grant.key, proxy=proxy)
    )
    return StorePath(zarr_store, "")


async def acreate_s3_store(
    grant: "S3UploadGrantLike",
    datalayer: "DataLayer",
    client_options: "ClientConfig | None" = None,
    retry_config: "RetryConfig | None" = None,
) -> S3Store:
    """Create an obstore S3 client asynchronously using the active datalayer."""
    endpoint_url = await datalayer.get_endpoint_url()

    return create_s3_store(
        endpoint_url,
        grant,
        client_options=client_options,
        retry_config=retry_config,
        proxy=datalayer.proxy,
    )


#: How many uncompressed bytes of shards may be in flight at once. A shard is built whole in
#: memory -- the block, its encoded chunks, and the combined object -- so the thread count,
#: not the array, is what bounds a write.
WRITE_BUFFER_BYTES = 1024**3


def _write_workers(layout: ChunkLayout, itemsize: int) -> int:
    """Threads to store with, so in-flight shards stay inside :data:`WRITE_BUFFER_BYTES`."""
    block_bytes = itemsize * math.prod(layout.shards or layout.chunks)
    return max(1, min(os.cpu_count() or 1, WRITE_BUFFER_BYTES // (3 * block_bytes)))


def write_dataarray_to_zarr(
    store_path: StorePath,
    array: xr.DataArray,
    *,
    layout: ChunkLayout | None = None,
) -> None:
    """Write a DataArray to a zarr v3 array synchronously.

    Without a ``layout`` the array is chunked by the bare-name convention of its dimensions
    (see :func:`mikro.io.chunking.roles_for`); a dataset declaration knows the axis types and
    the rest of the pyramid, and passes the layout it chose. The default codecs are kept
    deliberately: zarr's stock sharded layout (sole top-level ``sharding_indexed``, declared
    crc32c index codecs) is exactly what the platform's readers require.

    Dask-backed arrays are streamed via ``dask.array.store`` so the full array is
    never materialised in memory; numpy arrays are written directly.
    """
    dims = [str(dim) for dim in array.dims]
    if layout is None:
        layout = chunk_layout(array.shape, roles_for(dims), array.dtype.itemsize)
    elif len(layout.chunks) != array.ndim:
        raise ValueError(
            f"layout chunks {layout.chunks} do not have the array's {array.ndim} dimensions {dims}."
        )
    zarr_array = zarr.create_array(
        store_path,
        shape=array.shape,
        chunks=layout.chunks,
        shards=layout.shards,
        dtype=array.dtype,
        dimension_names=dims,
        zarr_format=3,
        overwrite=True,
    )
    data = array.data
    if is_dask_array(data):
        from dask.array.core import store as dask_store

        # Align dask blocks to the *storage object* grid — the shard when sharding,
        # else the chunk — so concurrent, lock-free writes never target the same
        # object from two blocks. A sub-shard write is a read-modify-write of the
        # whole shard, so two blocks in one shard would silently drop inner chunks.
        data = data.rechunk(layout.shards or layout.chunks)
        dask_store(
            data,
            zarr_array,
            lock=False,
            scheduler="threads",
            num_workers=_write_workers(layout, array.dtype.itemsize),
        )
    else:
        zarr_array[...] = np.asarray(data)


async def awrite_dataarray_to_zarr(
    store_path: StorePath,
    array: xr.DataArray,
    *,
    layout: ChunkLayout | None = None,
) -> None:
    """Write a DataArray to a zarr v3 array without blocking the event loop.

    Delegates to the synchronous streaming writer in a worker thread so that
    dask-backed arrays are streamed to zarr chunk-by-chunk (via ``dask.array.store``)
    and are never fully materialised in memory. ``dask.array.store`` runs the dask
    scheduler synchronously, so it must not be awaited directly on the event loop.
    """
    await asyncio.to_thread(write_dataarray_to_zarr, store_path, array, layout=layout)


async def awrite_xarray_to_obstore(
    da: xr.DataArray,
    grant: "S3UploadGrantLike",
    datalayer: "DataLayer",
) -> None:
    """
    Asynchronously write an xarray dataset to S3 via obstore and Zarr.
    """
    store_path = create_zarr_store_path(
        await datalayer.get_endpoint_url(), grant, proxy=datalayer.proxy
    )
    await awrite_dataarray_to_zarr(store_path, da)


def get_bytes(store: ObstoreObjectStore, path: str) -> bytes:
    """Read an object fully into memory."""
    return bytes(obstore.get(store, path).bytes())


async def aget_bytes(store: ObstoreObjectStore, path: str) -> bytes:
    """Read an object fully into memory asynchronously."""
    return bytes((await obstore.get_async(store, path)).bytes())


class ParquetDatasetViaObstore:
    """Minimal parquet dataset adapter backed by obstore."""

    def __init__(self, store: ObstoreObjectStore, path: str) -> None:
        """Bind a parquet object path to a concrete obstore-backed S3 client."""
        self.store = store
        self.path = path

    def read_pandas(self) -> "Table":
        """Read the parquet object into a pyarrow table."""
        import pyarrow.parquet as pq  # type: ignore

        return pq.read_table(BytesIO(get_bytes(self.store, self.path)))
