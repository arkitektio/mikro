"""The network path, from a built collection to the store id the mutation actually sends.

The graph twin of ``test_meshes.py``. Everything below the wire belongs to `konnektion` and is
tested there; what is mikro's, and so what is tested here, is the seam: the scalar the mutation
field takes, and the upload -- a grant, a whole tree written under its prefix, and a second call
saying the manifest landed.

One test here has no mesh counterpart and is the reason this file is not a copy: **the two
formats must not be interchangeable at the type level**. A konnektion blob is a segment list and
a fabriks blob is a triangle list, and reading either as the other raises nothing at any layer,
so the only place that mistake can be caught cheaply is the scalar.

No network. The S3 store is an obstore ``MemoryStore``.
"""

from types import SimpleNamespace
from typing import Any

import konnektion
import numpy as np
import pytest
from obstore.store import MemoryStore

from mikro_next.io.errors import UploadError
from mikro_next.io.upload import store_konnektion_collection
from mikro_next.scalars import KonnektionLike

#: Anisotropic, because a cubic cell makes a transposed writer look correct.
CELL_SIZE = (64, 64, 32)

#: A key shaped like the one a grant hands back: server-minted, opaque, and nested.
GRANT_KEY = "f3068f8f055245278c31994582675357"


@pytest.fixture(scope="module")
def collection() -> konnektion.NetworkCollection:
    """Two small arbors, far enough apart to occupy different cells."""

    def arbor(origin: tuple[float, float, float]) -> tuple[np.ndarray, np.ndarray]:
        nodes = [np.array(origin, dtype=float)]
        edges = []
        for step in range(1, 12):
            nodes.append(np.array(origin, dtype=float) + np.array([step * 5.0, step * 2.0, step]))
            edges.append([step - 1, step])
        # one branch, so the thing is a tree rather than a chain
        nodes.append(np.array(origin, dtype=float) + np.array([25.0, -18.0, 6.0]))
        edges.append([5, len(nodes) - 1])
        return np.asarray(nodes), np.asarray(edges)

    return konnektion.build_collection(
        {7: arbor((70.0, 60.0, 25.0)), 3: arbor((150.0, 30.0, 15.0))},
        cell_size=CELL_SIZE,
    )


def grant() -> SimpleNamespace:
    """A konnektion upload grant, with the fields `create_s3_store` and the writer read."""
    return SimpleNamespace(
        access_key="access",
        secret_key="secret",
        session_token="token",
        bucket="a-bucket",
        key=GRANT_KEY,
        path=f"s3://a-bucket/{GRANT_KEY}",
        store="42",
        expires_in=3600,
        max_bytes=0,
    )


def written_paths(store: MemoryStore) -> list[str]:
    """Every object key in a memory store. obstore lists in batches, not one by one."""
    return sorted(entry["path"] for batch in store.list() for entry in batch)


# ---------------------------------------------------------------------------
# The scalar the mutation field takes
# ---------------------------------------------------------------------------


def test_a_built_collection_is_what_the_scalar_accepts(
    collection: konnektion.NetworkCollection,
) -> None:
    """The whole collection goes on the wire, and the upload link needs a key to track it by."""
    coerced = KonnektionLike.validate(collection)

    assert coerced.value is collection
    assert coerced.key, "the middleware matches the grant to the value by this key"


def test_an_already_coerced_collection_passes_through_unchanged(
    collection: konnektion.NetworkCollection,
) -> None:
    """Validation runs more than once on the way to the wire, and must be idempotent."""
    once = KonnektionLike.validate(collection)
    assert KonnektionLike.validate(once) is once


def test_a_mesh_collection_is_refused_and_the_message_says_which_format_it_is() -> None:
    """The mistake this scalar exists to make impossible rather than merely unlikely.

    A `fabriks.MeshCollection` is the other thing in this codebase that is "a built collection".
    Nothing about the bytes would distinguish them downstream -- a triangle list read as a
    segment list divides evenly, indexes in range, and draws a plausible, wrong graph -- so the
    refusal has to happen here, at the type, and name the format it actually got.
    """
    fabriks = pytest.importorskip("fabriks")
    trimesh = pytest.importorskip("trimesh")

    from mikro_next.meshes import build_mesh_collection

    box = trimesh.creation.box(extents=[10.0, 10.0, 10.0]).apply_translation([30.0, 30.0, 30.0])
    mesh = build_mesh_collection({1: box})

    with pytest.raises(ValueError, match="MeshCollection"):
        KonnektionLike.validate(mesh)

    assert isinstance(mesh, fabriks.MeshCollection)


def test_something_that_is_not_a_collection_at_all_is_refused() -> None:
    """And the message says what to build, because that is the next thing a caller needs."""
    with pytest.raises(ValueError, match="konnektion.build_collection"):
        KonnektionLike.validate({"nodes": [], "edges": []})


# ---------------------------------------------------------------------------
# The upload: a grant, a tree, and the prefix it has to land under
# ---------------------------------------------------------------------------


def test_the_whole_tree_lands_under_the_granted_prefix(
    collection: konnektion.NetworkCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every object inside the grant's key, manifest included, and readable back.

    A grant covers one prefix and the server looks for ``konnektion.json`` at the root of
    exactly that one, so a write that escapes it, or doubles a separator on the way in,
    produces a tree nothing can find -- and no exception.
    """
    store = MemoryStore()
    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *_, **__: store)

    credentials = grant()
    returned = store_konnektion_collection(
        KonnektionLike.validate(collection),
        credentials,
        SimpleNamespace(endpoint_url="http://s3.test"),
    )

    assert returned == credentials.store, "the store id replaces the collection in the variables"

    paths = written_paths(store)
    assert paths, "nothing was written"
    assert all(path.startswith(f"{GRANT_KEY}/") for path in paths), paths
    assert not any("//" in path for path in paths), paths
    assert f"{GRANT_KEY}/konnektion.json" in paths, "the manifest is the completion protocol"

    reopened = konnektion.open_collection(store, GRANT_KEY)
    assert reopened.grid.cell_size == tuple(CELL_SIZE)
    assert reopened.manifest.counts["objects"] == 2
    assert konnektion.verify(reopened, tier="topology").ok


def test_the_manifest_is_written_last(
    collection: konnektion.NetworkCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interrupted upload has to look like one, and that is the manifest's absence."""
    store = MemoryStore()
    order: list[str] = []

    class Recording:
        """A store that remembers the order it was written in."""

        def put(self, path: str, data: Any) -> Any:  # noqa: ANN401
            order.append(path)
            return store.put(path, data)

        def get(self, path: str) -> Any:  # noqa: ANN401
            return store.get(path)

        def list(self, prefix: str | None = None) -> Any:  # noqa: ANN401
            return store.list(prefix)

    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *_, **__: Recording())

    store_konnektion_collection(
        KonnektionLike.validate(collection), grant(), SimpleNamespace(endpoint_url="http://s3.test")
    )

    assert order[-1].endswith("konnektion.json"), order


def test_a_failed_write_is_reported_as_an_upload_error(
    collection: konnektion.NetworkCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Named with the bucket and key, because a 404 from a proxy says nothing about which."""

    class Refusing:
        """A store that will not take anything."""

        def put(self, path: str, data: Any) -> Any:  # noqa: ANN401
            raise OSError("nope")

        def get(self, path: str) -> Any:  # noqa: ANN401
            raise OSError("nope")

        def list(self, prefix: str | None = None) -> Any:  # noqa: ANN401
            raise OSError("nope")

    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *_, **__: Refusing())

    with pytest.raises(UploadError, match=GRANT_KEY):
        store_konnektion_collection(
            KonnektionLike.validate(collection),
            grant(),
            SimpleNamespace(endpoint_url="http://s3.test"),
        )


def test_the_part_codec_is_one_the_viewer_can_decode() -> None:
    """A gzip default would upload, verify, and draw nothing, with no error anywhere."""
    from mikro_next.networks import refuse_an_unreadable_part_codec

    assert refuse_an_unreadable_part_codec().lower() in {"zstd", "snappy", "none", "uncompressed"}
