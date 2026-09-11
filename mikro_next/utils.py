import math
from collections.abc import Hashable, Mapping
from typing import cast

#: Inner chunk budget for sharded arrays. Inner chunks are the readable brick unit —
#: the frontend's residency system fetches and decodes them individually, so they stay
#: small (well under its 8 MiB per-GET coalesce budget once compressed).
INNER_CHUNK_BYTES = 2 * 1024**2

#: Shard budget: how many bytes one S3 object should hold. Shards exist purely to cut
#: object count; readers still address inner chunks via ranged GETs against the shard index.
SHARD_BYTES = 128 * 1024**2


def rechunk(
    sizes: Mapping[Hashable, int],
    itemsize: int = 8,
    chunksize_in_bytes: int = 20_000_000,
) -> Mapping[Hashable, int]:
    """Calculates Chunks for a given size

    Args:
        sizes (Mapping[Hashable, int]): The sizes of the image

    Returns:
        The chunks (Mapping[Hashable, int]): The chunks
    """
    assert "c" in sizes, "c must be in sizes"
    assert "z" in sizes, "z must be in sizes"
    assert "y" in sizes, "y must be in sizes"
    assert "x" in sizes, "x must be in sizes"
    assert "t" in sizes, "t must be in sizes"

    all_size = sizes["c"] * sizes["z"] * sizes["y"] * sizes["x"] * sizes["t"]

    # We will not rechunk if the size is smaller than 1MB
    if all_size < 1 * 2048 * 2048:
        return sizes

    x = (
        sizes["x"] if not sizes["x"] > 2048 else 2048
    )  # Biggest X but not bigger than 1024
    y = (
        sizes["y"] if not sizes["y"] > 2048 else 2048
    )  # Biggest Y but not bigger than 1024

    best_z = math.ceil(chunksize_in_bytes / (x * y * itemsize))
    z = min(sizes["z"], best_z)

    best_t = math.ceil(chunksize_in_bytes / (x * y * z * itemsize))
    t = min(sizes["t"], best_t)

    chunk = {
        "c": 1,
        "z": z,
        "y": y,
        "x": x,
        "t": t,
    }

    return cast(Mapping[Hashable, int], chunk)


def chunk_and_shard(
    sizes: Mapping[Hashable, int],
    itemsize: int = 8,
    inner_chunk_bytes: int = INNER_CHUNK_BYTES,
    shard_bytes: int = SHARD_BYTES,
) -> tuple[Mapping[Hashable, int], Mapping[Hashable, int]]:
    """Calculate the (inner chunk, shard) shapes for a canonical ctzyx array.

    Inner chunks are the brick unit readers decode: one channel, one timepoint,
    a y/x plane capped at 512, and z filling the inner byte budget. The shard
    groups 4×4×4 of them in z/y/x (restoring the old 2048 plane), then lets t
    absorb whatever remains of the shard budget. Every shard axis is an exact
    integer multiple of the inner chunk axis — readers reject anything else —
    with each multiplier clamped so a shard overhangs the array by less than
    one inner chunk.
    """
    for dim in ("c", "t", "z", "y", "x"):
        assert dim in sizes, f"{dim} must be in sizes"

    x = min(sizes["x"], 512)
    y = min(sizes["y"], 512)
    z = min(sizes["z"], max(1, math.ceil(inner_chunk_bytes / (x * y * itemsize))))
    inner = {"c": 1, "t": 1, "z": z, "y": y, "x": x}

    def multiplied(dim: Hashable, factor: int) -> int:
        return inner[dim] * min(factor, math.ceil(sizes[dim] / inner[dim]))

    shard = {
        "c": 1,
        "z": multiplied("z", 4),
        "y": multiplied("y", 4),
        "x": multiplied("x", 4),
    }
    bytes_so_far = itemsize * shard["z"] * shard["y"] * shard["x"]
    shard["t"] = multiplied("t", max(1, shard_bytes // bytes_so_far))

    for dim in inner:
        assert shard[dim] % inner[dim] == 0, f"shard must be a multiple of the inner chunk on {dim}"
    return cast(Mapping[Hashable, int], inner), cast(Mapping[Hashable, int], shard)
