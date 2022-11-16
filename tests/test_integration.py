from functools import cached_property
import numpy as np
import pytest
from mikro.api.schema import create_sample, from_xarray, get_random_rep
from .integration.utils import wait_for_http_response
from .utils import build_relative
import xarray as xr
import os
import subprocess
from testcontainers.compose import DockerCompose
from koil





class DockerV2Compose(DockerCompose):

    @cached_property
    def docker_cmd_comment(self):
        """Returns the base docker command by testing the docker compose api

        Returns:
            list[ſt]: _description_
        """
        return ["docker","compose"] if subprocess.run(["docker", "compose", "--help"], stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT).returncode == 0 else ["docker-compose"]

    def docker_compose_command(self):
        """
        Returns command parts used for the docker compose commands

        Returns
        -------
        list[str]
            The docker compose command parts
        """
        docker_compose_cmd = self.docker_cmd_comment
        for file in self.compose_file_names:
            docker_compose_cmd += ['-f', file]
        if self.env_file:
            docker_compose_cmd += ['--env-file', self.env_file]
        return docker_compose_cmd



@pytest.mark.integration
@pytest.fixture(scope="session")
def environment():

    assert os.path.exists(build_relative("integration")), "Integration tests not found"

    with DockerV2Compose(
        filepath=build_relative("integration"),
        compose_file_name="docker-compose.yml",
    ) as compose:
        wait_for_http_response("http://localhost:8019/ht", max_retries=5)
        wait_for_http_response("http://localhost:8088/ht", max_retries=5)
        yield


@pytest.mark.integration
@pytest.fixture
def app():
    from fakts import Fakts
    from arkitekt.apps.mikro import MikroApp
    from herre.fakts import FaktsHerre
    from fakts.grants.remote.claim import ClaimGrant
    from fakts.grants.remote.base import StaticDiscovery

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
        assert x.data.shape == (1, 1, 10, 1000, 1000), "Did not write data according to schema ( T, C, Z, Y, X )"


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
        assert (
            x.creator.email == "jhnnsr@gmail.com"
        ), "Sample did not have the right user name attached"
