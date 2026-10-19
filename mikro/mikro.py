from collections.abc import AsyncGenerator, Generator
from typing import Any

from koil import unkoil_gen
from koil.composition import Composition
from pydantic import Field
from rath.origin import origin_context
from rath.task import TASK_HEADER, TaskLike, current_task, token_of
from rath.turms.funcs import TOperation

from mikro.api.schema import MikroApi
from mikro.datalayer import DataLayer
from mikro.rath import MikroRath


class Mikro(Composition, MikroApi):
    """The Mikro Composition

    This composition provides a datalayer and a rath for interacting with the
    mikro api and beyond. Every operation of the API is a method of it, mixed in
    from the generated ``MikroApi``; each hands its operation class and variables
    to ``execute``/``aexecute`` (queries and mutations) or
    ``subscribe``/``asubscribe`` (subscriptions), implemented here over the rath.
    Nothing is looked up. The objects a call returns remember this client, so
    what they fetch later (``.data``, ``.download()``) goes through it too.

    Middleware:
        Serialized variables pass through the rath's ``middlewares`` chain
        before they reach the link chain. The sync path (``execute``/``subscribe``)
        calls ``process_variables``, which uses sync I/O (e.g. obstore for S3
        uploads); the async path (``aexecute``/``asubscribe``) calls
        ``aprocess_variables``.

    You shouldn't need to create this directly: an app gets one from the mikro
    service (``mikro.arkitekt.service``), which builds the rath and its links.
    """

    datalayer: DataLayer = Field(
        ..., description="The datalayer for interacting with the mikro api"
    )
    rath: MikroRath

    # --- executing the generated operations

    def _origin(self) -> dict[str, Any]:
        """What the objects of a result should remember: the client that fetched them.

        The origin names the client, so an object's later calls (``.data``,
        ``.download()``, a follow-up query) go through the exact client, rath and
        datalayer, that produced it.
        """
        return origin_context(client=self, rath=self.rath, datalayer=self.datalayer)

    def _headers(self, task: "TaskLike | None" = None) -> dict[str, Any] | None:
        """The per-call headers: the provenance token of the task this call is for.

        ``task`` when the caller named one, else whichever task is running. There
        is no per-task copy of this client: one instance serves every task, and
        what a request is attributed to is decided per call.
        """
        token = token_of(task)
        return {TASK_HEADER: token} if token else None

    @staticmethod
    def _serialize(operation: type[TOperation], variables: dict[str, Any]) -> dict[str, Any]:
        # pydantic validation + alias resolution; exclude_unset lets the server apply
        # its own defaults for what the caller never set.
        return operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True)

    def _apply_middlewares(
        self, variables: dict[str, Any], operation: type[TOperation]
    ) -> dict[str, Any]:
        """Runs the rath's middleware chain over the serialized variables (sync path).

        Each middleware processes the variables in order through its sync
        ``process_variables``. This happens *after* pydantic serialization
        (model_dump) but *before* the operation is sent to rath.
        """
        for middleware in self.rath.middlewares:
            variables = middleware.process_variables(variables, operation, self.rath)
        return variables

    async def _aapply_middlewares(
        self, variables: dict[str, Any], operation: type[TOperation]
    ) -> dict[str, Any]:
        """Runs the rath's middleware chain over the serialized variables (async path).

        Each middleware processes the variables in order through its async
        ``aprocess_variables``.
        """
        for middleware in self.rath.middlewares:
            variables = await middleware.aprocess_variables(variables, operation, self.rath)
        return variables

    def execute(
        self,
        operation: type[TOperation],
        variables: dict[str, Any],
        task: "TaskLike | None" = None,
    ) -> TOperation:
        """Executes a query or mutation in a blocking way.

        Uses the sync middleware path (process_variables) which runs
        uploads via obstore in the calling thread.
        """
        serialized = self._apply_middlewares(self._serialize(operation, variables), operation)
        x = self.rath.query(operation.Meta.document, serialized, headers=self._headers(task))
        return operation.model_validate(x.data, context=self._origin())

    async def aexecute(
        self,
        operation: type[TOperation],
        variables: dict[str, Any],
        task: "TaskLike | None" = None,
    ) -> TOperation:
        """Executes a query or mutation in a non-blocking way.

        Uses the async middleware path (aprocess_variables) which runs
        uploads via obstore.
        """
        serialized = await self._aapply_middlewares(
            self._serialize(operation, variables), operation
        )
        x = await self.rath.aquery(operation.Meta.document, serialized, headers=self._headers(task))
        return operation.model_validate(x.data, context=self._origin())

    def subscribe(
        self,
        operation: type[TOperation],
        variables: dict[str, Any],
        task: "TaskLike | None" = None,
    ) -> Generator[TOperation, None, None]:
        """Subscribes to an operation in a blocking way."""
        # Resolved here, on the caller's own thread, rather than after the koil
        # hop: the ambient task is the caller's, and this does not depend on how
        # faithfully the bridge copies context.
        return unkoil_gen(
            self.asubscribe,
            operation,
            variables,
            task=task if task is not None else current_task.get(),
        )

    async def asubscribe(
        self,
        operation: type[TOperation],
        variables: dict[str, Any],
        task: "TaskLike | None" = None,
    ) -> AsyncGenerator[TOperation, None]:
        """Subscribes to an operation in a non-blocking way.

        Uses the async middleware path (aprocess_variables).
        """
        serialized = await self._aapply_middlewares(
            self._serialize(operation, variables), operation
        )
        async for event in self.rath.asubscribe(
            operation.Meta.document, serialized, headers=self._headers(task)
        ):
            yield operation.model_validate(event.data, context=self._origin())
