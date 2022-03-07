from koil import koilable
from mikro.datalayer import DataLayer
from mikro.mikro import MikroRath


@koilable(add_connectors=True)
class Mikro:
    rath: MikroRath
    datalayer: DataLayer

    def __init__(self, rath: MikroRath, datalayer: DataLayer) -> None:
        self.rath = rath
        self.datalayer = datalayer

    async def __aenter__(self):
        await self.rath.__aenter__()
        await self.datalayer.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.datalayer.__aexit__(exc_type, exc_val, exc_tb)
        await self.rath.__aexit__(exc_type, exc_val, exc_tb)
