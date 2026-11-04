"""One long-lived thread pool for every dask computation mikro runs.

dask's ``"threads"`` scheduler keeps a pool per *calling thread* and per ``num_workers``
(``dask.threaded.pools``), and drops one only when its calling thread dies. mikro computes
from worker threads -- ``asyncio.to_thread``, koil's executor -- which never die, and asks
for a different ``num_workers`` per array, so every upload from a new (thread, size) pair
left another pool of up to ``cpu_count`` threads behind for the life of the process. Each
of those threads holds its own malloc arena, so an idle agent that had converted a few
large files sat on hundreds of threads and gigabytes.

Here there is one pool, shared by every caller, and a per-call cap on how many of its
threads one computation may occupy at once:

    dask.compute(x, scheduler=dask_scheduler())
    dask.array.store(x, target, scheduler=dask_scheduler(4))
    compute_numpy(x)   # np.asarray for numpy, dask and dask-backed xarray alike
"""

from __future__ import annotations

import atexit
import contextvars
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from typing import Any

import numpy as np

THREAD_NAME_PREFIX = "mikro-dask"

_pool: ThreadPoolExecutor | None = None
_pool_lock = threading.Lock()
_worker = threading.local()


def _mark_worker() -> None:
    _worker.active = True


def pool_size() -> int:
    """Threads in the shared pool: one per usable core.

    dask's count, which honours CPU affinity and a container's cgroup quota where
    ``os.cpu_count()`` reports every core of the host.
    """
    from dask.system import CPU_COUNT

    return max(1, int(CPU_COUNT))


def _shared_pool() -> ThreadPoolExecutor:
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = ThreadPoolExecutor(
                max_workers=pool_size(),
                thread_name_prefix=THREAD_NAME_PREFIX,
                initializer=_mark_worker,
            )
            atexit.register(_pool.shutdown, wait=False, cancel_futures=True)
        return _pool


def _submit(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future:  # noqa: ANN401
    # Each task runs in a copy of the submitter's context, as dask's own
    # ContextAwareThreadPoolExecutor does: a contextvar set by the caller stays visible.
    context = contextvars.copy_context()
    return _shared_pool().submit(context.run, fn, *args, **kwargs)


def dask_scheduler(num_workers: int | None = None) -> Callable[..., Any] | str:
    """A dask ``scheduler=`` that runs on the shared pool, at most `num_workers` tasks at once.

    ``num_workers`` bounds the computation's own in-flight tasks (and so its memory: a
    writer sizes it to its shard budget); ``None`` allows the whole pool. Many computations
    may share the pool at once; together they never add a thread to it.

    Called from inside one of the pool's own threads -- a task that computes another dask
    array -- it answers ``"sync"``: the nested computation would otherwise wait on a pool
    whose threads are busy waiting on it.
    """
    if getattr(_worker, "active", False):
        return "sync"
    from dask.local import get_async

    limit = pool_size() if num_workers is None else max(1, min(int(num_workers), pool_size()))
    return partial(get_async, _submit, limit)


def compute_numpy(value: Any, dtype: Any = None) -> np.ndarray:  # noqa: ANN401
    """``np.asarray(value, dtype)``, with any dask computation run on the shared pool.

    ``np.asarray`` on a dask array (or an xarray over one) computes it with dask's default
    scheduler -- a pool per calling thread. This computes it here first.
    """
    data = getattr(value, "data", value)  # xarray.DataArray -> its array
    if hasattr(data, "dask"):
        import dask

        (value,) = dask.compute(data, scheduler=dask_scheduler())
    return np.asarray(value, dtype=dtype)
