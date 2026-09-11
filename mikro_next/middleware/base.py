"""Base middleware classes for the funcs API.

Defines the abstract FuncsMiddleware interface that middleware implementations
must follow. Each middleware can intercept execute and subscribe calls, process
the serialized arguments, and pass through to the next middleware in the chain.

Both sync and async variants are supported:
    - `process_variables`: Sync path, called from `execute()` / `subscribe()`.
    - `aprocess_variables`: Async path, called from `aexecute()` / `asubscribe()`.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from mikro_next.rath import MikroNextRath

from rath.turms.funcs import TOperation


class FuncsMiddleware(BaseModel, abc.ABC):
    """Base class for funcs-level middleware.

    Middleware intercepts operations between the user-facing API functions
    (execute/subscribe) and the rath link chain. This allows pre-processing
    of serialized arguments—such as uploading arrays and files—before the
    operation reaches the graphql transport.

    Subclasses must implement:
        - process_variables: Sync processing of serialized variables dict.
        - aprocess_variables: Async processing of serialized variables dict.

    The middleware receives the fully serialized variables dict (after
    ``operation.Arguments(**variables).model_dump()``) and must return the
    processed dict. This ensures that pydantic validation and alias resolution
    have already occurred before the middleware runs.
    """

    @abc.abstractmethod
    def process_variables(
        self,
        variables: dict[str, Any],
        operation: type[TOperation],
        rath: MikroNextRath,
    ) -> dict[str, Any]:
        """Process the serialized variables dict synchronously.

        Called from ``execute()`` and ``subscribe()`` (the sync path).
        Implementations should use synchronous I/O (e.g., obstore for S3).

        Args:
            variables: The serialized variables dict (after model_dump).
            operation: The operation type being executed.
            rath: The rath client instance.

        Returns:
            The processed variables dict, ready to be sent to rath.
        """
        ...

    @abc.abstractmethod
    async def aprocess_variables(
        self,
        variables: dict[str, Any],
        operation: type[TOperation],
        rath: MikroNextRath,
    ) -> dict[str, Any]:
        """Process the serialized variables dict asynchronously.

        Called from ``aexecute()`` and ``asubscribe()`` (the async path).
        Implementations should use async I/O (e.g., obstore for S3).

        Args:
            variables: The serialized variables dict (after model_dump).
            operation: The operation type being executed.
            rath: The rath client instance.

        Returns:
            The processed variables dict, ready to be sent to rath.
        """
        ...

    async def aenter(self) -> None:
        """Called when the middleware stack is entered (async context)."""

    async def aexit(self) -> None:
        """Called when the middleware stack is exited (async context)."""
