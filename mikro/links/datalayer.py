import asyncio

from mikro.datalayer import DataLayer, current_datalayer
from mikro.scalars import XArrayInput, ParquetInput, BigFile
from rath.links.parsing import ParsingLink
from rath.operation import Operation, opify
from typing import Optional


async def apply_recursive(func, obj, typeguard):
    if isinstance(obj, dict):  # if dict, apply to each key
        return {k: await apply_recursive(func, v, typeguard) for k, v in obj.items()}
    elif isinstance(obj, list):  # if list, apply to each element
        return await asyncio.gather(
            *[apply_recursive(func, elem, typeguard) for elem in obj]
        )
    elif isinstance(obj, tuple):  # if tuple, apply to each element
        return tuple(await apply_recursive(func, elem, typeguard) for elem in obj)
    if isinstance(obj, typeguard):
        return await func(obj)
    else:
        return obj


class ParquetConversionException(Exception):
    pass


class DataLayerUploadLink(ParsingLink):
    """Data Layer Upload Link

    This link is used to upload  supported types to a DataLayer.
    It parses queries, mutatoin and subscription arguments and
    uploads the items to the DataLayer, and substitures the
    DataFrame with the S3 path.

    Args:
        ParsingLink (_type_): _description_


    """

    FILEVERSION = "0.1"
    _connected = False
    _lock: Optional[asyncio.Lock] = None

    datalayer: DataLayer

    async def aparse(self, operation: Operation) -> Operation:
        """Parse the operation (Async)

        Extracts the DataFrame from the operation and uploads it to the DataLayer.

        Args:
            operation (Operation): The operation to parse

        Returns:
            Operation: _description_
        """

        if not self._lock:
            self._lock = asyncio.Lock()

        if not self.datalayer._connected:
            await self.datalayer.aconnect()

        operation.variables = await apply_recursive(
            self.datalayer.astore_array_input, operation.variables, XArrayInput
        )
        operation.variables = await apply_recursive(
            self.datalayer.astore_parquet_input, operation.variables, ParquetInput
        )
        operation.variables = await apply_recursive(
            self.datalayer.astore_bigfile, operation.variables, BigFile
        )

        return operation

    class Config:
        """pydantic config class"""
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True
        extra = "forbid"
