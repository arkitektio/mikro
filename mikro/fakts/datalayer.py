from typing import Optional

from fakts.config.base import Config
from fakts.fakts import Fakts
from herre.herre import Herre, current_herre
from mikro.datalayer import DataLayer


class DataLayerConfig(Config):
    endpoint_url: str

    class Config:
        group = "mikro.datalayer"


class FaktsDataLayer(DataLayer):
    fakts_group: str
    fakts: Optional[Fakts] = None
    herre: Optional[Herre] = None

    def configure(self, config: DataLayerConfig, herre: Herre) -> None:
        self.herre = herre
        self.endpoint_url = config.endpoint_url

    async def aconnect(self):
        self.herre = self.herre or current_herre.get()
        config = await DataLayerConfig.from_fakts(self.fakts_group)
        self.configure(config, herre=self.herre)
        return await super().aconnect()

    async def __aenter__(self):
        return await super().__aenter__()
