""" 
Custom scalars for Mikro.


"""


import os
from typing import Any
import xarray as xr
import pyarrow.parquet as pq
import pandas as pd
import numpy as np


class XArrayConversionException(Exception):
    pass


MetricValue = Any
FeatureValue = Any



class XArrayInput:
    """A custom scalar for wrapping of every supported array like structure on
    the mikro platform. This scalar enables validation of various array formats
    into a mikro api compliant xr.DataArray.."""

    def __init__(self, value: xr.DataArray) -> None:
        self.value = value

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Validate the input array and convert it to a xr.DataArray."""

        if isinstance(v, np.ndarray):
            dims = ["c", "t", "z", "x", "y"]
            v = xr.DataArray(v, dims=dims[5 - v.ndim :])

        if not isinstance(v, xr.DataArray):
            raise ValueError("This needs to be a instance of xarray.DataArray")

        if "x" not in v.dims:
            raise ValueError("Representations must always have a 'x' Dimension")

        if "y" not in v.dims:
            raise ValueError("Representations must always have a 'y' Dimension")

        if "t" not in v.dims:
            v = v.expand_dims("t")
        if "c" not in v.dims:
            v = v.expand_dims("c")
        if "z" not in v.dims:
            v = v.expand_dims("z")

        chunks = {
            "t": 1,
            "x": 1024 if v.sizes["x"] > 1024 else v.sizes["x"],
            "y": 1024 if v.sizes["y"] > 1024 else v.sizes["y"],
            "z": 40 if v.sizes["z"] > 40 else 1,
            "c": 1,
        }

        v = v.chunk(
            {key: chunksize for key, chunksize in chunks.items() if key in v.dims}
        )

        v = v.transpose(*"ctzyx")

        return cls(v)

    def __repr__(self):
        return f"InputArray({self.value})"


class ParquetInput:
    """A custom scalar for ensuring a common format to support write to the
    parquet api supported by mikro. It converts the passed value into
    a compliant format.."""

    def __init__(self, value: pd.DataFrame) -> None:
        self.value = value

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, v):

        if not isinstance(v, pd.DataFrame):
            raise ValueError("This needs to be a instance of pandas DataFrame")

        return cls(v)

    def __repr__(self):
        return f"ParquetInput({self.value})"


class Store:
    """A custom scalar for ensuring an interface to the datalayer api supported by mikro. It converts the graphql
    value (a string pointed to a zarr store) into a zarr store object. This is used to access the data in the
    datalayer. The store is opened on the first access and then cached for later use. This is done to avoid
    opening the store on every access. The store is opened with the datalayer that is currently set in the
    datalayer context. Credentials are being retrieved on first access to the datalayer and when a permission
    denied error is raised. This is done to avoid unnecessary requests to the datalayer api.
    """

    def __init__(self, value) -> None:
        self.value = value
        self._openstore = None

    def arequest(self):
        """ToDO Imepelemtn, each store needs to have a request first to the resource owner
        and then we can access the data
        """

    def open(self, dl=None):
        """Opens the store and returns the zarr store object.

        The store is opened on the first access and then cached for later use. This is done to avoid
        opening the store on every access.


        Args:
            dl (Datalayer, optional): The datalayer. Defaults to active datalayer.

        Returns:
            xr.DataArray: the data array
        """
        from mikro.datalayer import current_datalayer

        dl = dl or current_datalayer.get()

        assert (
            dl
        ), "No datalayer set. This probably happened because you never connected the datalayer. Please connect (either with async or sync) and try again."
        if self._openstore is None:
            self._openstore = xr.open_zarr(
                store=dl.fs.get_mapper(self.value), consolidated=True
            )["data"]

        return self._openstore

    def aopen(self, dl=None):
        """Opens the store and returns the zarr store object.

        The store is opened on the first access and then cached for later use. This is done to avoid
        opening the store on every access.


        Args:
            dl (Datalayer, optional): The datalayer. Defaults to active datalayer.

        Returns:
            xr.DataArray: the data array
        """
        from mikro.datalayer import current_datalayer

        dl = dl or current_datalayer.get()

        assert (
            dl
        ), "No datalayer set. This probably happened because you never connected the datalayer. Please connect (either with async or sync) and try again."
        if self._openstore is None:
            self._openstore = xr.open_zarr(
                store=dl.fs.get_mapper(self.value), consolidated=True
            )["data"]

        return self._openstore

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(v)

    def __repr__(self):
        return f"Store({self.value})"


class Parquet:
    """A custom scalar for ensuring an interface to the datalayer api supported by mikro. It converts the graphql value
    (a string pointed to a zarr store) into a parquet dataset and then a dataframe. This is used to access the data
    in the datalayer. The store is opened on the first access and then cached for later use. This is done to avoid
    opening the store on every access. This is done to avoid unnecessary requests to the datalayer api.
    """

    def __init__(self, value) -> None:
        self.value = value
        self._openstore = None

    def open(self, dl=None):
        from mikro.datalayer import current_datalayer

        dl = dl or current_datalayer.get()

        assert (
            dl
        ), "No datalayer set. This probably happened because you never connected the datalayer. Please connect (either with async or sync) and try again."
        if not self._openstore:
            self._openstore = (
                pq.ParquetDataset(self.value, filesystem=dl.fs)
                .read_pandas()
                .to_pandas()
            )
        return self._openstore

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        return cls(v)

    def __repr__(self):
        return f"Parquet({self.value})"


class File:
    """A custom scalar for ensuring an interface to files api supported by mikro. It converts the graphql value
    (a string pointed to a zarr store) into a downloadable file. To access the file you need to call the download
    method. This is done to avoid unnecessary requests to the datalayer api.
    """

    __file__ = True

    def __init__(self, value) -> None:
        self.value = value

    def download(self, dl=None):
        from mikro.datalayer import current_datalayer
        import requests
        import shutil

        dl = dl or current_datalayer.get()
        url = f"{dl.endpoint_url}{self.value}"
        local_filename = self.value.split("/")[-1].split("?")[0]
        with requests.get(url, stream=True) as r:
            with open(local_filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)
                return local_filename

    def __enter__(self):
        self.local_file = self.download()
        return self.local_file

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.local_file)

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, v):
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(v)

    def __repr__(self):
        return f"File({self.value})"



class ModelFile:
    """A custom scalar to enable uploading files to the datalayer
    it enables serialization of everythign
    """

    __file__ = True

    def __init__(self, value) -> None:
        self.value = value


    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator


        yield cls.validate

    @classmethod
    def validate(cls, v):
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        if isinstance(v, str):
            return cls(open(v, "rb"))
        

        return cls(v)

    def __repr__(self):
        return f"ModelFile({self.value})"




class ModelData:
    """A custom scalar for ensuring an interface to files api supported by mikro. It converts the graphql value
    (a string pointed to a zarr store) into a downloadable file. To access the file you need to call the download
    method. This is done to avoid unnecessary requests to the datalayer api.
    """

    __file__ = True

    def __init__(self, value) -> None:
        self.value = value

    def download(self, dl=None):
        from mikro.datalayer import current_datalayer
        import requests
        import shutil

        dl = dl or current_datalayer.get()
        url = f"{dl.endpoint_url}{self.value}"
        local_filename = self.value.split("/")[-1].split("?")[0]
        with requests.get(url, stream=True) as r:
            with open(local_filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)
                return local_filename

    def __enter__(self):
        self.local_file = self.download()
        return self.local_file

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.local_file)

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator


        yield cls.validate

    @classmethod
    def validate(cls, v):
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(v)

    def __repr__(self):
        return f"Model({self.value})"
