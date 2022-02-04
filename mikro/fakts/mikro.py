from pydantic import BaseModel
from fakts.fakts import Fakts, get_current_fakts
from herre.herre import Herre, get_current_herre
from mikro.datalayer import DataLayer, get_current_datalayer
from mikro.mikro import Mikro
from mikro.links.parquet import DataLayerParquetUploadLink
from mikro.links.xarray import DataLayerXArrayUploadLink
from rath.fakts.links import FaktsAioHttpLink
from rath.herre.links import HerreAuthTokenLink
from rath.links.aiohttp import AIOHttpLink
from rath.links.auth import AuthTokenLink
from rath.links.compose import compose
from rath.links.context import SwitchAsyncLink


class S3Config(BaseModel):
    host: str
    port: int
    secure: bool


class MikroConfig(BaseModel):
    base_url: str
    s3: S3Config

    class Config:
        group = "mikro"
        env_prefix = "mikro_"


class AccessParams(BaseModel):
    access_key: str
    secret_key: str


class Transcript(BaseModel):
    protocol: str
    path: str
    params: AccessParams


class FaktsMikro(Mikro):
    def __init__(
        self,
        herre: Herre = None,
        fakts: Fakts = None,
        datalayer: DataLayer = None,
        autoconnect=True,
    ) -> None:

        herre = herre or get_current_herre()
        fakts = fakts or get_current_fakts()
        datalayer = datalayer or get_current_datalayer()

        link = compose(
            DataLayerParquetUploadLink(datalayer=datalayer),
            DataLayerXArrayUploadLink(datalayer=datalayer),
            SwitchAsyncLink(),
            HerreAuthTokenLink(herre=herre),
            FaktsAioHttpLink(fakts=fakts, fakts_key="mikro"),
        )

        super().__init__(link, autoconnect)
