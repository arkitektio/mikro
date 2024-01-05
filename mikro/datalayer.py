"""
This modules provides the datalayer. 

Example:

    A simple datalayer that connects to an s3 instance via access_key and secret_key.
    You can define all of the logic within the context manager

    ```python
    from mikro. imports Datalayer

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
import botocore
import xarray as xr
from pydantic import Field, SecretStr
from koil.composition import KoiledModel
import s3fs
from koil import unkoil
from mikro.scalars import XArrayInput, ParquetInput, BigFile
from aiobotocore.session import get_session
import ntpath
import logging
import zarr
from pyarrow import Table
import pyarrow.parquet as pq
from zarr._storage.store import BaseStore



logger = logging.getLogger(__name__)
current_datalayer: contextvars.ContextVar[Optional["DataLayer"]] = contextvars.ContextVar("current_datalayer", default=None)


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

    executor: Executor = Field(
        default_factory=lambda: ThreadPoolExecutor(max_workers=4), exclude=True
    )
    _executor_session: Optional[Executor] = None

    access_key: SecretStr = Field(default="")
    secret_key: SecretStr = Field(default="")
    session_token: SecretStr = Field(default="")
    endpoint_url: str = ""
    max_retries: int = 5

    _s3fs: Optional[s3fs.S3FileSystem] = None
    _connected = False
    auto_connect = True
    cache: int = 2**30
    """ O means no cache, 2**30 means 1GB cache"""
    strict: bool = False
    """ If True, it will not try to recover potential errors form the boto core client (only accept PermissionError). This is due to bad error handling on the boto core client when accesskeys are expired. """

    def _storedataset(self, dataset: xr.Dataset, path: str) -> str:
        store = self.fs.get_mapper(path)
        dataset.to_zarr(store=store, consolidated=True, compute=True)
        return path

    def _storetable(self, table: Table, path: str ) -> str:
        

        s3_path = f"s3://parquet/{path}"
        pq.write_table(table, s3_path, filesystem=self.fs)
        return s3_path

    async def astore_array_input(self, xarray: XArrayInput, retry: int = 0) -> str:
        """Stores an xarray in the DataLayer"""
        if not self._connected:
            if self.auto_connect:
                await self.aconnect()

        assert self._executor_session is not None, "Executor is not set"

        random_uuid = str(uuid.uuid4())
        s3_path = f"zarr/{random_uuid}.zarr"
        dataset = xarray.value.to_dataset(name="data")
        dataset.attrs["fileversion"] = "v1"
        try:
            co_future = self._executor_session.submit(
                self._storedataset, dataset, s3_path
            )
            return await asyncio.wrap_future(co_future)
        except PermissionError as e:
            logger.warning("Permission error, trying to get new credentials")
            if retry < self.max_retries:
                await self.aconnect()
                return await self.astore_array_input(xarray, retry=retry + 1)
            else:
                raise e
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "InvalidAccessKeyId":
                logger.warning("Access Key is invalid, trying to get new credentials")
                if retry < self.max_retries:
                    await self.aconnect()
                    return await self.astore_array_input(xarray, retry=retry + 1)

            else:
                raise e
        
        return s3_path

    async def astore_parquet_input(self, pqinput: ParquetInput) -> str:
        """Store a DataFrame in the DataLayer"""
        

        if not self._connected:
            if self.auto_connect:
                await self.aconnect()

        assert self._executor_session is not None, "Executor is not set"

        random_ui = str(uuid.uuid4())
        table: Table = Table.from_pandas(pqinput.value)
        co_future = self._executor_session.submit(self._storetable, table, random_ui)
        return await asyncio.wrap_future(co_future)

    async def astore_bigfile(self, file: BigFile, retry: int = 0) -> str:
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
            try:
                resp = await client.put_object(
                    Bucket="mikromedia", Key=key, Body=file.value
                )
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "InvalidAccessKeyId":
                    logger.debug("Access Key is invalid, trying to get new credentials")
                    if retry < self.max_retries:
                        await self.aget_credentials()
                        return await self.astore_bigfile(file, retry=retry + 1)

                raise e

        return f"{key}"

    def test_path_accessible(self, path: str, retry: int =0) -> bool:
        """Tests if the path is accessible with the current credentials
        
        Parameters:
        __________
        path: str
            The path to test
        retry: int
            The retry counter (will be incremented by the function itself)
            
        Returns:
        ________
        bool
            True if the path is accessible, False otherwise
        """



        # Check if we can access the path with the current credentials
        try:
            self.fs.ls(path)
            return True
        except PermissionError as e:
            logger.debug("Permission error, trying to get new credentials")
            if retry < self.max_retries:
                self.reconnect()
                return self.test_path_accessible(path, retry=retry + 1)
            else:
                logger.warning("Permission error, could not get new credentials")
                raise e
        except Exception as e:
            if self.strict:
                raise e
            else:
                logger.warning("Permission error, trying to get new credentials")
                if retry < self.max_retries:
                    self.reconnect()
                    return self.test_path_accessible(path, retry=retry + 1)
                else:
                    logger.error("Permission error, could not get new credentials")
                    raise e

    def open_store(self, path:str , cached: bool=True) -> BaseStore:
        """Opens a store for the given path

        Parameters:
        __________
        path: str
            The path to open
        cached: bool
            If True, it will use a LRU cache for the store

        Returns:
        ________
        zarr.Store
            The store object
        """


        if self.test_path_accessible(path):
            if self.cache > 0 and cached:
                return zarr.LRUStoreCache(self.fs.get_mapper(path), self.cache)
            else:
                return self.fs.get_mapper(path)

    @property
    def fs(self) -> s3fs.S3FileSystem:
        """The filesystem object"""
        assert (
            self._s3fs is not None
        ), "Filesystem is not connected yet, please make sure to connect first"
        return self._s3fs

    async def aget_credentials(self, id: Optional[str] = None) -> None:
        """ Get credentials from the mikro api
        
        Parameters:
        __________
        id: str, optional
            The id of the file to get. 
            If None, it will get the default credentials-

        Returns:
        ________
        None

        """


        from mikro.api.schema import arequest

        c = await arequest()
        if c:
            self.access_key = c.access_key
            self.secret_key = c.secret_key
            self.session_token = c.session_token
        else:
            raise Exception("Could not get credentials")

    async def aconnect(self) -> "DataLayer":
        """ Connect to the S3 instance""
        
        Connects to the S3 instance and gets the credentials from the mikro api
        to connect to the S3 instance.
        
        
        """
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

    def reconnect(self) -> None:
        unkoil(self.adisconnect)
        unkoil(self.aconnect)

    async def areconnect(self) -> None:
        await self.adisconnect()
        await self.aconnect()

    def _repr_html_inline_(self):
        """Returns the html representation of the datalayer"""
        return (
            f"<table><tr><td>auto_connect</td><td>{self.auto_connect}</td></tr></table>"
        )

    async def adisconnect(self) -> "DataLayer":
        """Disconnect from the S3 instance
        
        Disconnects from the S3 instance and clears the credentials.
        
        """
        self._connected = False
        return self

    async def __aenter__(self) -> "DataLayer":
        """ Enters the context manager
        
        Enters the context manager and sets the current datalayer to this datalayer.
        This is used for the global datalayer variable."""
        
        self._executor_session = self.executor.__enter__()
        current_datalayer.set(self)
        return self

    async def __aexit__(self, *args, **kwargs):
        """ Exits the context manager

        Exits the context manager and clears the current datalayer variable."""
        current_datalayer.set(None)
        self.executor.__exit__(*args, **kwargs)
        return self

    class Config:
        """pydantic config class"""
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True
