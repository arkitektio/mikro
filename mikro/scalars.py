""" 
Custom scalars for Mikro.


"""


import xarray as xr
import pyarrow.parquet as pq
from mikro.datalayer import current_datalayer


class XArray:
    """A custom scalar for xarray."""

    def __init__(self, value) -> None:
        self.value = value

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern="^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$",
            # some example postcodes
            examples=["SP11 9DG", "w1j7bu"],
        )

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
        return f"XArray({self.value})"


class Store:
    def __init__(self, value) -> None:
        self.value = value
        self._openstore = None

    def open(self, dl=None):
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
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern="^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$",
            # some example postcodes
            examples=["SP11 9DG", "w1j7bu"],
        )

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
    def __init__(self, value) -> None:
        self.value = value
        self._openstore = None

    @property
    def df(self):
        if not self._openstore:
            s3_path = f"zarr/{self.value}"
            return (
                pq.ParquetDataset(s3_path, filesystem=self._getFileSystem())
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
    def __init__(self, value) -> None:
        self.value = value

    def download(self, dl=None):
        dl = dl or current_datalayer.get()
        url = f"{dl.endpoint_url}{self.value}"
        local_filename = "test.tif"
        # requests.get(url, stream=True) as r:
        #    with open(local_filename, "wb") as f:
        #        shutil.copyfileobj(r.raw, f)

        return local_filename

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
        return f"File({self.value})"


class Upload:
    def __init__(self, value) -> None:
        self.value = value

    def download(self, dl=None):
        dl = dl or current_datalayer.get()
        url = f"{dl.endpoint_url}{self.value}"
        local_filename = "test.tif"
        # with requests.get(url, stream=True) as r:
        #    with open(local_filename, "wb") as f:
        #       shutil.copyfileobj(r.raw, f)

        return local_filename

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern="^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$",
            # some example postcodes
            examples=["SP11 9DG", "w1j7bu"],
        )

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
        return f"File({self.value})"


class DataFrame:
    def __init__(self, value) -> None:
        self.value = value

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern="^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$",
            # some example postcodes
            examples=["SP11 9DG", "w1j7bu"],
        )

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
        return f"File({self.value})"
