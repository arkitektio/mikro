from graphql import OperationType
from pydantic import Field
from mikro.links.datalayer import DataLayerUploadLink
from rath import rath
import contextvars
from rath.contrib.fakts.links.aiohttp import FaktsAIOHttpLink
from rath.contrib.fakts.links.websocket import FaktsWebsocketLink
from rath.contrib.herre.links.auth import HerreAuthLink
from rath.links.base import TerminatingLink
from rath.links.compose import compose
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.shrink import ShrinkingLink
from rath.links.split import SplitLink


current_mikro_rath = contextvars.ContextVar("current_mikro_rath")


class MikroRath(rath.Rath):
    link: TerminatingLink = Field(
        default_factory=lambda: compose(
            DataLayerUploadLink(),
            FileExtraction(),
            ShrinkingLink(),
            DictingLink(),
            HerreAuthLink(),
            SplitLink(
                left=FaktsAIOHttpLink(fakts_group="mikro"),
                right=FaktsWebsocketLink(fakts_group="mikro"),
                split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
            ),
        )
    )

    async def __aenter__(self):
        await super().__aenter__()
        current_mikro_rath.set(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        current_mikro_rath.set(None)
