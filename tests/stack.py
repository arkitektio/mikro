"""The mikro these tests run against: the real service, started in Docker.

Mikro's own suite keeps a stack of its own (the server, its database and its
object storage, with a static token) rather than a whole hub: a failure here is
then mikro's, not another service's. An app that uses mikro is tested against a
hub instead (``arkitekt.testing``), made from the image the service declares.
"""

import os
import socket
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from graphql import OperationType
from rath.links.aiohttp import AIOHttpLink
from rath.links.auth import ComposedAuthLink
from rath.links.graphql_ws import GraphQLWSLink

from mikro.datalayer import DataLayer
from mikro.middleware.upload import UploadMiddleware
from mikro.mikro import Mikro
from mikro.rath import MikroLinkComposition, MikroRath, SplitLink

from dokker import Deployment, testing
from dokker.log_watcher import LogWatcher


#: The stack: mikro, its database, redis and object storage.
COMPOSE_FILE = Path(__file__).parent / "integration" / "docker-compose.yml"

#: The token the stack's configuration maps to its test user (``configs/mikro.yaml``).
TEST_TOKEN = "test"

#: The environment variables the compose file takes its host ports from.
MIKRO_PORT_ENVVAR = "MIKRO_HOST_PORT"
RUSTFS_PORT_ENVVAR = "RUSTFS_HOST_PORT"


def _reserve_free_ports(count: int) -> list[int]:
    """Ask the OS for `count` distinct free TCP ports.

    All sockets are held open until every port has been assigned, so the kernel
    cannot hand out the same port twice within one call. They are released
    before compose binds them -- a race in theory, but the ephemeral range is
    large and this is what keeps concurrent runs (and the leftovers of a crashed
    one) from colliding on a fixed port.
    """
    sockets: list[socket.socket] = []
    try:
        for _ in range(count):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [int(sock.getsockname()[1]) for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


@contextmanager
def _host_ports() -> Generator[None]:
    """Pick this stack's host ports and point compose at them.

    Reserved rather than left to docker (`ports: - "80"`) because
    `Deployment.spec` is rendered by `docker compose config`, which is static:
    an unpublished port reads back as ``None`` and the URLs would quietly
    become ``http://localhost:None`` instead of failing loudly.
    """
    mikro_port, rustfs_port = _reserve_free_ports(2)
    env = {MIKRO_PORT_ENVVAR: str(mikro_port), RUSTFS_PORT_ENVVAR: str(rustfs_port)}
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@dataclass
class MikroStack:
    """A running mikro: where it answers, and clients for it."""

    deployment: Deployment
    http_url: str
    ws_url: str
    datalayer_url: str
    mikro_watcher: LogWatcher
    rustfs_watcher: LogWatcher

    def client(self, token: str = TEST_TOKEN) -> Mikro:
        """A new client for this stack, not yet entered.

        A new one each call, because a client is entered and left by whoever
        uses it: a test in a ``with``, a local run of an arkitekt app for as
        long as it runs.

        Args:
            token: The token it authenticates with. The stack knows ``"test"``,
                its static token; add others in ``configs/mikro.yaml``.
        """

        async def token_loader() -> str:
            return token

        datalayer = DataLayer(endpoint_url=self.datalayer_url)
        return Mikro(
            datalayer=datalayer,
            rath=MikroRath(
                link=MikroLinkComposition(
                    auth=ComposedAuthLink(token_loader=token_loader, token_refresher=token_loader),
                    split=SplitLink(
                        left=AIOHttpLink(endpoint_url=self.http_url),
                        right=GraphQLWSLink(ws_endpoint_url=self.ws_url),
                        split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                    ),
                ),
                middlewares=[UploadMiddleware(datalayer=datalayer)],
            ),
        )


@contextmanager
def start_mikro(
    extra_compose_files: Sequence[str | Path] = (),
) -> Generator[MikroStack]:
    """Start mikro in Docker, and remove it on leaving.

    The image is ``jhnnsrs/mikro:$MIKRO_SERVICE_TAG`` (``latest`` when unset).

    Args:
        extra_compose_files: Compose files laid over the stack's own, e.g. one
            that mounts a server source tree over the image.

    Yields:
        The stack, up and healthy.
    """
    with _host_ports():
        setup = testing([COMPOSE_FILE, *(Path(file) for file in extra_compose_files)])
        setup.add_health_check(
            url=lambda spec: (
                f"http://localhost:{spec.find_service('mikro').get_port_for_internal(80).published}/graphql"
            ),
            service="mikro",
            timeout=5,
            max_retries=20,
        )

        watcher = setup.create_watcher("mikro")
        rustfs_watcher = setup.create_watcher("rustfs")

        with setup:
            # dokker >= 2.6 does nothing on enter: the spec below has to be resolved
            # explicitly. `up()` (testing policy) also reaps the stacks earlier,
            # since-killed test runs left behind and labels this one with our PID,
            # so a stranded copy of it is removed by the next run instead of by a
            # `docker rm -f` sweep that could hit a live sibling.
            setup.down()
            setup.pull()
            setup.inspect()

            mikro_port = setup.spec.find_service("mikro").get_port_for_internal(80).published
            rustfs_port = setup.spec.find_service("rustfs").get_port_for_internal(9000).published

            setup.up()
            setup.run("initc", command="python init.py")
            setup.check_health()

            yield MikroStack(
                deployment=setup,
                http_url=f"http://localhost:{mikro_port}/graphql",
                ws_url=f"ws://localhost:{mikro_port}/graphql",
                datalayer_url=f"http://localhost:{rustfs_port}",
                mikro_watcher=watcher,
                rustfs_watcher=rustfs_watcher,
            )

