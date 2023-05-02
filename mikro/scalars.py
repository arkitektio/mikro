""" 
Custom scalars for Mikro.


"""


import os
from typing import Any, List, IO, Optional
import xarray as xr
import pandas as pd
import numpy as np
import io
from typing import TYPE_CHECKING
from .utils import rechunk
import logging

if TYPE_CHECKING:
    from mikro.datalayer import DataLayer


class AssignationID(str):
    """A custom scalar to represent an affine matrix."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Validate the input array and convert it to a xr.DataArray."""
        return cls(v)


try:
    from rekuest.actors.vars import (
        get_current_assignation_helper,
        NotWithinAnAssignationError,
    )

    def get_current_id(cls, value) -> AssignationID:
        try:
            return value or get_current_assignation_helper().assignation.assignation
        except NotWithinAnAssignationError:
            return value

except ImportError:

    def get_current_id(cls, value):
        return value


class XArrayConversionException(Exception):
    """An exception that is raised when a conversion to xarray fails."""

    pass


MetricValue = Any
FeatureValue = Any


class AffineMatrix(list):
    """A custom scalar to represent an affine matrix."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Validate the input array and convert it to a xr.DataArray."""
        if isinstance(v, np.ndarray):
            assert v.ndim == 2
            assert v.shape[0] == v.shape[1]
            assert v.shape == (3, 3)
            v = v.tolist()

        assert isinstance(v, list)
        return cls(v)


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
    def validate(cls, v: xr.DataArray):
        """Validate the input array and convert it to a xr.DataArray."""

        if isinstance(v, np.ndarray):
            dims = ["c", "t", "z", "y", "x"]
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

        chunks = rechunk(
            v.sizes, itemsize=v.data.itemsize, chunksize_in_bytes=20_000_000
        )
        print(chunks)

        v = v.chunk(
            {key: chunksize for key, chunksize in chunks.items() if key in v.dims}
        )

        v = v.transpose(*"ctzyx")

        return cls(v)

    def __repr__(self):
        return f"InputArray({self.value})"


class BigFile:
    """A custom scalar for wrapping of every supported array like structure on
    the mikro platform. This scalar enables validation of various array formats
    into a mikro api compliant xr.DataArray.."""

    def __init__(self, value: IO) -> None:
        self.value = value

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Validate the input array and convert it to a xr.DataArray."""

        if isinstance(v, str):
            v = open(v, "rb")

        if not isinstance(v, io.IOBase):
            raise ValueError("This needs to be a instance of a file")

        return cls(v)

    def __repr__(self):
        return f"BigFile({self.value})"


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

    def open(self, dl: Optional["DataLayer"] = None):
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
                store=dl.open_store(self.value), consolidated=True
            )["data"]

        return self._openstore

    async def aopen(self, dl=None):
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
            try:
                self._openstore = xr.open_zarr(
                    store=dl.open_store(self.value), consolidated=True
                )["data"]
            except PermissionError as e:
                logging.warning(
                    "Permission denied. Trying to reconnect datalayer and retrieve credentials"
                )
                await dl.areconnect()
                self._openstore = xr.open_zarr(
                    store=dl.open_store(self.value), consolidated=True
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

    def __init__(self, value: str) -> None:
        self.value = value
        self._openstore = None

    def open(self, dl: Optional["DataLayer"] = None):
        from mikro.datalayer import current_datalayer
        import pyarrow.parquet as pq

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

    def download(
        self, dl: Optional["DataLayer"] = None, filename: Optional[str] = None
    ) -> str:
        """Downloads the file to the current working directory.

        Args:
            dl (DataLayer, optional): The datalayer. Defaults to active datalayer.
            filename (str, optional): The filename to save the file as. Defaults to the original filename.

        Returns:
            str: The filename of the downloaded file.
        """
        from mikro.datalayer import current_datalayer
        import requests
        import shutil

        dl = dl or current_datalayer.get()
        assert (
            dl
        ), "No datalayer set. This probably happened because you never connected the datalayer. Please connect (either with async or sync) and try again."
        url = f"{dl.endpoint_url}{self.value}"
        local_filename = filename or self.value.split("/")[-1].split("?")[0]
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
