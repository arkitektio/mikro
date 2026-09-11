"""Building a konnektion collection, and the one thing worth refusing before an upload.

The graph counterpart of :mod:`mikro_next.meshes`. It is thinner, because konnektion needs less
from a caller: a network is nodes and edges, and there is no axis-order helper here because a
collection's own component order is the only one it ever states.

    from konnektion import build_collection
    from mikro_next.api.schema import create_network_collection

    collection = build_collection({1: (nodes, edges)}, cell_size=(128, 128, 32))
    create_network_collection(version="v1", store=collection, axes=["x", "y", "z"])

**Node positions are in voxels, ordered ``(x, y, z)``** -- slots 0, 1 and 2, which the format
never interprets. A collection traced out of a ``(z, y, x)`` image reverses its components
before building and declares ``axes=["x", "y", "z"]``; the reversal is then stated where a
machine can read it, on the derivation edge, as a MAP_AXIS naming each axis on both sides.
Declaring the image's order here instead is the transposed-overlay bug: `axes` is positional,
the server checks rank 3, the round trip is self-consistent, the layer still reports PLACED --
and every object draws transposed.
"""

from __future__ import annotations


def refuse_an_unreadable_part_codec() -> str:
    """Refuse to write a collection whose Parquet parts the viewer could not decode.

    A network collection's *file* compression is konnektion's, not this library's --
    ``write_collection`` passes nothing and ``konnektion.frames.table_to_parquet`` picks the
    codec. Today that is ZSTD, which is fine. What makes it worth checking rather than trusting
    is the shape of the failure if it ever changes: ``konnektion.frames.ParquetCompression`` is
    ``Literal["none", "snappy", "gzip", "brotli", "lz4", "zstd"]``, and three of those six are
    codecs the viewer cannot decode -- it reads these parts with **hyparquet**, whose built-ins
    are UNCOMPRESSED and SNAPPY, plus the ZSTD it registers by hand out of ``fzstd``.

    So a gzip default would upload cleanly, verify cleanly, and draw nothing, with no error
    anywhere to attach the cause to. Nothing on the server checks this; it stores what arrives.

    Distinct from the ``compression`` a collection is *built* with, which is the per-blob codec
    inside a row and is the manifest's business. This is the file's.

    Returns the codec that will be written, so a caller can log it.
    """
    import inspect

    from konnektion import frames

    from mikro_next.compression import MESH_CODECS, UnreadableCodecError

    codec = inspect.signature(frames.table_to_parquet).parameters["compression"].default
    if str(codec).upper() not in {name.replace("UNCOMPRESSED", "NONE") for name in MESH_CODECS}:
        raise UnreadableCodecError(
            f"konnektion writes its Parquet parts with {codec!r}, which the viewer cannot "
            f"decode -- it reads them with hyparquet, whose codecs here are "
            f"{', '.join(sorted(MESH_CODECS))} and nothing else, because `hyparquet-compressors` "
            "is not installed in the frontend.\n"
            "\n"
            "Nothing on the server checks this; it stores whatever arrives. A collection written "
            "this way would upload, verify and then draw nothing."
        )
    return str(codec)


__all__ = ["refuse_an_unreadable_part_codec"]
