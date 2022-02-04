






from pydantic import BaseModel
from fakts.fakts import Fakts, get_current_fakts
from herre.herre import Herre, get_current_herre
from mikro.datalayer import DataLayer



class DataLayerConfig(BaseModel):
    secret_key: str
    access_key: str
    endpoint_url: str

class FaktsDataLayer(DataLayer):

    def __init__(self, *args, fakts: Fakts = None, herre: Herre = None, fakts_key= "mikro.s3", **kwargs) -> None:
        self.fakts = fakts or get_current_fakts()
        self.herre = herre or get_current_herre()
        self.fakts_key = fakts_key
        self.config = None
        super().__init__(*args, **kwargs)

    def configure(self, fakts: DataLayerConfig):
        self.access_key = fakts.access_key
        self.secret_key = fakts.secret_key
        self.endpoint_url = fakts.endpoint_url

    async def aconnect(self):

        if not self.config:
            self.fakts = await self.fakts.aget(self.fakts_key)
            self.configure(DataLayerConfig(**self.fakts))

        return await super().aconnect()