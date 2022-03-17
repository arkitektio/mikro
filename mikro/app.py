from typing import Optional
from pydantic import BaseModel, Field
from herre import Herre
from fakts import Fakts
from herre.fakts.herre import FaktsHerre
from koil.composition import Composition
from koil.decorators import koilable
from koil.helpers import unkoil
from koil.koil import Koil
from mikro.composition.base import Mikro


class MikroApp(Composition):
    fakts: Fakts = Field(default_factory=Fakts)
    herre: Herre = Field(default_factory=FaktsHerre)
    mikro: Mikro = Field(default_factory=Mikro)
