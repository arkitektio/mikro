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


import contextvars
import logging
import os
from koil.decorators import koilable
import s3fs


current_datalayer = contextvars.ContextVar("current_datalayer", default=None)
GLOBAL_DATALAYER = None


@koilable(add_connectors=True)
class DataLayer:
    """Implements a S3 DataLayer

    This will be used to upload and download files from S3.
    Make sure to set the access_key and secret_key and enter the context
    manager to connect to S3 (if authentication is required for the S3 instance
    and to ensure that the context is exited when the context manager is exited
    (for future cleanup purposes on other datalayers).

    Attributes:
        fs (s3fs.S3FileSystem): The filesystem object

    """

    access_key: str
    secret_key: str
    endpoint_url: str

    def __init__(self, access_key="", secret_key="", endpoint_url="") -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self.connected = False
        self._s3fs = None
        super().__init__()

    @property
    def fs(self):
        assert self.endpoint_url, "Endpoint url is not set"
        if not self._s3fs:
            if self.access_key:
                os.environ["AWS_ACCESS_KEY_ID"] = self.access_key
            if self.secret_key:
                os.environ["AWS_SECRET_ACCESS_KEY"] = self.secret_key

            self._s3fs = s3fs.S3FileSystem(
                secret=self.secret_key,
                key=self.access_key,
                client_kwargs={"endpoint_url": self.endpoint_url},
            )

        assert (
            self._s3fs is not None
        ), "Filesystem is not connected yet, please make sure to connect first"
        return self._s3fs

    async def __aenter__(self):
        current_datalayer.set(self)
        return self

    async def __aexit__(self, *args, **kwargs):
        current_datalayer.set(None)
        return self
