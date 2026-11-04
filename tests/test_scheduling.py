"""Every dask computation mikro runs shares one pool, whichever thread it is called from.

dask's "threads" scheduler keeps a pool per calling thread and per ``num_workers`` until
the calling thread dies (``dask.threaded.pools``). Upload paths call it from executor
threads that never die, so each new (thread, size) pair used to leave a pool behind.
"""

import contextvars
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import dask
import dask.array as da
import dask.threaded
import numpy as np
import xarray as xr
from obstore.store import MemoryStore
from zarr.storage import ObjectStore as ZarrObjectStore
from zarr.storage import StorePath

from mikro.api.schema import ValueHistogramInput
from mikro.io.obstore import write_dataarray_to_zarr
from mikro.io.scheduling import compute_numpy, dask_scheduler, pool_size
from mikro.pyramid import build_pyramid


def _dask_pools() -> int:
    return sum(len(by_workers) for by_workers in dask.threaded.pools.values())


def _lazy(side: int, depth: int = 4) -> xr.DataArray:
    data = da.random.randint(0, 4000, (2, depth, side, side), chunks=(1, 1, side, side))
    return xr.DataArray(data.astype("uint16"), dims=["c", "z", "y", "x"])


def _write(index: int, side: int) -> None:
    write_dataarray_to_zarr(StorePath(ZarrObjectStore(MemoryStore()), f"a{index}"), _lazy(side))


def test_writes_from_long_lived_threads_add_no_pools_or_threads() -> None:
    # Like asyncio's default executor: the calling threads stay alive between uploads,
    # and the sizes differ, so dask's own scheduler would be asked for new worker counts.
    sides = [64, 96, 128, 160]
    before = _dask_pools()
    with ThreadPoolExecutor(max_workers=4) as callers:
        for round_ in range(3):
            list(callers.map(_write, range(8 * round_, 8 * round_ + 8), sides * 2))
            # dask's own cache: one pool per (calling thread, num_workers), kept until
            # the calling thread dies. These callers are alive, so any entry is a leak.
            assert _dask_pools() == before
        ours = [t for t in threading.enumerate() if t.name.startswith("mikro-dask")]
        assert len(ours) <= pool_size()


def test_a_computation_never_runs_more_tasks_than_it_was_allowed() -> None:
    running = 0
    peak = 0
    lock = threading.Lock()

    def task(i: int) -> int:
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        time.sleep(0.02)
        with lock:
            running -= 1
        return i

    limit = min(3, pool_size())
    results = dask.compute(*[dask.delayed(task)(i) for i in range(12)], scheduler=dask_scheduler(limit))
    assert list(results) == list(range(12))
    assert peak <= limit


def test_a_task_that_computes_dask_itself_does_not_deadlock() -> None:
    inner = da.ones((16, 16), chunks=(4, 4))

    def nested(_: int) -> float:
        return float(compute_numpy(inner).sum())

    # More nesting tasks than pool threads: without the guard each would wait on a pool
    # whose every thread is one of them.
    tasks = [dask.delayed(nested)(i) for i in range(pool_size() * 2)]
    done: list[tuple[float, ...]] = []
    worker = threading.Thread(target=lambda: done.append(dask.compute(*tasks, scheduler=dask_scheduler())))
    worker.start()
    worker.join(timeout=60)
    assert not worker.is_alive(), "nested dask computation deadlocked on the shared pool"
    assert done and all(value == 256.0 for value in done[0])


def test_tasks_see_the_callers_context() -> None:
    marker: contextvars.ContextVar[str] = contextvars.ContextVar("marker", default="unset")
    marker.set("caller")
    (seen,) = dask.compute(dask.delayed(marker.get)(), scheduler=dask_scheduler())
    assert seen == "caller"


def test_histogram_and_materialized_pyramid_add_no_pools() -> None:
    values = np.random.random((32, 32, 32))
    lazy = xr.DataArray(da.from_array(values, chunks=(8, 32, 32)), dims=["z", "y", "x"])

    def from_worker() -> tuple[ValueHistogramInput, list[xr.DataArray]]:
        return ValueHistogramInput.from_array(lazy, bins=8), build_pyramid(
            lazy, levels=3, method="mean", materialize=True
        )

    before = _dask_pools()
    with ThreadPoolExecutor(max_workers=1) as caller:
        histogram, pyramid = caller.submit(from_worker).result()
        assert _dask_pools() == before

    assert sum(histogram.histogram) == values.size
    np.testing.assert_allclose(compute_numpy(pyramid[0]), values)


def test_compute_numpy_passes_numpy_and_xarray_through() -> None:
    plain = np.arange(6).reshape(2, 3)
    assert compute_numpy(plain) is plain or np.array_equal(compute_numpy(plain), plain)
    labelled = xr.DataArray(plain, dims=["y", "x"])
    np.testing.assert_array_equal(compute_numpy(labelled, dtype=float), plain.astype(float))
