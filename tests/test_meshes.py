"""The mesh path, from a built collection to the store id the mutation actually sends.

Everything below the wire belongs to `fabriks` and is tested there. What is mikro's, and so
what is tested here, is the seam: the scalar the mutation field takes, the axis convention
`fabriks` deliberately does not own, and the upload -- a grant, a whole tree written under its
prefix, and a second call saying the manifest landed.

No network. The S3 store is an obstore ``MemoryStore`` and the rath client is a stub that
records what it was asked, which is enough because the failures this path actually had were
never about S3: they were a value that reached the transport uncoerced, and a tree written
somewhere the server would not look for it.
"""

from types import SimpleNamespace
from typing import Any

import fabriks
import pytest
import trimesh
from obstore.store import MemoryStore

from mikro_next.api.schema import AxisInput, AxisType, CreateMeshCollectionInput
from mikro_next.datalayer import DataLayer
from mikro_next.io.errors import UploadError
from mikro_next.io.upload import store_fabriks_collection
from mikro_next.meshes import axis_order_to_xyz, build_mesh_collection
from mikro_next.middleware.upload import UploadMiddleware
from mikro_next.scalars import FabriksLike

#: Small and cheap: the octree only has to exist, and building is the slow part of every test
#: here. Anisotropic anyway, because a cubic cell makes a transposed writer look correct.
CELL_SIZE = (64, 64, 32)
LEVELS = 2

#: A key shaped like the one a grant hands back: server-minted, opaque, and nested.
GRANT_KEY = "f3068f8f055245278c31994582675357"


@pytest.fixture(scope="module")
def collection() -> fabriks.MeshCollection:
    """Two boxes that disagree under a permutation of the axes, cut into a small octree."""
    return build_mesh_collection(
        {
            7: trimesh.creation.box(extents=[90.0, 50.0, 30.0]).apply_translation([70.0, 60.0, 25.0]),
            3: trimesh.creation.box(extents=[20.0, 12.0, 8.0]).apply_translation([30.0, 25.0, 15.0]),
        },
        cell_size=CELL_SIZE,
        levels=LEVELS,
    )


def grant() -> SimpleNamespace:
    """A fabriks upload grant, with the fields `create_s3_store` and the writer read."""
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


def test_a_built_collection_is_what_the_scalar_accepts(collection: fabriks.MeshCollection) -> None:
    """The whole collection goes on the wire, and the upload link needs a key to track it by."""
    coerced = FabriksLike.validate(collection)

    assert isinstance(coerced, FabriksLike)
    assert coerced.value is collection
    assert coerced.key, "the scalar needs an id of its own before a grant exists"


def test_an_already_coerced_collection_passes_through_unchanged(
    collection: fabriks.MeshCollection,
) -> None:
    """Validation runs more than once on a nested input, and must not re-wrap or re-key."""
    coerced = FabriksLike.validate(collection)

    assert FabriksLike.validate(coerced) is coerced


def test_a_bare_catalog_table_is_refused_and_the_message_says_what_to_build(
    collection: fabriks.MeshCollection,
) -> None:
    """The mistake the previous wire format invited, and the one a caller still has in hand.

    A collection used to be uploaded as three Parquet frames, so passing the cell catalog here
    is exactly what a caller with the old shape in mind would try -- and a table would otherwise
    travel a long way before anything objected.
    """
    with pytest.raises(ValueError, match="MeshCollection") as raised:
        FabriksLike.validate(collection.cell_catalog)

    assert "build_mesh_collection" in str(raised.value), "the error should name the way out"


def test_the_input_type_coerces_a_collection_on_the_way_in(
    collection: fabriks.MeshCollection,
) -> None:
    """The seam that actually matters: the generated input model has to run the scalar.

    Nothing else checks that the schema's ``FabriksLike`` is wired to this class -- and when it
    was not, the collection reached the transport as itself and failed there, at JSON encoding,
    a long way from the cause.
    """
    parsed = CreateMeshCollectionInput(
        version="v1",
        store=collection,
        axes=[AxisInput(name=name, type=AxisType.SPACE) for name in ("x", "y", "z")],
    )

    assert isinstance(parsed.store, FabriksLike)
    assert parsed.store.value is collection


# ---------------------------------------------------------------------------
# What mikro decides, rather than fabriks
# ---------------------------------------------------------------------------


def test_the_default_codec_needs_no_decoder_on_either_side(
    collection: fabriks.MeshCollection,
) -> None:
    """``NONE`` is a deliberate default, not an accident of fabriks's own.

    A blob is then the raw layout a consumer uploads to the GPU as-is. ``MESHOPT`` is smaller
    and needs `meshoptimizer` here *and* a decoder in whatever draws the result, which is the
    renderer's trade to make -- so changing this default silently changes what every collection
    written from here demands of its reader.
    """
    assert collection.encoding.codec == "NONE"
    assert collection.encoding.compression == "NONE"


def test_the_ids_it_was_given_are_the_ids_it_writes(collection: fabriks.MeshCollection) -> None:
    """Object ids are a label volume's instance ids, so they are carried, never renumbered."""
    assert set(collection.object_catalog.column("object_id").to_pylist()) == {3, 7}


def test_the_axis_reversal_is_the_one_place_the_transposition_happens() -> None:
    """``(z, y, x)`` in, ``(x, y, z)`` out -- and a rank that is not 3 is refused.

    The server validates rank only, so a permutation done by hand anywhere else is a mistake
    with no downstream symptom: the collection registers, the layer reports PLACED, and every
    object draws in the wrong place.
    """
    assert axis_order_to_xyz((64, 256, 512)) == (512.0, 256.0, 64.0)

    with pytest.raises(ValueError, match="three-dimensional"):
        axis_order_to_xyz((256, 512))


# ---------------------------------------------------------------------------
# The upload: a grant, a tree, and the prefix it has to land under
# ---------------------------------------------------------------------------


def test_the_whole_tree_lands_under_the_granted_prefix(
    collection: fabriks.MeshCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every object inside the grant's key, manifest included, and readable back as a collection.

    The prefix is the check worth having. A grant covers one prefix and the server looks for
    ``fabriks.json`` at the root of exactly that one, so a write that escapes it, or that
    doubles a separator on the way in, produces a tree nothing can find -- and no exception.
    """
    store = MemoryStore()
    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *_, **__: store)

    credentials = grant()
    returned = store_fabriks_collection(
        FabriksLike.validate(collection), credentials, SimpleNamespace(endpoint_url="http://s3.test")
    )

    assert returned == credentials.store, "the store id is what replaces the collection in the variables"

    paths = written_paths(store)
    assert paths, "nothing was written"
    assert all(path.startswith(f"{GRANT_KEY}/") for path in paths), paths
    assert not any("//" in path for path in paths), paths
    assert f"{GRANT_KEY}/fabriks.json" in paths, "the manifest is the completion protocol"

    # The server reads the grid and the encoding off the artifact rather than being told, so
    # what matters is that the artifact reads back as the collection that went in.
    reopened = fabriks.open_collection(store, GRANT_KEY)
    assert reopened.grid.cell_size == tuple(CELL_SIZE)
    assert reopened.manifest.counts["objects"] == 2


def test_the_manifest_is_written_last(
    collection: fabriks.MeshCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interrupted upload has to look like one, and that is the manifest's absence.

    ``finishFabriksUpload`` refuses a prefix without a manifest, which only distinguishes a
    half-written tree from a whole one if the manifest is genuinely the last object to land.
    """
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

    store_fabriks_collection(
        FabriksLike.validate(collection), grant(), SimpleNamespace(endpoint_url="http://s3.test")
    )

    assert order[-1].endswith("fabriks.json"), order


def test_a_failed_write_is_reported_as_an_upload_error(
    collection: fabriks.MeshCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Named with the bucket and key, because a 404 from a proxy says nothing about which."""

    class Refusing:
        """A store that will not take anything."""

        def put(self, path: str, data: Any) -> Any:  # noqa: ANN401
            raise OSError("nope")

        def get(self, path: str) -> Any:  # noqa: ANN401
            raise OSError("nope")

        def list(self, prefix: str | None = None) -> Any:  # noqa: ANN401
            return iter(())

    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *_, **__: Refusing())

    with pytest.raises(UploadError, match=GRANT_KEY):
        store_fabriks_collection(
            FabriksLike.validate(collection), grant(), SimpleNamespace(endpoint_url="http://s3.test")
        )


# ---------------------------------------------------------------------------
# The middleware: the only thing that turns a collection into a store id
# ---------------------------------------------------------------------------


class StubRath:
    """A rath that answers the two fabriks mutations and records what it was asked."""

    def __init__(self) -> None:
        """Start with nothing asked."""
        self.documents: list[str] = []
        self.variables: list[dict[str, Any]] = []

    def query(self, document: str, variables: dict[str, Any], **_: Any) -> SimpleNamespace:  # noqa: ANN401
        """Answer by which mutation was asked for, the way the server would."""
        self.documents.append(document)
        self.variables.append(variables)

        if "requestFabriksUpload" in document:
            credentials = grant()
            return SimpleNamespace(
                data={
                    "requestFabriksUpload": {
                        "accessKey": credentials.access_key,
                        "secretKey": credentials.secret_key,
                        "sessionToken": credentials.session_token,
                        "path": credentials.path,
                        "key": credentials.key,
                        "bucket": credentials.bucket,
                        "expiresIn": credentials.expires_in,
                        "maxBytes": credentials.max_bytes,
                        "store": credentials.store,
                    }
                }
            )
        if "finishFabriksUpload" in document:
            return SimpleNamespace(
                data={
                    "finishFabriksUpload": {
                        "id": "1",
                        "key": GRANT_KEY,
                        "bucket": "a-bucket",
                        "path": f"s3://a-bucket/{GRANT_KEY}",
                        "specVersion": fabriks.SPEC_VERSION,
                        "grid": {"cellSize": list(CELL_SIZE), "levels": LEVELS, "sortKey": "MORTON"},
                        "encoding": {},
                        "axes": ["x", "y", "z"],
                        "counts": {"objects": 2},
                        "files": {},
                    }
                }
            )
        raise AssertionError(f"the middleware asked for something unexpected: {document[:80]}")


def test_the_middleware_replaces_a_collection_with_the_store_it_uploaded_to(
    collection: fabriks.MeshCollection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The dispatch itself, which is the piece that has no other test.

    A type the middleware does not know is not an error anywhere -- it travels on and fails at
    JSON encoding, or worse, is dropped. So this asserts the substitution *and* that both calls
    of the two-step protocol were made, since a tree written but never finished is a prefix the
    server will not register.
    """
    monkeypatch.setattr("mikro_next.io.obstore.create_s3_store", lambda *_, **__: MemoryStore())

    middleware = UploadMiddleware(datalayer=DataLayer(endpoint_url="http://s3.test"))
    middleware._cached_datalayer_url = "http://s3.test"  # else it resolves through koil
    rath = StubRath()

    variables = {"input": {"version": "v1", "store": FabriksLike.validate(collection)}}
    processed = middleware.process_variables(variables, None, rath)  # type: ignore[arg-type]

    assert processed["input"]["store"] == "42", "the collection should be replaced by its store id"
    assert processed["input"]["version"] == "v1", "nothing else should be touched"

    asked = [
        "request" if "requestFabriksUpload" in document else "finish" for document in rath.documents
    ]
    assert asked == ["request", "finish"], asked
    assert rath.variables[-1]["input"] == {"storeId": "42", "valid": True}


def test_the_parquet_parts_are_written_with_a_codec_the_viewer_can_decode() -> None:
    """A mesh collection's *file* compression is fabriks's, not this library's -- and three
    of the six codecs fabriks can select are ones the viewer cannot decode.

    It reads meshes with hyparquet, whose built-ins are UNCOMPRESSED and SNAPPY, plus the
    ZSTD the frontend registers by hand out of `fzstd`; `hyparquet-compressors` is not a
    dependency there. So gzip, brotli or lz4 would upload cleanly, verify cleanly and draw
    nothing. Today the default is zstd; this is what notices if that ever changes.

    Distinct from `build_mesh_collection`'s `compression`, which is the per-blob codec inside
    a row and is the manifest's business.
    """
    from mikro_next.compression import MESH_CODECS
    from mikro_next.meshes import refuse_an_unreadable_part_codec

    codec = refuse_an_unreadable_part_codec()
    assert codec.upper().replace("NONE", "UNCOMPRESSED") in MESH_CODECS


def test_an_unreadable_part_codec_is_refused_with_the_reason(monkeypatch) -> None:
    """The failure it prevents has no error attached to it anywhere else."""
    import inspect

    from fabriks import frames

    from mikro_next.compression import UnreadableCodecError
    from mikro_next.meshes import refuse_an_unreadable_part_codec

    def gzip_default(table, *, compression="gzip"):  # noqa: ANN001
        raise AssertionError("not called")

    monkeypatch.setattr(frames, "table_to_parquet", gzip_default)
    assert inspect.signature(frames.table_to_parquet).parameters["compression"].default == "gzip"

    with pytest.raises(UnreadableCodecError) as raised:
        refuse_an_unreadable_part_codec()
    assert "hyparquet" in str(raised.value)
    assert "draw nothing" in str(raised.value)
