from pydantic import BaseModel
from fakts.config.base import Config
from fakts.fakts import Fakts, current_fakts
from herre.herre import Herre, current_herre
from mikro.datalayer import DataLayer


class DataLayerConfig(Config):
    secret_key: str
    access_key: str
    endpoint_url: str

    class Config:
        group = "mikro.datalayer"


class FaktsDataLayer(DataLayer):
    def __init__(
        self, *args, fakts: Fakts = None, herre: Herre = None, **kwargs
    ) -> None:
        self.fakts = fakts
        self.herre = herre
        super().__init__(*args, **kwargs)

    def configure(self, config: DataLayerConfig, herre: Herre) -> None:
        self.herre = herre
        self.access_key = config.access_key
        self.secret_key = config.secret_key
        self.endpoint_url = config.endpoint_url

    async def __aenter__(self):
        self.herre = self.herre or current_herre.get()
        config = await DataLayerConfig.from_fakts(self.fakts)
        self.configure(config, herre=self.herre)

        return await super().__aenter__()
