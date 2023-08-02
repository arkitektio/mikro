import uuid
from mikro_new.scalars import (
    BigFile,
    ParquetInput,
    ArrayLike,
)
from typing import Tuple
import ntpath
import uuid


async def aname_bigfile(file: BigFile) -> Tuple[str, str]:
    key = ntpath.basename(file.value.name)
    return "mikromedia", key


async def aname_parquet(parquet: ParquetInput) -> Tuple[str, str]:
    key = uuid.uuid4()
    return "parquet", f"{key}.parquet"


async def aname_xarray(array: ArrayLike) -> Tuple[str, str]:
    key = uuid.uuid4()
    return "zarr", f"{key}.zarr"
