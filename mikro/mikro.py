from pydantic import Field
from koil import koilable
from koil.composition import Composition
from mikro.datalayer import DataLayer
from mikro.rath import MikroRath


@koilable(add_connectors=True)
class Mikro(Composition):
    """ The Mikro Composition
    
    This composition provides a datalayer and a rath for interacting with the
    mikro api.

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


    datalayer: DataLayer
    rath: MikroRath = Field(default_factory=MikroRath)
