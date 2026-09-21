"""Which mikro client answers: a reference if there is one, else mikro's own current client.

No server: the rath clients are fakes returning canned data, and a "context" is
a client passed explicitly. mikro knows nothing about
apps beyond that. Passed or current, it is asked the same question.
"""

from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict


from mikro.mikro import TASK_HEADER
from mikro.datalayer import DataLayer
from mikro.errors import NoMikroFound
from mikro.mikro import Mikro
from mikro.traits import HasDownloadAccessor, HasZarrStoreAccessor, MikroFetchable


class FakeRath:
    """Answers every query with the same canned store, and remembers being asked."""

    middlewares: list[Any] = []

    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def _answer(self) -> Any:
        self.calls += 1
        return SimpleNamespace(data={"store": {"id": "store-1", "nested": {"id": "n-1"}}})

    def query(self, document: str, variables: dict[str, Any], headers: Any = None) -> Any:
        return self._answer()

    async def aquery(
        self, document: str, variables: dict[str, Any], headers: Any = None
    ) -> Any:
        return self._answer()


class FakeApp:
    """What an app is to mikro: it has a mikro client."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.rath = FakeRath(name)
        self.datalayer = DataLayer(endpoint_url=f"http://{name}.invalid")
        # A real client over fakes: `client_of` only follows an origin that is one.
        self.mikro = Mikro.model_construct(
            rath=self.rath, datalayer=self.datalayer
        )

    def get(self, key: type) -> Any:
        return self.mikro if key is Mikro else None




class Nested(HasZarrStoreAccessor):
    """An inline selection: it carries an accessor trait but is not MikroFetchable."""

    model_config = ConfigDict(frozen=True)
    id: str


class Store(HasZarrStoreAccessor, MikroFetchable, BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    nested: Nested


class GetStore(BaseModel):
    """Shaped like a generated operation."""

    store: Store

    class Arguments(BaseModel):
        id: str

    class Meta:
        document = "query GetStore($id: ID!) { store(id: $id) { id nested { id } } }"


@pytest.fixture()
def apps() -> tuple[FakeApp, FakeApp]:
    return FakeApp("a"), FakeApp("b")


# --------------------------------------------------------------------------- #
# Calls, and what they return
# --------------------------------------------------------------------------- #


def test_execute_goes_through_the_client_it_is_handed(apps: tuple[FakeApp, FakeApp]) -> None:
    """What is current plays no part: the client is an argument."""
    a, b = apps

    result = a.mikro.execute(GetStore, {"id": "store-1"})

    assert (a.rath.calls, b.rath.calls) == (1, 0)
    assert result.store.bound_client() is a.mikro
    assert result.store.bound_rath() is a.rath


@pytest.mark.asyncio
async def test_aexecute_remembers_the_client_it_was_called_on(
    apps: tuple[FakeApp, FakeApp],
) -> None:
    """The client is remembered, and with it its rath and datalayer."""
    from rath.origin import get_origin

    a, b = apps

    result = await a.mikro.aexecute(GetStore, {"id": "store-1"})

    assert (a.rath.calls, b.rath.calls) == (1, 0)
    origin = get_origin(result.store.nested)
    assert origin is not None and origin.client is a.mikro
    assert origin.rath is a.rath and origin.clients["datalayer"] is a.datalayer


def test_nested_objects_without_mikrofetchable_are_bound_too(
    apps: tuple[FakeApp, FakeApp],
) -> None:
    """Several generated classes carry an accessor trait but not MikroFetchable."""
    a, _ = apps

    result = a.mikro.execute(GetStore, {"id": "store-1"})

    assert not isinstance(result.store.nested, MikroFetchable)
    assert result.store.nested.bound_client() is a.mikro


# --------------------------------------------------------------------------- #
# What an object fetches later
# --------------------------------------------------------------------------- #


@pytest.fixture()
def opened(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Record which client the zarr accessor goes through, without any I/O."""
    seen: list[Any] = []

    def fake_unkoil(function: Any, mikro: Any, store_id: str) -> Any:
        seen.append(mikro)
        return SimpleNamespace(), "http://endpoint.invalid"

    monkeypatch.setattr("mikro.io.download.unkoil", fake_unkoil)
    monkeypatch.setattr(
        "mikro.io.download.create_zarr_store_path", lambda *args: "a-store-path"
    )
    return seen


def test_object_keeps_to_its_own_client_while_another_app_is_current(
    apps: tuple[FakeApp, FakeApp], opened: list[Any]
) -> None:
    """The case that leaked: an object from app A touched while app B is current."""
    a, b = apps
    store = a.mikro.execute(GetStore, {"id": "store-1"}).store

    assert store.zarr_store == "a-store-path"
    assert store.nested.zarr_store == "a-store-path"

    assert opened == [a.mikro, a.mikro]


def test_an_object_fetched_through_no_client_says_so(opened: list[Any]) -> None:
    """Built by hand (or unpickled): there is no client to fall back to."""
    store = Store(id="store-1", nested=Nested(id="n-1"))

    with pytest.raises(NoMikroFound, match="not fetched through a Mikro client"):
        store.zarr_store
    assert opened == []


def test_fetching_by_id_binds_what_it_fetched_to_the_client(
    apps: tuple[FakeApp, FakeApp],
) -> None:
    """``Type.expand(id, client)`` is rath's; mikro binds its datalayer too."""
    from rath.origin import ORIGIN_KEY

    a, _ = apps
    origin = Store.fetch_origin(a.mikro)[ORIGIN_KEY]

    assert origin.client is a.mikro and origin.rath is a.rath
    assert origin.clients == {"datalayer": a.datalayer}


def test_download_accessor_goes_through_its_objects_client(
    apps: tuple[FakeApp, FakeApp], monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b = apps
    seen: list[Any] = []

    class Big(HasDownloadAccessor):
        id: str
        key: str

    def fake_download(mikro: Any, store_id: str, file_name: str) -> str:
        seen.append(mikro)
        return file_name

    monkeypatch.setattr("mikro.io.download.download_file", fake_download)
    big = Big.model_validate(
        {"id": "1", "key": "file.bin"}, context=a.mikro._origin()
    )

    assert big.download() == "file.bin"

    assert seen == [a.mikro]


# --------------------------------------------------------------------------- #
# The service answers for itself
# --------------------------------------------------------------------------- #


def real_service(name: str) -> Mikro:
    from rath.links.testing.direct_succeeding_link import DirectSucceedingLink

    from mikro.rath import MikroRath

    return Mikro(
        rath=MikroRath(link=DirectSucceedingLink()),
        datalayer=DataLayer(endpoint_url=name),
    )


def test_the_client_has_exactly_its_fields() -> None:
    real_service("self")

    assert set(Mikro.model_fields) == {
        "datalayer",
        "federated_expansion",
        "rath",
    }








async def _expand_store_through(app: FakeApp, current: FakeApp, fetch: Any) -> Any:
    """Expand one ``Store`` argument the way an actor does.

    The registry is bound to ``app``'s client, as entering an app binds its own.
    ``current`` stands for another app that happens to be entered in this process;
    nothing is made current for the expansion, and the object is then touched with
    only ``current`` current, so what it reaches can only come from what it
    remembered.
    """
    pytest.importorskip("rekuest.app")
    from typing import Annotated

    from fakts import Alias, Require

    from rekuest.app import AppRegistry
    from rekuest.definition.define import prepare_definition
    from rekuest.structures.serialization.actor import expand_inputs

    class StoreClient:
        """The mikro client, as far as expanding the test store goes."""

        async def aget_store(self, id: str) -> Store:
            return await fetch(app.mikro, id)

    def mikro(alias: Annotated[Alias, Require("live.test.mikro")]) -> StoreClient:
        """A parameter is only a client once a registered service returns its type."""
        return StoreClient()

    async def expand_store(id: str, mikro: StoreClient) -> Store:
        """The expander names the client it needs; binding supplies it."""
        return await mikro.aget_store(id)

    app_registry = AppRegistry()
    app_registry.service()(mikro)
    app_registry.structure("@mikro/teststore")(expand_store)
    registry = app_registry.structure_registry.bound({"mikro": StoreClient()})

    def uses_store(store: Store) -> str:
        """Takes a store."""
        return store.id

    definition = prepare_definition(uses_store, structure_registry=registry)
    wire = {"store": {"__identifier": "@mikro/teststore", "object": "store-1"}}

    expanded = await expand_inputs(
        definition, wire, structure_registry=registry, shelver=None  # type: ignore[arg-type]
    )
    expanded["store"].zarr_store  # touched while the OTHER app is current
    return expanded["store"]


@pytest.mark.asyncio
async def test_rekuest_expands_through_the_client_its_registry_was_bound_to(
    apps: tuple[FakeApp, FakeApp], opened: list[dict[str, Any]]
) -> None:
    """The whole chain, as an actor drives it.

    The expander is handed the client its registry was bound to; B being current
    plays no part. The object then remembers that client, which is what keeps it
    on app A afterwards even though B is the only app current by then.
    """
    from rath.origin import get_origin

    a, b = apps

    async def aget_store(client: Any, id: str) -> Store:
        return (await client.aexecute(GetStore, {"id": id})).store

    store = await _expand_store_through(a, current=b, fetch=aget_store)

    assert (a.rath.calls, b.rath.calls) == (1, 0)
    assert opened == [a.mikro]
    origin = get_origin(store)
    assert origin is not None and origin.rath is a.rath


# --------------------------------------------------------------------------- #
# Attributing a shared client's calls to the running task
# --------------------------------------------------------------------------- #


class HeaderRath(FakeRath):
    """Remembers the headers each request carried."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.headers: list[Any] = []

    async def aquery(
        self, document: str, variables: dict[str, Any], headers: Any = None
    ) -> Any:
        self.headers.append(headers)
        return self._answer()




# --------------------------------------------------------------------------- #
# The task a call is for: ambient, or named at the call
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_the_ambient_task_is_stamped_without_a_view() -> None:
    """One shared client attributes each call to whatever task is running."""
    from rath.task import task_scope

    rath = HeaderRath("shared")
    client = Mikro.model_construct(rath=rath, datalayer=DataLayer(endpoint_url="http://x.invalid"))

    await client.aexecute(GetStore, {"id": "store-1"})
    with task_scope(SimpleNamespace(token="token-1")):
        await client.aexecute(GetStore, {"id": "store-1"})
    await client.aexecute(GetStore, {"id": "store-1"})

    assert rath.headers == [None, {TASK_HEADER: "token-1"}, None]
    assert "task_token" not in Mikro.model_fields, "no per-task copy exists"


@pytest.mark.asyncio
async def test_a_task_named_at_the_call_beats_the_ambient_one() -> None:
    from rath.task import task_scope

    rath = HeaderRath("shared")
    client = Mikro.model_construct(rath=rath, datalayer=DataLayer(endpoint_url="http://x.invalid"))

    with task_scope(SimpleNamespace(token="ambient")):
        await client.aexecute(
            GetStore, {"id": "store-1"}, task=SimpleNamespace(token="explicit")
        )

    assert rath.headers == [{TASK_HEADER: "explicit"}]


@pytest.mark.asyncio
async def test_a_task_without_a_token_stamps_no_header_at_all() -> None:
    """Not a header with a `None` value -- no header."""
    from rath.task import task_scope

    rath = HeaderRath("shared")
    client = Mikro.model_construct(rath=rath, datalayer=DataLayer(endpoint_url="http://x.invalid"))

    with task_scope(SimpleNamespace(token=None)):
        await client.aexecute(GetStore, {"id": "store-1"})

    assert rath.headers == [None]
