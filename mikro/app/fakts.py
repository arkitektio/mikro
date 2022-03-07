from pydantic import BaseModel
from fakts.config.base import Config
from koil import koilable
from mikro.app.mikro import Mikro
from mikro.datalayer import DataLayer
from mikro.fakts.datalayer import FaktsDataLayer, DataLayerConfig
from mikro.fakts.rath import FaktsMikroRath, MikroRathConfig
from fakts import Fakts, Config
from mikro.fakts.rath import FaktsMikroRath
from herre import Herre, current_herre


class MikroConfig(MikroRathConfig):
    datalayer: DataLayerConfig

    class Config:
        group = "mikro"
        env_prefix = "mikro_"


class FaktsMikro(Mikro):
    fakts: Fakts

    def __init__(self, fakts: Fakts = None):
        super().__init__(FaktsMikroRath(fakts=fakts), FaktsDataLayer(fakts=fakts))
