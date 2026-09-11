"""Upload middleware for the funcs API.

This middleware intercepts serialized operation variables and uploads
uploadable types (ArrayLike, ParquetLike, SporadikLike, etc.) to the datalayer
*before* the operation reaches the rath link chain.

It provides both sync and async paths:
    - Sync (process_variables): Uses obstore for S3 uploads, called from execute().
    - Async (aprocess_variables): Uses obstore, called from aexecute().

Credential acquisition always goes through rath.query/aquery directly
(bypassing the middleware itself) to avoid infinite recursion.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING, Any

from koil import unkoil
from pydantic import ConfigDict, Field

from mikro_next.datalayer import DataLayer
from mikro_next.io.upload import (
    astore_fabriks_collection,
    astore_konnektion_collection,
    astore_media_file,
    astore_sparse_matrix,
    # Async paths (obstore)
    aupload_bigfile,
    aupload_parquet,
    aupload_xarray,
    store_fabriks_collection,
    store_konnektion_collection,
    store_media_file,
    store_sparse_matrix,
    upload_bigfile,
    upload_parquet,
    # Sync paths (obstore)
    upload_xarray,
)
from mikro_next.middleware.base import FuncsMiddleware
from mikro_next.scalars import (
    ArrayLike,
    FabriksLike,
    KonnektionLike,
    FileLike,
    ImageFileLike,
    ParquetLike,
    SporadikLike,
)

if TYPE_CHECKING:
    from mikro_next.api.schema import (
        BigFileUploadGrant,
        FabriksUploadGrant,
        MediaUploadGrant,
        ParquetUploadGrant,
        SparseUploadGrant,
        ZarrUploadGrant,
    )
    from mikro_next.rath import MikroNextRath

from rath.turms.funcs import TOperation

logger = logging.getLogger(__name__)


# ========================================================================
# Recursive applicators (async and sync)
# ========================================================================


async def _apply_recursive_async(
    func,  # noqa: ANN001
    obj: Any,  # noqa: ANN401
    typeguard: type[Any] | tuple[type[Any], ...],
) -> Any:  # noqa: ANN401
    """Recursively applies an async function to matching elements in a nested structure."""
    if isinstance(obj, dict):
        return {k: await _apply_recursive_async(func, v, typeguard) for k, v in obj.items()}
    elif isinstance(obj, list):
        return await asyncio.gather(
            *[_apply_recursive_async(func, elem, typeguard) for elem in obj]
        )
    elif isinstance(obj, tuple):
        return tuple(
            await asyncio.gather(*[_apply_recursive_async(func, elem, typeguard) for elem in obj])
        )
    elif isinstance(obj, typeguard):
        return await func(obj)
    else:
        return obj


def _apply_recursive_sync(
    func,  # noqa: ANN001
    obj: Any,  # noqa: ANN401
    typeguard: type[Any] | tuple[type[Any], ...],
) -> Any:  # noqa: ANN401
    """Recursively applies a sync function to matching elements in a nested structure."""
    if isinstance(obj, dict):
        return {k: _apply_recursive_sync(func, v, typeguard) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_apply_recursive_sync(func, elem, typeguard) for elem in obj]
    elif isinstance(obj, tuple):
        return tuple(_apply_recursive_sync(func, elem, typeguard) for elem in obj)
    elif isinstance(obj, typeguard):
        return func(obj)
    else:
        return obj


class UploadMiddleware(FuncsMiddleware):
    """Middleware that uploads supported data types to the datalayer.

    This middleware walks the serialized variables dict, finds instances of
    uploadable scalar types (ArrayLike, ParquetLike, FileLike, ImageFileLike,
    FabriksLike, SporadikLike), uploads them to S3, and replaces
    them with their store IDs.

    Provides two paths:
        - **Sync** (``process_variables``): Uses obstore for S3 operations.
          Called when the user invokes ``execute()`` / ``subscribe()``.
        - **Async** (``aprocess_variables``): Uses obstore.
          Called when the user invokes ``aexecute()`` / ``asubscribe()``.

    Args:
        datalayer: The DataLayer instance for S3 connectivity.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    datalayer: DataLayer

    executor: ThreadPoolExecutor = Field(
        default_factory=lambda: ThreadPoolExecutor(max_workers=4), exclude=True
    )
    _executor_session: Any = None
    _cached_datalayer_url: str | None = None

    async def aenter(self) -> None:
        """Enter the middleware context, initializing the thread pool."""
        self._executor_session = self.executor.__enter__()

    async def aexit(self) -> None:
        """Exit the middleware context, shutting down the thread pool."""
        self.executor.__exit__(None, None, None)

    # ====================================================================
    # Credential acquisition helpers (sync)
    # ====================================================================

    def _get_zarr_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "ZarrUploadGrant":
        """Get zarr upload credentials synchronously."""
        from mikro_next.api.schema import (
            RequestZarrUploadInput,
            RequestZarrUploadMutation,
        )

        x = rath.query(
            RequestZarrUploadMutation.Meta.document,
            RequestZarrUploadMutation.Arguments(input=RequestZarrUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestZarrUploadMutation(**x.data).request_zarr_upload

    def _finish_zarr_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish zarr upload synchronously."""
        from mikro_next.api.schema import (
            FinishZarrUploadInput,
            FinishZarrUploadMutation,
        )

        rath.query(
            FinishZarrUploadMutation.Meta.document,
            FinishZarrUploadMutation.Arguments(
                input=FinishZarrUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    def _get_fabriks_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "FabriksUploadGrant":
        """Get fabriks upload credentials synchronously.

        One grant for the whole prefix -- the manifest, both catalogs and every level -- because
        a fabriks store is a tree rather than an object.
        """
        from mikro_next.api.schema import (
            RequestFabriksUploadInput,
            RequestFabriksUploadMutation,
        )

        x = rath.query(
            RequestFabriksUploadMutation.Meta.document,
            RequestFabriksUploadMutation.Arguments(input=RequestFabriksUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestFabriksUploadMutation(**x.data).request_fabriks_upload

    def _finish_fabriks_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish a fabriks upload synchronously.

        The completion protocol, not a formality: the server reads the prefix's `fabriks.json`
        and refuses one that has none, which is exactly what an interrupted write looks like
        since the manifest is written last.
        """
        from mikro_next.api.schema import (
            FinishFabriksUploadInput,
            FinishFabriksUploadMutation,
        )

        rath.query(
            FinishFabriksUploadMutation.Meta.document,
            FinishFabriksUploadMutation.Arguments(
                input=FinishFabriksUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    def _get_konnektion_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "KonnektionUploadGrant":
        """Get konnektion upload credentials synchronously.

        One grant for the whole prefix -- the manifest, both catalogs and every level -- because
        a konnektion store is a tree rather than an object.
        """
        from mikro_next.api.schema import (
            RequestKonnektionUploadInput,
            RequestKonnektionUploadMutation,
        )

        x = rath.query(
            RequestKonnektionUploadMutation.Meta.document,
            RequestKonnektionUploadMutation.Arguments(input=RequestKonnektionUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestKonnektionUploadMutation(**x.data).request_konnektion_upload

    def _finish_konnektion_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish a konnektion upload synchronously.

        The completion protocol, not a formality: the server reads the prefix's `konnektion.json`
        and refuses one that has none, which is exactly what an interrupted write looks like
        since the manifest is written last.
        """
        from mikro_next.api.schema import (
            FinishKonnektionUploadInput,
            FinishKonnektionUploadMutation,
        )

        rath.query(
            FinishKonnektionUploadMutation.Meta.document,
            FinishKonnektionUploadMutation.Arguments(
                input=FinishKonnektionUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    def _get_sparse_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "SparseUploadGrant":
        """Get sparse upload credentials synchronously.

        One grant for the whole prefix, as for fabriks: a sparse matrix is a zarr *group* --
        three arrays and the attributes that say what they mean -- not a single object.
        """
        from mikro_next.api.schema import (
            RequestSparseUploadInput,
            RequestSparseUploadMutation,
        )

        x = rath.query(
            RequestSparseUploadMutation.Meta.document,
            RequestSparseUploadMutation.Arguments(input=RequestSparseUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestSparseUploadMutation(**x.data).request_sparse_upload

    def _finish_sparse_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish a sparse upload synchronously.

        Where the server reads the group back: the encoding, the shape, the nnz and the chunking
        all come off the artifact here, which is why `createSparseDataset` declares none of them.
        A prefix missing `encoding-type` or any of the three arrays is refused at this point --
        which is what an interrupted write looks like.
        """
        from mikro_next.api.schema import (
            FinishSparseUploadInput,
            FinishSparseUploadMutation,
        )

        rath.query(
            FinishSparseUploadMutation.Meta.document,
            FinishSparseUploadMutation.Arguments(
                input=FinishSparseUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    def _get_table_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "ParquetUploadGrant":
        """Get table upload credentials synchronously."""
        from mikro_next.api.schema import (
            RequestParquetUploadInput,
            RequestParquetUploadMutation,
        )

        x = rath.query(
            RequestParquetUploadMutation.Meta.document,
            RequestParquetUploadMutation.Arguments(input=RequestParquetUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestParquetUploadMutation(**x.data).request_parquet_upload

    def _get_bigfile_credentials(
        self, file: FileLike, datalayer: str, rath: "MikroNextRath"
    ) -> "BigFileUploadGrant":
        """Get big file upload credentials synchronously."""
        from mikro_next.api.schema import (
            RequestBigFileUploadInput,
            RequestBigfileUploadMutation,
        )

        original_file_name = getattr(file, "file_name", getattr(file, "key", "upload"))

        x = rath.query(
            RequestBigfileUploadMutation.Meta.document,
            RequestBigfileUploadMutation.Arguments(
                input=RequestBigFileUploadInput(original_file_name=original_file_name)
            ).model_dump(by_alias=True, exclude_unset=True),
        )
        return RequestBigfileUploadMutation(**x.data).request_bigfile_upload

    def _request_media_credentials(
        self, file_name: str, datalayer: str, rath: "MikroNextRath"
    ) -> "MediaUploadGrant":
        """Get media upload credentials synchronously."""
        from mikro_next.api.schema import (
            RequestMediaUploadInput,
            RequestMediaUploadMutation,
        )

        x = rath.query(
            RequestMediaUploadMutation.Meta.document,
            RequestMediaUploadMutation.Arguments(
                input=RequestMediaUploadInput(original_file_name=file_name)
            ).model_dump(by_alias=True, exclude_unset=True),
        )
        return RequestMediaUploadMutation(**x.data).request_media_upload

    # ====================================================================
    # Credential acquisition helpers (async)
    # ====================================================================

    async def _aget_zarr_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "ZarrUploadGrant":
        """Get zarr upload credentials asynchronously."""
        from mikro_next.api.schema import (
            RequestZarrUploadInput,
            RequestZarrUploadMutation,
        )

        x = await rath.aquery(
            RequestZarrUploadMutation.Meta.document,
            RequestZarrUploadMutation.Arguments(input=RequestZarrUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestZarrUploadMutation(**x.data).request_zarr_upload

    async def _afinish_zarr_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish zarr upload asynchronously."""
        from mikro_next.api.schema import (
            FinishZarrUploadInput,
            FinishZarrUploadMutation,
        )

        await rath.aquery(
            FinishZarrUploadMutation.Meta.document,
            FinishZarrUploadMutation.Arguments(
                input=FinishZarrUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    async def _aget_fabriks_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "FabriksUploadGrant":
        """Get fabriks upload credentials asynchronously."""
        from mikro_next.api.schema import (
            RequestFabriksUploadInput,
            RequestFabriksUploadMutation,
        )

        x = await rath.aquery(
            RequestFabriksUploadMutation.Meta.document,
            RequestFabriksUploadMutation.Arguments(input=RequestFabriksUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestFabriksUploadMutation(**x.data).request_fabriks_upload

    async def _afinish_fabriks_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish a fabriks upload asynchronously."""
        from mikro_next.api.schema import (
            FinishFabriksUploadInput,
            FinishFabriksUploadMutation,
        )

        await rath.aquery(
            FinishFabriksUploadMutation.Meta.document,
            FinishFabriksUploadMutation.Arguments(
                input=FinishFabriksUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    async def _aget_konnektion_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "KonnektionUploadGrant":
        """Get konnektion upload credentials asynchronously."""
        from mikro_next.api.schema import (
            RequestKonnektionUploadInput,
            RequestKonnektionUploadMutation,
        )

        x = await rath.aquery(
            RequestKonnektionUploadMutation.Meta.document,
            RequestKonnektionUploadMutation.Arguments(input=RequestKonnektionUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestKonnektionUploadMutation(**x.data).request_konnektion_upload

    async def _afinish_konnektion_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish a konnektion upload asynchronously."""
        from mikro_next.api.schema import (
            FinishKonnektionUploadInput,
            FinishKonnektionUploadMutation,
        )

        await rath.aquery(
            FinishKonnektionUploadMutation.Meta.document,
            FinishKonnektionUploadMutation.Arguments(
                input=FinishKonnektionUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    async def _aget_sparse_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "SparseUploadGrant":
        """Get sparse upload credentials asynchronously."""
        from mikro_next.api.schema import (
            RequestSparseUploadInput,
            RequestSparseUploadMutation,
        )

        x = await rath.aquery(
            RequestSparseUploadMutation.Meta.document,
            RequestSparseUploadMutation.Arguments(input=RequestSparseUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestSparseUploadMutation(**x.data).request_sparse_upload

    async def _afinish_sparse_upload(self, store_id: str, rath: "MikroNextRath") -> None:
        """Finish a sparse upload asynchronously."""
        from mikro_next.api.schema import (
            FinishSparseUploadInput,
            FinishSparseUploadMutation,
        )

        await rath.aquery(
            FinishSparseUploadMutation.Meta.document,
            FinishSparseUploadMutation.Arguments(
                input=FinishSparseUploadInput(store_id=store_id, valid=True)
            ).model_dump(by_alias=True, exclude_unset=True),
        )

    async def _aget_table_credentials(
        self, key: str, datalayer: str, rath: "MikroNextRath"
    ) -> "ParquetUploadGrant":
        """Get table upload credentials asynchronously."""
        from mikro_next.api.schema import (
            RequestParquetUploadInput,
            RequestParquetUploadMutation,
        )

        x = await rath.aquery(
            RequestParquetUploadMutation.Meta.document,
            RequestParquetUploadMutation.Arguments(input=RequestParquetUploadInput()).model_dump(
                by_alias=True, exclude_unset=True
            ),
        )
        return RequestParquetUploadMutation(**x.data).request_parquet_upload

    async def _aget_bigfile_credentials(
        self, file: FileLike, datalayer: str, rath: "MikroNextRath"
    ) -> "BigFileUploadGrant":
        """Get big file upload credentials asynchronously."""
        from mikro_next.api.schema import (
            RequestBigFileUploadInput,
            RequestBigfileUploadMutation,
        )

        original_file_name = getattr(file, "file_name", getattr(file, "key", "upload"))

        x = await rath.aquery(
            RequestBigfileUploadMutation.Meta.document,
            RequestBigfileUploadMutation.Arguments(
                input=RequestBigFileUploadInput(original_file_name=original_file_name)
            ).model_dump(by_alias=True, exclude_unset=True),
        )
        return RequestBigfileUploadMutation(**x.data).request_bigfile_upload

    async def _arequest_media_credentials(
        self, file_name: str, datalayer: str, rath: "MikroNextRath"
    ) -> "MediaUploadGrant":
        """Get media upload credentials asynchronously."""
        from mikro_next.api.schema import (
            RequestMediaUploadInput,
            RequestMediaUploadMutation,
        )

        x = await rath.aquery(
            RequestMediaUploadMutation.Meta.document,
            RequestMediaUploadMutation.Arguments(
                input=RequestMediaUploadInput(original_file_name=file_name)
            ).model_dump(by_alias=True, exclude_unset=True),
        )
        return RequestMediaUploadMutation(**x.data).request_media_upload

    # ====================================================================
    # Sync upload methods (obstore path)
    # ====================================================================

    def get_datalayer_url(self) -> str:
        """Helper to get the datalayer endpoint URL."""
        if self._cached_datalayer_url is None:
            self._cached_datalayer_url = unkoil(self.datalayer.get_endpoint_url)
        return self._cached_datalayer_url

    def _upload_xarray(
        self, datalayer: "DataLayer", rath: "MikroNextRath", xarray: ArrayLike
    ) -> str:
        """Upload an xarray synchronously via obstore."""
        endpoint_url = self.get_datalayer_url()

        credentials = self._get_zarr_credentials(xarray.key, endpoint_url, rath)
        store_id = upload_xarray(xarray, credentials, datalayer)
        self._finish_zarr_upload(store_id, rath)
        return store_id

    def _upload_parquet(
        self,
        datalayer: "DataLayer",
        rath: "MikroNextRath",
        parquet_input: ParquetLike,
    ) -> str:
        """Upload a Parquet file synchronously."""
        endpoint_url = self.get_datalayer_url()

        credentials = self._get_table_credentials(parquet_input.key, endpoint_url, rath)
        return upload_parquet(parquet_input, credentials, datalayer)

    def _upload_bigfile(self, datalayer: "DataLayer", rath: "MikroNextRath", file: FileLike) -> str:
        """Upload a big file synchronously via obstore."""
        endpoint_url = self.get_datalayer_url()

        credentials = self._get_bigfile_credentials(file, endpoint_url, rath)
        return upload_bigfile(file, credentials, datalayer)

    def _upload_mediafile(
        self, datalayer: "DataLayer", rath: "MikroNextRath", file: ImageFileLike
    ) -> str:
        """Upload a media file synchronously via obstore."""
        endpoint_url = self.get_datalayer_url()

        credentials = self._request_media_credentials(file.file_name, endpoint_url, rath)
        return store_media_file(file, credentials, datalayer)

    def _store_fabriks(
        self, datalayer: "DataLayer", rath: "MikroNextRath", collection: FabriksLike
    ) -> str:
        """Write a fabriks collection into a granted prefix and register it as complete."""
        endpoint_url = self.get_datalayer_url()

        credentials = self._get_fabriks_credentials(collection.key, endpoint_url, rath)
        store_id = store_fabriks_collection(collection, credentials, datalayer)
        self._finish_fabriks_upload(store_id, rath)
        return store_id

    def _store_konnektion(
        self, datalayer: "DataLayer", rath: "MikroNextRath", collection: KonnektionLike
    ) -> str:
        """Write a konnektion collection into a granted prefix and register it as complete."""
        endpoint_url = self.get_datalayer_url()

        credentials = self._get_konnektion_credentials(collection.key, endpoint_url, rath)
        store_id = store_konnektion_collection(collection, credentials, datalayer)
        self._finish_konnektion_upload(store_id, rath)
        return store_id

    def _store_sparse(
        self, datalayer: "DataLayer", rath: "MikroNextRath", sparse: SporadikLike
    ) -> str:
        """Write a sparse matrix into a granted prefix and register it as complete."""
        endpoint_url = self.get_datalayer_url()

        credentials = self._get_sparse_credentials(sparse.key, endpoint_url, rath)
        store_id = store_sparse_matrix(sparse, credentials, datalayer)
        self._finish_sparse_upload(store_id, rath)
        return store_id

    # ====================================================================
    # Async upload methods (obstore path)
    # ====================================================================

    async def _aupload_xarray(
        self, datalayer: "DataLayer", rath: "MikroNextRath", xarray: ArrayLike
    ) -> str:
        """Upload an xarray asynchronously."""
        endpoint_url = await datalayer.get_endpoint_url()

        credentials = await self._aget_zarr_credentials(xarray.key, endpoint_url, rath)
        store_id = await aupload_xarray(xarray, credentials, datalayer)
        await self._afinish_zarr_upload(store_id, rath)
        return store_id

    async def _aupload_parquet(
        self,
        datalayer: "DataLayer",
        rath: "MikroNextRath",
        parquet_input: ParquetLike,
    ) -> str:
        """Upload a Parquet file asynchronously."""
        endpoint_url = await datalayer.get_endpoint_url()

        credentials = await self._aget_table_credentials(parquet_input.key, endpoint_url, rath)
        return await aupload_parquet(parquet_input, credentials, datalayer, self._executor_session)

    async def _aupload_bigfile(
        self, datalayer: "DataLayer", rath: "MikroNextRath", file: FileLike
    ) -> str:
        """Upload a big file asynchronously."""
        endpoint_url = await datalayer.get_endpoint_url()

        credentials = await self._aget_bigfile_credentials(file, endpoint_url, rath)
        return await aupload_bigfile(file, credentials, datalayer)

    async def _aupload_mediafile(
        self, datalayer: "DataLayer", rath: "MikroNextRath", file: ImageFileLike
    ) -> str:
        """Upload a media file asynchronously."""
        endpoint_url = await datalayer.get_endpoint_url()

        credentials = await self._arequest_media_credentials(file.file_name, endpoint_url, rath)
        return await astore_media_file(file, credentials, datalayer)

    async def _astore_fabriks(
        self, datalayer: "DataLayer", rath: "MikroNextRath", collection: FabriksLike
    ) -> str:
        """Write a fabriks collection into a granted prefix and register it as complete."""
        endpoint_url = await datalayer.get_endpoint_url()

        credentials = await self._aget_fabriks_credentials(collection.key, endpoint_url, rath)
        store_id = await astore_fabriks_collection(collection, credentials, datalayer)
        await self._afinish_fabriks_upload(store_id, rath)
        return store_id

    async def _astore_konnektion(
        self, datalayer: "DataLayer", rath: "MikroNextRath", collection: KonnektionLike
    ) -> str:
        """Write a konnektion collection into a granted prefix and register it as complete."""
        endpoint_url = await datalayer.get_endpoint_url()

        credentials = await self._aget_konnektion_credentials(collection.key, endpoint_url, rath)
        store_id = await astore_konnektion_collection(collection, credentials, datalayer)
        await self._afinish_konnektion_upload(store_id, rath)
        return store_id

    async def _astore_sparse(
        self, datalayer: "DataLayer", rath: "MikroNextRath", sparse: SporadikLike
    ) -> str:
        """Write a sparse matrix into a granted prefix and register it as complete."""
        endpoint_url = await datalayer.get_endpoint_url()

        credentials = await self._aget_sparse_credentials(sparse.key, endpoint_url, rath)
        store_id = await astore_sparse_matrix(sparse, credentials, datalayer)
        await self._afinish_sparse_upload(store_id, rath)
        return store_id

    # ====================================================================
    # Core middleware methods
    # ====================================================================

    def process_variables(
        self,
        variables: dict[str, Any],
        operation: type[TOperation],
        rath: "MikroNextRath",
    ) -> dict[str, Any]:
        """Process serialized variables synchronously (obstore path).

        Called from ``execute()`` and ``subscribe()``. Uses sync I/O
        for all S3 uploads.

        Args:
            variables: The serialized variables dict.
            operation: The operation type being executed.
            rath: The rath client instance.

        Returns:
            The variables dict with uploadable types replaced by store IDs.
        """
        datalayer = self.datalayer

        variables = _apply_recursive_sync(
            partial(self._upload_xarray, datalayer, rath),
            variables,
            (ArrayLike,),
        )
        variables = _apply_recursive_sync(
            partial(self._upload_parquet, datalayer, rath),
            variables,
            (ParquetLike,),
        )
        variables = _apply_recursive_sync(
            partial(self._upload_bigfile, datalayer, rath),
            variables,
            (FileLike,),
        )
        variables = _apply_recursive_sync(
            partial(self._upload_mediafile, datalayer, rath),
            variables,
            (ImageFileLike,),
        )
        variables = _apply_recursive_sync(
            partial(self._store_fabriks, datalayer, rath),
            variables,
            FabriksLike,
        )
        variables = _apply_recursive_sync(
            partial(self._store_konnektion, datalayer, rath),
            variables,
            KonnektionLike,
        )
        variables = _apply_recursive_sync(
            partial(self._store_sparse, datalayer, rath),
            variables,
            SporadikLike,
        )

        return variables

    async def aprocess_variables(
        self,
        variables: dict[str, Any],
        operation: type[TOperation],
        rath: "MikroNextRath",
    ) -> dict[str, Any]:
        """Process serialized variables asynchronously (obstore path).

        Called from ``aexecute()`` and ``asubscribe()``. Uses async I/O
        for all S3 uploads.

        Args:
            variables: The serialized variables dict.
            operation: The operation type being executed.
            rath: The rath client instance.

        Returns:
            The variables dict with uploadable types replaced by store IDs.
        """
        datalayer = self.datalayer

        variables = await _apply_recursive_async(
            partial(self._aupload_xarray, datalayer, rath),
            variables,
            (ArrayLike,),
        )
        variables = await _apply_recursive_async(
            partial(self._aupload_parquet, datalayer, rath),
            variables,
            (ParquetLike,),
        )
        variables = await _apply_recursive_async(
            partial(self._aupload_bigfile, datalayer, rath),
            variables,
            (FileLike,),
        )
        variables = await _apply_recursive_async(
            partial(self._aupload_mediafile, datalayer, rath),
            variables,
            (ImageFileLike,),
        )
        variables = await _apply_recursive_async(
            partial(self._astore_fabriks, datalayer, rath),
            variables,
            FabriksLike,
        )
        variables = await _apply_recursive_async(
            partial(self._astore_konnektion, datalayer, rath),
            variables,
            KonnektionLike,
        )
        variables = await _apply_recursive_async(
            partial(self._astore_sparse, datalayer, rath),
            variables,
            SporadikLike,
        )

        return variables
