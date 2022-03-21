"""
This modules provides the main app. It is responsible for setting up the connection to the mikro-server and
handling authentification and setting up the configuration. Mikro handles the creation of the datalayer and
the graphql client.

You can compose this app together with other apps to create a full fledged app. (Like combining with
arkitekt to enable to call functions that you define on the app)

Example:

    A simple app that takes it configuraiton from basic.fakts and connects to the mikro-server.
    You can define all of the logic within the context manager

    ```python
    from mikro.app import MikroApp

    app = MikroApp(fakts=Fakts(subapp="basic"))

    with app:
        # do stuff

    ```

    Async Usage:


    ```python
    from mikro.app import MikroApp

    app = MikroApp(fakts=Fakts(subapp="basic"))

    async with app:
        # do stuff

    ```

 
"""


from pydantic import Field
from herre import Herre
from fakts import Fakts
from herre.fakts.herre import FaktsHerre
from koil.composition import Composition
from mikro.composition.base import Mikro


class MikroApp(Composition):
    """Mikro App

    It is responsible for setting up the connection to the mikro-server and
    handling authentification and setting up the configuration. Mikro handles the creation of the datalayer and
    the graphql client.

    You can compose this app together with other apps to create a full fledged app. (Like combining with
    arkitekt to enable to call functions that you define on the app). See the example in the docstring.

    Attributes:
        fakts (Fakts): The fakts instance to use.
        mikro (Mikro): The mikro instance to use.
        herre (Herre): The herre instance to use.

    """

    fakts: Fakts = Field(default_factory=Fakts)
    """The fakts layer that is used for configuration
    """

    herre: Herre = Field(default_factory=FaktsHerre)
    """The herre layer that is used for authentication
    """
    mikro: Mikro = Field(default_factory=Mikro)
    """The mikro layer that is used for the datalayer and
    api client
    """
