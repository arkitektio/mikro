"""
This modules provides the datalayer. 

Example:

    A simple datalayer that connects to an s3 instance via access_key and secret_key.
    You can define all of the logic within the context manager

    ```python
    from mikro.datalayer import Datalayer

    dl = Datalayer(access_key="XXXX", secret_key="XXXX", endpoint_url="s3.amazonaws.com")

    with dl:
        print(df.fs.ls())

    ```

    Async Usage:

    ```python
    from mikro.datalayer import Datalayer

    dl = Datalayer(access_key="XXXX", secret_key="XXXX", endpoint_url="s3.amazonaws.com")

    async with dl:
        print(df.fs.ls())

    ```

 
"""


import asyncio
from concurrent.futures import Executor, ThreadPoolExecutor
import contextvars
from typing import Optional
import uuid

import xarray as xr
from pydantic import Field, SecretStr
from koil.composition import KoiledModel
import s3fs
from koil import unkoil
from mikro.scalars import XArrayInput, ParquetInput, BigFile
from aiobotocore.session import get_session
import ntpath

current_datalayer = contextvars.ContextVar("current_datalayer", default=None)


class DataLayer(KoiledModel):
    """Implements a S3 DataLayer

    This will be used to upload and download files from S3.


    Make sure to set the access_key and secret_key and enter the context
    manager to connect to S3 (if authentication is required for the S3 instance
    and to ensure that the context is exited when the context manager is exited
    (for future cleanup purposes on other datalayers).

    Attributes:
        fs (s3fs.S3FileSystem): The filesystem object

    """

    executor: Optional[Executor] = Field(
        default_factory=lambda: ThreadPoolExecutor(max_workers=4), exclude=True
    )
    _executor_session: Optional[Executor] = None

    access_key: SecretStr = Field(default="")
    secret_key: SecretStr = Field(default="")
    session_token: SecretStr = Field(default="")
    endpoint_url: str = ""

    _s3fs: Optional[s3fs.S3FileSystem] = None
    _connected = False
    auto_connect = True

    def _storedataset(self, dataset: xr.Dataset, path):
        store = self.fs.get_mapper(path)
        dataset.to_zarr(store=store, consolidated=True, compute=True)
        return path

    def _storetable(self, table, path):
        import pyarrow.parquet as pq

        s3_path = f"s3://parquet/{path}"
        pq.write_table(table, s3_path, filesystem=self.fs)
        return path

    async def astore_array_input(self, xarray: XArrayInput) -> str:
        """Stores an xarray in the DataLayer"""
        if not self._connected:
            if self.auto_connect:
                await self.aconnect()

        assert self._executor_session is not None, "Executor is not set"

        random_uuid = uuid.uuid4()
        s3_path = f"zarr/{random_uuid}.zarr"
        dataset = xarray.value.to_dataset(name="data")
        dataset.attrs["fileversion"] = "v1"
        try:
            co_future = self._executor_session.submit(
                self._storedataset, dataset, s3_path
            )
            return await asyncio.wrap_future(co_future)
        except PermissionError as e:
            print(e)
            await self.aconnect()
            co_future = self._executor_session.submit(
                self._storedataset, dataset, s3_path
            )
            return await asyncio.wrap_future(co_future)

    async def astore_parquet_input(self, pqinput: ParquetInput) -> str:
        """Store a DataFrame in the DataLayer"""
        from pyarrow import Table

        if not self._connected:
            if self.auto_connect:
                await self.aconnect()

        assert self._executor_session is not None, "Executor is not set"

        random_ui = uuid.uuid4()
        table: Table = Table.from_pandas(pqinput.value)
        co_future = self._executor_session.submit(self._storetable, table, random_ui)
        return await asyncio.wrap_future(co_future)

    async def astore_bigfile(self, file: BigFile) -> str:
        """Store a DataFrame in the DataLayer"""
        if not self._connected:
            if self.auto_connect:
                await self.aconnect()

        key = ntpath.basename(file.value.name)
        session = get_session()
        async with session.create_client(
            "s3",
            region_name="us-west-2",
            endpoint_url=self.endpoint_url,
            aws_secret_access_key=self.secret_key,
            aws_access_key_id=self.access_key,
            aws_session_token=self.session_token,
        ) as client:
            resp = await client.put_object(
                Bucket="mikromedia", Key=key, Body=file.value
            )

        return f"mikromedia/{key}"

    def open_store(self, path):
        return self.fs.get_mapper(path)

    @property
    def fs(self):
        assert (
            self._s3fs is not None
        ), "Filesystem is not connected yet, please make sure to connect first"
        return self._s3fs

    async def aget_credentials(self, id=None):
        from mikro.api.schema import arequest

        c = await arequest()
        self.access_key = c.access_key
        self.secret_key = c.secret_key
        self.session_token = c.session_token

    async def aconnect(self):
        """Connect to the S3 instance"""
        self._connected = True
        await self.aget_credentials()

        self._s3fs = s3fs.S3FileSystem(
            secret=self.secret_key,
            key=self.access_key,
            client_kwargs={
                "endpoint_url": self.endpoint_url,
                "aws_session_token": self.session_token,
            },
        )

        return self

    def reconnect(self):
        unkoil(self.adisconnect)
        unkoil(self.aconnect)

    async def areconnect(self):
        await self.adisconnect()
        await self.aconnect()

    def _repr_html_inline_(self):
        return (
            f"<table><tr><td>auto_connect</td><td>{self.auto_connect}</td></tr></table>"
        )

    async def adisconnect(self):
        """Disconnect from the S3 instance"""
        self._connected = False
        return self

    async def __aenter__(self):
        self._executor_session = self.executor.__enter__()
        current_datalayer.set(self)
        return self

    async def __aexit__(self, *args, **kwargs):
        current_datalayer.set(None)
        self.executor.__exit__(*args, **kwargs)
        return self

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True
