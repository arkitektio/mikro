from koil.composition import Composition
from pydantic import Field

from mikro_next.datalayer import DataLayer
from mikro_next.rath import MikroNextRath


class MikroNext(Composition):
    """The Mikro Composition

    This composition provides a datalayer and a rath for interacting with the
    mikro api and beyond

    You shouldn't need to create this directly, instead use the builder functions
    to generate a new instance of this composition.

    ```python

    from mikro import Mikro

    async def aget_token():
        return "XXXX"

    m = Mikro(
        datalayer= DataLayer(endpoint_url="s3.amazonaws.com", access_key="XXXX", secret_key="XXXX"),
        mikro = MikroRath(link=MikroLinkComposition(auth=AuthTokenLink(token_loader=aget_token)))),
    )
    ```
    """

    datalayer: DataLayer = Field(
        ..., description="The datalayer for interacting with the mikro api"
    )
    rath: MikroNextRath
