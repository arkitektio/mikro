from concurrent.futures import Executor, ThreadPoolExecutor
from typing import Optional
from uuid import uuid4
from graphql import NamedTypeNode
from pydantic import Field
from mikro.datalayer import DataLayer
from rath.links.parsing import ParsingLink
from rath.operation import Operation
from graphql.language import NonNullTypeNode
import xarray as xr
import asyncio


def filter_xarray_nodes(operation: Operation):
    try:
        return [
            v
            for v in operation.node.variable_definitions
            if (
                (
                    isinstance(v.type, NonNullTypeNode)
                    and v.type.type.name.value == "XArray"
                )
                or (isinstance(v.type, NamedTypeNode) and v.type.name.value == "XArray")
            )
        ]
    except AttributeError:
        return []


class XArrayConversionException(Exception):
    pass


class DataLayerXArrayUploadLink(ParsingLink):
    """Data Layer Xarray Upload Link

    This link is used to upload a Xarray to a DataLayer.
    It parses queries, mutatoin and subscription arguments and
    uploads the items to the DataLayer, and substitures the
    XArray with the S3 path.

    Args:
        ParsingLink (_type_): _description_

    Attributes:
        FileVersion (str): The version of the file format.

    """

    datalayer: Optional[DataLayer] = None
    bucket: Optional[str] = "zarr"
    executor: Optional[Executor] = Field(
        default_factory=lambda: ThreadPoolExecutor(max_workers=4)
    )

    FILEVERSION = "0.1"
    _connected = False
    _lock: asyncio.Lock = False
    _executor_session = None

    def store_xarray(self, xarray: xr.DataArray) -> None:
        random_uuid = uuid4()
        s3_path = f"zarr/{random_uuid}"

        store = self.datalayer.fs.get_mapper(s3_path)

        if "x" not in xarray.dims:
            raise XArrayConversionException(
                "Representations must always have a 'x' Dimension"
            )

        if "y" not in xarray.dims:
            raise XArrayConversionException(
                "Representations must always have a 'y' Dimension"
            )

        if "t" not in xarray.dims:
            xarray = xarray.expand_dims("t")
        if "c" not in xarray.dims:
            xarray = xarray.expand_dims("c")
        if "z" not in xarray.dims:
            xarray = xarray.expand_dims("z")

        chunks = {
            "t": 1,
            "x": xarray.sizes["x"],
            "y": xarray.sizes["y"],
            "z": 1,
        }

        xarray = xarray.chunk(
            {key: chunksize for key, chunksize in chunks.items() if key in xarray.dims}
        )
        if self.FILEVERSION == "0.1":
            dataset = xarray.to_dataset(name="data")
            dataset.attrs["fileversion"] = self.FILEVERSION
        else:
            raise NotImplementedError("This API Version has not been Implemented Yet")

        dataset.to_zarr(store=store, consolidated=True, compute=True)
        return s3_path

    def parse(self, operation: Operation) -> Operation:

        for node in filter_xarray_nodes(operation):
            array = operation.variables[node.variable.name.value]

            if isinstance(array, xr.DataArray):
                operation.variables[node.variable.name.value] = self.store_xarray(array)

            else:
                raise NotImplementedError("Can only store XArray at this moment")

        return operation

    async def aparse(self, operation: Operation) -> Operation:

        shrinky = filter_xarray_nodes(operation)
        if shrinky:
            shrinked_v = []
            shrinked_f = []

            for node in shrinky:
                array = operation.variables[node.variable.name.value]
                co_future = self._executor_session.submit(self.store_xarray, array)
                shrinked_f.append(asyncio.wrap_future(co_future))
                shrinked_v.append(node.variable.name.value)

            shrinked_x = await asyncio.gather(*shrinked_f)

            update_dict = {v: x for v, x in zip(shrinked_v, shrinked_x)}
            operation.variables.update(update_dict)

        return operation

    async def __aenter__(self) -> None:
        """Enter the executor"""
        self._executor_session = self.executor.__enter__()

    async def __aexit__(self, *args, **kwargs) -> None:
        self.executor.__exit__(*args, **kwargs)

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True
        extra = "forbid"
