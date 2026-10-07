"""The datalayer and the service links reach a mesh-only address through the sidecar proxy.

A store behind a private mesh is only reachable through the sidecar's local HTTP
forward proxy, which fakts stamps on the resolved alias as ``alias.proxy``. These
tests pin the two ways that can go wrong:

- the proxy must be *merged* into the store's client options -- replacing them drops
  ``allow_http`` and breaks every plain ``http://`` store, proxied or not;
- with the proxy set, requests must actually go to it, in absolute form, naming the
  mesh host rather than resolving it locally.

No deployment: a local socket plays the store (or the proxy) and answers 404.
"""

import socket
import threading
from types import SimpleNamespace
from typing import Any

import obstore
import pytest
from fakts import Alias
from rath.links.aiohttp import AIOHttpLink
from rath.links.graphql_ws import GraphQLWSLink

import mikro.arkitekt.service as mikro_arkitekt
from mikro.datalayer import DataLayer
from mikro.io.obstore import acreate_s3_store, create_s3_store

GRANT = SimpleNamespace(
    access_key="access",
    secret_key="secret",
    session_token="",
    bucket="bucket",
    key="some/object",
)

_PROXY_ENV = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")


@pytest.fixture(autouse=True)
def _no_ambient_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a proxy configured in the environment from deciding where requests go."""
    for name in _PROXY_ENV:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)


class Answer404:
    """A one-thread HTTP endpoint that records each request line and answers 404."""

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.request_lines: list[str] = []
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.sock.getsockname()[1]}"

    def _serve(self) -> None:
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            with conn:
                data = b""
                while b"\r\n\r\n" not in data:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    data += chunk
                if data:
                    self.request_lines.append(data.split(b"\r\n", 1)[0].decode())
                conn.sendall(
                    b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                )

    def close(self) -> None:
        self.sock.close()


@pytest.fixture()
def endpoint() -> Any:
    server = Answer404()
    yield server
    server.close()


def test_a_plain_http_store_without_proxy_reaches_the_endpoint(endpoint: Answer404) -> None:
    """allow_http survives: the request is sent (and answered 404), not refused locally."""
    store = create_s3_store(endpoint.url, GRANT)

    with pytest.raises(FileNotFoundError):
        obstore.get(store, GRANT.key)

    assert endpoint.request_lines, "the store never reached the endpoint"
    assert endpoint.request_lines[0].startswith("GET /bucket/some/object ")


def test_the_proxy_is_merged_into_the_client_options() -> None:
    store = create_s3_store(
        "http://mesh-host:9000",
        GRANT,
        client_options={"timeout": "5s"},
        proxy="http://127.0.0.1:41234",
    )

    options = store.client_options
    assert options["proxy_url"] == "http://127.0.0.1:41234"
    assert str(options["allow_http"]).lower() == "true"
    assert options["timeout"] == "5s"


def test_no_proxy_leaves_the_client_options_as_they_were() -> None:
    store = create_s3_store("http://mesh-host:9000", GRANT)

    assert "proxy_url" not in (store.client_options or {})


@pytest.mark.asyncio
async def test_a_proxied_datalayer_sends_absolute_form_requests_to_the_proxy(
    endpoint: Answer404,
) -> None:
    """The alias's proxy travels from the datalayer to the store, and is used."""
    alias = Alias(id="s3", host="mesh-host.invalid", port=9000, proxy=endpoint.url)
    datalayer = DataLayer.from_alias(alias)
    assert datalayer.proxy == endpoint.url

    store = await acreate_s3_store(GRANT, datalayer)
    with pytest.raises(FileNotFoundError):
        await obstore.get_async(store, GRANT.key)

    assert endpoint.request_lines, "nothing went through the proxy"
    assert endpoint.request_lines[0].startswith(
        "GET http://mesh-host.invalid:9000/bucket/some/object "
    )


# --- the service builder ------------------------------------------------------------


class RecordingHttpLink(AIOHttpLink):
    """The real link, with the ``proxy`` field a newer rath adds."""

    proxy: str | None = None


class RecordingWsLink(GraphQLWSLink):
    proxy: str | None = None


class Tokens:
    async def aget_token(self) -> str:
        return "token"

    async def arefresh_token(self, stale_token: str | None = None) -> str:
        return "token"


def _alias(proxy: str | None = None) -> Alias:
    return Alias(id="a", host="mesh-host", port=9000, proxy=proxy)


def _links(client: Any) -> tuple[Any, Any]:
    split = client.rath.link.links[-1]
    return split.left, split.right


def test_the_builder_puts_the_alias_proxy_on_both_links(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mikro_arkitekt, "AIOHttpLink", RecordingHttpLink)
    monkeypatch.setattr(mikro_arkitekt, "GraphQLWSLink", RecordingWsLink)
    proxy = "http://127.0.0.1:41234"

    client = mikro_arkitekt.mikro._function(
        mikro=_alias(proxy=proxy), s3=_alias(proxy=proxy), tokens=Tokens()
    )

    http, ws = _links(client)
    assert http.proxy == proxy
    assert ws.proxy == proxy
    assert client.datalayer.proxy == proxy


def test_the_builder_passes_no_proxy_when_the_alias_has_none() -> None:
    """A direct (not mesh) alias builds links and a datalayer without a proxy."""
    client = mikro_arkitekt.mikro._function(mikro=_alias(), s3=_alias(), tokens=Tokens())

    http, ws = _links(client)
    assert http.endpoint_url == "http://mesh-host:9000/graphql"
    assert http.proxy is None
    assert ws.proxy is None
    assert client.datalayer.proxy is None
