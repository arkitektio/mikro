from pydantic import Field
from koil import koilable
from koil.composition import Composition
from mikro.fakts.rath import FaktsMikroRath
from mikro.fakts.datalayer import FaktsDataLayer
from mikro.datalayer import DataLayer
from mikro.mikro import MikroRath


@koilable(add_connectors=True)
class Mikro(Composition):
    rath: MikroRath = Field(default_factory=FaktsMikroRath)
    datalayer: DataLayer = Field(default_factory=FaktsDataLayer)
