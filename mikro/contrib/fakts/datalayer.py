from typing import Any, Dict, Optional

from pydantic import BaseModel
from fakts.fakts import Fakts
from herre.herre import Herre
from mikro.datalayer import DataLayer


class DataLayerFakt(BaseModel):
    endpoint_url: str

    class Config:
        group = "mikro.datalayer"


class FaktsDataLayer(DataLayer):
    """A fakts implementation of the datalayer. This will allow you to connect to a datalayer
    that is defined asnychronously in fakts. This is useful for connecting to a datalayer that
    is not known at compile time. Will get the server configuration from fakts and connect to the
    datalayer."""

    fakts_group: str
    fakts: Fakts
    herre: Herre

    _old_fakt: Dict[str, Any] = {}

    def configure(self, fakt: DataLayerFakt) -> None:
        self.endpoint_url = fakt.endpoint_url

    async def aconnect(self):
        if self.fakts.has_changed(self._old_fakt, self.fakts_group):
            self._old_fakt = await self.fakts.aget(self.fakts_group)
            self.configure(DataLayerFakt(**self._old_fakt))
        return await super().aconnect()

    async def __aenter__(self):
        return await super().__aenter__()
