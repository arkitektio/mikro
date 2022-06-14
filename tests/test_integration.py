import numpy as np
import pytest
from mikro.app import MikroApp
from fakts import Fakts
from mikro.api.schema import create_sample, from_xarray, get_random_rep
from .integration.utils import wait_for_http_response
from .utils import build_relative
import xarray as xr
from testcontainers.compose import DockerCompose
from herre.fakts import FaktsHerre
from fakts.grants.remote.claim import ClaimGrant
from fakts.grants.remote.base import StaticDiscovery


@pytest.mark.integration
@pytest.fixture(scope="session")
def environment():
    with DockerCompose(
        filepath=build_relative("integration"),
        compose_file_name="docker-compose.yaml",
    ) as compose:
        wait_for_http_response("http://localhost:8019/ht", max_retries=5)
        wait_for_http_response("http://localhost:8088/ht", max_retries=5)
        yield


@pytest.mark.integration
@pytest.fixture
def app():

    return MikroApp(
        fakts=Fakts(
            grant=ClaimGrant(
                client_id="DSNwVKbSmvKuIUln36FmpWNVE2KrbS2oRX0ke8PJ",
                client_secret="Gp3VldiWUmHgKkIxZjL2aEjVmNwnSyIGHWbQJo6bWMDoIUlBqvUyoGWUWAe6jI3KRXDOsD13gkYVCZR0po1BLFO9QT4lktKODHDs0GyyJEzmIjkpEOItfdCC4zIa3Qzu",
                graph="localhost",
                discovery=StaticDiscovery(base_url="http://localhost:8019/f/"),
            ),
            force_refresh=True,
        ),
        herre=FaktsHerre(no_temp=True),
    )


@pytest.mark.integration
def test_write_random(app, environment):

    with app:
        x = from_xarray(
            xr.DataArray(data=np.random.random((1000, 1000, 10)), dims=["x", "y", "z"]),
            tags=["test"],
            name="test_random_write",
        )
        assert x.id, "Did not get a random rep"
        assert x.data.shape == (1, 1, 1000, 1000, 10), "Did not write data"


@pytest.mark.integration
def test_get_random(app, environment):

    with app:
        x = get_random_rep()
        assert x.id, "Did not get a random rep"

@pytest.mark.integration
def test_create_sample(app, environment):

    with app:
        x = create_sample(name="johannes")
        assert x.id, "Was not able to create a sample"
        assert x.creator.email == "jhnnsr@gmail.com", "Sample did not have the right user name attached"