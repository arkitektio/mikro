import os
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Mapping, Sequence
from typing import Any, ClassVar

from koil import unkoil_gen
from koil.composition import Composition
from pydantic import Field
from rath.origin import origin_context
from rath.task import TASK_HEADER, TaskLike, current_task, token_of
from rath.turms.fragment import afetch_fragments_via
from rath.turms.funcs import TOperation

from mikro.api import schema
from mikro.api.schema import MikroApi
from mikro.datalayer import DataLayer
from mikro.rath import MikroRath


FEDERATED_EXPANSION_ENV = "MIKRO_FEDERATED_EXPANSION"
"""The environment variable :attr:`Mikro.federated_expansion` defaults from (``"1"`` = on)."""


def _federated_expansion_default() -> bool:
    return os.environ.get(FEDERATED_EXPANSION_ENV, "") == "1"


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

    You shouldn't need to create this directly, instead use the builder functions
    to generate a new instance of this composition.

    ```python

    from mikro import Mikro

    async def aget_token():
        return "XXXX"

    m = Mikro(
        datalayer= DataLayer(endpoint_url="s3.amazonaws.com", access_key="XXXX", secret_key="XXXX"),
        mikro = MikroRath(link=MikroLinkComposition(auth=AuthTokenLink(token_loader=aget_token)))),
    )
    ```
    """

    FRAGMENTS: ClassVar[Mapping[str, type]] = {
        "@mikro/arraydataset": schema.ArrayDataset,
        "@mikro/tabledataset": schema.TableDataset,
        "@mikro/meshcollection": schema.MeshCollection,
        "@mikro/annotationcollection": schema.AnnotationCollection,
        "@mikro/annotation": schema.Annotation,
        "@mikro/lens": schema.Lens,
        "@mikro/coordinatesystem": schema.CoordinateSystem,
        "@mikro/scene": schema.Scene,
        "@mikro/scenesnapshot": schema.SceneSnapshot,
        "@mikro/animation": schema.Animation,
        "@mikro/dataset": schema.Folder,
        "@mikro/file": schema.File,
    }
    """The fragment each structure is, for federated batch expansion."""

    datalayer: DataLayer = Field(
        ..., description="The datalayer for interacting with the mikro api"
    )
    rath: MikroRath
    federated_expansion: bool = Field(default_factory=_federated_expansion_default)
    """Whether a list of mikro structures expands in one ``_entities`` request.

    Off by default, and only to be switched on against a mikro server whose kante
    is 2.3.0 or newer *and* that sets ``KANTE_REFERENCE_QUERYSET``. Older servers
    answer ``_entities`` without organisation scoping, so a guessed id would
    expand into another organisation's object where the ``get_x`` query refuses
    it. A setting of *this client*: it defaults from ``MIKRO_FEDERATED_EXPANSION``
    when the client is built, so two clients in one process may differ.
    """


    async def aexpand_many(self, identifier: str, ids: Sequence[Any]) -> Sequence[Any]:
        """Expand several ids of one structure.

        One ``_entities`` request. Only called when :meth:`can_expand_many` said so,
        so the identifier is known to have a fragment. What ``_entities`` returns is
        bound to this client, as a ``get_x`` result is.

        Args:
            identifier: The structure's identifier, e.g. ``@mikro/arraydataset``.
            ids: The ids to expand.

        Returns:
            One object per id, in order, ``None`` where there is none.
        """
        fragment = self.FRAGMENTS[identifier]
        return await afetch_fragments_via(fragment, ids, rath=self.rath, origin=self._origin())

    def can_expand_many(self, identifier: str) -> bool:
        """Whether this client can fetch several ids of ``identifier`` in one request.

        Read when a run binds its structures: only then does expansion go through
        :meth:`aexpand_many` instead of one request per id. Says no unless
        :attr:`federated_expansion` is on *and* the structure has a fragment to
        ask ``_entities`` for.

        Args:
            identifier: The structure's identifier.

        Returns:
            Whether a batch request would work.
        """
        return self.federated_expansion and identifier in self.FRAGMENTS

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
