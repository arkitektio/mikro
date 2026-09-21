from types import TracebackType

from pydantic import Field
from rath import rath
from rath.links.auth import AuthTokenLink
from rath.links.compose import TypedComposedLink
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.split import SplitLink

from mikro.middleware.base import OperationMiddleware

class MikroLinkComposition(TypedComposedLink):
    """The MikroLinkComposition

    This is a composition of links that are traversed before a request is sent to the
    mikro api. This link composition contains the default links for mikro.

    Upload logic has been moved to the UploadMiddleware, which runs at the operation
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


#: The name the generated ``mikro.api.schema`` still imports. That module is
#: generated and is not edited by hand, so the old spelling has to resolve until
#: the next ``turms gen`` — ``graphql.config.yaml`` already names ``MikroRath``,
#: so the regen drops it and this alias can go with it.
