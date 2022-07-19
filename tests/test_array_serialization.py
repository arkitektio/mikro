from pydantic import BaseModel
import pydantic
import pytest
from mikro.app import MikroApp
from fakts import Fakts
from fakts.grants import YamlGrant
import numpy as np
import xarray as xr

from mikro.scalars import ArrayInput


class Arguments(BaseModel):
    x: ArrayInput


def test_numpy_serialization():
    x = np.random.random((1000, 1000, 10))

    t = Arguments(x=x)
    assert t.x.value.ndim == 5, "Should be five dimensionsal"


def test_xarray_serialization():
    x = xr.DataArray(np.zeros((1000, 1000, 10)), dims=["x", "y", "z"])

    t = Arguments(x=x)
    assert t.x.value.ndim == 5, "Should be five dimensionsal"
