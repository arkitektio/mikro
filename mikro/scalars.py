import shutil
from tomlkit import value
import requests
import xarray as xr
from herre.wards.registry import get_ward_registry


class XArray:
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

    @property
    def store(self):
        if not self._openstore:
            ward = get_ward_registry().get_ward_instance("mikro")
            s3_path = f"zarr/{self.value}"
            self._openstore = xr.open_zarr(
                store=ward.s3fs.get_mapper(s3_path), consolidated=True
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


class File:
    def __init__(self, value) -> None:
        self.value = value

    def download(self):
        ward = get_ward_registry().get_ward_instance("mikro")
        protocol = "https" if ward.config.s3.secure else "http"
        endpoint_url = f"{protocol}://{ward.config.s3.host}:{ward.config.s3.port}"
        url = f"{endpoint_url}{self.value}"
        local_filename = "test.tif"
        with requests.get(url, stream=True) as r:
            with open(local_filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)

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


class Upload:
    def __init__(self, value) -> None:
        self.value = value

    def download(self):
        ward = get_ward_registry().get_ward_instance("mikro")
        protocol = "https" if ward.config.s3.secure else "http"
        endpoint_url = f"{protocol}://{ward.config.s3.host}:{ward.config.s3.port}"
        url = f"{endpoint_url}{self.value}"
        local_filename = "test.tif"
        with requests.get(url, stream=True) as r:
            with open(local_filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)

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

    def download(self):
        ward = get_ward_registry().get_ward_instance("mikro")
        protocol = "https" if ward.config.s3.secure else "http"
        endpoint_url = f"{protocol}://{ward.config.s3.host}:{ward.config.s3.port}"
        url = f"{endpoint_url}{self.value}"
        local_filename = "test.tif"
        with requests.get(url, stream=True) as r:
            with open(local_filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)

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
