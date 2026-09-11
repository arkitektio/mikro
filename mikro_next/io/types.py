from collections.abc import Awaitable
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    runtime_checkable,
)

if TYPE_CHECKING:
    from mikro_next.api.schema import (
        Credentials,
    )
from concurrent.futures import ThreadPoolExecutor


@runtime_checkable
class Namer(Protocol):
    """Protocol for Namer

    Protocol for Uploader

    This protocol is used to define the interface for uploading
    files to a Datalayer. It should return the s3_path to the file
    """

    def __call__(
        self,
        file: Any,
    ) -> Awaitable[tuple[str, str]]: ...


@runtime_checkable
class Downloader(Protocol):
    """Protocol for objects that download a file from the DataLayer."""

    def __call__(
        self,
        file: str,
        endpoint_url: str,
        bucket: str,
        key: str,
        credentials: "Credentials",
        executor: ThreadPoolExecutor | None = None,
    ) -> Any:
        """Download a file from the DataLayer and return the local path."""
        ...


@runtime_checkable
class Uploader(Protocol):
    """Protocol for Uploader

    This protocol is used to define the interface for uploading
    files to a Datalayer. It should return the s3_path to the file

    """

    def __call__(
        self,
        file: Any,
        credentials: "Credentials",
        endpoint_url: str,
        executor: ThreadPoolExecutor | None = None,
    ) -> str: ...
