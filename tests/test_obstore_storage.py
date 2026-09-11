from io import BytesIO
from types import SimpleNamespace

import dask.array as da
import numpy as np
import obstore
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import xarray as xr
import zarr
from obstore.store import MemoryStore
from zarr.storage import ObjectStore as ZarrObjectStore
from zarr.storage import StorePath

from mikro_next.io.download import download_file
from mikro_next.io.obstore import (
    ParquetDatasetViaObstore,
    awrite_dataarray_to_zarr,
    write_dataarray_to_zarr,
)
from mikro_next.scalars import ArrayLike


def test_parquet_dataset_via_obstore_reads_dataframe() -> None:
    store = MemoryStore()
    dataframe = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    buffer = BytesIO()

    pq.write_table(pa.Table.from_pandas(dataframe), buffer)
    obstore.put(store, "tables/example.parquet", buffer.getvalue())

    dataset = ParquetDatasetViaObstore(store, "tables/example.parquet")

    assert dataset.read_pandas().to_pandas().equals(dataframe)


def test_download_file_reads_bytes_via_obstore(tmp_path, monkeypatch) -> None:
    store = MemoryStore()
    payload = b"hello via obstore"
    target = tmp_path / "download.bin"
    credentials = SimpleNamespace(
        access_key="access",
        secret_key="secret",
        session_token="token",
        bucket="bucket",
        key="files/download.bin",
        path="bucket/files/download.bin",
    )

    obstore.put(store, credentials.key, payload)

    monkeypatch.setattr(
        "mikro_next.io.download.unkoil",
        lambda function, store_id: (credentials, "http://example.invalid"),
    )
    monkeypatch.setattr("mikro_next.io.download.create_s3_store", lambda *_args: store)

    result = download_file("store-id", str(target))

    assert result == str(target)
    assert target.read_bytes() == payload


def _store_path(key: str = "arr") -> StorePath:
    return StorePath(ZarrObjectStore(MemoryStore()), key)


def test_write_dataarray_to_zarr_numpy_roundtrips_with_chunks() -> None:
    array = xr.DataArray(
        np.arange(1 * 1 * 4 * 64 * 64, dtype="uint16").reshape(1, 1, 4, 64, 64),
        dims=list("ctzyx"),
    )
    sp = _store_path()

    write_dataarray_to_zarr(sp, array)

    back = zarr.open_array(sp, mode="r")
    assert back.shape == (1, 1, 4, 64, 64)
    assert np.array_equal(back[:], array.to_numpy())


def test_write_dataarray_to_zarr_streams_dask_arrays() -> None:
    # A larger array so rechunk actually splits it into multiple on-disk chunks.
    source = np.arange(2 * 50 * 2048 * 2048, dtype="uint16").reshape(1, 2, 50, 2048, 2048)
    array = xr.DataArray(
        da.from_array(source, chunks=(1, 1, 10, 2048, 2048)), dims=list("ctzyx")
    )
    sp = _store_path("big")

    write_dataarray_to_zarr(sp, array)

    back = zarr.open_array(sp, mode="r")
    # rechunk targets ~20MB chunks, so the z axis is split rather than written whole.
    assert back.chunks[2] < 50
    assert np.array_equal(back[:], source)


@pytest.mark.asyncio
async def test_awrite_dataarray_to_zarr_roundtrips() -> None:
    array = xr.DataArray(
        np.arange(1 * 1 * 2 * 32 * 32, dtype="float32").reshape(1, 1, 2, 32, 32),
        dims=list("ctzyx"),
    )
    sp = _store_path("async")

    await awrite_dataarray_to_zarr(sp, array)

    back = zarr.open_array(sp, mode="r")
    assert np.array_equal(back[:], array.to_numpy())


@pytest.mark.asyncio
async def test_awrite_dataarray_to_zarr_streams_dask_arrays(monkeypatch) -> None:
    # A larger array so rechunk actually splits it into multiple on-disk chunks.
    source = np.arange(2 * 50 * 2048 * 2048, dtype="uint16").reshape(1, 2, 50, 2048, 2048)
    array = xr.DataArray(
        da.from_array(source, chunks=(1, 1, 10, 2048, 2048)), dims=list("ctzyx")
    )
    sp = _store_path("async-big")

    # Guard against out-of-core breakage: the whole array must never be pulled
    # into memory in one shot via Array.compute(). Streaming uses dask.array.store
    # (per-block stores), not a single compute of the full array.
    import dask.array.core as dac

    original_compute = dac.Array.compute

    def _fail_on_full_compute(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        raise AssertionError(
            "dask array was fully computed into memory; out-of-core streaming was broken"
        )

    monkeypatch.setattr(dac.Array, "compute", _fail_on_full_compute)
    try:
        await awrite_dataarray_to_zarr(sp, array)
    finally:
        monkeypatch.setattr(dac.Array, "compute", original_compute)

    back = zarr.open_array(sp, mode="r")
    # rechunk targets ~20MB chunks, so the z axis is split rather than written whole.
    assert back.chunks[2] < 50
    assert np.array_equal(back[:], source)


def test_array_like_preserves_labels() -> None:
    # ArrayLike preserves the caller's labelled dims/order verbatim (no ctzyx).
    labeled = xr.DataArray(np.zeros((4, 8, 8, 2), dtype="uint16"), dims=["z", "y", "x", "c"])
    arr = ArrayLike.validate(labeled)
    assert arr.value.dims == ("z", "y", "x", "c")
    assert arr.value.shape == (4, 8, 8, 2)

    # Bare arrays carry no labels, so xarray's default names are assigned.
    bare = ArrayLike.validate(np.zeros((3, 4), dtype="uint16"))
    assert bare.value.dims == ("dim_0", "dim_1")


def test_write_dataarray_to_zarr_shards_large_dask_arrays() -> None:
    # A >64 MiB array with extents that are NOT multiples of the brick/shard sizes,
    # so boundary shards (partial trailing objects) are exercised end to end.
    source = np.arange(16 * 3000 * 3000, dtype="uint8").reshape(1, 1, 16, 3000, 3000)
    array = xr.DataArray(da.from_array(source, chunks=(1, 1, 8, 1500, 1500)), dims=list("ctzyx"))
    memory_store = MemoryStore()
    sp = StorePath(ZarrObjectStore(memory_store), "sharded")

    write_dataarray_to_zarr(sp, array)

    # The written zarr.json must match the reader contract exactly: a sole
    # top-level sharding_indexed codec whose shard is an exact per-axis multiple
    # of the inner chunk, with the crc32c-checksummed index declared.
    import json

    metadata = json.loads(bytes(obstore.get(memory_store, "sharded/zarr.json").bytes()))
    codecs = metadata["codecs"]
    assert len(codecs) == 1 and codecs[0]["name"] == "sharding_indexed"
    shard = metadata["chunk_grid"]["configuration"]["chunk_shape"]
    inner = codecs[0]["configuration"]["chunk_shape"]
    assert len(inner) == len(shard)
    assert all(s % i == 0 for s, i in zip(shard, inner))
    index_codecs = codecs[0]["configuration"]["index_codecs"]
    assert any(codec["name"] == "crc32c" for codec in index_codecs), (
        "a checksummed index must be declared, or readers slice the index short"
    )
    assert codecs[0]["configuration"]["index_location"] in ("start", "end")

    back = zarr.open_array(sp, mode="r")
    assert back.shards == tuple(shard)
    assert back.chunks == tuple(inner)
    assert np.array_equal(back[:], source)


def test_write_dataarray_to_zarr_leaves_small_arrays_unsharded() -> None:
    # Below the size threshold (small uploads, low pyramid levels) the layout is
    # exactly what it was before sharding existed: plain chunks, no sharding codec.
    array = xr.DataArray(
        np.zeros((1, 1, 4, 256, 256), dtype="uint16"),
        dims=list("ctzyx"),
    )
    sp = _store_path("small-unsharded")

    write_dataarray_to_zarr(sp, array)

    back = zarr.open_array(sp, mode="r")
    assert back.shards is None
    assert all(codec.__class__.__name__ != "ShardingCodec" for codec in back.metadata.codecs)


def test_write_dataarray_to_zarr_shards_numpy_arrays() -> None:
    # The sharded layout applies to eagerly-held arrays too, not just dask.
    source = np.arange(2 * 40 * 1024 * 1024, dtype="uint16").reshape(1, 2, 40, 1024, 1024)
    array = xr.DataArray(source, dims=list("ctzyx"))
    sp = _store_path("numpy-sharded")

    write_dataarray_to_zarr(sp, array)

    back = zarr.open_array(sp, mode="r")
    assert back.shards is not None
    assert np.array_equal(back[:], source)


def test_write_dataarray_to_zarr_honors_explicit_chunk_and_shard_overrides() -> None:
    array = xr.DataArray(np.zeros((8, 1024, 1024), dtype="uint8"), dims=["z", "y", "x"])
    sp = _store_path("override")

    write_dataarray_to_zarr(sp, array, chunks=(2, 256, 256), shards=(8, 1024, 1024))
    back = zarr.open_array(sp, mode="r")
    assert back.chunks == (2, 256, 256)
    assert back.shards == (8, 1024, 1024)

    # An explicit chunk shape without shards means "unsharded", even above the threshold.
    sp2 = _store_path("override-unsharded")
    write_dataarray_to_zarr(sp2, array, chunks=(2, 256, 256))
    assert zarr.open_array(sp2, mode="r").shards is None

    with pytest.raises(ValueError, match="without the inner chunks"):
        write_dataarray_to_zarr(_store_path("bad"), array, shards=(8, 1024, 1024))


@pytest.mark.asyncio
async def test_awrite_dataarray_to_zarr_forwards_sharding_overrides() -> None:
    array = xr.DataArray(np.zeros((8, 512, 512), dtype="uint8"), dims=["z", "y", "x"])
    sp = _store_path("async-override")

    await awrite_dataarray_to_zarr(sp, array, chunks=(2, 256, 256), shards=(4, 512, 512))

    back = zarr.open_array(sp, mode="r")
    assert back.chunks == (2, 256, 256)
    assert back.shards == (4, 512, 512)


def test_write_dataarray_to_zarr_streams_arbitrary_dims() -> None:
    # A large non-ctzyx array must chunk and round-trip via the generic chunker.
    source = np.arange(50 * 2048 * 2048, dtype="uint16").reshape(50, 2048, 2048)
    array = xr.DataArray(da.from_array(source, chunks=(10, 2048, 2048)), dims=["z", "y", "x"])
    sp = _store_path("arbitrary")

    write_dataarray_to_zarr(sp, array)

    back = zarr.open_array(sp, mode="r")
    # ~20MB target splits the z axis rather than writing all 50 planes in one chunk.
    assert back.chunks[0] < 50
    assert back.metadata.dimension_names == ("z", "y", "x")
    assert np.array_equal(back[:], source)
