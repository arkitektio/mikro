"""Mesh collections for mikro, built by :mod:`fabriks`.

A mesh collection is an **octree of surfaces**: a manifest, a cell catalog (the spatial index,
one row per ``(level, cell)``), an object catalog (the identity index, one row per object) and
one Parquet part per octree level -- so a renderer fetches the detail the view needs instead of
the whole thing. fabriks is the format and the writer; this module is the thin layer that builds
one for mikro and states the one thing fabriks deliberately does not own.

**The byte format lives in `fabriks`, not here.** The octree, the quantization, the boundary
argument and the blob codecs are defined in :mod:`fabriks.codecs`, :mod:`fabriks.octree`,
:mod:`fabriks.geometry` and :mod:`fabriks.manifest`. A second copy of a byte format is a second
thing to drift, so there is none.

Usage::

    import trimesh
    from mikro_next.meshes import build_mesh_collection
    from mikro_next.api.schema import create_mesh_collection

    spheres = {1: trimesh.creation.icosphere(radius=4.0), 2: ...}
    collection = build_mesh_collection(spheres, levels=3)   # cell_size chosen from the objects

    create_mesh_collection(
        version="v1",
        store=collection,   # written to a granted prefix on the way out, manifest last
        # In the order the vertex components are stored, which is (x, y, z). A collection
        # extracted from a (z, y, x) image states the reversal in its `derived_from`
        # transform -- a MAP_AXIS naming each axis on both sides -- never by declaring the
        # image's axis order over vertices that are not in it.
        axes=["x", "y", "z"],
    )

**The collection goes on the wire, not its tables.** ``store`` is a ``FabriksLike``: the upload
link asks for a prefix grant, has fabriks write the tree into it, and calls
``finishFabriksUpload``, which reads the manifest and refuses a prefix without one -- the
manifest lands last, so its absence *is* what an interrupted write looks like. The registration
therefore declares no grid and no encoding: the server reads them off the artifact, where they
describe what was actually written rather than what a caller claimed.

Coordinates
-----------
Vertex components are ``(x, y, z)``, and so are ``cell_size`` and the ``bbox_*_{x,y,z}``
columns. A collection extracted from a ``(z, y, x)`` image therefore declares
``axes=["x", "y", "z"]`` -- **its own axis order, matching its vertices**, never the image's.

That is the one mistake here with no downstream symptom. ``axes`` is positional, so declaring
``[z, y, x]`` over ``(x, y, z)`` vertices asserts that component 0 is the image's ``z`` when it
holds ``x``; the server validates rank 3 only, a round trip is self-consistent under either
convention, and the layer still reports ``PLACED``. It simply draws everything transposed.

The reversal belongs in the derivation instead, where a machine can read it: derive from the
source with a **MAP_AXIS** naming each axis on both sides (``input_axes=["x","y","z"]``,
``output_axes=["x","y","z"]`` -- the names match, the positions do not). An ``IDENTITY`` is
only truthful when the two spaces really do list their axes in the same order.

Every conversion into this order goes through :func:`axis_order_to_xyz`. fabriks itself addresses
components by position and never asks what they mean, which is why naming them is mikro's job:
it is a statement about how the collection relates to the image it came from, and that is what
the coordinate graph is.

Units are **voxels of the collection's own coordinate system**, which is what lets the octree
align to the grid the meshes were extracted from.

Encoding defaults
-----------------
``codec`` defaults to **``NONE``**, which is fabriks's default too: a blob is then the raw
little-endian layout the format describes, which a consumer reads out of the Parquet column and
uploads to the GPU with nothing in between -- no decoder on the reading side, and no optional
dependency on the writing side.

``codec="MESHOPT"`` is one argument away: glTF's ``EXT_meshopt_compression``, roughly a third
smaller, and it needs ``meshoptimizer`` here *and* a decoder in whatever draws the result. That
is the trade, and it is the renderer's to make rather than this module's to assume.

``compression`` is ``NONE``. The Parquet file already compresses the column the blobs sit in,
with a whole column chunk of context rather than one cell's worth, so per-blob ZSTD buys very
little; and it is refused with ``MESHOPT`` outright, because ZSTD framing derives a blob's
length from the row's counts and a meshopt blob has no fixed size per element.

Coarse levels are made by fabriks's default **QUADRIC** backend (``fast-simplification``), which
pins every vertex on the cut boundary at exactly its input position -- that is what makes
``boundary: LOCKED`` provable rather than intended. Pass ``simplifier="GREEDY"`` where a
heavily cut object stops the quadric collapse short of its budget; fabriks warns when a level
misses ``decimation: QUARTER`` and names the cause the numbers support.

Checking one before registering it
----------------------------------
The declarations a renderer acts on are kept by the writer or not at all, and
:func:`fabriks.verify` is what checks them::

    import fabriks

    collection = build_mesh_collection(spheres)
    store = fabriks.MemoryStore()
    collection.write(store, "check")
    report = fabriks.verify(fabriks.open_collection(store, "check"), tier="geometry")
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from fabriks import (
    CODEC_MESHOPT,
    CODEC_NONE,
    COMPRESSION_NONE,
    COMPRESSION_ZSTD,
    Decimation,
    MeshCollection,
    build_collection,
    choose_cell_size,
    decimate_fixed,
    decode_indices,
    decode_positions,
    encode_indices,
    encode_positions,
    morton_decode,
    morton_encode,
    snap_boundary,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from fabriks import MeshSource, Simplifier


def require_trimesh() -> Any:  # noqa: ANN401
    """Import trimesh lazily, raising a helpful error if the extra is missing."""
    try:
        import trimesh  # type: ignore
    except ImportError as error:  # pragma: no cover - depends on the environment
        raise ImportError(
            "trimesh is required to build a mesh collection. Install it with "
            "`pip install mikro-next[mesh]`."
        ) from error
    return trimesh


def require_meshoptimizer() -> Any:  # noqa: ANN401
    """Import meshoptimizer lazily, raising a helpful error if the extra is missing."""
    try:
        import meshoptimizer  # type: ignore
    except ImportError as error:  # pragma: no cover - depends on the environment
        raise ImportError(
            "meshoptimizer is required for `codec='MESHOPT'`. Install it with "
            "`pip install mikro-next[meshopt]`, or leave `codec` at its default `NONE`, which "
            "writes the blobs raw and needs no decoder on either side."
        ) from error
    return meshoptimizer


def axis_order_to_xyz(values: Sequence[float]) -> tuple[float, float, float]:
    """Reverse a value stated in declared-axis order ``(z, y, x)`` into the format's ``(x, y, z)``.

    The single place the transposition happens. The server checks rank 3 and nothing else, so
    doing this by hand anywhere else is a mistake nothing downstream would report.
    """
    if len(values) != 3:
        raise ValueError(f"A mesh grid is three-dimensional, so this takes 3 values, got {values!r}.")
    return (float(values[2]), float(values[1]), float(values[0]))


def build_mesh_collection(
    objects: Mapping[int, MeshSource],
    *,
    cell_size: Sequence[int] | None = None,
    levels: int = 3,
    codec: str = CODEC_NONE,
    compression: str = COMPRESSION_NONE,
    simplifier: Simplifier | str | None = None,
    decimation: Decimation | None = None,
) -> MeshCollection:
    """Turn ``{object_id: mesh}`` into a :class:`fabriks.MeshCollection`, ready to register.

    ``objects`` is keyed by the id the object carries in whatever it was extracted from -- a
    label volume's instance id, say -- and those ids are written through unchanged. Each value
    is a ``trimesh.Trimesh``, a :class:`fabriks.Mesh`, or a ``(vertices, faces)`` pair of arrays.
    Vertices are in voxels, ordered ``(x, y, z)`` -- see the module docstring for why that order
    is the collection's own and not the source image's.

    ``cell_size`` is the level-0 cell in voxels, ``(x, y, z)``. **Left unset it is chosen from
    the objects** by :func:`fabriks.choose_cell_size` -- pass it when you know the source array's
    chunk shape, which is the value worth matching and the one no amount of looking at meshes
    can reveal. ``levels`` is how deep the octree goes.

    ``codec``, ``compression``, ``simplifier`` and ``decimation`` are fabriks's, passed through:
    the blob codec, the per-blob compression, which backend makes a coarse level and how much
    of it survives. The defaults are fabriks's own -- ``NONE`` / ``NONE`` / ``QUADRIC`` /
    ``QUARTER`` -- and whatever they are, the manifest declares what was actually done.

    Nothing is written here. The collection is built in memory and serialized on the way out,
    when it is passed as the ``store`` of ``create_mesh_collection``; :meth:`fabriks.MeshCollection.write`
    is the same bytes into a store of your own, which is how you inspect or verify one first.

    This function exists rather than :func:`fabriks.build_collection` being called directly
    because mikro's default is not fabriks's on one point -- and because the axis convention this
    module documents is the thing a caller most needs to have read.
    """
    return build_collection(
        objects,
        cell_size=cell_size,
        levels=levels,
        codec=codec,
        compression=compression,
        simplifier=simplifier,
        decimation=decimation,
    )


def refuse_an_unreadable_part_codec() -> str:
    """Refuse to write a collection whose Parquet parts the mesh viewer could not decode.

    A mesh collection's *file* compression is fabriks's, not this library's -- ``write_collection``
    passes nothing and ``fabriks.frames.table_to_parquet`` picks the codec. Today that is ZSTD,
    which is fine. What makes it worth checking rather than trusting is the shape of the failure
    if it ever changes: ``fabriks.frames.ParquetCompression`` is
    ``Literal["none", "snappy", "gzip", "brotli", "lz4", "zstd"]``, and three of those six are
    codecs the viewer cannot decode -- it reads meshes with **hyparquet**, whose built-ins are
    UNCOMPRESSED and SNAPPY, plus the ZSTD it registers by hand out of ``fzstd``
    (``components/scene/features/meshes/fabriks/parquetPart.ts``); ``hyparquet-compressors`` is
    not a dependency there. So a gzip default would upload cleanly, verify cleanly, and draw
    nothing, with no error anywhere to attach the cause to.

    Distinct from ``build_mesh_collection``'s ``compression``, which is the *per-blob* codec
    inside a row and is the manifest's business. This is the file's.

    Returns the codec that will be written, so a caller can log it.
    """
    import inspect

    from fabriks import frames

    from mikro_next.compression import MESH_CODECS, UnreadableCodecError

    codec = inspect.signature(frames.table_to_parquet).parameters["compression"].default
    if str(codec).upper() not in {name.replace("UNCOMPRESSED", "NONE") for name in MESH_CODECS}:
        raise UnreadableCodecError(
            f"fabriks writes its Parquet parts with {codec!r}, which the mesh viewer cannot "
            f"decode -- it reads them with hyparquet, whose codecs here are "
            f"{', '.join(sorted(MESH_CODECS))} and nothing else, because `hyparquet-compressors` "
            "is not installed in the frontend.\n"
            "\n"
            "Nothing on the server checks this; it stores whatever arrives. A collection written "
            "this way would upload, verify and then draw nothing."
        )
    return str(codec)


__all__ = [
    "CODEC_MESHOPT",
    "CODEC_NONE",
    "COMPRESSION_NONE",
    "COMPRESSION_ZSTD",
    "Decimation",
    "MeshCollection",
    "axis_order_to_xyz",
    "build_mesh_collection",
    "choose_cell_size",
    "decimate_fixed",
    "decode_indices",
    "decode_positions",
    "encode_indices",
    "encode_positions",
    "morton_decode",
    "morton_encode",
    "refuse_an_unreadable_part_codec",
    "require_meshoptimizer",
    "require_trimesh",
    "snap_boundary",
]
