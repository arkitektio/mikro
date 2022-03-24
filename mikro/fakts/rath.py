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
from rath.links.dictinglink import DictingLink
from rath.links.shrink import ShrinkingLink
from rath.links.split import SplitLink
from rath.links.websockets import WebSocketLink
from fakts import Config
from rath.links.transpile import TranspileLink, TranspileRegistry
from mikro.api.schema import InputVector
import numpy as np


class MikroRathConfig(Config):
    endpoint_url: str
    ws_endpoint_url: str

    class Config:
        group = "mikro"


registry = TranspileRegistry()


@registry.register_list(
    "InputVector", lambda x, d: isinstance(x, np.ndarray) and d == 1
)
def transpile_np_to_vector(x, d):
    """Transpiles numpy vectors to InputVector"""
    assert x.ndim == 2, "Needs to be a List array of vectors"
    if x.shape[1] == 3:
        return [InputVector(x=i[0], y=i[1], z=i[2]) for i in x.tolist()]
    elif x.shape[1] == 2:
        return [InputVector(x=i[0], y=i[1]) for i in x.tolist()]
    else:
        raise NotImplementedError(
            f"Incompatible shape {x.shape} of {d}. List dimension needs to either be of size 2 or 3"
        )


class FaktsMikroRath(MikroRath):
    def configure(
        self, config: MikroRathConfig, datalayer: DataLayer, herre: Herre
    ) -> None:
        self.link = compose(
            DataLayerParquetUploadLink(datalayer=datalayer),
            DataLayerXArrayUploadLink(datalayer=datalayer),
            TranspileLink(registry=registry),
            ShrinkingLink(),
            DictingLink(),
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
