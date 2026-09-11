"""Module for uploading various data types to a DataLayer.

Provides both async and sync upload paths via obstore:
    - Async: aupload_xarray, aupload_parquet, aupload_bigfile, astore_media_file,
      astore_fabriks_collection
    - Sync: upload_xarray, upload_parquet, upload_bigfile, store_media_file,
      store_fabriks_collection
"""

import asyncio
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import obstore

from mikro_next.compression import DEFAULT_COMPRESSION
from mikro_next.scalars import (
    ArrayLike,
    FabriksLike,
    KonnektionLike,
    FileLike,
    ImageFileLike,
    ParquetLike,
    SporadikLike,
)

from .errors import UploadError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mikro_next.api.schema import (
        BigFileUploadGrant,
        FabriksUploadGrant,
        KonnektionUploadGrant,
        MediaUploadGrant,
        ParquetUploadGrant,
        SparseUploadGrant,
        ZarrUploadGrant,
    )
    from mikro_next.datalayer import DataLayer


# ========================================================================
# Async upload functions (obstore)
# ========================================================================


async def astore_xarray_input(
    xarray: ArrayLike,
    credentials: "ZarrUploadGrant",
    endpoint_url: str,
) -> str:
    """Stores an xarray in the DataLayer"""
    from mikro_next.io.obstore import awrite_dataarray_to_zarr, create_zarr_store_path

    array = xarray.value
    store_path = create_zarr_store_path(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading zarr t to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        await awrite_dataarray_to_zarr(store_path, array)
        logger.info(
            f"Successfully uploaded zarr to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )

        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def _parquet_payload(value: object) -> "tuple[object, Path | None]":
    """What to hand ``obstore.put``, and the scratch file to delete afterwards.

    Four inputs, three shapes of answer (see :class:`mikro_next.scalars.ParquetLike`):

    - a ``Path`` is already a parquet file, so it goes to obstore as-is — obstore reads
      it in chunks and multipart-uploads it, so a 4 GB table never enters this process;
    - a ``RecordBatchReader`` is written batch by batch to a scratch file and then
      streamed, which is the whole point of accepting one: peak memory is a batch;
    - a ``Table`` is serialized to that same scratch file rather than to a ``BytesIO``,
      because it is already the largest object in the process and a second full copy of
      it is the thing worth avoiding;
    - a ``DataFrame`` keeps the original in-memory path exactly. It is the small case,
      and routing it through a temp file would make every existing caller depend on
      writable scratch space for no gain.

    Returns:
        ``(payload, scratch)`` — ``scratch`` is None when nothing needs cleaning up.
    """
    import pyarrow.parquet as pq  # type: ignore
    from pyarrow import RecordBatchReader, Table  # type: ignore

    if isinstance(value, Path):
        return value, None

    if isinstance(value, (Table, RecordBatchReader)):
        handle, name = tempfile.mkstemp(suffix=".parquet", prefix="mikro-parquet-")
        os.close(handle)
        scratch = Path(name)
        try:
            if isinstance(value, Table):
                pq.write_table(value, scratch, compression=DEFAULT_COMPRESSION)
            else:
                with pq.ParquetWriter(scratch, value.schema, compression=DEFAULT_COMPRESSION) as writer:
                    for batch in value:
                        writer.write_batch(batch)
        except BaseException:
            # A half-written scratch file is not a parquet file, and leaving it behind
            # would be a silent disk leak on every failed upload.
            scratch.unlink(missing_ok=True)
            raise
        return scratch, scratch

    table = Table.from_pandas(value)  # type: ignore
    buffer = BytesIO()
    pq.write_table(table, buffer, compression=DEFAULT_COMPRESSION)
    buffer.seek(0)
    return buffer, None


def _store_parquet_input(
    parquet_input: ParquetLike,
    credentials: "ParquetUploadGrant",
    endpoint_url: str,
) -> str:
    """Store a parquet table in the DataLayer via obstore."""
    from mikro_next.io.obstore import create_s3_store

    store = create_s3_store(endpoint_url, credentials)

    payload, scratch = _parquet_payload(parquet_input.value)

    s3_path = f"s3://{credentials.bucket}/{credentials.key}"
    try:
        logger.debug(
            f"Uploading parquet to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        obstore.put(store, credentials.key, payload)
        logger.info(
            f"Successfully uploaded parquet to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(f"Error while uploading to {s3_path}") from e
    finally:
        if scratch is not None:
            scratch.unlink(missing_ok=True)


async def astore_sparse_matrix(
    sparse: SporadikLike,
    credentials: "SparseUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Write a sparse matrix into the granted prefix as one store, and return its store id.

    One prefix per matrix, holding one or both layouts under ``layouts/<encoding>`` in the
    spelling anndata uses -- so the server reads the encoding, the shape and the chunking back
    off the artifact and ``createSparseDataset`` declares none of them.

    Rooted at ``grant.key`` with the group at the store's root, for the reason
    :func:`create_zarr_store_path` gives: zarr walks a node's parents to create intermediate
    groups, and the parent of a bucket-rooted ``grant.key`` is the bucket root, which a
    prefix-scoped grant denies with a 403.

    The chunking is chosen here rather than by the caller, and it is the one number that decides
    what a read costs: `indptr` names exactly which bytes a lookup wants, and a chunk is the
    granularity at which they can be fetched, so the two have to agree. See
    :data:`sporadik.DEFAULT_CHUNK` for the measurement.
    """
    return _store_sparse_into_grant(sparse, credentials, await datalayer.get_endpoint_url())


def store_sparse_matrix(
    sparse: SporadikLike,
    credentials: "SparseUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Write a sparse matrix into the granted prefix synchronously.

    The same write as :func:`astore_sparse_matrix` -- zarr's obstore path is synchronous either
    way -- so the two differ only in how they reach the endpoint url.
    """
    return _store_sparse_into_grant(sparse, credentials, datalayer.endpoint_url)


def _store_sparse_into_grant(
    sparse: SporadikLike,
    credentials: "SparseUploadGrant",
    endpoint_url: str,
) -> str:
    """The write itself, shared by both paths.

    The block `sporadik.write_store_into` lands last is what makes an interrupted upload
    detectable: everything written before it declares something before it is true, because zarr
    writes an array's metadata ahead of its chunks and substitutes the fill value for a chunk it
    cannot fetch. A prefix that got this far and no further reads back as zeros, silently, which
    is the failure the block exists to convert into a refusal.
    """
    import zarr

    from mikro_next.io.obstore import create_zarr_store_path
    from mikro_next.scalars import _sporadik

    write_store_into = _sporadik().write_store_into

    layouts = sparse.layouts
    shape = tuple(next(iter(layouts.values())).shape)
    nnz = sum(len(layout.data) for layout in layouts.values())
    store_path = create_zarr_store_path(endpoint_url, credentials)

    try:
        logger.debug(f"Uploading sparse matrix to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}...")
        group = zarr.open_group(store=store_path, mode="w")
        write_store_into(group, list(layouts.values()))
        logger.info(
            f"Successfully uploaded a matrix of shape {shape}, compressed along "
            f"{'+'.join(f'axis{axis}' for axis in sorted(layouts))} "
            f"({nnz} nonzero across {len(layouts)} layout(s)) to s3://{credentials.bucket}/{credentials.key}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def astore_fabriks_collection(
    collection: FabriksLike,
    credentials: "FabriksUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Write a fabriks collection into the granted prefix, and return the store it landed in.

    A whole tree rather than one object -- ``fabriks.json``, both catalogs and a part file per
    octree level -- which is why the grant covers a prefix and permits reading and deleting
    inside it. The ordering is fabriks's and is load-bearing: every file the manifest names is
    written before the manifest is, so a prefix without one is an interrupted write rather than
    a collection. ``finishFabriksUpload`` is the other half of that protocol -- it reads the
    manifest and refuses a prefix that has none -- so nothing here retries or reorders the
    write; the writer owns it.

    ``awrite_collection`` does the whole write in a worker thread, since Parquet serialization
    is CPU-bound and obstore's ``put`` releases the GIL -- which also keeps the manifest-last
    ordering trivially true rather than a scheduling question.
    """
    from fabriks import awrite_collection

    from mikro_next.io.obstore import create_s3_store
    from mikro_next.meshes import refuse_an_unreadable_part_codec

    endpoint_url = await datalayer.get_endpoint_url()
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading fabriks collection to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        refuse_an_unreadable_part_codec()
        manifest = await awrite_collection(collection.value, store, credentials.key)
        logger.info(
            f"Successfully uploaded fabriks collection to s3://{credentials.bucket}/{credentials.key} "
            f"at {endpoint_url} ({manifest.counts})"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def astore_media_file(
    file: ImageFileLike,
    credentials: "MediaUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Store a media file in the DataLayer asynchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    endpoint_url = await datalayer.get_endpoint_url()
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        await obstore.put_async(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def aupload_bigfile(
    file: FileLike | ImageFileLike,
    credentials: "BigFileUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Upload a big file to the DataLayer asynchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    endpoint_url = await datalayer.get_endpoint_url()
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        await obstore.put_async(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def aupload_xarray(
    array: ArrayLike,
    credentials: "ZarrUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Upload an xarray to the DataLayer asynchronously via obstore."""
    return await astore_xarray_input(array, credentials, await datalayer.get_endpoint_url())


async def aupload_parquet(
    parquet: ParquetLike,
    credentials: "ParquetUploadGrant",
    datalayer: "DataLayer",
    executor: ThreadPoolExecutor,
) -> str:
    """Upload a parquet table to the DataLayer asynchronously via a thread executor."""
    co_future = executor.submit(
        _store_parquet_input, parquet, credentials, await datalayer.get_endpoint_url()
    )
    return await asyncio.wrap_future(co_future)


# ========================================================================
# Sync upload functions (obstore)
# ========================================================================


def _store_xarray_via_obstore(
    xarray: ArrayLike,
    credentials: "ZarrUploadGrant",
    endpoint_url: str,
) -> str:
    """Stores an xarray in the DataLayer synchronously via obstore/zarr."""
    from mikro_next.io.obstore import create_zarr_store_path, write_dataarray_to_zarr

    store_path = create_zarr_store_path(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading zarr (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        write_dataarray_to_zarr(store_path, xarray.value)
        logger.info(
            f"Successfully uploaded zarr (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def _store_bigfile_via_obstore(
    file: FileLike | ImageFileLike,
    credentials: "BigFileUploadGrant",
    endpoint_url: str,
) -> str:
    """Store a big file in the DataLayer synchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        obstore.put(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def _store_media_file_via_obstore(
    file: ImageFileLike,
    credentials: "MediaUploadGrant",
    endpoint_url: str,
) -> str:
    """Store a media file in the DataLayer synchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading media file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        obstore.put(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded media file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def astore_konnektion_collection(
    collection: KonnektionLike,
    credentials: "KonnektionUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Write a konnektion collection into the granted prefix, and return the store it landed in.

    A whole tree rather than one object -- ``konnektion.json``, both catalogs and a part file per
    octree level -- which is why the grant covers a prefix and permits reading and deleting
    inside it. The ordering is konnektion's and is load-bearing: every file the manifest names is
    written before the manifest is, so a prefix without one is an interrupted write rather than
    a collection. ``finishKonnektionUpload`` is the other half of that protocol -- it reads the
    manifest and refuses a prefix that has none -- so nothing here retries or reorders the
    write; the writer owns it.

    ``awrite_collection`` does the whole write in a worker thread, since Parquet serialization
    is CPU-bound and obstore's ``put`` releases the GIL -- which also keeps the manifest-last
    ordering trivially true rather than a scheduling question.
    """
    from konnektion import awrite_collection

    from mikro_next.io.obstore import create_s3_store
    from mikro_next.networks import refuse_an_unreadable_part_codec

    endpoint_url = await datalayer.get_endpoint_url()
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading konnektion collection to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        refuse_an_unreadable_part_codec()
        manifest = await awrite_collection(collection.value, store, credentials.key)
        logger.info(
            f"Successfully uploaded konnektion collection to s3://{credentials.bucket}/{credentials.key} "
            f"at {endpoint_url} ({manifest.counts})"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def astore_media_file(
    file: ImageFileLike,
    credentials: "MediaUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Store a media file in the DataLayer asynchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    endpoint_url = await datalayer.get_endpoint_url()
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        await obstore.put_async(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def aupload_bigfile(
    file: FileLike | ImageFileLike,
    credentials: "BigFileUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Upload a big file to the DataLayer asynchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    endpoint_url = await datalayer.get_endpoint_url()
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        await obstore.put_async(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded file to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


async def aupload_xarray(
    array: ArrayLike,
    credentials: "ZarrUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Upload an xarray to the DataLayer asynchronously via obstore."""
    return await astore_xarray_input(array, credentials, await datalayer.get_endpoint_url())


async def aupload_parquet(
    parquet: ParquetLike,
    credentials: "ParquetUploadGrant",
    datalayer: "DataLayer",
    executor: ThreadPoolExecutor,
) -> str:
    """Upload a parquet table to the DataLayer asynchronously via a thread executor."""
    co_future = executor.submit(
        _store_parquet_input, parquet, credentials, await datalayer.get_endpoint_url()
    )
    return await asyncio.wrap_future(co_future)


# ========================================================================
# Sync upload functions (obstore)
# ========================================================================


def _store_xarray_via_obstore(
    xarray: ArrayLike,
    credentials: "ZarrUploadGrant",
    endpoint_url: str,
) -> str:
    """Stores an xarray in the DataLayer synchronously via obstore/zarr."""
    from mikro_next.io.obstore import create_zarr_store_path, write_dataarray_to_zarr

    store_path = create_zarr_store_path(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading zarr (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        write_dataarray_to_zarr(store_path, xarray.value)
        logger.info(
            f"Successfully uploaded zarr (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def _store_bigfile_via_obstore(
    file: FileLike | ImageFileLike,
    credentials: "BigFileUploadGrant",
    endpoint_url: str,
) -> str:
    """Store a big file in the DataLayer synchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        obstore.put(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def _store_media_file_via_obstore(
    file: ImageFileLike,
    credentials: "MediaUploadGrant",
    endpoint_url: str,
) -> str:
    """Store a media file in the DataLayer synchronously via obstore."""
    from mikro_next.io.obstore import create_s3_store

    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading media file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        obstore.put(store, credentials.key, file.value)
        logger.info(
            f"Successfully uploaded media file (sync/obstore) to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def store_fabriks_collection(
    collection: FabriksLike,
    credentials: "FabriksUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Write a fabriks collection into the granted prefix synchronously.

    The same write as :func:`astore_fabriks_collection` -- fabriks's writer is synchronous and the
    async path is it in a worker thread -- so this is the writer itself rather than a second
    implementation of it.
    """
    from fabriks import write_collection

    from mikro_next.io.obstore import create_s3_store
    from mikro_next.meshes import refuse_an_unreadable_part_codec

    endpoint_url = datalayer.endpoint_url
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading fabriks collection to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        refuse_an_unreadable_part_codec()
        manifest = write_collection(collection.value, store, credentials.key)
        logger.info(
            f"Successfully uploaded fabriks collection to s3://{credentials.bucket}/{credentials.key} "
            f"at {endpoint_url} ({manifest.counts})"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def store_konnektion_collection(
    collection: KonnektionLike,
    credentials: "KonnektionUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Write a konnektion collection into the granted prefix synchronously.

    The same write as :func:`astore_konnektion_collection` -- konnektion's writer is synchronous and the
    async path is it in a worker thread -- so this is the writer itself rather than a second
    implementation of it.
    """
    from konnektion import write_collection

    from mikro_next.io.obstore import create_s3_store
    from mikro_next.networks import refuse_an_unreadable_part_codec

    endpoint_url = datalayer.endpoint_url
    store = create_s3_store(endpoint_url, credentials)

    try:
        logger.debug(
            f"Uploading konnektion collection to s3://{credentials.bucket}/{credentials.key} at {endpoint_url}..."
        )
        refuse_an_unreadable_part_codec()
        manifest = write_collection(collection.value, store, credentials.key)
        logger.info(
            f"Successfully uploaded konnektion collection to s3://{credentials.bucket}/{credentials.key} "
            f"at {endpoint_url} ({manifest.counts})"
        )
        return credentials.store
    except Exception as e:
        raise UploadError(
            f"Error while uploading to s3://{credentials.bucket}/{credentials.key} on {endpoint_url}"
        ) from e


def upload_xarray(
    array: ArrayLike,
    credentials: "ZarrUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Upload an xarray synchronously via obstore."""
    return _store_xarray_via_obstore(array, credentials, datalayer.endpoint_url)


def upload_parquet(
    parquet: ParquetLike,
    credentials: "ParquetUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Upload a parquet file synchronously."""
    return _store_parquet_input(parquet, credentials, datalayer.endpoint_url)


def upload_bigfile(
    file: FileLike | ImageFileLike,
    credentials: "BigFileUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Upload a big file synchronously via obstore."""
    return _store_bigfile_via_obstore(file, credentials, datalayer.endpoint_url)


def store_media_file(
    file: ImageFileLike,
    credentials: "MediaUploadGrant",
    datalayer: "DataLayer",
) -> str:
    """Store a media file synchronously via obstore."""
    return _store_media_file_via_obstore(file, credentials, datalayer.endpoint_url)
