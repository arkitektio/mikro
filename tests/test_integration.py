import numpy as np
import pytest
from mikro.app import MikroApp
from fakts import Fakts
from fakts.grants import YamlGrant
from mikro.api.schema import from_xarray, get_random_rep
from .integration.utils import wait_for_http_response
from .utils import build_relative
import xarray as xr
from testcontainers.compose import DockerCompose
from herre.fakts import FaktsHerre


@pytest.mark.integration
@pytest.fixture(scope="session")
def environment():
    with DockerCompose(
        filepath=build_relative("integration"),
        compose_file_name="docker-compose.yaml",
    ) as compose:
        wait_for_http_response("http://localhost:8008/ht", max_retries=5)
        yield


@pytest.mark.integration
@pytest.fixture
def app():

    return MikroApp(
        fakts=Fakts(
            subapp="test",
            grants=[YamlGrant(filepath=build_relative("configs/test.yaml"))],
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
