from concurrent.futures import ThreadPoolExecutor
import uuid
from herre.wards.graphql import GraphQLWard
from herre.wards.registry import get_ward_registry
import asyncio
import pandas as pd
import xarray as xr
import pyarrow.parquet as pq
from pyarrow import Table as ArrowTable


class RepresentationException(Exception):
    pass


def save_array(array: xr.DataArray, ward):
    random_ui = uuid.uuid4()
    s3_path = f"zarr/{random_ui}"

    store = ward.s3fs.get_mapper(s3_path)

    apiversion = "0.1"
    fileversion = "0.1"

    if "x" not in array.dims:
        raise RepresentationException(
            "Representations must always have a 'x' Dimension"
        )

    if "y" not in array.dims:
        raise RepresentationException(
            "Representations must always have a 'y' Dimension"
        )

    if "t" not in array.dims:
        array = array.expand_dims("t")
    if "c" not in array.dims:
        array = array.expand_dims("c")
    if "z" not in array.dims:
        array = array.expand_dims("z")

    chunks = {
        "t": 1,
        "x": array.sizes["x"],
        "y": array.sizes["y"],
        "z": 1,
    }

    array = array.chunk(
        {key: chunksize for key, chunksize in chunks.items() if key in array.dims}
    )
    if apiversion == "0.1":
        dataset = array.to_dataset(name="data")
        dataset.attrs["apiversion"] = apiversion
        dataset.attrs["fileversion"] = fileversion
    else:
        raise NotImplementedError("This API Version has not been Implemented Yet")

    data = dataset.to_zarr(store=store, consolidated=True, compute=True)
    return s3_path


def save_df(df: pd.DataFrame, ward):
    random_ui = uuid.uuid4()
    table: ArrowTable = ArrowTable.from_pandas(df)
    s3_path = f"parquet/{random_ui}"
    pq.write_table(table, s3_path, filesystem=ward.s3fs)

    return s3_path


async def shrink_xarray(array: xr.DataArray, ward: GraphQLWard = None):
    print("Shrinking XArray")
    with ThreadPoolExecutor(max_workers=4) as executor:
        co_future = executor.submit(save_array, array, ward)
        return await asyncio.wrap_future(co_future)


async def shrink_df(df: pd.DataFrame, ward: GraphQLWard = None):
    print("Shrinking DF")
    with ThreadPoolExecutor(max_workers=4) as executor:
        co_future = executor.submit(save_df, df, ward)
        return await asyncio.wrap_future(co_future)
