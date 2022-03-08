from graphql import OperationType
from pydantic import BaseModel
from herre.herre import Herre, current_herre
from mikro.datalayer import DataLayer, current_datalayer
from mikro.mikro import MikroRath
from mikro.links.parquet import DataLayerParquetUploadLink
from mikro.links.xarray import DataLayerXArrayUploadLink
from rath.links.aiohttp import AIOHttpLink
from rath.links.compose import compose
from rath.links.auth import AuthTokenLink
from rath.links.context import SwitchAsyncLink
from rath.links.split import SplitLink
from rath.links.websockets import WebSocketLink
from fakts import Fakts, Config


class MikroRathConfig(Config):
    endpoint_url: str
    ws_endpoint_url: str

    class Config:
        group = "mikro"


class FaktsMikroRath(MikroRath):
    def __init__(
        self, fakts: Fakts = None, datalayer: DataLayer = None, herre: Herre = None
    ) -> None:
        link = None
        self.datalayer = datalayer
        self.herre = herre
        self.fakts = fakts
        super().__init__(link=link)

    def configure(
        self, config: MikroRathConfig, datalayer: DataLayer, herre: Herre
    ) -> None:
        self.link = compose(
            DataLayerParquetUploadLink(datalayer=datalayer),
            DataLayerXArrayUploadLink(datalayer=datalayer),
            SwitchAsyncLink(),
            AuthTokenLink(token_loader=herre.aget_token),
            SplitLink(
                AIOHttpLink(url=config.endpoint_url),
                WebSocketLink(
                    url=config.ws_endpoint_url, token_loader=herre.aget_token
                ),
                lambda o: o.node.operation != OperationType.SUBSCRIPTION,
            ),
        )

    async def __aenter__(self):

        herre = current_herre.get()
        datalayer = current_datalayer.get()

        config = await MikroRathConfig.from_fakts(fakts=self.fakts)
        self.configure(config, datalayer, herre)

        await super().__aenter__()
