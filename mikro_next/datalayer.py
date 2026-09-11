"""
This modules provides the datalayer.

Example:

    A simple datalayer that connects to an s3 instance via access_key and secret_key.
    You can define all of the logic within the context manager

    ```python
    from mikro_next imports Datalayer

    dl = Datalayer(access_key="XXXX", secret_key="XXXX", endpoint_url="s3.amazonaws.com")

    with dl:

    ```

    Async Usage:

    ```python
    from mikro_nextdatalayer import Datalayer

    dl = Datalayer(access_key="XXXX", secret_key="XXXX", endpoint_url="s3.amazonaws.com")

    async with dl:

    ```


"""

import contextvars
from types import TracebackType
from typing import Optional

from koil.composition import KoiledModel

current_next_datalayer: contextvars.ContextVar[Optional["DataLayer"]] = contextvars.ContextVar(
    "current_next_datalayer", default=None
)


class DataLayer(KoiledModel):
    """Implements a S3 DataLayer

    This will be used to upload and download files from S3.

    Make sure to set the access_key and secret_key and enter the context
    manager to connect to S3 (if authentication is required for the S3 instance
    and to ensure that the context is exited when the context manager is exited
    (for future cleanup purposes on other datalayers).

    """

    endpoint_url: str = ""

    async def get_endpoint_url(self) -> str:
        """Return the configured S3 endpoint URL."""
        return self.endpoint_url

    async def __aenter__(self) -> "DataLayer":
        """Enter the DataLayer context and register it as the active instance."""
        current_next_datalayer.set(self)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the DataLayer context and deregister the active instance."""
        current_next_datalayer.set(None)
