"""Tests for reading a remote object as a seekable file.

The interesting behaviour is not "does it read bytes" but what happens around the edges
of a grant: what a read does when the credentials it was opened with have expired, and
how many requests a small read costs. Both are things that only show up in production
otherwise, and both show up there as something else -- an expired grant looks like a
corrupt file, and a bad cache policy looks like the network being slow.
"""

import os
import random
from types import SimpleNamespace

import obstore
import pytest
from obstore.exceptions import GenericError, NotFoundError, PermissionDeniedError
from obstore.store import MemoryStore

from mikro_next.api.schema import BigFileStore, File
from mikro_next.io.errors import DownloadError
from mikro_next.io.remote import GrantedObject, RemoteFile, download_to_scratch
from mikro_next.traits import FileTrait, HasDownloadAccessor

PAYLOAD = bytes(random.Random(1234).getrandbits(8) for _ in range(300_000))


@pytest.fixture
def stored() -> "tuple[MemoryStore, str]":
    """A MemoryStore holding PAYLOAD under a key."""
    store = MemoryStore()
    obstore.put(store, "files/big.bin", PAYLOAD)
    return store, "files/big.bin"


@pytest.fixture
def handle(stored) -> RemoteFile:
    store, key = stored
    return RemoteFile(GrantedObject.from_store(store, key), block_size=65_536)


def _grant(key: str = "files/big.bin", expires_in: int = 3600) -> SimpleNamespace:
    return SimpleNamespace(
        access_key="access",
        secret_key="secret",
        session_token="token",
        bucket="bucket",
        key=key,
        path=f"bucket/{key}",
        expires_in=expires_in,
    )


# --- the file protocol ------------------------------------------------------------


def test_reports_size_without_reading(stored) -> None:
    store, key = stored
    assert GrantedObject.from_store(store, key).size() == len(PAYLOAD)


def test_reads_whole_object(handle: RemoteFile) -> None:
    assert handle.read() == PAYLOAD


def test_is_readable_and_seekable(handle: RemoteFile) -> None:
    assert handle.readable()
    assert handle.seekable()
    assert not handle.writable()


def test_seeks_relative_to_the_end(handle: RemoteFile) -> None:
    """`seek(0, SEEK_END)` is the move TIFF makes to find its IFDs, so it has to work
    without the file having been read forwards first."""
    handle.seek(-128, os.SEEK_END)
    assert handle.read(128) == PAYLOAD[-128:]
    assert handle.tell() == len(PAYLOAD)


def test_reads_backwards(handle: RemoteFile) -> None:
    handle.seek(200_000)
    tail = handle.read(1_000)
    handle.seek(1_000)
    head = handle.read(1_000)

    assert tail == PAYLOAD[200_000:201_000]
    assert head == PAYLOAD[1_000:2_000]


@pytest.mark.parametrize("seed", range(5))
def test_random_access_matches_the_payload(handle: RemoteFile, seed: int) -> None:
    """Reads that straddle block boundaries are where a cache implementation goes wrong,
    so the offsets are chosen to land on both sides of one."""
    rng = random.Random(seed)
    for _ in range(50):
        offset = rng.randrange(0, len(PAYLOAD))
        length = rng.randrange(1, 150_000)
        handle.seek(offset)
        assert handle.read(length) == PAYLOAD[offset : offset + length]


def test_readinto_fills_the_buffer(handle: RemoteFile) -> None:
    buffer = bytearray(64)
    handle.seek(4_096)

    assert handle.readinto(buffer) == 64
    assert bytes(buffer) == PAYLOAD[4_096:4_160]


def test_reading_at_the_end_returns_empty(handle: RemoteFile) -> None:
    handle.seek(len(PAYLOAD))
    assert handle.read(100) == b""


def test_reading_past_the_end_truncates(handle: RemoteFile) -> None:
    handle.seek(len(PAYLOAD) - 5)
    assert handle.read(100) == PAYLOAD[-5:]


def test_close_is_idempotent(handle: RemoteFile) -> None:
    handle.close()
    handle.close()
    assert handle.closed


# --- what the reads cost ----------------------------------------------------------


def test_a_small_header_read_costs_few_requests(stored, monkeypatch) -> None:
    """The whole point of the class. Reading a kilobyte out of a 300 KB object must not
    transfer the object -- if this assertion ever starts failing, the class has quietly
    become a slow download."""
    store, key = stored
    calls: list[tuple[int, int]] = []
    real = obstore.get_range

    def counting(store_, path, *, start, end=None, length=None):
        calls.append((start, end))
        return real(store_, path, start=start, end=end, length=length)

    monkeypatch.setattr("mikro_next.io.remote.obstore.get_range", counting)

    handle = RemoteFile(GrantedObject.from_store(store, key), block_size=65_536)
    assert handle.read(1_024) == PAYLOAD[:1_024]

    # One request, and it transfers the block the read landed in rather than the object.
    assert len(calls) == 1
    assert calls[0][1] - calls[0][0] < len(PAYLOAD) // 4


def test_cache_false_passes_reads_through(stored) -> None:
    handle = RemoteFile(GrantedObject.from_store(store=stored[0], key=stored[1]), cache=False)
    assert handle.read(10) == PAYLOAD[:10]


# --- grants expire ----------------------------------------------------------------


def test_refreshes_the_grant_before_it_expires(stored, monkeypatch) -> None:
    """A handle open for longer than its grant must re-mint rather than fail. The margin
    is what makes this happen before the 403 rather than after it."""
    store, key = stored
    resolved = []

    def resolve():
        resolved.append(1)
        return _grant(key, expires_in=61), "http://example.invalid"

    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *a, **k: store)

    # A clock under the test's control -- the real one starts at the machine's uptime,
    # so a hardcoded "later" is only later on a machine that booted recently.
    now = [1_000.0]
    monkeypatch.setattr("mikro_next.io.remote.time.monotonic", lambda: now[0])

    granted = GrantedObject(resolve)
    granted.store_and_key()
    assert len(resolved) == 1

    # 61s of lifetime minus the 60s margin leaves a one-second window. Stay inside it,
    # then step past it.
    now[0] = 1_000.5
    granted.store_and_key()
    assert len(resolved) == 1

    now[0] = 1_002.0
    granted.store_and_key()
    assert len(resolved) == 2


def test_a_grant_without_an_expiry_is_never_refreshed(stored, monkeypatch) -> None:
    store, key = stored
    resolved = []

    def resolve():
        resolved.append(1)
        return SimpleNamespace(**{**vars(_grant(key)), "expires_in": None}), "http://x"

    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *a, **k: store)
    granted = GrantedObject(resolve)

    granted.store_and_key()
    monkeypatch.setattr("mikro_next.io.remote.time.monotonic", lambda: 1e12)
    granted.store_and_key()

    assert len(resolved) == 1


def test_denied_read_re_mints_the_grant_once(stored, monkeypatch) -> None:
    """Clock skew can put a 403 inside the safety margin. One re-mint covers it."""
    store, key = stored
    resolved = []

    def resolve():
        resolved.append(1)
        return _grant(key), "http://example.invalid"

    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *a, **k: store)

    attempts = []
    real = obstore.get_range

    def flaky(store_, path, *, start, end=None, length=None):
        attempts.append(start)
        if len(attempts) == 1:
            raise PermissionDeniedError("expired")
        return real(store_, path, start=start, end=end, length=length)

    monkeypatch.setattr("mikro_next.io.remote.obstore.get_range", flaky)

    handle = RemoteFile(GrantedObject(resolve), size=len(PAYLOAD))
    assert handle.read(16) == PAYLOAD[:16]
    assert len(resolved) == 2


def test_persistent_denial_is_reported_not_retried_forever(stored, monkeypatch) -> None:
    store, key = stored
    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *a, **k: store)
    monkeypatch.setattr(
        "mikro_next.io.remote.obstore.get_range",
        lambda *a, **k: (_ for _ in ()).throw(PermissionDeniedError("nope")),
    )

    handle = RemoteFile(GrantedObject(lambda: (_grant(key), "http://x")), size=len(PAYLOAD))

    with pytest.raises(DownloadError):
        handle.read(16)


# --- failures are translated ------------------------------------------------------


def test_transient_error_is_retried(stored, monkeypatch) -> None:
    store, key = stored
    attempts = []
    real = obstore.get_range

    def flaky(store_, path, *, start, end=None, length=None):
        attempts.append(start)
        if len(attempts) == 1:
            raise GenericError("503")
        return real(store_, path, start=start, end=end, length=length)

    monkeypatch.setattr("mikro_next.io.remote.obstore.get_range", flaky)
    monkeypatch.setattr("mikro_next.io.remote.BACKOFF_SECONDS", 0)

    handle = RemoteFile(GrantedObject.from_store(store, key))
    assert handle.read(16) == PAYLOAD[:16]
    assert len(attempts) == 2


def test_exhausted_retries_raise_download_error(stored, monkeypatch) -> None:
    """A raw obstore error reaching the reader above arrives as a parse failure, which
    sends whoever is debugging it to look at the bytes instead of the network."""
    store, key = stored
    monkeypatch.setattr(
        "mikro_next.io.remote.obstore.get_range",
        lambda *a, **k: (_ for _ in ()).throw(GenericError("503")),
    )
    monkeypatch.setattr("mikro_next.io.remote.BACKOFF_SECONDS", 0)

    handle = RemoteFile(GrantedObject.from_store(store, key))

    with pytest.raises(DownloadError, match="after 3 attempts"):
        handle.read(16)


def test_object_vanishing_is_reported_immediately(stored, monkeypatch) -> None:
    store, key = stored
    monkeypatch.setattr(
        "mikro_next.io.remote.obstore.get_range",
        lambda *a, **k: (_ for _ in ()).throw(NotFoundError("gone")),
    )

    handle = RemoteFile(GrantedObject.from_store(store, key))

    with pytest.raises(DownloadError, match="disappeared"):
        handle.read(16)


def test_writing_is_refused(handle: RemoteFile) -> None:
    with pytest.raises(NotImplementedError):
        handle._initiate_upload()


# --- the traits that expose all this ----------------------------------------------


class _Store(HasDownloadAccessor):
    id: str = "store-id"
    key: str = "files/big.bin"


class _File(FileTrait):
    def __init__(self, store: _Store) -> None:
        self.store = store


def test_accessor_open_yields_a_handle_and_closes_it(stored, monkeypatch) -> None:
    store, key = stored
    handle = RemoteFile(GrantedObject.from_store(store, key))
    monkeypatch.setattr("mikro_next.io.remote.open_remote_file", lambda *a, **k: handle)

    with _Store().open() as opened:
        assert opened.read(8) == PAYLOAD[:8]

    assert handle.closed


def test_accessor_open_passes_the_cache_policy_through(stored, monkeypatch) -> None:
    """`cache` is the knob that decides whether a scattered reader costs one request or
    hundreds, so it has to reach the file rather than stop at the trait."""
    store, key = stored
    seen: dict[str, object] = {}

    def capture(store_id, *, block_size=None, cache=True, max_cached_blocks=32, **kwargs):
        seen.update(
            store_id=store_id,
            block_size=block_size,
            cache=cache,
            max_cached_blocks=max_cached_blocks,
        )
        return RemoteFile(GrantedObject.from_store(store, key))

    monkeypatch.setattr("mikro_next.io.remote.open_remote_file", capture)

    with _Store().open(cache=False, block_size=4096, max_cached_blocks=8):
        pass

    assert seen == {
        "store_id": "store-id",
        "block_size": 4096,
        "cache": False,
        "max_cached_blocks": 8,
    }


def test_file_trait_open_delegates_to_its_store(stored, monkeypatch) -> None:
    store, key = stored
    monkeypatch.setattr(
        "mikro_next.io.remote.open_remote_file",
        lambda *a, **k: RemoteFile(GrantedObject.from_store(store, key)),
    )

    with _File(_Store()).open() as handle:
        assert handle.read(4) == PAYLOAD[:4]


def _real_file(name: str = "acquisition.tif") -> File:
    """A real `File` from the generated schema, not a stand-in.

    `as_path` reaches through `store` for the id and key, and the doubles above cannot
    show whether that reach matches the type the server actually returns -- `File`
    carries `FileTrait`, its store is a frozen `BigFileStore`, and the field names have
    to line up for any of this to work in production.
    """
    return File(
        id="file-id",
        name=name,
        store=BigFileStore(
            id="store-id",
            key="a3f9c2e1",
            bucket="bucket",
            path="bucket/a3f9c2e1",
            presignedUrl="http://example.invalid/a3f9c2e1",
        ),
    )


def test_as_path_yields_a_real_file_and_removes_it(tmp_path, monkeypatch) -> None:
    """Native and JVM readers open the path themselves, so `as_path` owes them a file
    that exists -- and owes the disk its removal afterwards."""
    directory = tmp_path / "scratch"
    directory.mkdir()

    def fake_download(store_id, file_name=None, prefix="mikro_file_"):
        target = directory / (file_name or "download")
        target.write_bytes(PAYLOAD[:100])
        return str(target)

    monkeypatch.setattr("mikro_next.io.remote.download_to_scratch", fake_download)

    with _real_file().as_path() as path:
        assert os.path.exists(path)
        assert open(path, "rb").read() == PAYLOAD[:100]

    assert not os.path.exists(directory)


def test_as_path_keeps_the_extension(tmp_path, monkeypatch) -> None:
    """Store keys are opaque -- this one is a bare UUID. A reader that dispatches on
    the suffix would refuse the file under that name, so the file's own name wins."""
    seen: dict[str, object] = {}

    def fake_download(store_id, file_name=None, prefix="mikro_file_"):
        seen["file_name"] = file_name
        target = tmp_path / str(file_name)
        target.write_bytes(b"II*\x00")
        return str(target)

    monkeypatch.setattr("mikro_next.io.remote.download_to_scratch", fake_download)

    with _real_file("acquisition.tif").as_path() as path:
        assert os.path.basename(path) == "acquisition.tif"

    assert seen["file_name"] == "acquisition.tif"


def test_as_path_falls_back_to_the_key(tmp_path, monkeypatch) -> None:
    def fake_download(store_id, file_name=None, prefix="mikro_file_"):
        target = tmp_path / str(file_name)
        target.write_bytes(b"x")
        return str(target)

    monkeypatch.setattr("mikro_next.io.remote.download_to_scratch", fake_download)

    with _File(_Store()).as_path() as path:
        assert os.path.basename(path) == "big.bin"


def test_download_to_scratch_honours_the_scratch_environment(tmp_path, monkeypatch) -> None:
    """Not the working directory, and not TMPDIR when MIKRO_SCRATCH_DIR says otherwise.

    The variable is the only lever a caller has over where a multi-gigabyte download
    lands, and `testing/imaris_converter_live.py` sets it for exactly that reason."""
    monkeypatch.setenv("MIKRO_SCRATCH_DIR", str(tmp_path))
    captured: dict[str, object] = {}

    def fake_download_file(store_id, file_name, datalayer=None):
        captured.update(store_id=store_id, file_name=file_name)
        return file_name

    monkeypatch.setattr("mikro_next.io.download.download_file", fake_download_file)

    result = download_to_scratch("store-id", "big.bin")

    # A directory of its own under the named root, so nothing collides and the whole
    # thing can be removed at once.
    assert os.path.dirname(os.path.dirname(result)) == str(tmp_path)
    assert os.path.basename(result) == "big.bin"
    assert captured["store_id"] == "store-id"


def test_download_to_scratch_takes_an_explicit_directory(tmp_path, monkeypatch) -> None:
    """A caller who knows the file is 27 GB names the disk, rather than being warned about
    the default after the fact. `directory=` wins over the environment."""
    monkeypatch.setenv("MIKRO_SCRATCH_DIR", str(tmp_path / "ignored"))
    named = tmp_path / "named"
    named.mkdir()
    monkeypatch.setattr(
        "mikro_next.io.download.download_file", lambda store_id, file_name, datalayer=None: file_name
    )

    result = download_to_scratch("store-id", "big.bin", directory=str(named))

    assert os.path.dirname(os.path.dirname(result)) == str(named)


def test_download_to_scratch_removes_the_directory_when_the_download_fails(
    tmp_path, monkeypatch
) -> None:
    """A download that dies partway is the case that matters -- the caller never learns
    the directory's name, so nothing else can clean it up."""
    root = tmp_path / "scratch"
    root.mkdir()

    def failing(store_id, file_name, datalayer=None):
        open(file_name, "wb").write(b"half a fi")
        raise DownloadError("connection reset")

    monkeypatch.setattr("mikro_next.io.download.download_file", failing)

    with pytest.raises(DownloadError):
        download_to_scratch("store-id", "big.bin", directory=str(root))

    # The root the caller named survives; the directory made inside it does not.
    assert os.path.exists(root)
    assert list(root.iterdir()) == []


def test_a_real_reader_can_parse_through_the_handle(stored, monkeypatch) -> None:
    """The claim this whole module rests on: a reader written against Python file
    objects works unmodified. `tifffile` is a fair test of it -- it seeks to the end for
    the IFD offsets, then hops backwards through the file, which is exactly the access
    pattern that a naive stream would fail on.
    """
    tifffile = pytest.importorskip("tifffile")
    numpy = pytest.importorskip("numpy")

    image = numpy.arange(256 * 256, dtype="uint16").reshape(256, 256)
    buffer = __import__("io").BytesIO()
    tifffile.imwrite(buffer, image)

    store = MemoryStore()
    obstore.put(store, "files/image.tif", buffer.getvalue())

    handle = RemoteFile(
        GrantedObject.from_store(store, "files/image.tif"), block_size=4_096
    )
    with tifffile.TiffFile(handle) as tif:
        assert numpy.array_equal(tif.asarray(), image)


# --- caching -----------------------------------------------------------------------


def _count_requests(monkeypatch) -> "list[tuple[int, int]]":
    """Record every range request made from here on."""
    calls: list[tuple[int, int]] = []
    real = obstore.get_range

    def counting(store_, path, *, start, end=None, length=None):
        calls.append((start, end))
        return real(store_, path, start=start, end=end, length=length)

    monkeypatch.setattr("mikro_next.io.remote.obstore.get_range", counting)
    return calls


def test_revisiting_an_offset_is_free_when_caching(stored, monkeypatch) -> None:
    """The reason `cache=True` is the default. A reader bouncing between its index and
    its data revisits offsets constantly, and each revisit must not be a request."""
    store, key = stored
    calls = _count_requests(monkeypatch)

    handle = RemoteFile(GrantedObject.from_store(store, key), block_size=65_536)
    for offset in [0, 250_000] * 3:
        handle.seek(offset)
        handle.read(64)

    assert len(calls) == 2


def test_readahead_refetches_on_every_hop(stored, monkeypatch) -> None:
    """The contrast that justifies the default: fsspec's usual policy holds one block,
    so the same bouncing pattern pays for every hop."""
    store, key = stored
    calls = _count_requests(monkeypatch)

    handle = RemoteFile(
        GrantedObject.from_store(store, key), block_size=65_536, cache="readahead"
    )
    for offset in [0, 250_000] * 3:
        handle.seek(offset)
        handle.read(64)

    assert len(calls) == 6


def test_cache_false_fetches_exactly_what_was_asked_for(stored, monkeypatch) -> None:
    store, key = stored
    calls = _count_requests(monkeypatch)

    handle = RemoteFile(GrantedObject.from_store(store, key), cache=False)
    handle.seek(1_000)
    assert handle.read(64) == PAYLOAD[1_000:1_064]

    assert calls == [(1_000, 1_064)]


def test_caching_a_read_past_the_end_truncates_rather_than_raising(stored) -> None:
    """`AbstractBufferedFile.read` hands `loc + length` to the cache unclamped, and
    `BlockCache` raises on a block past the last one. Asking for more than remains is
    how a short read is spelled, so this has to truncate."""
    store, key = stored
    handle = RemoteFile(GrantedObject.from_store(store, key), block_size=65_536)

    handle.seek(len(PAYLOAD) - 100)
    assert handle.read(500_000) == PAYLOAD[-100:]


def test_the_memory_ceiling_is_bounded(stored, monkeypatch) -> None:
    """A cache that grew without limit would be a slow way to run out of memory. Reading
    a whole object through a two-block LRU must not retain more than two blocks."""
    store, key = stored
    handle = RemoteFile(
        GrantedObject.from_store(store, key), block_size=65_536, max_cached_blocks=2
    )

    assert handle.read() == PAYLOAD

    # Five blocks were touched and two are resident -- an equality, so this cannot start
    # passing vacuously if the LRU ever stops evicting.
    info = handle.cache.cache_info()
    assert info.misses == 5
    assert info.currsize == 2


def test_cache_policy_maps_the_flag(stored) -> None:
    store, key = stored

    def cache_of(**kwargs):
        return type(RemoteFile(GrantedObject.from_store(store, key), **kwargs).cache).__name__

    assert cache_of() == "BlockCache"
    assert cache_of(cache=True) == "BlockCache"
    assert cache_of(cache=False) == "BaseCache"
    assert cache_of(cache="all") == "AllBytes"
    assert cache_of(cache="readahead") == "ReadAheadCache"
