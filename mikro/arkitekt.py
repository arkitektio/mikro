from typing import Optional
from pydantic import BaseModel, Field
from herre import Herre
from fakts import Fakts
from herre.fakts.herre import FaktsHerre
from koil.decorators import koilable
from koil.helpers import unkoil
from koil.koil import Koil
from mikro import Mikro
from mikro.app.fakts import FaktsMikro
from arkitekt import Arkitekt


@koilable(fieldname="koil", add_connectors=True)
class App(BaseModel):
    herre: Herre = Field(default_factory=FaktsHerre)
    fakts: Fakts = Field(default_factory=Fakts)
    mikro: Mikro = Field(default_factory=FaktsMikro)
    arkitekt: Arkitekt = Field(default_factory=Arkitekt)
    koil: Optional[Koil] = None

    async def __aenter__(self):
        await self.fakts.__aenter__()
        await self.herre.__aenter__()
        await self.mikro.__aenter__()
        await self.arkitekt.__aenter__()

        return self

    async def __aexit__(self, *args, **kwargs):
        await self.arkitekt.__aexit__(*args, **kwargs)
        await self.mikro.__aexit__(*args, **kwargs)
        await self.herre.__aexit__(*args, **kwargs)
        await self.fakts.__aexit__(*args, **kwargs)

    async def arun(self):
        await self.arkitekt.arun()

    def __enter__(self) -> "App":
        ...

    def run(self, *args, **kwargs):
        return unkoil(self.arun, *args, **kwargs)

    class Config:
        arbitrary_types_allowed = True
