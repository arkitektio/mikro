"""
Custom scalars for mikro_next


"""

from __future__ import annotations

import io
import mimetypes
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, TypeAlias

import numpy as np
import xarray as xr
from numpy.typing import NDArray
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
    import pandas as pd
    from fabriks import MeshCollection
    from konnektion import NetworkCollection

OneDArray = NDArray[np.generic]
TwoDArray = NDArray[np.generic]


TwoDVectorCoercible: TypeAlias = list[float] | OneDArray | list[int]
""" A type alias for 2D vector-like structures that can be coerced into a TwoDVector."""

ThreeDVectorCoercible: TypeAlias = list[float] | OneDArray | list[int]
""" A type alias for 3D vector-like structures that can be coerced into a ThreeDVector."""

FourDVectorCoercible: TypeAlias = list[float] | OneDArray | list[int]
""" A type alias for 4D vector-like structures that can be coerced into a FourDVector."""

ArrayCoercible: TypeAlias = xr.DataArray | OneDArray | list[float] | list[list[float]]
""" A type alias for array-like structures that can be coerced into an xarray DataArray."""

ImageFileCoercible: TypeAlias = str | bytes | Path | io.BufferedReader
""" A type alias for image file-like structures that can be coerced into an xarray DataArray."""

ParquetCoercible: TypeAlias = "Mapping[str, Any] | pd.DataFrame | str | Path | Any"
""" A type alias for parquet-like structures: a dict of ``{column: values}``, an
in-memory DataFrame, a path to a parquet file already on disk, or a pyarrow
``Table``/``RecordBatchReader``."""

FileCoercible: TypeAlias = str | bytes | Path | io.BufferedReader
""" A type alias for file-like structures that can be coerced into an xarray DataArray."""

FourByFourMatrixCoercible: TypeAlias = list[list[float]] | TwoDArray | list[list[int]]
""" A type alias for 4x4 matrix-like structures that can be coerced into an xarray DataArray."""

MillisecondsCoercible: TypeAlias = int | float
""" A type alias for millisecond-like structures that can be coerced into an xarray DataArray."""

MicrometersCoercible: TypeAlias = int | float
""" A type alias for micrometer-like structures that can be coerced into an xarray DataArray."""

RGBAColorCoercible: TypeAlias = list[float] | list[int] | OneDArray
""" A type alias for RGBA color-like structures that can be coerced into an RGBA Value"""


def _require_pandas() -> Any:  # noqa: ANN401
    """Import pandas lazily, raising a helpful error if the extra is missing.

    pandas is only needed for the table/labels (parquet) paths, so it is an
    optional dependency. Install it via ``mikro-next[table]``.
    """
    try:
        import pandas as pd
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "pandas is required for table/labels support. "
            "Install it with `pip install mikro-next[table]`."
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


def coerce_to_labeled_array(v: ArrayCoercible) -> xr.DataArray:
    """Coerce array-like input into a labelled ``xr.DataArray`` without forcing ``ctzyx``.

    This preserves the caller's dimension labels and order verbatim: no dimensions are added,
    removed, or transposed. This is the generic dataset path where the user
    supplies arbitrary, explicitly-labelled dimensions alongside matching
    ``axes`` (validated at the model level by ``CreateADatasetTrait``).

    Bare numpy/dask arrays carry no labels, so they are wrapped with xarray's
    default dimension names (``dim_0``, ``dim_1``, ...). The array is returned
    lazily (dask chunks preserved) so the upload path can stream it to zarr.
    """
    if isinstance(v, np.ndarray) or is_dask_array(v):
        return xr.DataArray(v)

    if not isinstance(v, xr.DataArray):
        raise ValueError("This needs to be a instance of xarray.DataArray")

    return v


class RGBAColor(list[float]):
    """A custom scalar to represent an affine matrix."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_before_validator_function(cls.validate, handler(float))

    @classmethod
    def validate(cls, v: RGBAColorCoercible) -> RGBAColor:
        """Validate the input array and convert it to a xr.DataArray."""
        if isinstance(v, np.ndarray):
            if v.ndim == 1:
                v = v.tolist()
            else:
                raise ValueError("The input array must be a 1D array")

        if not isinstance(v, list):
            raise ValueError("The input must be a list or a 1-D numpy array.")

        v = [float(i) for i in v]  # Convert all elements to float

        if len(v) == 3:
            v.append(1.0)  # Add alpha channel if not present

        if len(v) != 4:
            raise ValueError(
                f"The input must be a list of 3 or 4 elements (R, G, B, [A]). You provided a list of {len(v)} elements"
            )

        return cls(v)


class XArrayConversionException(Exception):
    """An exception that is raised when a conversion to xarray fails."""



MetricValue = Any
FeatureValue = Any


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
        """Validate the input array and convert it to a xr.DataArray."""
        return cls(v)


class Milliseconds(float):
    """A custom scalar to represent a millisecond."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_before_validator_function(cls.validate, handler(float))

    @classmethod
    def validate(cls, v: MillisecondsCoercible) -> Milliseconds:
        """Validate the input array and convert it to a xr.DataArray."""
        return cls(v)


class TwoDVector(list[float]):
    """A custom scalar to represent a vector."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: TwoDVectorCoercible) -> TwoDVector:
        """Validate the input array and convert it to a xr.DataArray."""
        if isinstance(v, np.ndarray):
            assert v.ndim == 1
            v = v.tolist()  # Convert numpy array to list #type: ignore

        assert isinstance(v, list)
        assert len(v) == 3
        return cls(v)

    def as_vector(self) -> OneDArray:
        """Convert the TwoDVector to a numpy array."""
        return np.array(self)


class ThreeDVector(list[float]):
    """A custom scalar to represent a vector."""

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
        """Validate the input array and convert it to a xr.DataArray."""
        if isinstance(v, np.ndarray):
            assert v.ndim == 1
            v = v.tolist()

        assert isinstance(v, list)
        assert len(v) == 3
        return cls(v)

    def as_vector(self) -> OneDArray:
        """Convert the ThreeDVector to a numpy array."""
        return np.array(self)


class FourDVector(list[float]):
    """A custom scalar to represent a vector."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: FourDVectorCoercible) -> FourDVector:
        """Validate the input array and convert it to a xr.DataArray."""
        if isinstance(v, np.ndarray):
            assert v.ndim == 1
            v = v.tolist()

        assert isinstance(v, list)
        assert len(v) == 4
        return cls(v)

    def as_vector(self) -> OneDArray:
        """Convert the FourDVector to a numpy array."""
        return np.array(self).reshape(-1)


class FourByFourMatrix(list[list[float]]):
    """A custom scalar to represent a four by four matrix (e.g 3D affine matrix.)"""

    def __get__(self, instance, owner) -> FourByFourMatrix: ...  # type: ignore # noqa: ANN001, D105

    def __set__(self, instance, value: FourByFourMatrixCoercible) -> None: ...  # type: ignore # noqa: ANN001, D105

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema for the validator function"""
        return core_schema.no_info_before_validator_function(cls.validate, handler(list))

    @classmethod
    def validate(cls, v: FourByFourMatrixCoercible) -> FourByFourMatrix:
        """Validate the input array and convert it to a xr.DataArray."""
        if isinstance(v, np.ndarray):
            if not v.ndim == 2:
                raise ValueError("The input array must be a 2D array")
            if not v.shape[0] == v.shape[1]:
                raise ValueError("The input array must be a square matrix")
            if not v.shape == (4, 4):
                raise ValueError("The input array must be a 4x4 matrix")
            clean = [[float(v[i, j]) for j in range(4)] for i in range(4)]
        else:
            clean = v

        if not isinstance(clean, list):  # type: ignore
            raise ValueError(
                f"Expected a list or numpy array, got {type(clean)}. Please provide a 4x4 matrix."
            )

        if len(clean) != 4 or any(len(row) != 4 for row in clean):
            raise ValueError(
                f"Expected a 4x4 matrix, got {len(clean)} rows and {[len(row) for row in clean]} columns."
            )

        for row in clean:
            if not all(isinstance(x, (int, float)) for x in row):  # type: ignore
                raise ValueError("All elements of the 4x4 matrix must be integers or floats.")

        return cls(clean)  # type: ignore

    def as_matrix(self) -> TwoDArray:
        """Convert the FourByFourMatrix to a numpy array."""
        return np.array(self).reshape(4, 4)

    @classmethod
    def from_np(cls, v: TwoDArray) -> FourByFourMatrix:
        """Validate the input array and convert it to a xr.DataArray."""
        return cls.validate(v)


class ArrayLike:
    """A custom scalar for wrapping of every supported array like structure on
    the mikro platform. This scalar enables validation of various array formats
    into a mikro api compliant xr.DataArray.."""

    def __init__(self, value: xr.DataArray) -> None:
        """Initialize the ArrayLike scalar with an xarray DataArray."""
        self.value = value
        self.key = str(uuid.uuid4())

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
        """Validate the input array, preserving its labelled dimensions as-is."""
        return cls(coerce_to_labeled_array(v))

    def __repr__(self) -> str:
        """Return a string representation of the ArrayLike scalar."""
        return f"InputArray({self.value})"


class BigFile:
    """A custom scalar for wrapping of every supported array like structure on
    the mikro platform. This scalar enables validation of various array formats
    into a mikro api compliant xr.DataArray.."""

    def __init__(self, value: IO[bytes]) -> None:
        """Initialize the BigFile scalar with a file-like object."""
        self.value = value
        self.key = str(value.name)

    def __get__(self, instance, owner) -> BigFile: ...  # noqa: ANN001, D105 # type: ignore

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
    def validate(cls, v: FileCoercible) -> BigFile:
        """Validate the input array and convert it to a xr.DataArray."""

        if isinstance(v, str):
            v = open(v, "rb")

        if not isinstance(v, io.IOBase):
            raise ValueError("This needs to be a instance of a file")

        return cls(v)

    def __repr__(self) -> str:
        """Return a string representation of the BigFile scalar."""
        return f"BigFile({self.value})"


class ParquetLike:
    """A custom scalar for ensuring a common format to support write to the
    parquet api supported by mikro_next It converts the passed value into
    a compliant format..

    Five things count as parquet-like, and the difference matters at upload time
    rather than here (see :func:`mikro_next.io.upload._store_parquet_input`):

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
            "pip install 'mikro-next[sparse]'. Nothing else in this client needs it, which is why it is not "
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
                "`pip install mikro-next[mesh]`."
            ) from error

        if isinstance(v, MeshCollection):
            return cls(v)

        # The single-frame mistake is worth naming: under the previous wire format a caller
        # passed the catalog table here, and a pyarrow Table is exactly what they still have in
        # hand after building one.
        raise ValueError(
            f"This is uploaded as a fabriks collection -- one prefix holding the manifest, both "
            f"catalogs and every octree level -- so it takes a `fabriks.MeshCollection`, not a "
            f"{type(v).__name__}. Build one with `mikro_next.meshes.build_mesh_collection(objects)`."
        )

    def __repr__(self) -> str:
        """Return a string representation of the FabriksLike scalar.

        The counts and the grid rather than the value: a collection holds every object's
        geometry, and repr is what an error message and a log line are built out of.
        """
        manifest = self.value.manifest
        return f"FabriksLike({manifest.counts}, cellSize={manifest.grid.cell_size}, levels={manifest.grid.levels})"


#: What a caller may hand to a `FabriksLike` field. Deliberately narrow: everything a collection
#: could be built *from* is an argument to `build_mesh_collection`, not a value on the wire.
SporadikCoercible: TypeAlias = "Any | SporadikLike"
"""What :class:`SporadikLike` accepts: a `scipy.sparse` CSR or CSC matrix, or one already wrapped."""

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
                "with `pip install mikro-next[network]`."
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
    parquet api supported by mikro_next It converts the passed value into
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


class FileLike:
    """A custom scalar for ensuring a common format to support write to the
    parquet api supported by mikro_next It converts the passed value into
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
