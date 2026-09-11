"""A seekable file-like view over a remote object, backed by S3 range requests.

Some readers want bytes and some readers want a path, and the difference decides what
is possible. A reader written in Python -- ``tifffile``, ``zarr``, ``h5py`` with
``driver="fileobj"``, ``pyarrow.parquet`` -- asks its input for ``read`` and ``seek``,
and any object answering those questions will do. That is what :class:`RemoteFile` is:
each ``read`` becomes a ranged GET, so opening a multi-gigabyte acquisition to look at
its header transfers the header rather than the acquisition.

A reader that hands the path to C or to a JVM -- Bio-Formats, anything built on libtiff,
anything that ``mmap``s -- cannot use this at all. The file object never crosses that
boundary; the operating system does, and it wants a real descriptor. There is no partial
version of this to build, which is why :func:`mikro_next.io.remote.download_to_scratch`
exists alongside and why ``FileTrait`` exposes both.

The trade is latency for volume, and it is only a good trade one way. A ranged read is a
round trip, and container formats seek a lot -- TIFF chases IFD offsets that usually sit
near the end of the file. Reading most of an object this way means hundreds of small
serialised requests where :func:`mikro_next.io.download.download_file` would issue
parallel multipart GETs at the full bandwidth of the link. Below roughly a fifth of the
bytes this wins; above it, it loses, and it loses by more the larger the object is.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import obstore
from obstore.exceptions import (
    BaseError as ObstoreError,
)
from obstore.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    UnauthenticatedError,
)

from mikro_next.io.errors import DownloadError

if TYPE_CHECKING:
    from obstore.store import S3Store

    from mikro_next.datalayer import DataLayer
    from mikro_next.io.obstore import S3UploadGrantLike
    from mikro_next.rath import MikroNextRath


logger = logging.getLogger(__name__)

__all__ = [
    "SCRATCH_ENV",
    "GrantedObject",
    "RemoteFile",
    "aopen_remote_file",
    "download_to_scratch",
    "open_remote_file",
]


#: Where a downloaded file lands, when the caller does not say. Separate from ``TMPDIR`` on
#: purpose: ``TMPDIR`` is also where every library's small scratch file goes, and the right
#: answer for a multi-gigabyte download is often not the right answer for those.
SCRATCH_ENV = "MIKRO_SCRATCH_DIR"


try:
    from fsspec.spec import AbstractBufferedFile
except ImportError as error:  # pragma: no cover - fsspec ships with dask, a core dep
    raise ImportError(
        "Reading a remote object as a file requires fsspec, which normally arrives "
        "with dask. Install it with `pip install fsspec`."
    ) from error


# How long before a grant expires we go and ask for another one. Grants are minted with
# lifetimes in the tens of minutes and a handle can outlive one easily, so the refresh
# has to happen on a clock rather than in response to the 403 -- by the time the 403
# arrives the reader is already several frames into parsing and will report the failure
# as a corrupt file.
REFRESH_MARGIN_SECONDS = 60.0

# Retries here sit *on top of* obstore's own retry_config, which already handles the
# transport-level flakiness. What is left for this layer is the failure obstore cannot
# know is retryable: a grant that expired mid-read, where the fix is new credentials
# rather than another attempt with the old ones.
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 0.5


class GrantedObject:
    """One remote object, and a store for it that stays inside a live grant.

    Grants expire. A download outruns that by finishing inside a single grant's lifetime,
    but a file handle held open across a slow parse does not, and the expiry surfaces as
    a 403 in the middle of a read -- which the reader above will report as a malformed
    file, because from where it stands that is what it looks like. So the store is not a
    value here but a thing with a deadline: `store_and_key` hands one back and re-mints
    it first if it is close to running out.

    Refreshes are serialised, since one handle can be read from several threads and two
    simultaneous refreshes would mint two grants and race to install them.
    """

    def __init__(
        self,
        resolve: Callable[[], tuple[S3UploadGrantLike, str]],
        *,
        expires_in: Callable[[S3UploadGrantLike], int | None] | None = None,
    ) -> None:
        """Wrap a grant resolver.

        Args:
            resolve: Called to obtain ``(grant, endpoint_url)``. Called again whenever
                the current grant nears expiry, so it must be safe to call repeatedly
                and must be synchronous -- reads block, and resolving through the async
                client from inside a blocking read would deadlock the loop.
            expires_in: Reads the grant's lifetime in seconds. Defaults to the
                ``expires_in`` attribute the access grants carry; a grant without one
                is treated as never expiring.
        """
        self._resolve = resolve
        self._expires_in = expires_in or (lambda grant: getattr(grant, "expires_in", None))
        self._lock = threading.Lock()
        self._store: S3Store | None = None
        self._key: str = ""
        self._deadline: float | None = None

    @classmethod
    def from_store(cls, store: S3Store, key: str) -> GrantedObject:
        """Wrap a store that is already built and does not expire.

        For callers that hold their own store -- and for tests, which want a
        `LocalStore` and no grant machinery at all. Everything downstream reads
        through `store_and_key`, so a non-expiring object is simply one whose
        deadline never arrives.
        """
        granted = cls(lambda: (_ for _ in ()).throw(AssertionError("static store")))
        granted._store = store
        granted._key = key
        granted._deadline = None
        return granted

    @property
    def key(self) -> str:
        """The object key currently being read."""
        return self._key

    def store_and_key(self, *, force: bool = False) -> tuple[S3Store, str]:
        """The store and object key to read through, refreshed if the grant is stale.

        Args:
            force: Re-mint even if the current grant still looks live. Used when a read
                came back denied anyway, which happens when our clock and the issuer's
                disagree by more than the safety margin.
        """
        with self._lock:
            if force or self._store is None or self._expired():
                self._refresh()
            assert self._store is not None
            return self._store, self._key

    def _expired(self) -> bool:
        if self._deadline is None:
            return False
        return time.monotonic() >= self._deadline

    def _refresh(self) -> None:
        from mikro_next.io.obstore import create_s3_store

        grant, endpoint_url = self._resolve()

        # Bucket-rooted, addressing the key directly -- the shape `download_file` already
        # uses. The prefix-rooted store in `create_zarr_store_path` exists because zarr
        # walks a node's parents; a single ranged read has no parents to walk.
        self._store = create_s3_store(endpoint_url, grant)
        self._key = grant.key

        lifetime = self._expires_in(grant)
        if lifetime is None:
            self._deadline = None
        else:
            self._deadline = time.monotonic() + max(lifetime - REFRESH_MARGIN_SECONDS, 0.0)

    def size(self) -> int:
        """The object's size in bytes, from a HEAD request."""
        store, key = self.store_and_key()
        return int(obstore.head(store, key)["size"])


def _cache_policy(
    cache: bool | str, max_cached_blocks: int
) -> tuple[str, dict[str, object] | None]:
    """Turn ``cache=True`` into an fsspec caching policy.

    ``True`` means `blockcache` rather than fsspec's usual `readahead` default, and the
    difference is not small. `readahead` holds exactly one block: it makes a forward
    scan cheap and a *revisit* free only if it lands in the block still in hand. Readers
    of container formats do not scan forwards -- a TIFF reads its IFDs, jumps to pixel
    data, comes back for the next IFD -- and against that pattern a one-block cache
    misses on nearly every hop, turning each one back into a request. `blockcache` keeps
    an LRU instead, so the second visit to an offset is free regardless of where the
    reader has been in between.

    It is not free, and the cost is worth stating rather than burying. An LRU fetches on
    a fixed grid, so a reader doing one straight pass through an object pays in request
    *count* what it saves in nothing at all -- measured on a tiled 8.4 MB TIFF decoded in
    full, `blockcache` made 33 requests and `readahead` made 2, for identical bytes. The
    default is chosen for the access pattern this module exists to serve, which is a
    reader taking a slice out of something large; a caller who knows it is reading
    straight through should say ``cache="readahead"``, and one reading nearly all of it
    should not be using this class at all.

    The other cost is memory, which is at least bounded and predictable:
    ``block_size * max_cached_blocks``.
    """
    if cache is True:
        return "blockcache", {"maxblocks": max_cached_blocks}
    if cache is False:
        return "none", None
    if cache == "blockcache":
        return "blockcache", {"maxblocks": max_cached_blocks}
    return cache, None


class RemoteFile(AbstractBufferedFile):
    """A read-only binary file whose reads are S3 range requests.

    Implements the one method `fsspec.spec.AbstractBufferedFile` leaves abstract, and
    inherits the rest of the file protocol from it -- ``read``, ``seek``, ``tell``,
    ``readinto``, ``readline``, iteration, and the block cache that turns a reader's
    many small reads into few requests.

    Caching is on by default and holds an LRU of blocks, because the readers this exists
    for revisit offsets constantly and a request already paid for should not be paid for
    twice. See `_cache_policy` for why the usual `readahead` default is the wrong one
    here. Memory is bounded by ``block_size * max_cached_blocks``, 32 MB as it stands.

    Not thread-safe, and the reason is structural rather than incidental: a file has one
    cursor, so two threads reading through one handle interleave their seeks and each
    gets the other's bytes. `tifffile` with ``maxworkers > 1`` and pyarrow with
    ``use_threads=True`` both do exactly that. Open a handle per thread.
    """

    # One MiB, matching obstore's own reader. Smaller than fsspec's 5 MiB default on
    # purpose: the block size is also the cache's granularity, so it multiplies by
    # `max_cached_blocks` into the memory ceiling, and 5 MiB x 32 is 160 MB for a file
    # nobody asked to have in memory.
    DEFAULT_BLOCK_SIZE = 1024 * 1024

    def __init__(
        self,
        granted: GrantedObject,
        *,
        size: int | None = None,
        block_size: int | None = None,
        cache: bool | str = True,
        max_cached_blocks: int = 32,
        **kwargs: object,
    ) -> None:
        """Open a remote object for reading.

        Args:
            granted: Supplies the store and key, re-minting the grant as it expires.
            size: The object's size. Fetched with a HEAD request when omitted. Passing
                it avoids that round trip, and it is what makes ``seek(0, SEEK_END)``
                free -- fsspec only consults the filesystem for size when it is not
                given, which is also why this class needs no filesystem at all.
            block_size: Bytes fetched per request, and the granularity of the cache.
            cache: ``True`` keeps fetched blocks in a bounded LRU, so a reader that
                revisits an offset does not pay for it twice. ``False`` fetches exactly
                the bytes asked for and keeps nothing. A string selects an fsspec policy
                by name -- ``"readahead"`` for a pure forward scan, ``"all"`` to pull the
                whole object once, ``"first"`` to pin only the header.
            max_cached_blocks: How many blocks the LRU holds when ``cache=True``. The
                memory ceiling is this times ``block_size`` -- 32 MB by default.
        """
        self._granted = granted
        resolved_size = granted.size() if size is None else size

        cache_type, cache_options = _cache_policy(cache, max_cached_blocks)

        super().__init__(
            fs=None,
            path=granted.key or "<remote>",
            mode="rb",
            block_size=block_size or self.DEFAULT_BLOCK_SIZE,
            cache_type=cache_type,
            cache_options=cache_options,
            size=resolved_size,
            **kwargs,
        )

    def read(self, length: int = -1) -> bytes:
        """Read up to ``length`` bytes, truncating at the end of the object.

        Overridden because `AbstractBufferedFile.read` hands ``loc + length`` to the
        cache without clamping it to the file, and `BlockCache` raises rather than
        truncating when that lands past the last block. Readers ask for more than
        remains all the time -- it is how a short read is spelled -- so without this the
        block cache fails on nearly every file whose tail is read with a generous
        length, and fails as `ValueError: block_number=6 is greater than ...` rather
        than as anything a caller could act on.
        """
        if length is not None and length >= 0:
            length = min(length, max(self.size - self.loc, 0))
        return super().read(length)

    def _fetch_range(self, start: int, end: int) -> bytes:
        """Fetch ``[start, end)`` from the object.

        Every failure here has to be translated. A short read or a raw obstore error
        propagating into the reader above arrives as a parse failure deep inside a
        format handler, where it reads as a corrupt file and sends whoever is debugging
        it to look at the bytes rather than the network.
        """
        if start >= self.size:
            return b""
        end = min(end, self.size)
        if end <= start:
            return b""

        force = False
        last_error: Exception | None = None

        for attempt in range(MAX_ATTEMPTS):
            store, key = self._granted.store_and_key(force=force)
            try:
                return obstore.get_range(store, key, start=start, end=end).to_bytes()
            except (PermissionDeniedError, UnauthenticatedError) as error:
                # Most likely the grant expired despite the margin -- clock skew between
                # us and the issuer. Worth exactly one re-mint; if fresh credentials are
                # also denied then the denial is real and retrying only delays saying so.
                last_error = error
                if force:
                    break
                logger.debug("Access denied reading %s, re-requesting grant", key)
                force = True
            except NotFoundError as error:
                raise DownloadError(
                    f"Object {key!r} disappeared while it was open for reading"
                ) from error
            except ObstoreError as error:
                last_error = error
                if attempt == MAX_ATTEMPTS - 1:
                    break
                time.sleep(BACKOFF_SECONDS * (2**attempt))

        raise DownloadError(
            f"Could not read bytes {start}-{end} of {self._granted.key!r} "
            f"after {MAX_ATTEMPTS} attempts"
        ) from last_error

    def _initiate_upload(self) -> None:  # pragma: no cover - read-only file
        raise NotImplementedError("RemoteFile is read-only")

    def _upload_chunk(self, final: bool = False) -> bool:  # pragma: no cover
        raise NotImplementedError("RemoteFile is read-only")


def _bigfile_granted_object(
    store_id: str,
    *,
    rath: MikroNextRath | None = None,
    datalayer: DataLayer | None = None,
) -> GrantedObject:
    """Build a :class:`GrantedObject` for a big-file store.

    The rath client and datalayer are captured here rather than read from the context
    at refresh time. A refresh happens inside a read, and a read runs wherever the
    caller put it -- typically a worker thread, because a blocking read has no business
    on the event loop -- so the ambient context the handle was opened in is not reliably
    the one the refresh sees.

    The endpoint URL is resolved once, eagerly: it is a property of the datalayer, not
    of the grant, so re-fetching it per refresh would buy nothing.
    """
    from koil import unkoil

    from mikro_next.api.schema import request_bigfile_access
    from mikro_next.datalayer import current_next_datalayer
    from mikro_next.rath import current_mikro_next_rath

    resolved_rath = rath if rath is not None else current_mikro_next_rath.get(None)
    resolved_datalayer = datalayer if datalayer is not None else current_next_datalayer.get()
    if resolved_datalayer is None:
        raise ValueError("Datalayer is not set")

    endpoint_url: str = unkoil(resolved_datalayer.get_endpoint_url)

    def resolve() -> tuple[S3UploadGrantLike, str]:
        return request_bigfile_access(store_id, rath=resolved_rath), endpoint_url

    return GrantedObject(resolve)


def open_remote_file(
    store_id: str,
    *,
    block_size: int | None = None,
    cache: bool | str = True,
    max_cached_blocks: int = 32,
    rath: MikroNextRath | None = None,
    datalayer: DataLayer | None = None,
) -> RemoteFile:
    """Open a big-file store as a seekable, read-only binary file.

    Nothing is transferred until the first read, and then only the block that read
    landed in. Suitable for readers that accept a file object; readers that want a path
    need :func:`download_to_scratch` instead, and readers that walk most of the object
    are better served by :func:`mikro_next.io.download.download_file`.

    Args:
        store_id: The ID of the big-file store to read.
        block_size: Bytes fetched per request, and the cache's granularity.
        cache: ``True`` (default) keeps fetched blocks in a bounded LRU; ``False``
            keeps nothing; a string names an fsspec policy directly.
        max_cached_blocks: LRU size when caching. Memory ceiling is this times
            ``block_size``.
        rath: Optional rath client override; the active one is captured otherwise.
        datalayer: Optional DataLayer override; the active one is captured otherwise.

    The cache lives on the handle and dies with it -- two `open()` calls for the same
    object share nothing. Reading one object repeatedly means keeping one handle open,
    not opening it again.
    """
    granted = _bigfile_granted_object(store_id, rath=rath, datalayer=datalayer)
    return RemoteFile(
        granted,
        block_size=block_size,
        cache=cache,
        max_cached_blocks=max_cached_blocks,
    )


async def aopen_remote_file(
    store_id: str,
    *,
    block_size: int | None = None,
    cache: bool | str = True,
    max_cached_blocks: int = 32,
    rath: MikroNextRath | None = None,
    datalayer: DataLayer | None = None,
) -> RemoteFile:
    """Open a big-file store as a seekable file, without blocking the event loop.

    The handle this returns is still a blocking one -- `read` is a synchronous ranged
    GET, because that is the protocol the readers on the other side speak. Only the
    opening is made safe here; the reading has to be handed to a thread, as in
    ``await asyncio.to_thread(tifffile.imread, handle)``.
    """
    import asyncio

    return await asyncio.to_thread(
        open_remote_file,
        store_id,
        block_size=block_size,
        cache=cache,
        max_cached_blocks=max_cached_blocks,
        rath=rath,
        datalayer=datalayer,
    )


def download_to_scratch(
    store_id: str,
    file_name: str | None = None,
    *,
    prefix: str = "mikro_file_",
    directory: str | None = None,
) -> str:
    """Download a big-file store into a temporary directory and return the local path.

    For readers that take a path rather than a file object -- which in practice means
    readers whose real work happens in C or on a JVM, where a Python object with a
    `seek` method is not visible at all.

    Downloads land in a directory of their own rather than the working directory, so
    nothing the download creates outlives the caller. Where that directory goes is
    ``directory``, else :data:`SCRATCH_ENV`, else ``TMPDIR``.

    **Naming the directory is the caller's job when the file is large.** Neither a `File`
    nor a `BigFileStore` carries a size, so nothing here can know whether the default has
    room -- and on a box whose ``/tmp`` is a tmpfs, the default is RAM, where a file bigger
    than memory does not fail cleanly but dies partway through with the machine in swap.
    A caller that knows the size should say where the bytes go; ``testing/imaris_converter_live.py``
    is the worked example, and it *refuses* rather than warns.
    """
    import os
    import shutil
    import tempfile

    from mikro_next.io.download import download_file

    root = str(directory or os.environ.get(SCRATCH_ENV) or tempfile.gettempdir())
    os.makedirs(root, exist_ok=True)
    directory = tempfile.mkdtemp(prefix=prefix, dir=root)
    try:
        return download_file(
            store_id, file_name=os.path.join(directory, file_name or "download")
        )
    except BaseException:
        # A download that dies partway leaves a partial file behind, and the caller
        # never learns the directory's name to clean it up -- so it has to go here or
        # it stays until the machine is rebooted, holding whatever was transferred.
        shutil.rmtree(directory, ignore_errors=True)
        raise
