from .app import MikroApp
from arkitekt.app import ArkitektApp


class ConnectedApp(MikroApp, ArkitektApp):
    """A connected app composed
    of both a Mikro App and a Arkitekt App.
    """

