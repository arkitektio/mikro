import os
import sys
from collections.abc import Generator
from dataclasses import dataclass

import pytest
from dokker import Deployment, testing
from dokker.log_watcher import LogWatcher
from rath.links.aiohttp import AIOHttpLink
from rath.links.auth import ComposedAuthLink
from rath.links.graphql_ws import GraphQLWSLink

from graphql import OperationType
from mikro_next.datalayer import DataLayer
from mikro_next.middleware.upload import UploadMiddleware
from mikro_next.mikro_next import MikroNext
from mikro_next.rath import (
    MikroNextLinkComposition,
    MikroNextRath,
    SplitLink,
)


def pytest_configure(config: pytest.Config) -> None:
    """Register custom platform markers."""
    config.addinivalue_line("markers", "linux_only: skip on non-Linux platforms")
    config.addinivalue_line("markers", "no_windows: skip on Windows")


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Skip tests marked linux_only or no_windows on the wrong platform."""
    for item in items:
        if item.get_closest_marker("linux_only") and sys.platform != "linux":
            item.add_marker(pytest.mark.skip(reason="Linux only"))
        if item.get_closest_marker("no_windows") and sys.platform == "win32":
            item.add_marker(pytest.mark.skip(reason="Not supported on Windows"))


project_path = os.path.join(os.path.dirname(__file__), "integration")
docker_compose_file = os.path.join(project_path, "docker-compose.yml")
# An untracked sibling override (see its own header): when a developer's checkout sits next
# to a live mikro source tree, it mounts that tree over the published image so the tests
# see the current schema instead of the last-pushed one. Absent (CI, anyone else), the
# published image is the schema under test, as before.
_local_override = os.path.join(project_path, "docker-compose.local.yml")
compose_files = [docker_compose_file] + ([_local_override] if os.path.exists(_local_override) else [])
private_key = os.path.join(project_path, "private_key.pem")


async def token_loader() -> str:
    """Asynchronous function to load a token for authentication.

    This returns the "test" token which is configured as a static token to map to
    the user "test" in the test environment. In a real application, this function
    will return an oauth2 token or similar authentication token.

    To change this mapping you can alter the static_token configuration in the
    mikro configuration file (inside the integration folder).

    """
    return "test"


@dataclass
class DeployedMikro:
    """Dataclass to hold the deployed MikroNext application and its components."""

    deployment: Deployment
    mikro_watcher: LogWatcher
    minio_watcher: LogWatcher
    mikro: MikroNext


@pytest.fixture(scope="session")
def deployed_app() -> Generator[DeployedMikro, None, None]:
    """Fixture to deploy the MikroNext application with Docker Compose.

    This fixture sets up the MikroNext application using Docker Compose,
    configures health checks, and provides a deployed instance of MikroNext
    for testing purposes. It also includes watchers for the Mikro and MinIO
    services to monitor their logs, when performing requests against the application.

    Yields:
        DeployedMikro: An instance containing the deployment, watchers, and MikroNext instance

    """
    setup = testing(compose_files)
    setup.add_health_check(
        url=lambda spec: (
            f"http://localhost:{spec.find_service('mikro').get_port_for_internal(80).published}/graphql"
        ),
        service="mikro",
        timeout=5,
        max_retries=20,
    )

    watcher = setup.create_watcher("mikro")
    minio_watcher = setup.create_watcher("minio")

    with setup:
        # dokker >= 2.6 does nothing on enter: the spec below has to be resolved
        # explicitly. `up()` (testing policy) also reaps the stacks earlier,
        # since-killed test runs left behind and labels this one with our PID,
        # so a stranded copy of it is removed by the next run instead of by a
        # `docker rm -f` sweep that could hit a live sibling.
        setup.down()
        setup.pull()
        setup.inspect()

        minio_url = f"http://localhost:{setup.spec.find_service('minio').get_port_for_internal(9000).published}"
        mikro_http_url = f"http://localhost:{setup.spec.find_service('mikro').get_port_for_internal(80).published}/graphql"
        mikro_ws_url = f"ws://localhost:{setup.spec.find_service('mikro').get_port_for_internal(80).published}/graphql"

        datalayer = DataLayer(
            endpoint_url=minio_url,
        )

        y = MikroNextRath(
            link=MikroNextLinkComposition(
                auth=ComposedAuthLink(token_loader=token_loader, token_refresher=token_loader),
                split=SplitLink(
                    left=AIOHttpLink(endpoint_url=mikro_http_url),
                    right=GraphQLWSLink(ws_endpoint_url=mikro_ws_url),
                    split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                ),
            ),
            middlewares=[
                UploadMiddleware(datalayer=datalayer),
            ],
        )

        mikro = MikroNext(
            datalayer=datalayer,
            rath=y,
        )

        setup.up()

        setup.run("initc", command="python init.py")

        setup.check_health()

        with mikro as mikro:
            deployed = DeployedMikro(
                deployment=setup,
                mikro_watcher=watcher,
                minio_watcher=minio_watcher,
                mikro=mikro,
            )

            yield deployed
