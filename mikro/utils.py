from typing import Dict


def rechunk(sizes: Dict[str, int]) -> Dict[str, int]:
    """Calculates Chunks for a given size

    Args:
        sizes (Dict): The sizes of the image

    Returns:
        The chunks(dict): The chunks
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
    z = 1
    t = 1

    chunk = {
        "c": 1,
        "z": z,
        "y": y,
        "x": x,
        "t": t,
    }

    return chunk
