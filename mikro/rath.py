from types import TracebackType

from pydantic import Field
from rath import rath

from mikro.middleware.base import OperationMiddleware


class MikroRath(rath.Rath):
    """Mikro Rath

    Mikro Rath is the GraphQL client for mikro It is a thin wrapper around Rath
    that provides some default links and a context manager to set the current
    client. (This allows you to use the `mikrorath.current` function to get the
    current client, within the context of mikro app).

    This is a subclass of Rath that adds some default links to convert files and array to support
    the graphql multipart request spec.

    Attributes:
        middlewares: A list of OperationMiddleware instances that process serialized
            variables before they reach the rath link chain. Middleware runs in
            order: first middleware processes first, then passes to the next.
    """

    middlewares: list[OperationMiddleware] = Field(default_factory=list)
    """Middleware chain applied to serialized variables in Mikro.execute/subscribe."""

    async def __aenter__(self) -> "MikroRath":
        """Enter the client and its middlewares.

        Entering does not make it "the current client": only the mikro service
        that owns it is current while entered (see :class:`mikro.mikro.Mikro`).
        A rath used on its own is passed where it is needed, as ``rath=``.
        """
        await super().__aenter__()
        for mw in self.middlewares:
            await mw.aenter()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the middlewares and the client"""
        for mw in self.middlewares:
            await mw.aexit()
        await super().__aexit__(exc_type, exc_val, exc_tb)
