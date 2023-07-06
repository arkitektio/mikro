from pydantic import Field
from mikro.links.datalayer import DataLayerUploadLink
from rath import rath
import contextvars
from rath.links.auth import AuthTokenLink
from rath.links.compose import TypedComposedLink
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.split import SplitLink


current_mikro_rath = contextvars.ContextVar("current_mikro_rath")


class MikroLinkComposition(TypedComposedLink):
    datalayer: DataLayerUploadLink = Field(default_factory=DataLayerUploadLink)
    fileextraction: FileExtraction = Field(default_factory=FileExtraction)
    dicting: DictingLink = Field(default_factory=DictingLink)
    auth: AuthTokenLink
    split: SplitLink


class MikroRath(rath.Rath):
    """ Mikro Rath

    Mikro Rath is the GraphQL client for Mikro. It is a thin wrapper around Rath
    that provides some default links and a context manager to set the current
    client. (This allows you to use the `mikro.rath.current` function to get the
    current client, within the context of mikro app).
    
    This is a subclass of Rath that adds some default links to convert files and array to support
    the graphql multipart request spec."""
    link: MikroLinkComposition

    def _repr_html_inline_(self):
        return f"<table><tr><td>auto_connect</td><td>{self.auto_connect}</td></tr></table>"

    async def __aenter__(self):
        await super().__aenter__()
        current_mikro_rath.set(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        current_mikro_rath.set(None)
