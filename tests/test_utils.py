"""Unit tests for the client-side helpers that are not tied to one mutation."""

from collections.abc import Hashable

from mikro_next.errors import MikroError, NoDataLayerFound, NoMikroFound, NotQueriedError
from mikro_next.utils import chunk_and_shard, rechunk


def test_mikro_error_classes() -> None:
    """Every mikro error is catchable as a ``MikroError``."""
    base_error = MikroError("Base error message")
    assert str(base_error) == "Base error message", "Error message should be preserved"
    assert isinstance(base_error, Exception), "Should be an Exception"

    assert isinstance(NoMikroFound("No mikro instance found"), MikroError)
    assert isinstance(NoDataLayerFound("No data layer found"), MikroError)
    assert isinstance(NotQueriedError("Field not queried"), MikroError)


def test_rechunk_picks_chunks_for_a_large_stack() -> None:
    """Chunking is per-plane: a channel is never chunked together with another,
    and the spatial chunk is capped so one chunk stays a reasonable request."""
    sizes: dict[Hashable, int] = {"c": 3, "t": 10, "z": 20, "y": 1024, "x": 1024}
    chunks = rechunk(sizes)

    assert set(chunks) == set(sizes), "Every dimension should be assigned a chunk"
    assert chunks["x"] <= 2048, "X chunk should not exceed 2048"
    assert chunks["y"] <= 2048, "Y chunk should not exceed 2048"
    assert chunks["c"] == 1, "C chunk should be 1"


def test_rechunk_leaves_a_small_stack_alone() -> None:
    """Nothing is gained by splitting an array that is already one chunk."""
    small_sizes: dict[Hashable, int] = {"c": 1, "t": 1, "z": 1, "y": 100, "x": 100}
    assert rechunk(small_sizes) == small_sizes, "Small images should not be rechunked"


def test_chunk_and_shard_targets_brick_and_shard_budgets() -> None:
    """A big uint16 volume gets 2 MiB bricks grouped 4×4×4 into 128 MiB shards."""
    sizes: dict[Hashable, int] = {"c": 2, "t": 1, "z": 64, "y": 4096, "x": 4096}
    inner, shard = chunk_and_shard(sizes, itemsize=2)

    assert inner == {"c": 1, "t": 1, "z": 4, "y": 512, "x": 512}
    assert shard == {"c": 1, "t": 1, "z": 16, "y": 2048, "x": 2048}
    for dim in inner:
        assert shard[dim] % inner[dim] == 0, "readers reject shards that are not exact multiples"


def test_chunk_and_shard_clamps_to_small_axes() -> None:
    """Small or non-multiple axes never yield a shard more than one brick past the array."""
    sizes: dict[Hashable, int] = {"c": 1, "t": 1, "z": 3, "y": 300, "x": 5000}
    inner, shard = chunk_and_shard(sizes, itemsize=2)

    for dim in inner:
        assert inner[dim] <= sizes[dim], "an inner chunk never exceeds the array"
        assert shard[dim] % inner[dim] == 0
        assert shard[dim] - sizes[dim] < inner[dim], "shard overhang stays under one brick"
