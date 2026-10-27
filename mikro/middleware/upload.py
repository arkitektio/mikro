"""Upload middleware for the operations.

This middleware intercepts serialized operation variables and uploads
uploadable types (ArrayLike, ParquetLike, SporadikLike, etc.) to the datalayer
*before* the operation reaches the rath link chain.

It provides both sync and async paths:
    - Sync (process_variables): Uses obstore for S3 uploads, called from execute().
    - Async (aprocess_variables): Uses obstore, called from aexecute().

Credential acquisition always goes through rath.query/aquery directly
(bypassing the middleware itself) to avoid infinite recursion. Every upload runs the same
protocol -- grant, write with self-renewing credentials, finish or report the failure --
in :meth:`UploadMiddleware._upload` / :meth:`UploadMiddleware._aupload`.
"""

import asyncio
import contextvars
import io
import logging
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

from koil import unkoil
from pydantic import ConfigDict, Field

from mikro.datalayer import DataLayer
from mikro.io.obstore import upload_refresher
from mikro.io.upload import (
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
from mikro.api.schema import (
    FinishBigFileUploadInput,
    FinishBigfileUploadMutation,
    FinishFabriksUploadInput,
    FinishFabriksUploadMutation,
    FinishKonnektionUploadInput,
    FinishKonnektionUploadMutation,
    FinishKulisseUploadInput,
    FinishKulisseUploadMutation,
    FinishMediaUploadInput,
    FinishMediaUploadMutation,
    FinishParquetUploadInput,
    FinishParquetUploadMutation,
    FinishSparseUploadInput,
    FinishSparseUploadMutation,
    FinishZarrUploadInput,
    FinishZarrUploadMutation,
    RefreshBigfileUploadMutation,
    RefreshFabriksUploadMutation,
    RefreshKonnektionUploadMutation,
    RefreshKulisseUploadMutation,
    RefreshMediaUploadMutation,
    RefreshParquetUploadMutation,
    RefreshSparseUploadMutation,
    RefreshUploadInput,
    RefreshZarrUploadMutation,
    RequestBigFileUploadInput,
    RequestBigfileUploadMutation,
    RequestFabriksUploadMutation,
    RequestKonnektionUploadMutation,
    RequestKulisseUploadInput,
    RequestKulisseUploadMutation,
    RequestMediaUploadInput,
    RequestMediaUploadMutation,
    RequestParquetUploadInput,
    RequestParquetUploadMutation,
    RequestSparseUploadMutation,
    RequestZarrUploadInput,
    RequestZarrUploadMutation,
)
from mikro.middleware.base import OperationMiddleware
from mikro.scalars import (
    ArrayLike,
    ByteCount,
    FabriksLike,
    FileLike,
    ImageFileLike,
    KonnektionLike,
    KulisseLike,
    ParquetLike,
    SporadikLike,
)

if TYPE_CHECKING:
    from mikro.rath import MikroRath

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


@dataclass(frozen=True)
class _Kind:
    """The three mutations of one store kind's upload protocol, and where each keeps its result."""

    request: Any
    request_field: str
    finish: Any
    finish_input: Any
    refresh: Any
    refresh_field: str


ZARR = _Kind(RequestZarrUploadMutation, "request_zarr_upload", FinishZarrUploadMutation, FinishZarrUploadInput, RefreshZarrUploadMutation, "refresh_zarr_upload")
PARQUET = _Kind(RequestParquetUploadMutation, "request_parquet_upload", FinishParquetUploadMutation, FinishParquetUploadInput, RefreshParquetUploadMutation, "refresh_parquet_upload")
BIGFILE = _Kind(RequestBigfileUploadMutation, "request_bigfile_upload", FinishBigfileUploadMutation, FinishBigFileUploadInput, RefreshBigfileUploadMutation, "refresh_bigfile_upload")
MEDIA = _Kind(RequestMediaUploadMutation, "request_media_upload", FinishMediaUploadMutation, FinishMediaUploadInput, RefreshMediaUploadMutation, "refresh_media_upload")
KULISSE = _Kind(RequestKulisseUploadMutation, "request_kulisse_upload", FinishKulisseUploadMutation, FinishKulisseUploadInput, RefreshKulisseUploadMutation, "refresh_kulisse_upload")
FABRIKS = _Kind(RequestFabriksUploadMutation, "request_fabriks_upload", FinishFabriksUploadMutation, FinishFabriksUploadInput, RefreshFabriksUploadMutation, "refresh_fabriks_upload")
KONNEKTION = _Kind(RequestKonnektionUploadMutation, "request_konnektion_upload", FinishKonnektionUploadMutation, FinishKonnektionUploadInput, RefreshKonnektionUploadMutation, "refresh_konnektion_upload")
SPARSE = _Kind(RequestSparseUploadMutation, "request_sparse_upload", FinishSparseUploadMutation, FinishSparseUploadInput, RefreshSparseUploadMutation, "refresh_sparse_upload")


def _request(mutation: Any, input: Any) -> dict[str, Any]:  # noqa: ANN401
    return mutation.Arguments(input=input).model_dump(by_alias=True, exclude_unset=True)


def _byte_size(value: Any) -> int:  # noqa: ANN401
    """How many bytes an upload will send: the size it declares, and is then held to.

    A file object is measured from where it stands to its end -- that is what gets read --
    and left where it was.
    """
    if isinstance(value, (bytes, bytearray, memoryview)):
        return len(value)
    position = value.tell()
    end = value.seek(0, io.SEEK_END)
    value.seek(position)
    return end - position


def _bigfile_request(file: FileLike) -> dict[str, Any]:
    name = getattr(file, "file_name", None) or getattr(file, "key", None) or "upload"
    return _request(RequestBigfileUploadMutation, RequestBigFileUploadInput(original_file_name=name, file_size=ByteCount(_byte_size(file.value))))


def _media_request(file: ImageFileLike) -> dict[str, Any]:
    return _request(RequestMediaUploadMutation, RequestMediaUploadInput(original_file_name=file.file_name, file_size=ByteCount(_byte_size(file.value))))


def _kulisse_request(model: KulisseLike) -> dict[str, Any]:
    return _request(RequestKulisseUploadMutation, RequestKulisseUploadInput(original_file_name=model.file_name, file_size=ByteCount(len(model.value))))


class UploadMiddleware(OperationMiddleware):
    """Middleware that uploads supported data types to the datalayer.

    This middleware walks the serialized variables dict, finds instances of
    uploadable scalar types (ArrayLike, ParquetLike, FileLike, ImageFileLike,
    KulisseLike, FabriksLike, SporadikLike), uploads them to S3, and replaces
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
    # One upload: request a grant, write under it, finish it
    # ====================================================================
    #
    # Every kind follows the same protocol, which is why it lives here once:
    #
    # - the grant's credentials renew themselves for as long as the write runs
    #   (``upload_refresher``: obstore asks for credentials, and near expiry gets a fresh
    #   session against the *same* key instead of a 403 halfway through);
    # - a write that raises is reported with ``valid=False`` -- the server ends the upload
    #   at once, releases what it reserved against the quota, and deletes what landed --
    #   and the error propagates unchanged;
    # - a write that returns is finished, which is where the server reads and checks what
    #   arrived. Nothing is registered that was not finished.

    def _query(self, rath: "MikroRath", mutation: Any, variables: dict[str, Any], field: str) -> Any:  # noqa: ANN401
        result = rath.query(mutation.Meta.document, variables)
        return getattr(mutation(**result.data), field)

    async def _aquery(self, rath: "MikroRath", mutation: Any, variables: dict[str, Any], field: str) -> Any:  # noqa: ANN401
        result = await rath.aquery(mutation.Meta.document, variables)
        return getattr(mutation(**result.data), field)

    def _refresher(self, rath: "MikroRath", kind: _Kind) -> Callable[[str], Any]:
        """How to renew a grant of ``kind``, callable from obstore's own worker threads.

        obstore asks for credentials from a thread of its runtime, which carries none of the
        caller's context -- and koil finds its loop through context. So the context is captured
        here and every refresh runs in a copy of it, which lets the synchronous query reach the
        loop whether the upload itself is synchronous or awaited.
        """
        captured = contextvars.copy_context()

        def refresh(store_id: str) -> Any:  # noqa: ANN401
            variables = kind.refresh.Arguments(input=RefreshUploadInput(store_id=store_id)).model_dump(by_alias=True, exclude_unset=True)
            return captured.copy().run(self._query, rath, kind.refresh, variables, kind.refresh_field)

        return refresh

    def _finish_variables(self, kind: _Kind, store_id: str, valid: bool) -> dict[str, Any]:
        return kind.finish.Arguments(input=kind.finish_input(store_id=store_id, valid=valid)).model_dump(by_alias=True, exclude_unset=True)

    def _upload(self, rath: "MikroRath", kind: _Kind, request: dict[str, Any], write: Callable[[Any], str]) -> str:
        """Run one upload synchronously: grant, write with self-renewing credentials, finish."""
        grant = self._query(rath, kind.request, request, kind.request_field)
        token = upload_refresher.set(self._refresher(rath, kind))
        try:
            store_id = write(grant)
        except BaseException:
            try:
                rath.query(kind.finish.Meta.document, self._finish_variables(kind, grant.store, valid=False))
            except Exception:  # noqa: BLE001 - the write's own error is the one to raise
                logger.warning("Could not report the failed upload of store %s; it is collected once its deadline passes.", grant.store, exc_info=True)
            raise
        finally:
            upload_refresher.reset(token)
        rath.query(kind.finish.Meta.document, self._finish_variables(kind, store_id, valid=True))
        return store_id

    async def _aupload(self, rath: "MikroRath", kind: _Kind, request: dict[str, Any], write: Callable[[Any], Awaitable[str]]) -> str:
        """Run one upload asynchronously: grant, write with self-renewing credentials, finish."""
        grant = await self._aquery(rath, kind.request, request, kind.request_field)
        token = upload_refresher.set(self._refresher(rath, kind))
        try:
            store_id = await write(grant)
        except BaseException:
            try:
                await rath.aquery(kind.finish.Meta.document, self._finish_variables(kind, grant.store, valid=False))
            except Exception:  # noqa: BLE001 - the write's own error is the one to raise
                logger.warning("Could not report the failed upload of store %s; it is collected once its deadline passes.", grant.store, exc_info=True)
            raise
        finally:
            upload_refresher.reset(token)
        await rath.aquery(kind.finish.Meta.document, self._finish_variables(kind, store_id, valid=True))
        return store_id

    # ====================================================================
    # The kinds (sync)
    # ====================================================================

    def get_datalayer_url(self) -> str:
        """Helper to get the datalayer endpoint URL."""
        if self._cached_datalayer_url is None:
            self._cached_datalayer_url = unkoil(self.datalayer.get_endpoint_url)
        return self._cached_datalayer_url

    def _upload_xarray(self, datalayer: "DataLayer", rath: "MikroRath", xarray: ArrayLike) -> str:
        """Upload an xarray as a zarr store."""
        return self._upload(rath, ZARR, _request(RequestZarrUploadMutation, RequestZarrUploadInput()), lambda grant: upload_xarray(xarray, grant, datalayer))

    def _upload_parquet(self, datalayer: "DataLayer", rath: "MikroRath", parquet_input: ParquetLike) -> str:
        """Upload a table as one parquet object."""
        return self._upload(rath, PARQUET, _request(RequestParquetUploadMutation, RequestParquetUploadInput()), lambda grant: upload_parquet(parquet_input, grant, datalayer))

    def _upload_bigfile(self, datalayer: "DataLayer", rath: "MikroRath", file: FileLike) -> str:
        """Upload a file, declaring its size: the server reserves it and holds the upload to it."""
        return self._upload(rath, BIGFILE, _bigfile_request(file), lambda grant: upload_bigfile(file, grant, datalayer))

    def _upload_mediafile(self, datalayer: "DataLayer", rath: "MikroRath", file: ImageFileLike) -> str:
        """Upload a media file, declaring its size."""
        return self._upload(rath, MEDIA, _media_request(file), lambda grant: store_media_file(file, grant, datalayer))

    def _store_kulisse(self, datalayer: "DataLayer", rath: "MikroRath", model: KulisseLike) -> str:
        """Upload a kulisse model; finishing it is when the server reads and checks it."""
        return self._upload(rath, KULISSE, _kulisse_request(model), lambda grant: store_media_file(model, grant, datalayer))

    def _store_fabriks(self, datalayer: "DataLayer", rath: "MikroRath", collection: FabriksLike) -> str:
        """Write a fabriks collection into a granted prefix."""
        return self._upload(rath, FABRIKS, {}, lambda grant: store_fabriks_collection(collection, grant, datalayer))

    def _store_konnektion(self, datalayer: "DataLayer", rath: "MikroRath", collection: KonnektionLike) -> str:
        """Write a konnektion collection into a granted prefix."""
        return self._upload(rath, KONNEKTION, {}, lambda grant: store_konnektion_collection(collection, grant, datalayer))

    def _store_sparse(self, datalayer: "DataLayer", rath: "MikroRath", sparse: SporadikLike) -> str:
        """Write a sparse matrix into a granted prefix."""
        return self._upload(rath, SPARSE, {}, lambda grant: store_sparse_matrix(sparse, grant, datalayer))

    # ====================================================================
    # The kinds (async)
    # ====================================================================

    async def _aupload_xarray(self, datalayer: "DataLayer", rath: "MikroRath", xarray: ArrayLike) -> str:
        """Upload an xarray as a zarr store."""
        return await self._aupload(rath, ZARR, _request(RequestZarrUploadMutation, RequestZarrUploadInput()), lambda grant: aupload_xarray(xarray, grant, datalayer))

    async def _aupload_parquet(self, datalayer: "DataLayer", rath: "MikroRath", parquet_input: ParquetLike) -> str:
        """Upload a table as one parquet object."""
        return await self._aupload(rath, PARQUET, _request(RequestParquetUploadMutation, RequestParquetUploadInput()), lambda grant: aupload_parquet(parquet_input, grant, datalayer, self._executor_session))

    async def _aupload_bigfile(self, datalayer: "DataLayer", rath: "MikroRath", file: FileLike) -> str:
        """Upload a file, declaring its size: the server reserves it and holds the upload to it."""
        return await self._aupload(rath, BIGFILE, _bigfile_request(file), lambda grant: aupload_bigfile(file, grant, datalayer))

    async def _aupload_mediafile(self, datalayer: "DataLayer", rath: "MikroRath", file: ImageFileLike) -> str:
        """Upload a media file, declaring its size."""
        return await self._aupload(rath, MEDIA, _media_request(file), lambda grant: astore_media_file(file, grant, datalayer))

    async def _astore_kulisse(self, datalayer: "DataLayer", rath: "MikroRath", model: KulisseLike) -> str:
        """Upload a kulisse model; finishing it is when the server reads and checks it."""
        return await self._aupload(rath, KULISSE, _kulisse_request(model), lambda grant: astore_media_file(model, grant, datalayer))

    async def _astore_fabriks(self, datalayer: "DataLayer", rath: "MikroRath", collection: FabriksLike) -> str:
        """Write a fabriks collection into a granted prefix."""
        return await self._aupload(rath, FABRIKS, {}, lambda grant: astore_fabriks_collection(collection, grant, datalayer))

    async def _astore_konnektion(self, datalayer: "DataLayer", rath: "MikroRath", collection: KonnektionLike) -> str:
        """Write a konnektion collection into a granted prefix."""
        return await self._aupload(rath, KONNEKTION, {}, lambda grant: astore_konnektion_collection(collection, grant, datalayer))

    async def _astore_sparse(self, datalayer: "DataLayer", rath: "MikroRath", sparse: SporadikLike) -> str:
        """Write a sparse matrix into a granted prefix."""
        return await self._aupload(rath, SPARSE, {}, lambda grant: astore_sparse_matrix(sparse, grant, datalayer))

    # ====================================================================
    # Core middleware methods
    # ====================================================================

    def process_variables(
        self,
        variables: dict[str, Any],
        operation: type[TOperation],
        rath: "MikroRath",
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
            partial(self._store_kulisse, datalayer, rath),
            variables,
            KulisseLike,
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
        rath: "MikroRath",
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
            partial(self._astore_kulisse, datalayer, rath),
            variables,
            KulisseLike,
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
