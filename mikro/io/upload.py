from mikro_new.api.schema import (
    RequestQueryRequest as Credentials,
    XArrayInput,
    BigFile,
    ParquetInput,
)
import asyncio
import uuid
import s3fs
import ntpath
from typing import Protocol, Any, runtime_checkable
from aiobotocore.session import get_session
import botocore
from pyarrow import Table
import pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor
from .errors import PermissionsError, UploadError


def _store_xarray_input(
    xarray: XArrayInput,
    endpoint_url: str,
    bucket: str,
    key: str,
    credentials: Credentials,
) -> str:
    """Stores an xarray in the DataLayer"""

    filesystem = s3fs.S3FileSystem(
        secret=credentials.secret_key,
        key=credentials.access_key,
        client_kwargs={
            "endpoint_url": endpoint_url,
            "aws_session_token": credentials.session_token,
        },
    )

    # random_uuid = uuid.uuid4()
    # s3_path = f"zarr/{random_uuid}.zarr"
    dataset = xarray.value.to_dataset(name="data")
    dataset.attrs["fileversion"] = "v1"

    s3_path = f"{bucket}/{key}"

    try:
        store = filesystem.get_mapper(s3_path)
        dataset.to_zarr(store=store, consolidated=True, compute=True)
        return s3_path
    except Exception as e:
        raise UploadError(f"Error while uploading to {s3_path}") from e


def _store_parquet_input(
    parquet_input: ParquetInput,
    endpoint_url: str,
    credentials: Credentials,
) -> str:
    """Stores an xarray in the DataLayer"""

    filesystem = s3fs.S3FileSystem(
        secret=credentials.secret_key,
        key=credentials.access_key,
        client_kwargs={
            "endpoint_url": endpoint_url,
            "aws_session_token": credentials.session_token,
        },
    )

    path = uuid.uuid4()
    table: Table = Table.from_pandas(parquet_input.value)

    try:
        s3_path = f"s3://parquet/{path}"
        pq.write_table(table, s3_path, filesystem=filesystem)
        return s3_path
    except Exception as e:
        raise UploadError(f"Error while uploading to {s3_path}") from e


async def aupload_bigfile(
    file: BigFile,
    endpoint_url: str,
    bucket: str,
    key: str,
    credentials: Credentials,
    executor: ThreadPoolExecutor = None,
) -> str:
    """Store a DataFrame in the DataLayer"""
    session = get_session()
    async with session.create_client(
        "s3",
        region_name="us-west-2",
        endpoint_url=endpoint_url,
        aws_secret_access_key=credentials.secret_key,
        aws_access_key_id=credentials.access_key,
        aws_session_token=credentials.session_token,
    ) as client:
        try:
            resp = await client.put_object(Bucket=bucket, Key=key, Body=file.value)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "InvalidAccessKeyId":
                return PermissionsError(
                    "Access Key is invalid, trying to get new credentials"
                )

            raise e

    return f"{key}"


async def aupload_xarray(
    array: XArrayInput,
    endpoint_url: str,
    bucket: str,
    key: str,
    credentials: Credentials,
    executor: ThreadPoolExecutor = None,
) -> str:
    """Store a DataFrame in the DataLayer"""
    co_future = executor.submit(
        _store_xarray_input, array, endpoint_url, bucket, key, credentials
    )
    return await asyncio.wrap_future(co_future)


async def aupload_parquet(
    parquet: ParquetInput,
    endpoint_url: str,
    bucket: str,
    key: str,
    credentials: Credentials,
    executor: ThreadPoolExecutor = None,
) -> str:
    """Store a DataFrame in the DataLayer"""
    co_future = executor.submit(
        _store_parquet_input, parquet, endpoint_url, bucket, key, credentials
    )
    return await asyncio.wrap_future(co_future)
