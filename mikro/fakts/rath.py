from graphql import OperationType
from herre.herre import Herre, current_herre
from mikro.datalayer import DataLayer, current_datalayer
from mikro.rath import MikroRath
from mikro.links.parquet import DataLayerParquetUploadLink
from mikro.links.xarray import DataLayerXArrayUploadLink
from rath.links.aiohttp import AIOHttpLink
from rath.links.compose import compose
from rath.links.auth import AuthTokenLink
from rath.links.context import SwitchAsyncLink
from rath.links.split import SplitLink
from rath.links.websockets import WebSocketLink
from fakts import Config


class MikroRathConfig(Config):
    endpoint_url: str
    ws_endpoint_url: str

    class Config:
        group = "mikro"


class FaktsMikroRath(MikroRath):
    def configure(
        self, config: MikroRathConfig, datalayer: DataLayer, herre: Herre
    ) -> None:
        self.link = compose(
            DataLayerParquetUploadLink(datalayer=datalayer),
            DataLayerXArrayUploadLink(datalayer=datalayer),
            SwitchAsyncLink(),
            AuthTokenLink(token_loader=herre.aget_token),
            SplitLink(
                left=AIOHttpLink(url=config.endpoint_url),
                right=WebSocketLink(
                    url=config.ws_endpoint_url, token_loader=herre.aget_token
                ),
                split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
            ),
        )

    async def __aenter__(self):

        herre = current_herre.get()
        datalayer = current_datalayer.get()

        config = await MikroRathConfig.from_fakts()
        self.configure(config, datalayer, herre)

        await super().__aenter__()
