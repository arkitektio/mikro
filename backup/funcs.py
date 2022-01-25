from concurrent.futures import ThreadPoolExecutor
import uuid
from herre.wards.registry import get_ward_registry
import asyncio


class RepresentationException(Exception):
    pass


def save_array(array):
    random_ui = uuid.uuid4()
    ward = get_ward_registry().get_ward_instance("mikro")
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


async def shrink_xarray(array):
    print("Called")
    with ThreadPoolExecutor(max_workers=4) as executor:
        co_future = executor.submit(save_array, array)
        return await asyncio.wrap_future(co_future)
