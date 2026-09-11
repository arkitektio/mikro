import contextvars
from types import TracebackType
from typing import Optional

from pydantic import Field
from rath import rath
from rath.links.auth import AuthTokenLink
from rath.links.compose import TypedComposedLink
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.split import SplitLink

from mikro_next.middleware.base import FuncsMiddleware

current_mikro_next_rath: contextvars.ContextVar[Optional["MikroNextRath"]] = (
    contextvars.ContextVar("current_mikro_next_rath")
)


class MikroNextLinkComposition(TypedComposedLink):
    """The MikroNextLinkComposition

    This is a composition of links that are traversed before a request is sent to the
    mikro api. This link composition contains the default links for mikro_next.

    Upload logic has been moved to the UploadMiddleware, which runs at the funcs
    level before the rath link chain is entered.

    You shouldn't need to create this directly.
    """

    fileextraction: FileExtraction = Field(default_factory=FileExtraction)
    """ A link that extracts files from the request and follows the graphql multipart request spec"""
    dicting: DictingLink = Field(default_factory=DictingLink)
    """ A link that converts basemodels to dicts"""
    auth: AuthTokenLink
    """ A link that adds auth tokens to the request"""
    split: SplitLink
    """ A link that splits the request into a http and a websocket request"""


class MikroNextRath(rath.Rath):
    """Mikro Rath

    Mikro Rath is the GraphQL client for mikro_next It is a thin wrapper around Rath
    that provides some default links and a context manager to set the current
    client. (This allows you to use the `mikro_nextrath.current` function to get the
    current client, within the context of mikro app).

    This is a subclass of Rath that adds some default links to convert files and array to support
    the graphql multipart request spec.

    Attributes:
        middlewares: A list of FuncsMiddleware instances that process serialized
            variables before they reach the rath link chain. Middleware runs in
            order: first middleware processes first, then passes to the next.
    """

    middlewares: list[FuncsMiddleware] = Field(default_factory=list)
    """Middleware chain applied to serialized variables in funcs.execute/subscribe."""

    async def __aenter__(self) -> "MikroNextRath":
        """Sets the current mikro_next rath to this instance"""
        await super().__aenter__()
        for mw in self.middlewares:
            await mw.aenter()
        current_mikro_next_rath.set(self)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Resets the current mikro_next rath to None"""
        for mw in self.middlewares:
            await mw.aexit()
        await super().__aexit__(exc_type, exc_val, exc_tb)
        current_mikro_next_rath.set(None)
