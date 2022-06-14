from fakts import Fakts
from fakts.grants.remote.claim import ClaimGrant
from fakts.grants.remote.base import StaticDiscovery

fakts = Fakts(
    grant=ClaimGrant(
        client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ",
        client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
        graph="localhost",
        discovery=StaticDiscovery(base_url="http://localhost:8008/f/"),
    )
)


with fakts:
    x = fakts.load()
    print(x)
