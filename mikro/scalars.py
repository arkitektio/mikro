"""
Custom scalars for mikro


"""

from __future__ import annotations

import io
from enum import Enum
import mimetypes
import uuid
from collections.abc import Hashable, Mapping, Sequence
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, ClassVar, Literal, Protocol, TypeAlias

import numpy as np
from numpy.typing import NDArray
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
    import dask.array as da
    import pandas as pd
    import xarray as xr
    import pyarrow as pa
    from fabriks import MeshCollection
    from konnektion import NetworkCollection

    from mikro.io.chunking import ChunkLayout

OneDArray = NDArray[np.generic]


ThreeDVectorCoercible: TypeAlias = list[float] | OneDArray | list[int]
""" A type alias for 3D vector-like structures that can be coerced into a ThreeDVector."""


if TYPE_CHECKING:
    ArrayCoercible: TypeAlias = (
        "ArrayLike | xr.DataArray | da.Array | NDArray[Any] | list[float] | list[list[float]]"
    )
else:
    # At runtime only a name: the real union names xarray and dask types, and neither is
    # imported to build it.
    ArrayCoercible = Any
""" What an array input accepts: a numpy or dask array, whose dimensions are then named by
the ``axes`` it is declared with, in order; or anything carrying its own names -- an
``xarray.DataArray``, read by duck typing, so xarray is never imported here."""

AxisName: TypeAlias = Hashable
"""An axis given by its name alone: any hashable, as xarray types its dims (see :func:`axis_name`)."""


def axis_name(name: AxisName) -> str:
    """The string an axis given by ``name`` is called: an enum's value, else ``str(name)``."""
    if isinstance(name, Enum):
        name = name.value
    return str(name)

ImageFileCoercible: TypeAlias = str | bytes | Path | io.BufferedReader
""" A type alias for image file-like structures."""

ParquetCoercible: TypeAlias = (
    "Mapping[str, Any] | pd.DataFrame | str | Path | pa.Table | pa.RecordBatchReader | ParquetLike"
)
""" A type alias for parquet-like structures: a dict of ``{column: values}``, an
in-memory DataFrame, a path to a parquet file already on disk, or a pyarrow
``Table``/``RecordBatchReader``."""

FileCoercible: TypeAlias = str | bytes | Path | io.BufferedReader
""" A type alias for file-like structures."""


# What a metric may be about, one protocol per structure. Every class turms generates
# for a type the server identifies is stamped `__identifier__: ClassVar[Literal[...]]`
# (`@identified`), a nested selection (`lens.dataset`) included, so a checker matches
# exactly the classes of these four types: a lens, a scene or a slice is flagged. The
# server stays the authority at runtime and refuses any other structure in prose.


class AnnotationTarget(Protocol):
    """An annotation, from any selection of one."""

    __identifier__: ClassVar[Literal["@mikro/annotation"]]

    @property
    def id(self) -> str: ...


class ArrayDatasetTarget(Protocol):
    """An array dataset, from any selection of one (``lens.dataset`` too)."""

    __identifier__: ClassVar[Literal["@mikro/arraydataset"]]

    @property
    def id(self) -> str: ...


class TableDatasetTarget(Protocol):
    """A table dataset, from any selection of one."""

    __identifier__: ClassVar[Literal["@mikro/tabledataset"]]

    @property
    def id(self) -> str: ...


class SparseDatasetTarget(Protocol):
    """A sparse dataset, from any selection of one."""

    __identifier__: ClassVar[Literal["@mikro/sparsedataset"]]

    @property
    def id(self) -> str: ...


MetricTargetCoercible: TypeAlias = AnnotationTarget | ArrayDatasetTarget | TableDatasetTarget | SparseDatasetTarget
""" What a metric's target accepts besides a ``MetricTargetInput``: the object itself, as fetched."""


MicrometersCoercible: TypeAlias = int | float
""" A type alias for micrometer-like structures."""

ByteCountCoercible: TypeAlias = int | str
""" What a ByteCount input accepts: an int, or a numeric string."""


def _require_pandas() -> Any:  # noqa: ANN401
    """Import pandas lazily, raising a helpful error if the extra is missing.

    pandas is only needed for the table/labels (parquet) paths, so it is an
    optional dependency. Install it via ``mikro[table]``.
    """
    try:
        import pandas as pd
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "pandas is required for table/labels support. "
            "Install it with `pip install mikro[table]`."
        ) from e
    return pd


def is_dask_array(v: Any) -> bool:  # noqa: ANN401
    """Check if the input is a dask array."""
    try:
        import dask.array.core as da

        return isinstance(v, da.Array)
    except ImportError:
        return False
    except Exception as e:
        raise ValueError(f"Error checking for dask array: {e}")


def _require_xarray() -> Any:  # noqa: ANN401
    """Import xarray lazily, raising a helpful error if the extra is missing.

    mikro reads and writes plain numpy/dask arrays; xarray (and the pandas it pulls in)
    is only needed to hand a dataset back as a labelled ``xarray.DataArray``. Install it
    via ``mikro[xarray]``.
    """
    try:
        import xarray as xr
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "xarray is required for labelled arrays (`.xarray_data`). "
            "Install it with `pip install mikro[xarray]`."
        ) from e
    return xr


def labelled(v: Any) -> tuple[Any, tuple[str, ...] | None]:  # noqa: ANN401
    """Split an array input into its data (numpy or dask) and its dimension names.

    Anything carrying ``.dims`` and ``.data`` -- an ``xarray.DataArray``, an
    :class:`ArrayLike` -- brings its own names, read verbatim: nothing is added, removed or
    transposed, and a dask array stays lazy. A bare numpy or dask array has no names
    (``None``); the dataset declaration names them from its ``axes``. Lists become numpy.
    """
    dims = getattr(v, "dims", None)
    if dims is not None and hasattr(v, "data"):
        return v.data, tuple(axis_name(d) for d in dims)
    if isinstance(v, ArrayLike):
        return v.data, None
    if isinstance(v, np.ndarray) or is_dask_array(v):
        return v, None
    if isinstance(v, (list, tuple)):
        return np.asarray(v), None
    raise ValueError(
        f"An array input is a numpy or dask array, or an xarray.DataArray, not a {type(v).__name__}"
    )


class ByteCount(int):
    """A number of bytes: 64-bit, unlike GraphQL's Int.

    Mirrors the server's scalar: a non-negative integer, sent as a JSON number and
    accepted as a number or a numeric string (from a client that cannot hold one).
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Validate with :meth:`validate`, serialize as a plain int."""
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(int),
        )

    @classmethod
    def validate(cls, v: ByteCountCoercible) -> ByteCount:
        """Take an int or a numeric string; refuse bools, fractions and negatives."""
        if isinstance(v, bool) or not isinstance(v, (int, str)):
            raise ValueError(f"ByteCount must be an integer, got {v!r}")
        count = int(v)
        if count < 0:
            raise ValueError(f"ByteCount cannot be negative, got {count}")
        return cls(count)


class Micrometers(float):
    """A custom scalar to represent a micrometer."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_before_validator_function(cls.validate, handler(float))

    @classmethod
    def validate(cls, v: MicrometersCoercible) -> Micrometers:
        """Validate the input as a float."""
        return cls(v)


class ThreeDVector(list[float]):
    """A custom scalar to represent a vertex of a shape.

    Its components are the SPACE axes of the coordinate system it is drawn in, in that
    system's axis order: ``(z, y, x)`` on a volume, ``(y, x)`` on a plane.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: ThreeDVectorCoercible) -> ThreeDVector:
        """Validate the input as a list of two or three components."""
        if isinstance(v, np.ndarray):
            assert v.ndim == 1
            v = v.tolist()

        assert isinstance(v, list)
        assert len(v) in (2, 3), f"A vertex has two or three space components, but got {len(v)}."
        return cls(v)

    def as_vector(self) -> OneDArray:
        """Convert the ThreeDVector to a numpy array."""
        return np.array(self)


class ArrayLike:
    """A custom scalar for wrapping every supported array-like structure on the mikro
    platform: the array itself (numpy or dask, kept lazy) and the names of its dimensions.

    ``dims`` is ``None`` for a bare array until the dataset declaration names it from its
    ``axes`` (see :class:`mikro.traits.CreateADatasetTrait`).
    """

    def __init__(
        self,
        data: Any,  # noqa: ANN401
        dims: Sequence[Hashable] | None = None,
        layout: ChunkLayout | None = None,
    ) -> None:
        """Wrap ``data`` (numpy or dask) with its dimension names.

        ``layout`` overrides the chunks and shards the array is written with; left unset, the
        dataset declaration it is uploaded for chooses them (see :mod:`mikro.io.chunking`).
        An array that carries its own names (an ``xarray.DataArray``) keeps them when ``dims``
        is not given.
        """
        unwrapped, own = labelled(data)
        if dims is None:
            dims = own
        elif own is not None and tuple(axis_name(d) for d in dims) != own:
            raise ValueError(f"dims={list(dims)} disagrees with the array's own {list(own)}")
        data = unwrapped
        self.data = data
        self.dims: tuple[str, ...] | None = (
            None if dims is None else tuple(axis_name(d) for d in dims)
        )
        if self.dims is not None and len(self.dims) != data.ndim:
            raise ValueError(
                f"{len(self.dims)} dimension names {self.dims} for an array of shape {data.shape}"
            )
        self.layout = layout
        self.key = str(uuid.uuid4())

    @property
    def shape(self) -> tuple[int, ...]:
        """The array's shape."""
        return tuple(self.data.shape)

    @property
    def dtype(self) -> np.dtype[Any]:
        """The array's dtype."""
        return self.data.dtype

    @property
    def ndim(self) -> int:
        """The array's rank."""
        return self.data.ndim

    @property
    def sizes(self) -> dict[str, int]:
        """Dimension name -> extent, once the dimensions are named."""
        if self.dims is None:
            raise ValueError("This array's dimensions are not named yet")
        return dict(zip(self.dims, self.shape))

    def __get__(self, instance, owner) -> ArrayLike: ...  # noqa: ANN001, D105 #type: ignore

    def __set__(self, instance, value: ArrayCoercible) -> None: ...  # noqa: ANN001, D105 #type: ignore

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: ArrayCoercible) -> ArrayLike:
        """Validate the input array, preserving any dimension names it carries as-is."""
        if isinstance(v, cls):
            return v
        data, dims = labelled(v)
        return cls(data, dims)

    def __repr__(self) -> str:
        """Return a string representation of the ArrayLike scalar."""
        return f"ArrayLike(dims={self.dims}, shape={self.shape}, dtype={self.dtype})"


class ParquetLike:
    """A custom scalar for ensuring a common format to support write to the
    parquet api supported by mikro It converts the passed value into
    a compliant format..

    Five things count as parquet-like, and the difference matters at upload time
    rather than here (see :func:`mikro.io.upload._store_parquet_input`):

    - a ``dict`` of ``{column: values}`` — turned into a ``pyarrow.Table`` here and
      then treated as one. The shortest way to say a small table, and the reason no
      caller needs a temporary file to upload one;
    - a ``pandas.DataFrame`` — converted and serialized in memory, the original path;
    - a ``str``/``Path`` naming a parquet file already on disk — streamed straight
      to the object store, never read into this process;
    - a ``pyarrow.Table`` — serialized in memory, but without the pandas round trip;
    - a ``pyarrow.RecordBatchReader`` — written batch by batch to a temporary file,
      then streamed.

    The last three exist because a table big enough to be interesting is a table too
    big to hold three copies of. A 128M-row expression matrix is ~1.5 GB as a frame,
    again as an arrow table, and again as a serialized buffer; written incrementally
    and streamed, peak memory is one batch.
    """

    def __init__(self, value: ParquetCoercible) -> None:
        """Initialize the ParquetLike scalar with a DataFrame, path or arrow object."""
        self.value = value
        self.key = str(uuid.uuid4())

    def __get__(self, instance, owner) -> ParquetLike: ...  # noqa: ANN001, D105 # type: ignore

    def __set__(self, instance, value: ParquetCoercible) -> None: ...  # noqa: ANN001, D105 # type: ignore

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: ParquetCoercible) -> ParquetLike:
        """Validate the validator function"""
        if isinstance(v, ParquetLike):
            return v

        if isinstance(v, (str, Path)):
            path = Path(v)
            # Checked here rather than at upload: a typo'd path should fail while the
            # caller still knows which table it meant, not inside an upload link three
            # mutations later.
            if not path.is_file():
                raise ValueError(f"No parquet file at {path}")
            return cls(path)

        if isinstance(v, Mapping):
            # A dict of columns is the shortest thing a table can be written as, and there is
            # no reason for the caller to reach for pyarrow to say it. Coerced eagerly, so
            # everything downstream -- the schema derivation, the uploader -- sees a Table and
            # the dict never exists past validation.
            import pyarrow as pa  # type: ignore

            try:
                return cls(pa.table(dict(v)))
            except Exception as error:
                raise ValueError(
                    "A dict of columns becomes a pyarrow Table, and this one could not: "
                    f"{error}. Every value has to be a column of the same length -- a numpy "
                    "array, a list, or a pyarrow array."
                ) from error

        # pyarrow is optional in the same way pandas is, so it is only imported when
        # the value might actually be one of its types.
        try:
            import pyarrow as pa  # type: ignore
        except ImportError:
            pa = None
        if pa is not None and isinstance(v, (pa.Table, pa.RecordBatchReader)):
            return cls(v)

        pd = _require_pandas()
        if not isinstance(v, pd.DataFrame):
            raise ValueError(
                "This needs to be a dict of columns, a pandas DataFrame, a path to a parquet "
                "file, or a pyarrow Table/RecordBatchReader"
            )

        return cls(v)

    def __repr__(self) -> str:
        """Return a string representation of the ParquetLike scalar."""
        return f"ParquetLike({self.value})"


def _sporadik() -> Any:  # noqa: ANN401 - the module object
    """The sparse wire format, or the reason it is missing.

    An extra rather than a dependency, exactly as `fabriks` is: a client that never uploads a sparse
    dataset should not carry the format. Which means the failure has to name the extra -- a bare
    `ModuleNotFoundError` on an indirect import reads like a broken install rather than an
    unchosen one.
    """
    try:
        import sporadik
    except ModuleNotFoundError as missing:  # pragma: no cover - depends on the environment
        raise ModuleNotFoundError(
            "A sparse dataset is written in the `sporadik` wire format, which is an optional extra here: "
            "pip install 'mikro[sparse]'. Nothing else in this client needs it, which is why it is not "
            "a dependency."
        ) from missing
    return sporadik


class SporadikLike:
    """A reference to a **sparse matrix**, uploaded as one prefix holding one or both layouts.

    The value is the matrix itself -- anything carrying ``.data``, ``.indices``, ``.indptr``,
    ``.shape`` and ``.format``, which a `scipy.sparse` CSR or CSC matrix does -- or a list of
    them, or :class:`sporadik.Layout` objects for an array of rank three or more. The upload writes them into a granted prefix in the spelling anndata uses and
    lands a block naming what it finished, and the server reads the encoding, the shape and the
    chunking back off the artifact -- which is why ``createSparseDataset`` declares none of them.

    **Which encodings you hand over is a decision, not a detail.** It is the whole of what the
    two layouts differ in, and it decides which question the store answers in one contiguous
    read: ``.tocsc()`` over an (objects, features) matrix makes one *feature* contiguous -- the
    colouring -- and ``.tocsr()`` makes one *object* contiguous, which is the hover. Ask the
    other of either and there is no range to read at all, only a scan: 1 777 ms against 2.2 ms,
    measured. A matrix that must answer both questions is passed as ``[counts.tocsc(),
    counts.tocsr()]`` -- **one upload**, one prefix, one store, two capabilities. Two axes is
    one case of this: an array of rank *n* takes up to *n* layouts, one per axis something
    selects along, and buys exactly one axis's worth of contiguity with each.

    Validated here rather than only server-side because the server's check comes after the
    bytes have moved, and a 1 GB matrix is an expensive way to learn that `indptr` is the wrong
    length.
    """

    def __init__(self, value: Any, layouts: dict[int, Any] | None = None) -> None:  # noqa: ANN401
        """Initialize the SporadikLike scalar with one or two CSR/CSC matrices.

        ``layouts`` is keyed by the axis each layout makes contiguous -- ``sporadik.layouts_of``
        returns ``dict[int, Layout]`` -- not by encoding. Above rank two the encoding no longer
        names an axis (every layout is a ``csr_matrix`` over the raveled view), so the key and
        ``Layout.indexed_axis`` are the same number by construction and the encoding is not.
        """
        layouts_of = _sporadik().layouts_of

        self.value = value
        #: The layouts to write, keyed by encoding. Resolved once here rather than at write time,
        #: so a matrix that cannot be stored is refused at the call site that passed it.
        self.layouts = layouts if layouts is not None else layouts_of(value)
        self.key = str(uuid.uuid4())

    def __get__(self, instance, owner) -> SporadikLike: ...  # noqa: ANN001, D105 # type: ignore

    def __set__(self, instance, value: SporadikCoercible) -> None: ...  # noqa: ANN001, D105 # type: ignore

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: SporadikCoercible) -> SporadikLike:
        """Accept one or two CSR/CSC matrices, and refuse what cannot be written as a store."""
        if isinstance(v, SporadikLike):
            return v

        sporadik = _sporadik()
        layouts_of, validate_layout = sporadik.layouts_of, sporadik.validate_layout

        layouts = layouts_of(v)
        for layout in layouts.values():
            validate_layout(
                data=layout.data,
                indices=layout.indices,
                indptr=layout.indptr,
                shape=layout.shape,
                indexed_axis=layout.indexed_axis,
            )
        return cls(v, layouts)

    def __repr__(self) -> str:
        """Return a string representation of the SporadikLike scalar."""
        shape = next(iter(self.layouts.values())).shape if self.layouts else "?"
        axes = "+".join(f"axis{axis}" for axis in sorted(self.layouts))
        return f"SporadikLike({axes}, shape={shape})"


class FabriksLike:
    """A reference to a **fabriks collection**, uploaded as one prefix rather than as tables.

    A fabriks store is `fabriks.json`, both catalogs and one part file per octree level under a
    single key -- so the value here is the built collection itself, and the upload link writes
    the tree into a granted prefix and lands the manifest last. The server then reads the grid
    and the encoding off that manifest instead of taking a caller's word for them, which is why
    ``createMeshCollection`` no longer has fields for either.

    That is also why there is nothing to validate here beyond identity. Under the previous wire
    format this client checked each frame's columns before spending an upload, because the
    server's check came a round trip too late; now the artifact carries its own declarations and
    the only client-side mistake left to catch is handing over something that is not a
    collection at all.

    **Declare ``axes`` in the collection's own component order, which is ``(x, y, z)``.**
    Vertex and node components are stored x, y, z, and ``axes`` is positional: declaring a
    ``(z, y, x)`` image's order over them registers cleanly, reports PLACED, and draws every
    object transposed. State the reversal on the derivation edge instead, as a MAP_AXIS naming
    each axis on both sides.
    """

    def __init__(self, value: MeshCollection) -> None:
        """Initialize the FabriksLike scalar with a built fabriks collection."""
        self.value = value
        self.key = str(uuid.uuid4())

    def __get__(self, instance, owner) -> FabriksLike: ...  # noqa: ANN001, D105 # type: ignore

    def __set__(self, instance, value: FabriksCoercible) -> None: ...  # noqa: ANN001, D105 # type: ignore

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: FabriksCoercible) -> FabriksLike:
        """Accept a built collection, and refuse the things that look like one but are not."""
        if isinstance(v, FabriksLike):
            return v

        # fabriks is an extra, so it is imported only where the value might be one of its types.
        try:
            from fabriks import MeshCollection  # type: ignore
        except ImportError as error:
            raise ValueError(
                "A mesh collection is built by `fabriks`, which is not installed. Install it with "
                "`pip install mikro[mesh]`."
            ) from error

        if isinstance(v, MeshCollection):
            return cls(v)

        # The single-frame mistake is worth naming: under the previous wire format a caller
        # passed the catalog table here, and a pyarrow Table is exactly what they still have in
        # hand after building one.
        raise ValueError(
            f"This is uploaded as a fabriks collection -- one prefix holding the manifest, both "
            f"catalogs and every octree level -- so it takes a `fabriks.MeshCollection`, not a "
            f"{type(v).__name__}. Build one with `fabriks.build_collection(objects)`."
        )

    def __repr__(self) -> str:
        """Return a string representation of the FabriksLike scalar.

        The counts and the grid rather than the value: a collection holds every object's
        geometry, and repr is what an error message and a log line are built out of.
        """
        manifest = self.value.manifest
        return f"FabriksLike({manifest.counts}, cellSize={manifest.grid.cell_size}, levels={manifest.grid.levels})"


class SparseMatrixLike(Protocol):
    """The structure a sparse matrix must have to be written as a sporadik store.

    Spelled structurally rather than as `scipy.sparse.csr_matrix | csc_matrix` because scipy is
    not a mikro dependency and `sporadik.layouts_of` only ever reads these five members -- so
    anndata's own matrix wrappers, and a rank-three array's `sporadik.Layout`, satisfy it too.

    Members are read-only properties because a mutable attribute is invariant, and a matrix's
    `NDArray[float64]` would then not satisfy a declared `NDArray[generic]`. ``.shape`` is
    deliberately absent: scipy's stubs do not expose it as a readable property, so declaring it
    here would make every real matrix fail the check. ``sporadik.validate_layout`` checks it at
    runtime regardless.
    """

    @property
    def data(self) -> OneDArray:
        """The stored values, in the order the layout's encoding puts them."""
        ...

    @property
    def indices(self) -> OneDArray:
        """The index within each compressed slice of every value in :attr:`data`."""
        ...

    @property
    def indptr(self) -> OneDArray:
        """Where each compressed slice starts in :attr:`data`; one longer than the slice count."""
        ...

    @property
    def format(self) -> str:
        """The encoding, ``"csr"`` or ``"csc"`` -- which axis the matrix makes contiguous."""
        ...


SporadikCoercible: TypeAlias = "SparseMatrixLike | list[SparseMatrixLike] | SporadikLike"
"""What :class:`SporadikLike` accepts: a `scipy.sparse` CSR or CSC matrix, a list of them for an
array of rank three or more, or one already wrapped."""

#: What a caller may hand to a `FabriksLike` field. Deliberately narrow: everything a collection
#: could be built *from* is an argument to `fabriks.build_collection`, not a value on the wire.
FabriksCoercible: TypeAlias = "MeshCollection | FabriksLike"


class KonnektionLike:
    """A reference to a **konnektion collection**, uploaded as one prefix rather than as tables.

    The graph twin of :class:`FabriksLike`, and the same shape: a konnektion store is
    ``konnektion.json``, both catalogs and one part file per octree level under a single key, so
    the value here is the built collection itself and the upload link writes the tree into a
    granted prefix and lands the manifest last. The server reads the grid and the encoding off
    that manifest rather than taking a caller's word for them.

    **A separate scalar rather than a flag on the mesh one**, because it names a separate format.
    The two differ where it is least visible: a konnektion blob is a segment list and a fabriks
    blob is a triangle list, and reading either as the other raises nothing at any layer.
    Keeping them apart at the type level is what makes that mistake impossible to make by
    accident rather than merely unlikely.

    **Declare ``axes`` in the collection's own component order, which is ``(x, y, z)``.**
    Vertex and node components are stored x, y, z, and ``axes`` is positional: declaring a
    ``(z, y, x)`` image's order over them registers cleanly, reports PLACED, and draws every
    object transposed. State the reversal on the derivation edge instead, as a MAP_AXIS naming
    each axis on both sides.
    """

    def __init__(self, value: NetworkCollection) -> None:
        """Initialize the KonnektionLike scalar with a built konnektion collection."""
        self.value = value
        self.key = str(uuid.uuid4())

    def __get__(self, instance, owner) -> KonnektionLike: ...  # noqa: ANN001, D105 # type: ignore

    def __set__(self, instance, value: KonnektionCoercible) -> None: ...  # noqa: ANN001, D105 # type: ignore

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: KonnektionCoercible) -> KonnektionLike:
        """Accept a built collection, and refuse the things that look like one but are not."""
        if isinstance(v, KonnektionLike):
            return v

        # konnektion is an extra, so it is imported only where the value might be one of its types.
        try:
            from konnektion import NetworkCollection  # type: ignore
        except ImportError as error:
            raise ValueError(
                "A network collection is built by `konnektion`, which is not installed. Install it "
                "with `pip install mikro[network]`."
            ) from error

        # The mistake worth naming is the neighbouring format: a mesh collection is the other
        # thing in this codebase that is "a built collection", and the server would refuse it a
        # round trip later on a manifest key it does not have.
        try:
            from fabriks import MeshCollection  # type: ignore
        except ImportError:
            MeshCollection = ()  # type: ignore[assignment]

        if isinstance(v, NetworkCollection):
            return cls(v)

        if MeshCollection and isinstance(v, MeshCollection):
            raise ValueError(
                "This is a `fabriks.MeshCollection` -- a collection of surfaces -- and this field "
                "takes a `konnektion.NetworkCollection`, a collection of node/edge graphs. The two "
                "are separate formats: a mesh index blob is triangles and a network one is "
                "segments. Register a mesh with `create_mesh_collection` instead."
            )

        raise ValueError(
            f"This is uploaded as a konnektion collection -- one prefix holding the manifest, both "
            f"catalogs and every octree level -- so it takes a `konnektion.NetworkCollection`, not "
            f"a {type(v).__name__}. Build one with `konnektion.build_collection(objects)`."
        )

    def __repr__(self) -> str:
        """Return a string representation of the KonnektionLike scalar."""
        manifest = self.value.manifest()
        return f"KonnektionLike({manifest.counts}, cellSize={manifest.grid.cell_size}, levels={manifest.grid.levels})"


KonnektionCoercible: TypeAlias = "NetworkCollection | KonnektionLike"


class ImageFileLike:
    """A custom scalar for ensuring a common format to support write to the
    parquet api supported by mikro It converts the passed value into
    a compliant format.."""

    def __init__(self, value: io.BufferedReader, name: str = "") -> None:
        """Initialize the ImageFileLike scalar with a file-like object."""
        self.value = value
        self.file_name = Path(name).name
        self.mime_type = mimetypes.guess_type(self.file_name)[0]

    def __get__(self, instance, owner) -> FileLike: ...  # noqa: ANN001, D105 # type: ignore

    def __set__(self, instance, value: FileCoercible) -> None: ...  # noqa: ANN001, D105 # type: ignore

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: FileCoercible) -> ImageFileLike:
        """Validate the validator function"""

        if isinstance(v, str):
            file = open(v, "rb")
            name = v
        elif isinstance(v, io.IOBase):
            file = v
            name = v.name
        elif isinstance(v, Path):
            file = open(v, "rb")
            name = str(v)
        else:
            raise ValueError(
                f"Unsupported type {type(v)}. Please provide a string or a Path object. Or a file object that is opened in binary mode."
            )

        if not isinstance(file, io.BufferedReader):  # type: ignore
            raise ValueError("This needs to be a instance of a file")

        return cls(file, name=name)

    def __repr__(self) -> str:
        """Return a string representation of the ImageFileLike scalar."""
        return f"FileLike({self.value})"


class KulisseLike:
    """A kulisse model -- a device or scene model, one self-contained binary glTF (``.glb``).

    A path, an open binary file, or the bytes themselves. The upload middleware requests a
    kulisse store, writes the file and finishes it; the server then reads and checks the model
    (container, joint table, budgets) and records its nodes, joints and bounds. Author and check
    a model before uploading it with the ``kulisse`` package (``kulisse check model.glb``).
    """

    def __init__(self, value: bytes, name: str = "") -> None:
        """Initialize the KulisseLike scalar with the model's bytes."""
        self.value = value
        self.file_name = Path(name).name if name else "model.glb"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: "KulisseCoercible") -> "KulisseLike":
        """Read a path, a binary file or bytes into the model's bytes."""
        if isinstance(v, KulisseLike):
            return v
        if isinstance(v, (str, Path)):
            path = Path(v)
            return cls(path.read_bytes(), name=path.name)
        if isinstance(v, (bytes, bytearray)):
            return cls(bytes(v))
        if isinstance(v, io.BufferedReader):
            return cls(v.read(), name=str(v.name))
        raise ValueError(f"A kulisse model is a path, a file opened in binary mode or bytes, not {type(v)}.")

    def __repr__(self) -> str:
        """Return a string representation of the KulisseLike scalar."""
        return f"KulisseLike({self.file_name}, {len(self.value)} bytes)"


KulisseCoercible: TypeAlias = str | Path | io.BufferedReader | bytes | KulisseLike


class FileLike:
    """A custom scalar for ensuring a common format to support write to the
    parquet api supported by mikro It converts the passed value into
    a compliant format.."""

    def __init__(self, value: IO[bytes], name: str = "") -> None:
        """Initialize the FileLike scalar with a file-like object."""
        self.value = value
        self.file_name = Path(name).name
        self.mime_type = mimetypes.guess_type(self.file_name)[0]

    def __get__(self, instance, owner) -> FileLike: ...  # noqa: ANN001, D105 # type: ignore

    def __set__(self, instance, value: FileCoercible) -> None: ...  # noqa: ANN001, D105 # type: ignore

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_after_validator_function(cls.validate, handler(object))

    @classmethod
    def validate(cls, v: FileCoercible) -> FileLike:
        """Validate the validator function"""

        if isinstance(v, str):
            file = open(v, "rb")
            name = v
        elif isinstance(v, io.IOBase):
            file = v
            name = v.name
        elif isinstance(v, Path):
            file = open(v, "rb")
            name = str(v)
        else:
            raise ValueError(
                f"Unsupported type {type(v)}. Please provide a string or a Path object. Or a file object that is opened in binary mode."
            )

        if not isinstance(file, io.IOBase):  # type: ignore
            raise ValueError("This needs to be a instance of a file")

        return cls(file, name=name)

    def __repr__(self) -> str:
        """Return a string representation of the FileLike scalar."""
        return f"FileLike({self.value})"
