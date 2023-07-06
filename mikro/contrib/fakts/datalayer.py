from typing import Any, Dict, Optional

from fakts.fakt.base import Fakt
from fakts.fakts import Fakts, get_current_fakts
from herre.herre import Herre, current_herre
from mikro.datalayer import DataLayer


class DataLayerFakt(Fakt):
    endpoint_url: str

    class Config:
        group = "mikro.datalayer"


class FaktsDataLayer(DataLayer):
    """ A fakts implementation of the datalayer. This will allow you to connect to a datalayer
    that is defined asnychronously in fakts. This is useful for connecting to a datalayer that
    is not known at compile time. Will get the server configuration from fakts and connect to the
    datalayer. """
    fakts_group: str
    fakts: Optional[Fakts] = None
    herre: Optional[Herre] = None

    _old_fakt: Dict[str, Any] = {}

    def configure(self, fakt: DataLayerFakt) -> None:
        self.herre = self.herre or current_herre.get()
        self.endpoint_url = fakt.endpoint_url

    async def aconnect(self):
        fakts = get_current_fakts()

        if fakts.has_changed(self._old_fakt, self.fakts_group):
            self._old_fakt = await fakts.aget(self.fakts_group)
            self.configure(DataLayerFakt(**self._old_fakt))
        return await super().aconnect()

    async def __aenter__(self):
        return await super().__aenter__()
