import numpy as np
import xarray as xr
from pydantic import BaseModel

from mikro_next.scalars import ArrayLike


class Arguments(BaseModel):
    """Arguments for testing serialization of numpy and xarray arrays."""

    x: ArrayLike


def test_numpy_serialization() -> None:
    """A bare numpy array keeps its own rank; xarray names the dims for it."""
    x = np.random.random((20, 1000, 1000))

    t = Arguments(x=x)
    assert t.x.value.ndim == 3, "Rank should be preserved, not padded to 5"
    assert t.x.value.dims == ("dim_0", "dim_1", "dim_2")


def test_xarray_serialization() -> None:
    """A labelled DataArray travels through the field with its labels intact."""
    x = xr.DataArray(np.zeros((1000, 1000, 10)), dims=["x", "y", "z"])

    t = Arguments(x=x)
    assert t.x.value.ndim == 3, "Rank should be preserved, not padded to 5"
    assert t.x.value.dims == ("x", "y", "z"), "Dimension order must be verbatim"
