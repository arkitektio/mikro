from pydantic import Field
from koil import koilable
from koil.composition import Composition
from mikro.fakts.datalayer import FaktsDataLayer
from mikro.datalayer import DataLayer
from mikro.rath import MikroRath


@koilable(add_connectors=True)
class Mikro(Composition):
    datalayer: DataLayer = Field(
        default_factory=lambda: FaktsDataLayer(fakts_group="mikro.datalayer")
    )
    rath: MikroRath = Field(default_factory=MikroRath)
