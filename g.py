from mikro.app import MikroApp
from fakts import Fakts
from herre.fakts import FaktsHerre
from fakts.grants.remote.claim import ClaimGrant
from fakts.grants.remote.base import StaticDiscovery
from mikro.api.schema import from_xarray

m = MikroApp(
        fakts=Fakts(
            grant=ClaimGrant(
                client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ",
                client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
                graph="localhost",
                discovery=StaticDiscovery(base_url="http://localhost:8008/f/"),
            ),
            force_refresh=True,
        ),
        herre=FaktsHerre(no_temp=True),
    )


    