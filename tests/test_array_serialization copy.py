from pydantic import BaseModel
import numpy as np
import xarray as xr

from mikro.scalars import XArrayInput


class Arguments(BaseModel):
    x: XArrayInput


def test_numpy_serialization():
    x = np.random.random((1000, 1000, 10))

    t = Arguments(x=x)
    assert t.x.value.ndim == 5, "Should be five dimensionsal"


def test_xarray_serialization():
    x = xr.DataArray(np.zeros((1000, 1000, 10)), dims=["x", "y", "z"])

    t = Arguments(x=x)
    assert t.x.value.ndim == 5, "Should be five dimensionsal"
