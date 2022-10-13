from graphql import OperationType
from pydantic import Field
from mikro.links.datalayer import DataLayerUploadLink
from rath import rath
import contextvars
from rath.links.auth import AuthTokenLink
from rath.links.compose import TypedComposedLink, compose
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.shrink import ShrinkingLink
from rath.links.split import SplitLink


current_mikro_rath = contextvars.ContextVar("current_mikro_rath")


class MikroLinkComposition(TypedComposedLink):
    datalayer: DataLayerUploadLink = Field(default_factory=DataLayerUploadLink)
    fileextraction: FileExtraction = Field(default_factory=FileExtraction)
    dicting: DictingLink = Field(default_factory=DictingLink)
    auth: AuthTokenLink
    split: SplitLink


class MikroRath(rath.Rath):
    link: MikroLinkComposition

    async def __aenter__(self):
        await super().__aenter__()
        current_mikro_rath.set(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        current_mikro_rath.set(None)
