"""
Traits for mikro

Traits are mixins that are added to every graphql type that exists on the mikro schema.
We use them to add functionality to the graphql types that extend from the base type.

Every GraphQL Model on Mikro gets a identifier and shrinking methods to ensure the compatibliity
with arkitekt. This is done by adding the identifier and the shrinking methods to the graphql type.
If you want to add your own traits to the graphql type, you can do so by adding them in the graphql
.config.yaml file.

"""

from __future__ import annotations

import os
from collections import deque
from collections.abc import Generator, Hashable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    NamedTuple,
    NoReturn,
    Protocol,
    Self,
    TypeVar,
    Union,
    cast,
)

import numpy as np
import xarray as xr
from dask.array.core import from_zarr  # type: ignore
from numpy.typing import NDArray
from pydantic import BaseModel, model_validator
from rath.scalars import ID, IDCoercible
from rath.origin import ContextBound
from rath.traits import FederationFetchable
from rath.turms.utils import get_attributes_or_error
from zarr.storage import StorePath

from .client import client_of
from .scalars import ArrayCoercible
from mikro.checks.arrays import check_dims_match_axes
from mikro.checks.arrays import check_layouts_agree
from mikro.io.chunking import lay_out_pyramid
from mikro.checks.sparse import check_against_store
from mikro.checks.sparse import check_axes
from mikro.checks.tables import TableDeclarationError
from mikro.checks.tables import file_columns_of
from mikro.checks.tables import resolve_columns
from mikro.scalars import axis_name
import shutil
from .vocabulary import (
    COMPOSABLE_KINDS,
    MATRIX_KINDS,
    QUALITATIVE_COLORMAP_VALUES,
    AxisSelection,
    AxisTypeName,
    Calibration,
    ResolvedTransformKind,
    TransformKind,
    Unit,
    WindowSelection,
    default_axis_type,
    enum_value,
    normalize_selection,
    normalize_window,
)

_Given = TypeVar("_Given")

TwoDArray = NDArray[np.generic]
OneDArray = NDArray[np.generic]

#: A point or a stack of them: a (N,) vector, a (K, N) array, or anything
#: `np.asarray` turns into one.
PointsLike = Union[Sequence[float], Sequence[Sequence[float]], NDArray[np.generic]]


ValueRelationName = Literal["IDENTICAL", "TRANSFORMED", "CATEGORIZED"]
"""A ``ValueRelation`` spelled by its value (``"TRANSFORMED"``), wherever one is taken."""


if TYPE_CHECKING:
    from datetime import datetime

    import duckdb

    from mikro.api.schema import (
        Annotation,
        AnnotationKind,
        ArrayLens,
        Axis,
        AxisInput,
        DimensionPartInput,
        AxisType,
        Chart,
        ChartPolicyInput,
        CoordinateAnchorInput,
        CoordinateSystem,
        CreateTransformationMutationCreateTransformationBase,
        DerivedFromInput,
        GetCoordinateGraphQueryCoordinateGraph,
        MeshLens,
        NetworkLens,
        PhysicalAxisInput,
        PlacementValidity,
        Scene,
        ScenePolicyInput,
        SparseLens,
        TableLens,
        TransformInput,
        WindowInput,
        ValueHistogramInput,
        ValueRelation,
    )
    from mikro.io.obstore import ParquetDatasetViaObstore
    from mikro.mikro import Mikro

    #: What `create_transformation` hands back: the shared base of every edge
    #: kind the mutation can return, the catch-all included.
    CreatedTransformation = CreateTransformationMutationCreateTransformationBase


class _LivesInItsOwnGrid(Protocol):
    """A dataset: it calls the space it lives in its *intrinsic* system, because
    that space is its own pixel grid."""

    @property
    def intrinsic_system(self) -> CoordinateSystem | None:
        """The dataset's own grid."""
        ...


class _LivesInASpace(Protocol):
    """A table dataset, a mesh collection, an annotation collection: containers
    whose coordinates are given in a space they simply name."""

    @property
    def coordinate_system(self) -> CoordinateSystem | None:
        """The space this container's coordinates are given in."""
        ...


#: Anything that can be registered into a space. Structural rather than a union
#: of the concrete models, because the operation-specific variants turms
#: generates are different classes with the same shape — what matters is that
#: the source can name its space, not which query returned it.
Registrable = Union[_LivesInItsOwnGrid, _LivesInASpace, "CoordinateSystemTrait"]


class AxisSource(Protocol):
    """A lens or a dataset: named axes, a shape, and a space that types them.

    Structural rather than a union of the concrete models, for the same reason
    `Registrable` is: the operation-specific variants turms generates are
    different classes with the same shape. It is also what lets a caller describe
    a candidate it built itself — the tests of `mikro.arkitekt.specs` stand in
    `SimpleNamespace` for a lens.

    Which field names the space is *not* part of the protocol: `_space_or_none`
    finds it whether it is called `space`, `coordinate_system` or
    `intrinsic_system`, and a source that names none is typed by the bare-name
    convention instead.
    """

    @property
    def axis_names(self) -> Sequence[str]:
        """The axis names, in array order."""
        ...

    @property
    def shape(self) -> Sequence[int]:
        """The extent of each axis, in array order."""
        ...


class HasNamedAxes:
    """A lens or a dataset: something whose axes have names, types and extents.

    `Lensable` and `DatasetTrait` both mix this in. They differ only in which
    field names the space their axes are typed by — `coordinate_system` on a
    lens, `intrinsic_system` on a dataset — and the `space` property each
    defines is the whole of that difference; everything here is written once
    against it.

    Every method reads `axis_names` and `shape`, which a partial fragment may
    not have selected. `get_attributes_or_error` names the missing field rather
    than failing with an `AttributeError` further in — the same contract
    `CoordinateSystemTrait.ndim` and `.units` already keep.
    """

    @property
    def axis_table(self) -> tuple[tuple[str, AxisTypeName, int], ...]:
        """``(name, axis_type, extent)`` per axis, in array order."""
        return axis_table(cast("AxisSource", self))

    @property
    def axis_types(self) -> tuple[AxisTypeName, ...]:
        """Per-axis semantic types in array order, as AxisType value strings."""
        return axis_types(cast("AxisSource", self))

    def axes_of_type(self, axis_type: AxisType | AxisTypeName) -> tuple[str, ...]:
        """The names of this object's axes of one AxisType, in array order.

        The runtime counterpart of the spec vocabulary: a function typed over
        ``TimelapseVolume`` should reduce over ``movie.axes_of_type(AxisType.TIME)``
        rather than hard-coding ``"t"`` — the spec guarantees the axis exists,
        not what it is called.
        """
        wanted = enum_value(axis_type)
        return tuple(
            name for name, found, _ in self.axis_table if found == wanted
        )

    def carried_axes(self, dims: Sequence[Hashable]) -> list[AxisInput]:
        """AxisInput for a derived array's dims, types carried from this source.

        For ``create_array_dataset(axes=...)`` on a dataset computed from this
        lens: an axis that survived the computation keeps the semantic type it
        had at the source instead of being re-guessed from its name, so the
        derived dataset's descriptors — and with them the action's Provides —
        stay true even for unconventionally named axes. A genuinely new dim
        falls back to the bare-name convention.
        """
        from mikro.api.schema import AxisInput, AxisType

        types = {name: found for name, found, _ in self.axis_table}
        names = [axis_name(dim) for dim in dims]
        return [
            AxisInput(
                name=name,
                type=AxisType(types[name] if name in types else default_axis_type(name)),
            )
            for name in names
        ]


class MikroFetchable(ContextBound, FederationFetchable):
    """A trait for Mikro Fetchable objects

    This trait allows to fetch an object from the mikro service using its ID.
    It is used to ensure that the object can be fetched from the mikro service.

    Fetched through a client (``Type.aexpand(id, client)``), an object remembers
    it, and what it fetches later goes through that same client.

    """

    @classmethod
    def fetch_origin(cls, client: "Mikro") -> dict:
        """Bind what is fetched by id to its client, as any other result is.

        Without it an object expanded through ``_entities`` would have its rath
        but no datalayer to read its data with, and no client to make its
        follow-up calls through.
        """
        return client._origin()


class HasParquestStoreTrait(ContextBound):
    """Table Trait

    Implements both identifier and shrinking methods.
    Also Implements the data attribute

    Attributes:
        data (pd.DataFrame): The data of the table.

    """

    @property
    def data(self) -> duckdb.DuckDBPyRelation:
        """The data of this table as a lazy DuckDB relation.

        The relation queries the parquet object directly on S3 through DuckDB's
        ``httpfs`` extension, so the table is never fully downloaded into memory.
        Filter/aggregate on the relation and call ``.df()`` to materialise just
        the result into a pandas DataFrame.

        Returns:
            duckdb.DuckDBPyRelation: A lazy relation over the parquet object.
        """
        store: HasParquetStoreAccesor = get_attributes_or_error(self, "store")
        return store.duckdb_relation


V = TypeVar("V")


class HasZarrStoreAccessor(ContextBound):
    """Zarr Store Accessor

    Allows to access the python zarr store of
    a ZarrStore object.


    """

    _openstore: StorePath | None = None

    @property
    def zarr_store(self) -> StorePath:
        """The zarr store of the ZarrStore object"""
        from mikro.io.download import open_zarr_store

        if self._openstore is None:
            id = get_attributes_or_error(self, "id")
            self._openstore = open_zarr_store(client_of(self), id)
        return self._openstore


class HasParquetStoreAccesor(ContextBound):
    """Parquet Store Accessor"""

    _dataset: ParquetDatasetViaObstore | None = None
    _duckdb_con: duckdb.DuckDBPyConnection | None = None
    _duckdb_rel: duckdb.DuckDBPyRelation | None = None

    @property
    def parquet_dataset(self) -> ParquetDatasetViaObstore:
        """The Parquet Dataset of the ParquetStore object"""
        from mikro.io.download import open_parquet_filesystem

        dataset = self._dataset
        if dataset is None:
            dataset = open_parquet_filesystem(
                client_of(self), get_attributes_or_error(self, "id")
            )
            self._dataset = dataset
        return dataset

    @property
    def duckdb_relation(self) -> duckdb.DuckDBPyRelation:
        """A lazy DuckDB relation over the parquet object, queried directly on S3.

        Reads through DuckDB's ``httpfs`` extension so the object is never fully
        downloaded. The backing connection is cached for the lifetime of this
        accessor (the relation is only valid while its connection is alive).
        """
        from mikro.io.download import open_parquet_duckdb

        relation = self._duckdb_rel
        if relation is None:
            self._duckdb_con, relation = open_parquet_duckdb(
                client_of(self), get_attributes_or_error(self, "id")
            )
            self._duckdb_rel = relation
        return relation


class HasDownloadAccessor(ContextBound):
    """Download Accessor"""

    _dataset: str | None = None

    def download(self, file_name: str | None = None) -> str:
        """Download the file from the backing store.

        Args:
            file_name (str | None): The name of the file to save the downloaded file as
                If None, the key from the store will be used as the file name.
        Returns:
            str: The path to the downloaded file
        """
        from mikro.io.download import download_file

        store_id, key = get_attributes_or_error(self, "id", "key")
        return download_file(client_of(self), store_id, file_name or key)

    @contextmanager
    def open(
        self,
        *,
        cache: bool | str = True,
        block_size: int | None = None,
        max_cached_blocks: int = 32,
    ) -> Generator[IO[bytes], None, None]:
        """Open the object as a seekable file, reading bytes on demand.

        Nothing transfers until the first read, and then only the block it lands in --
        so a reader that wants a header off a multi-gigabyte object transfers the
        header. Pass the result to any reader that accepts a file object: `tifffile`,
        `zarr`, `h5py` with ``driver="fileobj"``, `pyarrow.parquet`.

        Readers that want a *path* cannot use this. Once the path crosses into C or a
        JVM -- Bio-Formats, libtiff, anything that ``mmap``s -- a Python object with a
        `seek` method is not something the operating system can open. Those need
        `FileTrait.as_path`.

        This is also the wrong tool for reading most of an object. Each read is a round
        trip and formats seek a great deal, so a full pass becomes many small serialised
        requests where `download` would issue parallel multipart GETs at the full
        bandwidth of the link. Somewhere around a fifth of the bytes the two cross over.

        The handle is not thread-safe -- one file, one cursor. Readers that parallelise
        internally (`tifffile` with ``maxworkers > 1``, pyarrow with
        ``use_threads=True``) need a handle each. Reads block, so under asyncio this
        belongs in `asyncio.to_thread`.

        Blocks already fetched are kept, so a reader that comes back to an offset does
        not pay for it twice -- which container formats do constantly, jumping between
        their index and their data. The cache belongs to the handle and dies with it:
        two `open()` calls on the same file share nothing, so re-reading an object means
        holding one handle open rather than opening it again.

        Args:
            cache: ``True`` (default) keeps fetched blocks in a bounded LRU. ``False``
                fetches exactly what is asked for and keeps nothing -- for a reader that
                buffers on its own, or when memory matters more than requests. A string
                names an fsspec policy: ``"readahead"`` for a pure forward scan,
                ``"all"`` to pull the object once, ``"first"`` to pin only the header.
            block_size: Bytes fetched per request, and the granularity of the cache.
            max_cached_blocks: How many blocks the LRU holds. The memory ceiling is this
                times ``block_size`` -- 32 MB by default.
        """
        from mikro.io.remote import open_remote_file

        store_id = get_attributes_or_error(self, "id")
        handle = open_remote_file(
            client_of(self),
            store_id,
            block_size=block_size,
            cache=cache,
            max_cached_blocks=max_cached_blocks,
        )
        try:
            yield handle
        finally:
            handle.close()


class HasPresignedDownloadAccessor(ContextBound):
    """Presigned Download Accessor

    TODO: THis should probablry bre refactored to a more generic download accessor

    """

    _dataset: str | None = None

    def download(self, file_name: str | None = None) -> str:
        """Download the file from the presigned URL

        Args:
            file_name (str | None): The name of the file to save the downloaded file as
                If None, the key from the presigned URL will be used as the file name.
        Returns:
            str: The path to the downloaded file
        """
        from mikro.io.download import download_presigned_file

        url, key = get_attributes_or_error(self, "presigned_url", "key")
        return download_presigned_file(client_of(self), url, file_name or key)


class FileTrait:
    """A trait for file-like objects that can be downloaded
    because they have a big file store attached to them.
    """

    def download(self, file_name: str | None = None) -> str:
        """Download the file from the store

        Args:
            file_name (str | None): The name of the file to save the downloaded file as
                If None, the key from the store will be used as the file name.
        Returns:
            str: The path to the downloaded file
        """
        store: HasPresignedDownloadAccessor = get_attributes_or_error(self, "store")
        return store.download(file_name=file_name)

    @contextmanager
    def open(
        self,
        *,
        cache: bool | str = True,
        block_size: int | None = None,
        max_cached_blocks: int = 32,
    ) -> Generator[IO[bytes], None, None]:
        """Open the file as a seekable file object, reading bytes on demand.

        See `HasDownloadAccessor.open` for what this costs and when `as_path` is the
        better answer.
        """
        store: HasDownloadAccessor = get_attributes_or_error(self, "store")
        with store.open(
            cache=cache, block_size=block_size, max_cached_blocks=max_cached_blocks
        ) as handle:
            yield handle

    @contextmanager
    def as_path(self) -> Generator[str, None, None]:
        """Download the file and yield a real local path, deleting it on exit.

        What `open` cannot do: readers whose work happens in C or on a JVM take a path
        and open it themselves, so the bytes have to exist as a file. The whole object
        is transferred, which for those readers is not a choice.

        Unlike `temporary`, the download lands in a directory of its own rather than the
        working directory, chosen by ``MIKRO_SCRATCH_DIR`` and falling back to ``TMPDIR``.
        Nothing here knows how big the file is -- neither a `File` nor a `BigFileStore`
        carries a size -- so a caller who does should set that variable rather than find
        out that ``/tmp`` was a tmpfs by filling memory partway through.
        """
        from mikro.io.remote import download_to_scratch

        store_id, key = get_attributes_or_error(
            get_attributes_or_error(self, "store"), "id", "key"
        )

        # The file's own name, not the store key. Keys are opaque -- often a UUID with
        # no suffix -- and a reader that dispatches on the extension will refuse a
        # vendor file handed to it as `a3f9c2e1` that it would have opened as
        # `a3f9c2e1.tif`. The name is what the file was uploaded as.
        name = getattr(self, "name", None) or os.path.basename(key) or "download"
        # The File's own origin: it fetched the store it names.
        path = download_to_scratch(client_of(self), store_id, file_name=name)
        try:
            yield path
        finally:
            shutil.rmtree(os.path.dirname(path), ignore_errors=True)

    @contextmanager
    def temporary(self) -> Generator[str, None, None]:
        """Download the file and yield its local path, deleting it on exit.

        Kept for callers that already use it; `as_path` is the same idea with a
        deliberate download destination.
        """
        path = None
        try:
            path = self.download()
            yield path
        finally:
            if path and os.path.exists(path):
                os.remove(path)


class DataArrayTrait:
    """A trait for dataset-like objects that can be downloaded"""

    @property
    def data(self) -> xr.DataArray:
        """The data of this dataset as an xarray.DataArray"""
        store: HasZarrStoreAccessor = get_attributes_or_error(self, "store")
        array = from_zarr(store.zarr_store)
        return xr.DataArray(array)


def _as_calibration(axis: str, value: Any) -> Calibration:
    """Accept a bare ``(factor, unit)`` pair wherever a `Calibration` is wanted.

    `Calibration` is a NamedTuple, so a plain tuple looks interchangeable with one
    right up until `calibrate` reads ``.factor`` off it — and that happens *after*
    the dataset has uploaded, which is the expensive place to learn it.

    Only ``(factor, unit)`` — the reversed spelling is refused rather than repaired.
    `Calibration`'s own docstring is explicit that ``(0.2, "micrometer")`` and
    ``("micrometer", 0.2)`` are equally plausible and *only one of them works*, so
    quietly accepting both would discard the rule it exists to state. The order is
    the same as the NamedTuple's fields, and getting it wrong says so by name.
    """
    if isinstance(value, Calibration):
        return value
    if isinstance(value, str) or not isinstance(value, Sequence) or len(value) != 2:
        raise TypeError(
            f"The calibration for axis {axis!r} must be a Calibration(factor, unit) "
            f"or a (factor, unit) pair, got {value!r}"
        )
    factor, unit = value
    if isinstance(factor, bool) or not isinstance(factor, (int, float)):
        if isinstance(factor, (str, Unit)) and isinstance(unit, (int, float)):
            raise TypeError(
                f"The calibration for axis {axis!r} is the wrong way round: it "
                f"pairs (factor, unit), so write ({unit!r}, {str(factor)!r})"
            )
        raise TypeError(
            f"The calibration for axis {axis!r} must start with the factor, got {value!r}"
        )
    if not isinstance(unit, (str, Unit)):
        raise TypeError(
            f"The calibration for axis {axis!r} must pair the factor with a unit, got {value!r}"
        )
    return Calibration(float(factor), Unit(str(unit)))


class DatasetTrait(HasNamedAxes):
    """A trait for dataset-like objects that can be downloaded
    because they have a big file store attached to them.
    """

    @property
    def space(self) -> CoordinateSystem | None:
        """The space this dataset's axes are typed by: its own pixel grid.

        `None` when the query did not select `intrinsicSystem` — see
        `_space_or_none` for why that is an answer rather than a failure.
        """
        return getattr(self, "intrinsic_system", None)

    def stage(
        self,
        *,
        name: str | None = None,
        policy: "ScenePolicyInput | None" = None,
        mikro: "Mikro | None" = None,
    ) -> "Scene":
        """Stage this dataset: a renderable scene over its own pixel grid.

        ``dataset.intrinsic_system.stage(...)``, without the ``None`` the schema allows
        for a query that did not select ``intrinsicSystem``.

        Raises:
            ValueError: If this dataset was fetched without its intrinsic system.
        """
        intrinsic = self.space
        if intrinsic is None:
            raise ValueError(
                "This dataset was fetched without its intrinsic coordinate system "
                "(select intrinsicSystem), so there is no grid to stage."
            )
        return intrinsic.stage(name=name, policy=policy, mikro=mikro)

    def level_data(self, level: int = 0) -> xr.DataArray:
        """One pyramid level of this dataset, with its axes named.

        Level 0 is the full-resolution array; higher levels are coarser.
        """
        arrays = get_attributes_or_error(self, "data_arrays")
        dims = get_attributes_or_error(self, "axis_names")
        for array in arrays:
            if array.level == level:
                return xr.DataArray(from_zarr(array.store.zarr_store), dims=list(dims))
        raise ValueError(
            f"This dataset has no pyramid level {level}. Available levels: "
            f"{sorted(a.level for a in arrays)}"
        )

    def multi_scale_data(self) -> list[xr.DataArray]:
        """Every pyramid level of this dataset, finest first."""
        arrays = get_attributes_or_error(self, "data_arrays")
        dims = get_attributes_or_error(self, "axis_names")
        return [
            xr.DataArray(from_zarr(array.store.zarr_store), dims=list(dims))
            for array in sorted(arrays, key=lambda a: a.level)
        ]

    @property
    def data(self) -> xr.DataArray:
        """This dataset's full-resolution array, with its axes named."""
        return self.level_data(0)

    def calibrate(
        self,
        axes: Mapping[str, Calibration] | Sequence[PhysicalAxisInput],
        *,
        name: str = "physical",
        scale: Sequence[float] | None = None,
        translation: Sequence[float] | None = None,
        affine: Sequence[Sequence[float]] | None = None,
        epoch: datetime | None = None,
        mikro: "Mikro | None" = None,
    ) -> CoordinateSystem:
        """Give this dataset a physical size: a coordinate system carrying the
        units, and the edge registering the dataset's pixel grid into it.

        The primary form takes a mapping of every intrinsic axis name to a
        `Calibration` — ``{"z": Calibration(0.5, Unit("micrometer")), ...}`` —
        whose axis name and type are copied from the intrinsic axis, and whose
        factors become the edge's SCALE.
        Pass ``translation`` as well (a stage position, say) and the two fold
        into a single AFFINE, because an edge answers to exactly one kind.
        Power users can pass a sequence of ``PhysicalAxisInput`` directly,
        together with exactly one of ``scale=`` or ``affine=``.

        A physical space is not a kind of thing a dataset owns — it is an
        ordinary coordinate system with an edge into it — so this is one call,
        authored as one registration, rather than sugar on ingest:

            dataset.calibrate({d: Calibration(0.2, Unit("micrometer")) for d in "zyx"})

        Returns:
            The created coordinate system. The edge is authored with it.
        """
        from mikro.api.schema import (
            UNSET,
            PhysicalAxisInput,
            RegistrationPathInput,
        )

        intrinsic = get_attributes_or_error(self, "intrinsic_system")
        if intrinsic is None:
            raise ValueError(
                "This dataset has no intrinsic coordinate system to calibrate from"
            )

        intrinsic_axes = sorted(
            get_attributes_or_error(intrinsic, "axes"), key=lambda a: a.order
        )

        if isinstance(axes, Mapping):
            intrinsic_names = [a.name for a in intrinsic_axes]
            if set(axes) != set(intrinsic_names):
                raise ValueError(
                    f"The calibration must cover every intrinsic axis exactly: "
                    f"intrinsic axes are {intrinsic_names}, got {sorted(axes)}"
                )
            resolved = {name: _as_calibration(name, value) for name, value in axes.items()}
            factors = [float(resolved[a.name].factor) for a in intrinsic_axes]
            calibrated_axes = [
                PhysicalAxisInput(
                    name=a.name,
                    type=a.type,
                    unit=resolved[a.name].unit,
                    long_name=a.long_name,
                )
                for a in intrinsic_axes
            ]
            if affine is not None:
                if any(f != 1.0 for f in factors):
                    raise ValueError(
                        "When passing an explicit affine, all per-axis factors must "
                        "be 1.0 — otherwise the scaling would be applied twice"
                    )
                scale = None
            elif scale is not None:
                raise ValueError(
                    "Pass the factors in the axes mapping, not via scale=, when "
                    "using the mapping form"
                )
            else:
                scale = factors
        else:
            calibrated_axes = list(axes)
            if (scale is None) == (affine is None):
                raise ValueError(
                    "When passing PhysicalAxisInput objects directly, pass exactly "
                    "one of scale= or affine="
                )

        # One edge, one kind: a pixel size plus an offset is a single AFFINE, not
        # two stacked sugar fields.
        kind, scale, translation, affine = _infer_transform_kind(
            scale, translation, affine, None
        )

        registration = RegistrationPathInput(
            dataset=get_attributes_or_error(self, "id"),
            name=f"{getattr(self, 'name', 'dataset')} -> {name}",
            transform=_transform_member(
                kind, scale=scale, translation=translation, affine=affine
            ),
        )

        return client_of(self, mikro).create_coordinate_system(
            name=name,
            axes=calibrated_axes,
            registrations=[registration],
            epoch=epoch if epoch is not None else UNSET,
        )

    def lens(
        self,
        mikro: "Mikro | None" = None,
        **selections: AxisSelection,
    ) -> ArrayLens:
        """The lens over this dataset that pythonic per-axis selections describe.

        With no selections it is the dataset's whole lens — the tail every
        derivation edge starts from. Every dataset is created with one, so it is
        read, not made. Each keyword names an axis and selects along it: an
        ``int`` pins one index (a slice of size 1), a ``(start, stop)`` or
        ``(start, stop, step)`` tuple and a ``slice()`` object select a range.

        ``crop.lens(z=16, y=32)`` is the row through (z=16, y=32);
        ``source.lens(x=(0, 128))`` is the left half.

        A lens is one row per dataset and selection: asking twice answers with
        the same lens, and a selection that keeps everything is the whole lens.
        Its ``slices`` come back as the server normalized them, not as written.
        """
        from mikro.api.schema import SliceInput

        axis_names = getattr(self, "axis_names", None)
        slices: list[SliceInput] = []
        for axis, selection in selections.items():
            if axis_names is not None and axis not in axis_names:
                raise ValueError(
                    f"Invalid axis {axis!r} for dataset with axes {list(axis_names)}"
                )
            start, stop, step = normalize_selection(axis, selection)
            slices.append(SliceInput(axis=axis, start=start, stop=stop, step=step))

        client = client_of(self, mikro)
        dataset = get_attributes_or_error(self, "id")
        if not slices:
            whole = client.get_full_lens(dataset).full_lens
            if whole is not None:
                return whole
        # Also the answer for a dataset with no whole lens to read: the server
        # says what it cannot select over better than this could.
        return client.create_lens(dataset=dataset, slices=slices)

    def key_table(
        self,
        table: Registrable,
        *,
        name: str | None = None,
        validity: PlacementValidity | None = None,
        mikro: "Mikro | None" = None,
    ) -> CreatedTransformation:
        """Register this label dataset's voxels as the key into `table`: a BY_DIMENSION with a FIELD part.

        A label mask is exactly the case where the array being mapped is the
        array doing the mapping: its pixels consume this dataset's own axes and
        produce the table's coordinate axis (the object ids), so this dataset's
        intrinsic system is both the edge's input and the part's field. The
        axes the two share -- a timelapse's ``t`` -- are stated as an IDENTITY
        part, because nothing passes through unless a part says so. The key is
        many-to-one on purpose — an object is a set of voxels — and is never
        walked backwards.

        For a table that does not exist yet, prefer saying it on the column at
        creation -- ``ColumnInput(name="object_id", axis_type=AxisType.INDEX,
        identified_by=[DatasetIdentifiesInput(kind="DATASET", dataset=mask.id)])``
        in ``create_table_dataset``'s ``columns``. It says the same thing in the call
        that creates the table, so the pair is atomic, and the server derives the
        consumed and produced axes from the two spaces rather than taking them on
        trust. (It was a sibling ``keyed_by`` list until 2026-08-21, which named
        the source and not the axis it keyed.) This method is the standalone form,
        for keying a table that already exists.

        Args:
            table: The table dataset keyed by these labels (anything with a
                ``coordinate_system``), or that coordinate system directly.
            name: An optional name for the edge.
            validity: An optional PlacementValidity for the edge.

        Returns:
            The created key.
        """
        from mikro.api.schema import UNSET

        # The mixin has no fields of its own; the model it is mixed into has
        # `intrinsic_system`, which is what makes a dataset registrable.
        intrinsic = _space_of(cast("Registrable", self))

        target = _space_of(table)
        if getattr(target, "axes", None) is None:
            raise ValueError(
                "key_table needs the table's coordinate system with its axes "
                "selected in the query to order the output axes"
            )

        mine, theirs = _axis_names_in_order(intrinsic), _axis_names_in_order(target)
        shared = [axis for axis in mine if axis in theirs]
        parts = [_part("IDENTITY", shared, shared)] if shared else []
        parts.append(
            _part(
                "FIELD",
                [axis for axis in mine if axis not in theirs],
                [axis for axis in theirs if axis not in mine],
                field=get_attributes_or_error(intrinsic, "id"),
            )
        )
        transform = _transform_member("BY_DIMENSION", parts=parts)

        return client_of(self, mikro).create_transformation(
            input=get_attributes_or_error(intrinsic, "id"),
            output=get_attributes_or_error(target, "id"),
            transform=transform,
            name=name if name is not None else UNSET,
            validity=validity if validity is not None else UNSET,
        )


def _window_inputs(
    container: object, selections: Mapping[str, WindowSelection]
) -> list[WindowInput]:
    """The windows a container's ``lens()`` keywords describe, refused by axis name.

    The axis check runs only when the container says what its axes are: a table
    windows its coordinate columns and a collection the axes of its own space, and
    neither is selected as a flat list of names on its fragment, so for those the
    server names the axis it does not know.
    """
    from mikro.api.schema import WindowInput

    axis_names = getattr(container, "axis_names", None)
    windows: list[WindowInput] = []
    for axis, selection in selections.items():
        if axis_names is not None and axis not in axis_names:
            raise ValueError(f"Invalid axis {axis!r} for a container with axes {list(axis_names)}")
        low, high = normalize_window(axis, selection)
        windows.append(WindowInput(axis=axis, min=low, max=high))
    return windows


class TableDatasetLensTrait:
    """The lens over a table dataset: what a point, track or series layer draws."""

    def lens(self, mikro: "Mikro | None" = None, **windows: WindowSelection) -> TableLens:
        """The lens keeping these windows of the table's coordinate columns.

        With no windows it is the table's whole lens, which is what a layer over
        the whole table names: ``mikro.create_point_layer(scene=scene, lens=table.lens())``.
        ``table.lens(t=(0, 10))`` keeps the rows whose ``t`` lies in that range.
        One row per table and selection: asking twice answers with the same lens.
        """
        return client_of(self, mikro).create_table_lens(
            table_dataset=get_attributes_or_error(self, "id"),
            windows=_window_inputs(self, windows),
        )


class SparseDatasetTrait:
    """The lens over a sparse dataset: a slice of it is what a picker reads."""

    def lens(self, mikro: "Mikro | None" = None, **windows: WindowSelection) -> SparseLens:
        """The lens keeping these windows of the matrix's axes.

        A number pins one position, and pinning one on every axis the matrix
        identifies itself by is a *slice* -- one value per object, which is what
        a SPARSE colouring names: ``sparse_color_by(expression.lens(gene=4711))``.
        With no windows it is the whole lens. One row per matrix and selection, so
        every picker reading one gene shares one lens.

        A pinned position is checked against the axis' extent here, where the
        shape is held; whether the result is a slice a picker can read is the
        lens' own ``spec``, which `sparse_color_by` asks.
        """
        axis_names = list(getattr(self, "axis_names", None) or ())
        shape = list(getattr(self, "shape", None) or ())
        # Same condition the server guards its own bound check with: a store whose
        # rank disagrees with the declared axes has no extent to compare against.
        if len(axis_names) == len(shape):
            for axis, selection in windows.items():
                if axis not in axis_names or isinstance(selection, (tuple, list, bool)):
                    continue
                extent = int(shape[axis_names.index(axis)])
                if not 0 <= selection < extent:
                    raise ValueError(
                        f"Position {selection} along {axis!r} is outside 0..{extent - 1}. A position "
                        "is a row of the table that axis references, not an id of its own."
                    )
        return client_of(self, mikro).create_sparse_lens(
            sparse_dataset=get_attributes_or_error(self, "id"),
            windows=_window_inputs(self, windows),
        )


class MeshCollectionTrait:
    """The lens over a mesh collection: what a mesh layer draws."""

    def lens(self, mikro: "Mikro | None" = None, **windows: WindowSelection) -> MeshLens:
        """The lens keeping these windows of the collection's own space.

        With no windows it is the collection's whole lens:
        ``mikro.create_mesh_layer(scene=scene, lens=collection.lens())``.
        """
        return client_of(self, mikro).create_mesh_lens(
            mesh_collection=get_attributes_or_error(self, "id"),
            windows=_window_inputs(self, windows),
        )


class NetworkCollectionTrait:
    """The lens over a network collection: what a network layer draws."""

    def lens(self, mikro: "Mikro | None" = None, **windows: WindowSelection) -> NetworkLens:
        """The lens keeping these windows of the collection's own space.

        With no windows it is the collection's whole lens:
        ``mikro.create_network_layer(scene=scene, lens=collection.lens())``.
        """
        return client_of(self, mikro).create_network_lens(
            network_collection=get_attributes_or_error(self, "id"),
            windows=_window_inputs(self, windows),
        )


class CreateADatasetTrait:
    """Validation trait for the generic ``create_array_dataset`` input.

    Unlike the classic image path, the dataset path lets the user supply an
    arbitrarily-labelled array. This trait enforces that the labels are coherent
    at the model level: every dimension of the ``data`` array must have exactly
    one matching ``axis`` (by name), and every scale's array must share that same
    set of dimensions. Once they do, each level is given the chunk layout its axes
    imply, unless the caller set one.
    """

    @model_validator(mode="after")
    def _validate_dims_match_axes(self) -> Self:
        """Ensure the axes (and scale arrays) match the data array dims."""
        data = getattr(self, "data", None)
        axes = getattr(self, "axes", None)
        if data is None or axes is None:
            return self
        scales = getattr(self, "scales", None)
        check_dims_match_axes(data, axes, scales)

        # The declaration is the one place that sees the axis types and every level at once,
        # which is what a layout has to be chosen from: see `mikro.io.chunking`.
        levels = [data, *(scale.array for scale in sorted(scales or (), key=lambda s: s.level))]
        axis_types = {axis.name: str(getattr(axis.type, "value", axis.type)) for axis in axes}
        lay_out_pyramid(levels, axis_types)
        check_layouts_agree(levels, axis_types)
        return self


class CreateTableDatasetTrait(BaseModel):
    """Resolves `columns` against the frame, and checks the whole declaration against it.

    A table declares **every** column of its Parquet, in the file's order, with the DuckDB type
    name the server will read back off it -- and the server checks that declaration against the
    file. Every part of that is a fact about the file, so writing it out by hand is
    transcription, and the transcription is easy to get wrong in one specific way: `dtype` is
    DuckDB's vocabulary and a DataFrame speaks pandas', where a float64 is a ``double`` and a
    float32 is a ``float``.

    So the complete list is derived here from the frame's **Arrow** schema, which is what the
    upload actually writes, and what the caller passes in `columns` is merged onto it: a
    subset, in any order, with `dtype` omitted. A caller who states a `dtype` anyway is held to
    it -- an assertion about the data is worth checking, and this is the cheap side to check it
    on. The server checks again against the file itself; two statements about the same bytes,
    and the pair is worth more than either alone, because the client's copy is what the caller
    wrote and the server's is what arrived.

    Reading Arrow rather than ``frame.dtypes`` is not a detail. They disagree in ways that
    decide the answer: a ``category`` column is a ``VARCHAR``, a nullable ``Int64`` is a
    ``BIGINT``, and a column moved into the index may not reach the file at all.
    """

    @model_validator(mode="after")
    def _resolve_columns(self) -> Self:
        """Derive the declaration, merge the caller's onto it, and refuse what cannot describe this frame."""
        data = getattr(self, "data", None)
        if data is None:
            return self
        value = getattr(data, "value", data)

        try:
            file_columns = file_columns_of(value)
        except TableDeclarationError:
            # Our own refusals are the point of being here; only an unreadable object is a
            # reason to defer to the server.
            raise
        except Exception:
            # A path to a Parquet that does not exist yet, an object this cannot read: the
            # server still checks, so an unreadable frame is not a reason to refuse here.
            return self

        columns = resolve_columns(file_columns, self.columns or ())
        object.__setattr__(self, "columns", columns)
        # `object.__setattr__` does not touch `fields_set`, and `Mikro.execute` dumps with
        # `exclude_unset=True` -- so without this the resolved list would be dropped on the
        # way out for any caller who did not pass `columns` themselves.
        self.__pydantic_fields_set__.add("columns")
        return self


class CreateSparseDatasetTrait(BaseModel):
    """Checks a sparse dataset's declaration against its matrix, before the matrix moves.

    The sparse counterpart of :class:`CreateTableDatasetTrait`, and it makes the same argument
    for the same reason -- two statements about the same bytes, the caller's and the arrived
    one's -- with one difference in its favour. ``Mikro.execute`` validates (``_serialize``) and
    then hands the variables to the upload middleware, so every refusal below fires
    before a byte leaves the process. The server's copy of each fires after.

    One of them the server cannot make first at all: it compares the declared axis count
    against the store's ``shape``, and it reads that shape off a row written at
    ``finishSparseUpload``. Until then there is nothing to compare with. This side is holding
    the matrix, and a declaration that disagrees with it "places every lookup one position out
    and raises nothing" -- the server's own words for the failure.

    Refuses, never repairs. Every generated input is frozen, so a validator that rewrote a
    field would need ``object.__setattr__`` *and* a manual ``__pydantic_fields_set__.add`` --
    see :class:`CreateTableDatasetTrait`, where forgetting the second was a latent bug. There
    is nothing here worth paying that for.
    """

    @model_validator(mode="after")
    def _check_declaration(self) -> Self:
        """Check the axes, then check them against the matrix if one is in hand."""
        # `axes` is `... | None` with a GraphQL default of `[]`, and `()` is what the first
        # refusal is about -- so it is coerced rather than treated as "nothing to check",
        # which would skip the rank rule exactly where it applies.
        axes = getattr(self, "axes", None) or ()
        check_axes(axes)

        # Above this line is everything that is a statement about the axes alone. Below it is
        # the one that needs the matrix -- and a `store` that is not a `SporadikLike` (a bare
        # id, a value some other path built) is not a reason to refuse: the server checks too.
        layouts = getattr(getattr(self, "store", None), "layouts", None)
        if not layouts:
            return self
        check_against_store(axes, layouts)
        return self


class SparseAxisInputTrait(BaseModel):
    """Refuses the two axis declarations that otherwise fail unreadably or not at all.

    ``identifiedBy`` is a **list** because an axis can be keyed by more than one source -- a
    nucleus mask and a cell mask, each edge standing on its own. Handing it a single
    ``DatasetIdentifiesInput`` is the obvious mistake, and pydantic reports it as badly as it
    reports anything: a `BaseModel` iterates as ``(field, value)`` pairs, so the error names
    ``('kind', 'DATASET')`` and a ``model_attributes_type`` mismatch rather than the list.

    Coerced rather than refused? No. ``AxisInputTrait`` widens ``AxisInput`` to accept a bare
    string, but that widening is *declared* -- ``coercible_scalars``/``coercible_inputs`` in
    ``graphql.config.yaml`` makes turms publish ``AxisInput | str`` in the generated signature,
    so the type and the runtime agree. There is no such declaration here, and
    ``identified_by`` is typed ``tuple[IdentificationInput, ...]``. Accepting a bare model
    would leave a static checker flagging the very call the runtime had blessed, which is a
    lie about the type rather than an ergonomic.

    The second refusal is the empty list. The server refuses it too, and says why the best
    place is here: identification lives *on* the axis, so "identified at all" is a property of
    this input rather than a rule about it, "and the best time to catch it is at the keystroke
    rather than in a rank mismatch three functions later."
    """

    @model_validator(mode="before")
    @classmethod
    def _check_identifications(cls, value: Any) -> Any:  # noqa: ANN401
        if not isinstance(value, dict):
            return value
        # Both spellings: the field is `identified_by`, the alias is `identifiedBy`, and the
        # models are `populate_by_name=True`, so a caller may have written either.
        for key in ("identified_by", "identifiedBy"):
            if key not in value:
                continue
            entries = value[key]
            if isinstance(entries, BaseModel):
                raise ValueError(
                    f"`{key}` is a list, because an axis can be keyed by more than one source "
                    f"(a nucleus mask and a cell mask). Write "
                    f"{key}=[{type(entries).__name__}(...)]."
                )
            if entries is not None and not isinstance(entries, (str, bytes)) and not entries:
                raise ValueError(
                    f"`{key}` is empty. An axis of a sparse matrix is positions and nothing "
                    "else, so one that does not say what they are is one no source could ever "
                    "key -- there is no key onto it and no colouring along it. Name a "
                    "mask, a collection, or the table whose rows the positions are."
                )
        return value


class SparseColorByInputTrait(BaseModel):
    """The two rules a sparse colouring can be judged by from the input alone.

    A slice of a sparse matrix is a value per object, so it is **always measured**: it takes a
    colormap over its range. Nothing stores categories sparsely -- the zeros would be a
    category too -- which is why a qualitative colormap is refused rather than reinterpreted.

    On the input rather than in :func:`mikro.inputs.picker.sparse_color_by`, because
    ``label_render`` accepts entries that were built some other way and a guard in the builder
    is one anybody can walk past. The rest of what a sparse colouring can get wrong -- whether
    its lens pins exactly the axes the matrix identifies, each at one whole position, with a
    layout indexing one of them -- is the lens' ``spec``, and this input carries an id. That
    lives in the picker, which is where the caller holds the lens.
    """

    @model_validator(mode="after")
    def _a_slice_is_measured(self) -> Self:
        """Refuse a qualitative colormap, and an inverted window."""
        colormap = getattr(self, "colormap", None)
        name = enum_value(colormap)
        if name in QUALITATIVE_COLORMAP_VALUES:
            raise ValueError(
                f"A sparse colouring is measured -- a slice is a value per object, and "
                f"nothing stores categories sparsely, since the zeros would be a category "
                f"too -- so it takes a colormap over its range, and {name!r} is qualitative."
            )

        # Not `not max > min`: a degenerate window is legal server-side, and being stricter
        # than the server is the one thing a client-side check must not be.
        low, high = getattr(self, "min", None), getattr(self, "max", None)
        if low is not None and high is not None and low > high:
            raise ValueError(f"the colormap window is inverted: min={low} is above max={high}.")
        return self


class GraphColorByInputTrait(BaseModel):
    """The two rules a graph colouring can be judged by from the input alone.

    A per-node graph attribute -- Strahler order, degree, depth, a radius, a writer's own
    column -- is **always measured**: ordered values every one, so a qualitative palette is
    refused rather than reinterpreted, `component` included (one rule, no per-semantics
    branch; the server applies the same one). Whether the *attribute exists* needs the
    collection's manifest and stays server-side, exactly as a sparse entry's reachability
    does -- this input carries only a name.

    On the input rather than in :func:`mikro.inputs.picker.graph_color_by`, for
    :class:`SparseColorByInputTrait`'s reason: entries built some other way still pass
    through here.
    """

    @model_validator(mode="after")
    def _a_metric_is_measured(self) -> Self:
        """Refuse a qualitative colormap, and an inverted window."""
        colormap = getattr(self, "colormap", None)
        name = enum_value(colormap)
        if name in QUALITATIVE_COLORMAP_VALUES:
            raise ValueError(
                f"A graph colouring is measured -- a per-node metric is an ordered value -- "
                f"so it takes a colormap over its range, and {name!r} is qualitative."
            )

        # Not `not max > min`: a degenerate window is legal server-side, and being stricter
        # than the server is the one thing a client-side check must not be.
        low, high = getattr(self, "min", None), getattr(self, "max", None)
        if low is not None and high is not None and low > high:
            raise ValueError(f"the colormap window is inverted: min={low} is above max={high}.")
        return self


class RGBAColorInputTrait(BaseModel):
    """Completes a colour to RGBA, and rejects one that cannot be completed.

    The server takes ``color`` as exactly four components — red, green, blue,
    alpha — but the field arrives here as a bare ``[Int!]``, so nothing in the
    generated model says so and a three-component colour travels all the way to
    the backend before being refused. Writing ``(0, 255, 255)`` for cyan is the
    obvious thing to write, and the round trip is a poor way to find out it is
    wrong.

    So a three-component colour is completed with an opaque alpha, which is what
    the caller meant, and anything else fails here with the length it actually
    had::

        TransferFunctionInput(color=(0, 255, 255))       # -> (0, 255, 255, 255)
        TransferFunctionInput(color=(0, 255, 255, 128))  # left alone
        TransferFunctionInput(color=(0, 255))            # ValueError

    Alpha is 255 rather than 1.0 because these components are 0-255 integers.
    Nothing in the schema types the field as a colour, which is why this exists.
    """

    @model_validator(mode="before")
    @classmethod
    def _complete_rgba(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        color = value.get("color")
        if color is None or isinstance(color, (str, bytes)):
            return value
        try:
            components = [int(c) for c in color]
        except TypeError:
            return value  # not a sequence; let the field's own validation speak
        if len(components) == 3:
            components.append(255)
        elif len(components) != 4:
            raise ValueError(
                f"color is an RGBA colour, so it takes 3 components (alpha is "
                f"completed to 255) or 4, but got {len(components)}: {list(color)}"
            )
        return {**value, "color": components}


class AxisInputTrait(BaseModel):
    """Lets a structural axis be given as a bare name.

    ``axes=["z", "y", "x"]`` is enough for the common case: the axis type is
    inferred from the name (``t`` -> TIME, ``c`` -> CHANNEL, everything else
    SPACE). Pass a full ``AxisInput`` for anything the convention gets wrong.
    """

    @model_validator(mode="before")
    @classmethod
    def _coerce_bare_name(cls, value: Any) -> Any:
        if isinstance(value, (dict, BaseModel)) or not isinstance(value, Hashable):
            return value
        # A bare name: a str, or any hashable xarray dim.
        name = axis_name(value)
        return {"name": name, "type": default_axis_type(name)}


class MetricTargetInputTrait(BaseModel):
    """Lets the object a metric is about be given as the object itself.

    ``mikro.create_metric(target=dataset, key="my_app/mean", magnitude=3.2, unit="µm")``,
    or ``target=lens.dataset``: every class generated for a type the server identifies
    carries the structure it travels as (``__identifier__``, from the schema's
    ``@identified``), a nested selection included. Which structures a metric may be
    about is the server's to say, and it says so in prose: an object of any other
    identified structure is handed on, not refused here.

    The widening is declared (``coercible_inputs``), so the top-level ``target=`` of
    ``create_metric`` is typed to take the object. A target nested in a ``MetricInput``
    (``create_metrics``) is coerced too, but its field stays typed ``MetricTargetInput``,
    as a nested ``AxisInput`` does: a checker flags the object there.
    """

    @model_validator(mode="before")
    @classmethod
    def _coerce_object(cls, value: Any) -> Any:
        if isinstance(value, (dict, cls)):
            return value
        # Read off the class: a nested selection shares no base with the fragment of
        # its type, so only the stamp itself says what it is.
        identifier = getattr(type(value), "__identifier__", None)
        if identifier is None:
            raise ValueError(
                f"A metric target is an annotation or a dataset, or a MetricTargetInput, "
                f"not a {type(value).__name__}, which no structure identifies"
            )
        return {"identifier": identifier, "object": get_attributes_or_error(value, "id")}


class ValueHistogramInputTrait(BaseModel):
    """Builds the render metadata of an array in one call."""

    @classmethod
    def from_array(cls, array: ArrayCoercible, bins: int = 256) -> ValueHistogramInput:
        """Robust min/max, a 1st/99th-percentile contrast window and a UI
        histogram, computed from the array itself.

        The percentiles ignore hot/dead pixels so the default contrast sliders
        land somewhere sensible; compute on the base-resolution array.

        Args:
            array: Anything ``np.asarray`` accepts (numpy, xarray, dask).
            bins: The number of histogram bins.
        """
        from mikro.api.schema import ValueHistogramInput

        clean = np.asarray(array)
        clean = clean[np.isfinite(clean)]
        if clean.size == 0:
            raise ValueError(
                "Cannot build a value histogram of an array with no finite values"
            )
        lo, hi = float(clean.min()), float(clean.max())
        p1, p99 = np.percentile(clean, [1, 99])
        counts, edges = np.histogram(clean, bins=bins, range=(lo, hi))
        return ValueHistogramInput(
            min=lo,
            max=hi,
            p1=float(p1),
            p99=float(p99),
            bins=edges.tolist(),
            histogram=counts.tolist(),
        )


class CoordinateAnchorInputTrait(BaseModel):
    """Convenience constructors for coordinate anchors."""

    @classmethod
    def histogram_anchor(
        cls,
        array: ArrayCoercible,
        dims: Sequence[str] | None = None,
        bins: int = 256,
        at: Mapping[str, int] | None = None,
    ) -> CoordinateAnchorInput:
        """An anchor carrying the array's value histogram.

        A histogram is a single fact about the array it was computed from, so it
        hangs off one point rather than being repeated per position. By default
        that point is the origin — voxel (0, ..., 0) — which is what a histogram
        of the whole array wants.

        Pass ``at`` to say the fact is about one position instead: the usual case
        is one contrast window per channel, where each anchor is keyed by the
        channel it describes and the array handed in is that channel's slice::

            [CoordinateAnchorInput.histogram_anchor(arr.isel(c=i), at={"c": i})
             for i in range(arr.sizes["c"])]

        Args:
            array: The array to summarise. An ``xr.DataArray`` brings its own
                dims; anything else needs ``dims`` spelled out.
            dims: The axis names to pin at 0, in array order. Ignored when ``at``
                is given.
            bins: The number of histogram bins.
            at: Axis name -> position this anchor sits at.
        """
        from mikro.api.schema import (
            AxisAnchorInput,
            CoordinateAnchorInput,
            ValueHistogramInput,
        )

        if at is not None:
            anchors = [
                AxisAnchorInput(axis=str(axis), value=int(value))
                for axis, value in at.items()
            ]
        else:
            if dims is None:
                dims = getattr(array, "dims", None)
                if dims is None:
                    raise ValueError(
                        "dims= is required when the array does not carry its own "
                        "dimension names (pass an xr.DataArray, or spell them out)"
                    )
            anchors = [AxisAnchorInput(axis=str(d), value=0) for d in dims]

        return CoordinateAnchorInput(
            axis_anchors=anchors,
            value_histogram=ValueHistogramInput.from_array(array, bins=bins),
        )

    @classmethod
    def histogram_anchors(
        cls,
        # Narrower than its siblings on purpose: this one splits along a *named*
        # axis, so it needs an array that carries its own dimension names.
        array: xr.DataArray,
        axis: str = "c",
        bins: int = 256,
    ) -> list[CoordinateAnchorInput]:
        """One histogram anchor per position along ``axis`` — the whole
        ``anchors=`` argument in one call.

        A contrast window is per channel: a nuclear stain and a brightfield
        channel in the same stack share no sensible range, so one histogram over
        both describes neither. Each anchor is therefore computed from just that
        position's slice and keyed by it, which is what gives the frontend a
        usable default slider per channel.

        When the array has no such axis there is nothing to split on, so this
        falls back to a single anchor at the origin covering the whole array —
        meaning callers do not have to branch on whether the data has channels::

            anchors=CoordinateAnchorInput.histogram_anchors(arr)

        Args:
            array: An ``xr.DataArray`` to summarise.
            axis: The axis to produce one anchor per position of.
            bins: The number of histogram bins.
        """
        dims = getattr(array, "dims", None)
        if dims is None:
            raise ValueError(
                "histogram_anchors needs an array carrying its own dimension "
                "names (pass an xr.DataArray)"
            )
        if axis not in dims:
            return [cls.histogram_anchor(array, bins=bins)]
        return [
            cls.histogram_anchor(array.isel({axis: index}), bins=bins, at={axis: index})
            for index in range(array.sizes[axis])
        ]


class Lensable(HasNamedAxes):
    """What an array lens can do: read its selection and derive data from it."""

    @property
    def space(self) -> CoordinateSystem | None:
        """The space this lens' axes are typed by: the one its slices cut out.

        `None` when the query did not select `coordinateSystem` — see
        `_space_or_none` for why that is an answer rather than a failure.
        """
        return getattr(self, "coordinate_system", None)

    @property
    def data(self) -> xr.DataArray:
        """Download the file from the store

        Args:
            file_name (str | None): The name of the file to save the downloaded file as
                If None, the key from the store will be used as the file name.
        Returns:
            str: The path to the downloaded file
        """
        from mikro.api.schema import Slice

        store: DatasetTrait = get_attributes_or_error(self, "dataset")
        slices: list[Slice] = get_attributes_or_error(self, "slices")

        data = store.data

        for lens_slice in slices:
            if lens_slice.axis not in data.dims:
                raise ValueError(
                    f"Invalid slice dimension {lens_slice.axis} for data with dimensions {data.dims}"
                )
            if lens_slice.start is None and lens_slice.stop is None:
                continue

            data = data.isel(
                {
                    lens_slice.axis: slice(
                        lens_slice.start,
                        lens_slice.stop,
                        lens_slice.step,
                    )
                }
            )  # type: ignore

        return data

    def draw(
        self,
        kind: AnnotationKind,
        vectors: TwoDArray,
        name: str | None = None,
        collection: IDCoercible | None = None,
        scene: IDCoercible | None = None,
    ) -> Annotation:
        """Draw an annotation on the data of this lens

        The vectors are interpreted in the lens' own coordinate system, which already
        encodes the crop and step of its slices, so no dimension mapping is needed.
        Categorical axes that the lens pins to a single index (a channel) become
        pinned coordinates on the annotation.

        The annotation is drawn into `collection` or onto `scene` (at most one of
        the two). If neither is given, a new annotation collection is created on
        the lens' coordinate system.

        Args:
            kind (AnnotationKind): The kind of the annotation to draw
            vectors (TwoDArray): A 2D array of vectors to draw the annotation with. The last
                dimension holds the space components of each vertex, in the axis order of
                the lens: z, y, x on a volume, y, x on a plane.
            name (str | None): An optional name for the annotation
            collection (str | None): The ID of the annotation collection to draw into
            scene (str | None): The ID of the scene to draw onto

        Returns:
            Annotation: The drawn annotation
        """
        from mikro.api.schema import (
            AxisInput,
            AxisType,
            CoordinateInput,
            CoordinateSystemDerivedFromInput,
            IdentityTransformInput,
            Slice,
        )

        if collection is not None and scene is not None:
            raise ValueError("Pass either a collection or a scene, not both")

        coordinate_system = get_attributes_or_error(self, "coordinate_system")
        slices: list[Slice] = get_attributes_or_error(self, "slices")

        discrete_dims = {
            axis.name
            for axis in coordinate_system.axes
            if axis.type == AxisType.CHANNEL
        }

        coordinates = [
            CoordinateInput(name=lens_slice.axis, value=lens_slice.start)
            for lens_slice in slices
            if lens_slice.axis in discrete_dims and lens_slice.start is not None
        ]

        if collection is None and scene is None:
            # A collection owns a coordinate system rather than sharing the
            # lens', so it is created with the lens' axes and an identity edge
            # back to it: the shapes are drawn on that very grid, without the
            # two systems being made one.
            collection = client_of(self).create_annotation_collection(
                name=name or f"Drawings on {coordinate_system.name}",
                axes=[
                    AxisInput(
                        name=axis.name, type=axis.type, long_name=axis.long_name
                    )
                    for axis in coordinate_system.axes
                ],
                derived_from=[
                    CoordinateSystemDerivedFromInput(
                        coordinate_system=coordinate_system.id,
                        transform=IdentityTransformInput(),
                    )
                ],
            ).id

        return client_of(self).create_annotation(
            collection=collection,
            scene=scene,
            vectors=vectors,
            kind=kind,
            name=name,
            coordinates=coordinates,
        )

    def derive(
        self,
        *,
        kind: TransformKind | Enum | None = None,
        scale: Sequence[float] | None = None,
        translation: Sequence[float] | None = None,
        affine: Sequence[Sequence[float]] | None = None,
        input_axes: Sequence[str] | None = None,
        output_axes: Sequence[str] | None = None,
        parts: Sequence["DimensionPartInput"] | None = None,
        value_relation: ValueRelation | ValueRelationName | None = None,
        reason: str | None = None,
    ) -> DerivedFromInput:
        """A derivation edge pointing back into this lens, for a dataset about
        to be created from what the lens frames.

        The result goes into ``create_array_dataset(derived_from=[...])``. When
        `kind` is omitted it is inferred from which parameters are given:
        `affine` -> AFFINE, `scale` -> SCALE, `translation` -> TRANSLATION
        (scale and translation together fold into one AFFINE), `input_axes` ->
        MAP_AXIS, nothing -> IDENTITY; a BY_DIMENSION is its `parts` (see
        `_part`). An IDENTITY derivation states its
        transform like any other — the data is in the lens' space as-is, and
        *saying* so is what places it. Omitting the transform is the opposite
        claim: it makes the edge UNMAPPABLE, lineage without geometry, which is
        what a table of per-object measurements wants and what a same-grid
        computation never does.

        `value_relation` states what the derivation did to the *values* —
        orthogonal to the spatial kind: IDENTICAL for a cut, TRANSFORMED for a
        recomputation, CATEGORIZED for a labelling. `reason` is recorded only
        on an UNMAPPABLE derivation.
        """
        # `DerivedFromInput` is a union discriminated on the *source* kind, so it
        # is a typing alias and cannot be called. This method hangs off a lens, so
        # the member is the lens one — the transform kind (IDENTITY, SCALE, ...)
        # is a separate discriminator, carried inside `transform`.
        from mikro.api.schema import LensDerivedFromInput, ValueRelation

        if kind is None:
            kind, scale, translation, affine = _infer_transform_kind(
                scale, translation, affine, input_axes
            )

        transform = _transform_member(
            kind,
            scale=scale,
            translation=translation,
            affine=affine,
            input_axes=input_axes,
            output_axes=output_axes,
            parts=parts,
            reason=reason,
        )

        return LensDerivedFromInput(
            lens=get_attributes_or_error(self, "id"),
            transform=transform,
            value_relation=ValueRelation(value_relation) if value_relation is not None else None,
        )

    def derive_identity(
        self,
        value_relation: ValueRelation | ValueRelationName | None = None,
    ) -> DerivedFromInput:
        """An IDENTITY derivation edge: same axes, same voxels.

        The classic case is a dense computation on the same grid — a
        segmentation (`value_relation=CATEGORIZED`), a deconvolution
        (`value_relation=TRANSFORMED`). Why the computation happened belongs to
        task provenance, not to the edge — the edge carries no reason.
        """
        return self.derive(kind="IDENTITY", value_relation=value_relation)

    def derive_translation(
        self,
        offset: Sequence[float],
        *,
        value_relation: ValueRelation | ValueRelationName | None = None,
    ) -> DerivedFromInput:
        """A TRANSLATION derivation edge: same axes, shifted origin — a crop.

        `offset` is forward, derived -> source: the derived dataset's voxel
        (0, ..., 0) lands on this position in the lens' space. A crop cuts but
        does not compute, so `value_relation` defaults to IDENTICAL (statistics
        transfer); override it when the values were also recomputed.
        """
        from mikro.api.schema import ValueRelation

        if value_relation is None:
            value_relation = ValueRelation.IDENTICAL
        return self.derive(
            kind="TRANSLATION",
            translation=offset,
            value_relation=value_relation,
        )

    def derive_projection(
        self,
        axes: Sequence[str],
        *,
        value_relation: ValueRelation | ValueRelationName | None = None,
    ) -> DerivedFromInput:
        """A rank-dropping BY_DIMENSION derivation edge keeping only `axes`.

        One IDENTITY part over the kept axes IS the map; the axes no part names
        are the dropped ones — a line through a volume keeps ``["x"]``, a
        projection keeps ``["y", "x"]``. *Where* the kept axes sit along the
        dropped ones is the lens' business: slice the lens, don't restate it here.
        """
        return self.derive(kind="BY_DIMENSION", parts=[_part("IDENTITY", axes, axes)], value_relation=value_relation)


def _normalize_kind(kind: ResolvedTransformKind | Enum) -> ResolvedTransformKind:
    """Normalize a transformation kind to its plain string value.

    `use_enum_values=True` means a kind read off a model may be either the enum
    or its value, and the two compare unequal against a bare literal.
    """
    return enum_value(kind)


def _axis_names_in_order(system: CoordinateSystemTrait) -> list[str]:
    """The axis names of a coordinate system, ordered by their `order` field."""
    axes = get_attributes_or_error(system, "axes")
    return [a.name for a in sorted(axes, key=lambda a: a.order)]


def _space_or_none(source: Registrable | AxisSource) -> CoordinateSystem | None:
    """The coordinate system a source lives in, or None when it names none.

    The *optional* half of the pair: a missing system is an answer here, not a
    failure. `axis_table` depends on that — a lens whose query did not select
    `coordinateSystem` still has axis names, and the bare-name convention types
    them. `_space_of` is the raising half, for the callers that genuinely
    cannot proceed without a space.

    `source.space` is the answer whenever the source carries a trait that
    defines it. The `getattr` chain behind it is not dead code: a mesh
    collection and an annotation collection are `Registrable` and name their
    space in `coordinate_system`, but carry no trait at all, and so have no
    `space`. `coordinate_system` is tried first, which is the order
    `axis_table` has always used; no type carries both fields non-None.
    """
    space = getattr(source, "space", None)
    if space is not None:
        return cast("CoordinateSystem", space)
    for field in ("coordinate_system", "intrinsic_system"):
        found = getattr(source, field, None)
        if found is not None:
            return cast("CoordinateSystem", found)
    # A system passed directly: it has axes, and it is not a container.
    if getattr(source, "axes", None) is not None:
        return cast("CoordinateSystem", source)
    return None


def _space_of(source: Registrable) -> CoordinateSystem:
    """The coordinate system a registrable source lives in.

    Data lives in exactly one space and says so itself, but which field says it
    depends on the container: a dataset calls its own grid ``intrinsic_system``,
    while a table dataset, a mesh collection and an annotation collection each
    call theirs ``coordinate_system``. A coordinate system is its own space.

    Raises:
        ValueError: If the source has no space, or the query did not select it.
    """
    space = _space_or_none(source)
    if space is not None:
        return space
    raise ValueError(
        f"{getattr(source, 'name', source)!r} has no coordinate system, so there "
        f"is nothing to register. Either it genuinely lives in no space, or the "
        f"query did not select `intrinsicSystem` / `coordinateSystem` on it."
    )


def axis_table(source: AxisSource) -> tuple[tuple[str, AxisTypeName, int], ...]:
    """``(name, axis_type, extent)`` per axis of a lens or a dataset, in array order.

    Types come from the source's coordinate system when it was fetched with
    one; otherwise the bare-name convention (t/time -> TIME, c/channel ->
    CHANNEL, else SPACE).

    A function as well as `HasNamedAxes.axis_table` because callers outside the
    model hierarchy use it structurally — `mikro.arkitekt.specs` describes
    candidates that need only name a space, and its tests build them out of
    `SimpleNamespace`.
    """
    names = tuple(get_attributes_or_error(source, "axis_names"))
    shape = tuple(get_attributes_or_error(source, "shape"))
    system = _space_or_none(source)
    types: tuple[AxisTypeName, ...]
    if system is not None:
        axes = sorted(system.axes, key=lambda axis: axis.order)
        # `use_enum_values` means the field may hold either the enum or its value.
        types = tuple(enum_value(axis.type) for axis in axes)
    else:
        types = tuple(default_axis_type(name) for name in names)
    return tuple(zip(names, types, shape))


def axis_types(source: AxisSource) -> tuple[AxisTypeName, ...]:
    """Per-axis semantic types in array order, as AxisType value strings."""
    return tuple(axis_type for _, axis_type, _ in axis_table(source))


def _homogeneous_from_rows(rows: np.ndarray, ndim_in: int | None) -> np.ndarray:
    """Turn an M x (N+1) affine (last column translation) into a homogeneous
    (M+1) x (N+1) matrix. A square N x N matrix (a rotation given without a
    translation column) gets a zero translation column appended first."""
    rows = np.asarray(rows, dtype=float)
    if rows.ndim != 2:
        raise ValueError(f"Expected a 2D affine matrix, got shape {rows.shape}")
    m, cols = rows.shape
    if ndim_in is not None and cols == ndim_in:
        rows = np.hstack([rows, np.zeros((m, 1))])
    n = rows.shape[1] - 1
    bottom = np.zeros((1, n + 1))
    bottom[0, n] = 1.0
    return np.vstack([rows, bottom])


def _apply_homogeneous(matrix: np.ndarray, points: PointsLike) -> np.ndarray:
    """Apply a homogeneous (M+1) x (N+1) matrix to an (K, N) or (N,) point array."""
    pts = np.atleast_2d(np.asarray(points, dtype=float))
    n = matrix.shape[1] - 1
    if pts.shape[1] != n:
        raise ValueError(
            f"Points have dimension {pts.shape[1]}, but the transformation expects {n}"
        )
    out = (matrix @ np.hstack([pts, np.ones((len(pts), 1))]).T).T[:, :-1]
    return out[0] if np.ndim(points) == 1 else out


def _infer_transform_kind(
    scale: Sequence[float] | None,
    translation: Sequence[float] | None,
    affine: Sequence[Sequence[float]] | None,
    input_axes: Sequence[str] | None,
) -> tuple[
    TransformKind,
    Sequence[float] | None,
    Sequence[float] | None,
    Sequence[Sequence[float]] | None,
]:
    """Infer the transformation kind from which parameters were given.

    Returns (kind, scale, translation, affine); a combined scale + translation
    is folded into a single affine.
    """
    if affine is not None:
        if scale is not None or translation is not None:
            raise ValueError("Pass either affine= or scale=/translation=, not both")
        return "AFFINE", None, None, affine
    if scale is not None and translation is not None:
        if len(scale) != len(translation):
            raise ValueError(
                f"scale has {len(scale)} entries but translation has {len(translation)}"
            )
        folded = np.hstack(
            [
                np.diag(np.asarray(scale, dtype=float)),
                np.asarray(translation, dtype=float)[:, None],
            ]
        ).tolist()
        return "AFFINE", None, None, folded
    if scale is not None:
        return "SCALE", scale, None, None
    if translation is not None:
        return "TRANSLATION", None, translation, None
    if input_axes is not None:
        return "MAP_AXIS", None, None, None
    return "IDENTITY", None, None, None


def _part(
    kind: Literal["IDENTITY", "SCALE", "TRANSLATION", "AFFINE", "ROTATION", "FIELD"],
    input_axes: Sequence[str],
    output_axes: Sequence[str],
    *,
    scale: Sequence[float] | None = None,
    translation: Sequence[float] | None = None,
    affine: Sequence[Sequence[float]] | None = None,
    field: IDCoercible | None = None,
    unit: str | None = None,
    min: float | None = None,
    max: float | None = None,
) -> "DimensionPartInput":
    """One part of a BY_DIMENSION: `input_axes` onto `output_axes`, by one kind.

    Each kind reads only its own parameter -- SCALE `scale`, TRANSLATION
    `translation`, AFFINE and ROTATION `affine`, FIELD `field` (the array's
    coordinate system) with its values' `unit` and declared `min`/`max` -- and
    the server refuses any other. An IDENTITY part is a pass-through, stated.
    """
    from mikro.api.schema import DimensionPartInput, FieldInput, PartKind

    return DimensionPartInput(
        kind=PartKind(kind),
        input_axes=tuple(input_axes),
        output_axes=tuple(output_axes),
        scale=None if scale is None else tuple(float(s) for s in scale),
        translation=None if translation is None else tuple(float(t) for t in translation),
        affine=None if affine is None else tuple(tuple(float(v) for v in row) for row in affine),
        field=None if field is None else FieldInput(system=field, unit=unit, min=min, max=max),
    )


def _transform_member(
    kind: TransformKind | Enum,
    *,
    scale: Sequence[float] | None = None,
    translation: Sequence[float] | None = None,
    affine: Sequence[Sequence[float]] | None = None,
    input_axes: Sequence[str] | None = None,
    output_axes: Sequence[str] | None = None,
    reason: str | None = None,
    parts: Sequence["DimensionPartInput"] | None = None,
) -> TransformInput:
    """Build the tagged member input for a transformation ``kind``.

    The schema publishes ``TransformInput`` as a tagged union of per-kind
    member inputs, each the strict truth about which fields its kind reads —
    anything else is rejected, never dropped. This is where the flat parameter
    surface of the sugar methods narrows to the kind's own fields.

    Every kind builds a member, IDENTITY included — it carries nothing but its
    own discriminator, which is the whole point: omitting the transform is not
    a way to say "same grid", it is how the schema says UNMAPPABLE. The two are
    opposites, so an identity that returned ``None`` here did not lose
    precision, it inverted the claim.
    """
    from mikro.api import schema

    # Wider than the parameter: a caller reaching here untyped may still hand in
    # a resolved kind, and the dispatch below refuses it by name rather than by
    # falling through to the wrong member.
    normalized: ResolvedTransformKind = _normalize_kind(kind)

    if reason is not None and normalized != "UNMAPPABLE":
        raise ValueError(
            f"reason is only recorded on an UNMAPPABLE edge, not on a {normalized}: "
            "the coordinate graph reads nothing else from it"
        )

    if parts is not None and normalized != "BY_DIMENSION":
        raise ValueError(f"A {normalized} transformation takes no parts: only a BY_DIMENSION maps its axes part by part")

    def require(name: str, value: _Given | None) -> _Given:
        """The value, or a refusal naming the parameter the kind needs."""
        if value is None:
            raise ValueError(f"A {normalized} transformation needs {name}=")
        return value

    if normalized == "IDENTITY":
        given = (scale, translation, affine, input_axes, output_axes)
        if any(value is not None for value in given):
            raise ValueError("An IDENTITY transformation takes no parameters")
        return schema.IdentityTransformInput()
    if normalized == "SCALE":
        return schema.ScaleTransformInput(
            scale=tuple(float(s) for s in require("scale", scale))
        )
    if normalized == "TRANSLATION":
        return schema.TranslationTransformInput(
            translation=tuple(float(t) for t in require("translation", translation))
        )
    if normalized == "AFFINE":
        return schema.AffineTransformInput(
            affine=np.asarray(require("affine", affine), dtype=float).tolist()
        )
    if normalized == "ROTATION":
        return schema.RotationTransformInput(
            affine=np.asarray(require("affine", affine), dtype=float).tolist()
        )
    if normalized == "MAP_AXIS":
        return schema.MapAxisTransformInput(
            input_axes=list(require("input_axes", input_axes)),
            output_axes=list(require("output_axes", output_axes)),
        )
    if normalized == "BY_DIMENSION":
        given = {"scale": scale, "translation": translation, "affine": affine, "input_axes": input_axes, "output_axes": output_axes}
        stray = [name for name, value in given.items() if value is not None]
        if stray:
            raise ValueError(f"A BY_DIMENSION maps its axes in its parts, so it takes no {stray[0]}=: pass parts=[_part(...)] instead")
        return schema.ByDimensionTransformInput(parts=list(require("parts", parts)))
    if normalized == "UNMAPPABLE":
        if reason is None:
            return schema.UnmappableTransformInput()
        return schema.UnmappableTransformInput(reason=reason)
    raise ValueError(f"Unknown transformation kind {normalized!r}")


@dataclass(frozen=True, eq=False)
class AxisMap:
    """An affine map between two coordinate systems, keyed by axis name.

    `matrix` is homogeneous, ``(len(output_axes) + 1) x (len(input_axes) + 1)``:
    one row per output axis, one column per input axis, the last column the
    offset. `output_axes` names **only the axes the map states**. An axis a path
    says nothing about -- the channel of an image, seen from a shape drawn in
    space -- has no row, never a zero one: zero would be a claim.
    """

    input_axes: tuple[str, ...]
    output_axes: tuple[str, ...]
    matrix: NDArray[np.float64]

    def apply(
        self,
        points: PointsLike,
        *,
        input_axes: Sequence[str] | None = None,
        output_axes: Sequence[str] | None = None,
    ) -> NDArray[np.float64]:
        """Map points, one column per `input_axes`, to one column per `output_axes`.

        Both default to this map's own. Naming fewer input axes is how a point
        that has no value along some axis is mapped: it works whenever the
        requested output axes do not read the missing ones, and raises naming
        the axis when they do. Asking for an output axis the map does not state
        raises too.
        """
        given = tuple(input_axes) if input_axes is not None else self.input_axes
        wanted = tuple(output_axes) if output_axes is not None else self.output_axes
        unknown = [axis for axis in given if axis not in self.input_axes]
        if unknown:
            raise ValueError(
                f"The points name axes {unknown}, which the map's input does not have; "
                f"its axes are {list(self.input_axes)}"
            )
        unstated = [axis for axis in wanted if axis not in self.output_axes]
        if unstated:
            raise ValueError(
                f"The map says nothing about {unstated}: from {list(self.input_axes)} it "
                f"states only {list(self.output_axes)}"
            )
        rows = self.matrix[[self.output_axes.index(axis) for axis in wanted]]
        missing = [axis for axis in self.input_axes if axis not in given]
        for axis in missing:
            reading = [
                out for out, row in zip(wanted, rows) if row[self.input_axes.index(axis)] != 0.0
            ]
            if reading:
                raise ValueError(
                    f"{reading} depend on {axis!r}, which the points do not carry; "
                    f"they carry {list(given)}"
                )
        columns = [self.input_axes.index(axis) for axis in given]
        reduced = np.vstack(
            [
                np.hstack([rows[:, columns], rows[:, -1:]]),
                np.eye(1, len(columns) + 1, len(columns)),
            ]
        )
        return _apply_homogeneous(reduced, points)


def _pass_through_factor(source: object, target: object) -> float | None:
    """How much one unit of a passed-through axis is worth on the other side.

    An axis an edge passes through is the same position said twice, so two
    different units on its two ends are a conversion, not a relabelling. None
    when the units have no conversion between them: the axis then does not pass
    through at all. A missing or arbitrary unit claims nothing and converts by
    one. The same rule the server composes placements by.
    """
    if not source or not target or str(source) == str(target):
        return 1.0
    from kanne.scalars import get_current_registry, is_arbitrary_unit

    if is_arbitrary_unit(source) or is_arbitrary_unit(target):
        return 1.0
    try:
        return float(get_current_registry().Quantity(1.0, str(source)).to(str(target)).magnitude)
    except Exception:
        return None


def _units_in_order(system: CoordinateSystemTrait) -> dict[str, object]:
    axes = get_attributes_or_error(system, "axes")
    return {a.name: getattr(a, "unit", None) for a in axes}


def _field_parts(
    source: object,
    space: object,
    field: "Mapping[str, DatasetTrait]",
    units: Mapping[str, str],
    source_axes: Sequence[str],
    space_axes: Sequence[str],
) -> list["DimensionPartInput"]:
    """The FIELD parts `register(field=...)` describes -- one axis each, read from a 1-D array -- their values read once and checked.

    The server records the range as declared and never reads the array, so this
    is where "strictly increasing, one value per position" is actually checked.
    """
    parts = []
    for axis, dataset in field.items():
        if axis not in source_axes or axis not in space_axes:
            raise ValueError(f"field names '{axis}', which {getattr(source, 'name', 'the source')} {list(source_axes)} and the space {list(space_axes)} do not both have")

        values = np.asarray(dataset.data.values, dtype=float)
        if values.ndim != 1:
            raise ValueError(f"A field is one value per position, so it is rank one, but '{getattr(dataset, 'name', '?')}' has shape {values.shape}")
        if values.size < 2 or not bool(np.all(np.diff(values) > 0)):
            raise ValueError(f"A field's values strictly increase, but '{getattr(dataset, 'name', '?')}' does not: {values[:8]}")

        unit = units.get(axis) or next((a.unit for a in getattr(space, "axes", ()) or () if a.name == axis), None)
        if not unit:
            raise ValueError(f"Name the unit of the field's values for '{axis}' (field_units={{'{axis}': ...}}): the space's axis states none")

        system = getattr(dataset, "intrinsic_system", None)
        if system is None:
            raise ValueError(f"'{getattr(dataset, 'name', '?')}' was fetched without its intrinsicSystem, so its space cannot be named")
        parts.append(_part("FIELD", [axis], [axis], field=system.id, unit=str(unit), min=float(values[0]), max=float(values[-1])))
    return parts


def _shared_part(axes: Sequence[str], factors: Sequence[float] | None, offsets: Sequence[float]) -> "DimensionPartInput":
    """The one part a registration states over the axes the two spaces share: the kind its numbers are.

    No numbers is an IDENTITY -- the same positions, said twice; a factor alone a SCALE, an
    offset alone a TRANSLATION, both a diagonal AFFINE, which the server still reads as
    the scale it is.
    """
    moved = any(offset != 0.0 for offset in offsets)
    if factors is None and not moved:
        return _part("IDENTITY", axes, axes)
    if factors is None:
        return _part("TRANSLATION", axes, axes, translation=offsets)
    if not moved:
        return _part("SCALE", axes, axes, scale=factors)
    return _part(
        "AFFINE",
        axes,
        axes,
        affine=[[factors[row] if column == row else 0.0 for column in range(len(axes))] + [offsets[row]] for row in range(len(axes))],
    )


def _edge_axis_map(step: PathStep) -> AxisMap:
    """One edge of a path as an `AxisMap` in the direction it is walked.

    A kind with a matrix is that matrix, labelled with its two systems' axes.
    A BY_DIMENSION is its parts: each maps its own axes by its own kind's
    matrix, an IDENTITY part converting between the units its axes carry, and
    an axis no part names is one the edge states nothing about. A FIELD part's
    axes are read from an array, so they are left out here -- exactly as the
    server's `asAffine` leaves them to `fields` -- and make the edge
    forwards-only. Walked backwards, each part's block is inverted.
    """
    t = step.transformation
    kind = _normalize_kind(get_attributes_or_error(t, "kind"))
    input_system = getattr(t, "input", None)
    output_system = getattr(t, "output", None)
    if input_system is None or output_system is None:
        raise ValueError(
            f"Transformation {getattr(t, 'id', '?')} ({kind}) was fetched without its "
            "input and output coordinate systems, so its axes cannot be named"
        )
    in_names, out_names = _axis_names_in_order(input_system), _axis_names_in_order(output_system)
    in_units, out_units = _units_in_order(input_system), _units_in_order(output_system)

    if kind != "BY_DIMENSION":
        matrix = t.as_matrix()
        if matrix.shape != (len(out_names) + 1, len(in_names) + 1):
            raise ValueError(
                f"Transformation {getattr(t, 'id', '?')} ({kind}) maps "
                f"{matrix.shape[1] - 1} -> {matrix.shape[0] - 1} dimensions, but its systems "
                f"have axes {in_names} -> {out_names}"
            )
        if kind == "IDENTITY" and in_names == out_names:
            # Every axis of an identity passes through, so each is converted
            # between the units its two ends give it, or dropped if it cannot be.
            factors = [_pass_through_factor(in_units[a], out_units[a]) for a in in_names]
            kept = [i for i, factor in enumerate(factors) if factor is not None]
            matrix = np.vstack(
                [np.diag([factors[i] or 0.0 for i in range(len(in_names))] + [1.0])[kept], matrix[-1:]]
            )
            out_names = [out_names[i] for i in kept]
        if not step.inverted:
            return AxisMap(tuple(in_names), tuple(out_names), matrix)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(
                f"The path needs the inverse of transformation {getattr(t, 'id', '?')} "
                f"({kind}), but it maps {matrix.shape[1] - 1} -> {matrix.shape[0] - 1} "
                "dimensions and is not invertible"
            )
        try:
            inverse = np.linalg.inv(matrix)
        except np.linalg.LinAlgError as e:
            raise ValueError(
                f"Transformation {getattr(t, 'id', '?')} ({kind}) is singular and cannot "
                "be walked backwards"
            ) from e
        return AxisMap(tuple(out_names), tuple(in_names), inverse)

    parts = list(getattr(t, "parts", ()) or ())
    if step.inverted:
        fields = [list(part.output_axes) for part in parts if _normalize_kind(part.kind) == "FIELD"]
        if fields:
            raise ValueError(f"Transformation {getattr(t, 'id', '?')} (BY_DIMENSION) reads {fields} from an array and is walked forwards only")
        in_names, out_names, in_units, out_units = out_names, in_names, out_units, in_units

    rows: list[np.ndarray] = []
    stated: list[str] = []
    for part in parts:
        part_kind = _normalize_kind(part.kind)
        if part_kind == "FIELD":
            continue
        acts_in, acts_out = list(part.input_axes), list(part.output_axes)
        if step.inverted:
            acts_in, acts_out = acts_out, acts_in
        strangers = [a for a in acts_in if a not in in_names] + [a for a in acts_out if a not in out_names]
        if strangers:
            raise ValueError(
                f"Transformation {getattr(t, 'id', '?')} (BY_DIMENSION) has a {part_kind} part naming axes {strangers} "
                f"that its systems {in_names} -> {out_names} do not have"
            )
        if part_kind == "IDENTITY":
            for in_axis, out_axis in zip(acts_in, acts_out):
                factor = _pass_through_factor(in_units[in_axis], out_units[out_axis])
                if factor is None:
                    continue
                row = np.zeros(len(in_names) + 1)
                row[in_names.index(in_axis)] = factor
                rows.append(row)
                stated.append(out_axis)
            continue
        block = _part_matrix(part, part_kind)
        if step.inverted:
            if block.shape[0] != block.shape[1]:
                raise ValueError(f"Transformation {getattr(t, 'id', '?')} (BY_DIMENSION) has a {part_kind} part that changes rank and cannot be walked backwards")
            try:
                block = np.linalg.inv(block)
            except np.linalg.LinAlgError as e:
                raise ValueError(f"Transformation {getattr(t, 'id', '?')} (BY_DIMENSION) has a singular {part_kind} part and cannot be walked backwards") from e
        for index, out_axis in enumerate(acts_out):
            row = np.zeros(len(in_names) + 1)
            for column, in_axis in enumerate(acts_in):
                row[in_names.index(in_axis)] = block[index][column]
            row[-1] = block[index][len(acts_in)]
            rows.append(row)
            stated.append(out_axis)
    order = [axis for axis in out_names if axis in stated]
    bottom = np.zeros(len(in_names) + 1)
    bottom[-1] = 1.0
    return AxisMap(tuple(in_names), tuple(order), np.vstack([*[rows[stated.index(axis)] for axis in order], bottom]))


def _part_matrix(part: object, kind: str) -> NDArray[np.float64]:
    """One non-field part's map as a homogeneous matrix over its own axes, outputs by rows."""
    n_in, n_out = len(part.input_axes), len(part.output_axes)  # type: ignore[attr-defined]
    if kind in ("AFFINE", "ROTATION"):
        return _homogeneous_from_rows(np.asarray(part.affine, dtype=float), n_in)  # type: ignore[attr-defined]
    block = np.eye(n_in + 1)
    if kind == "SCALE":
        block[:n_in, :n_in] = np.diag([float(s) for s in part.scale])  # type: ignore[attr-defined]
    elif kind == "TRANSLATION":
        block[:n_in, n_in] = [float(v) for v in part.translation]  # type: ignore[attr-defined]
    if n_out != n_in:
        raise ValueError(f"A {kind} part maps its axes one for one, but this one names {n_in} onto {n_out}")
    return block


def _compose_axis_maps(steps: Sequence[PathStep], source_axes: Sequence[str]) -> AxisMap:
    """Compose a path into one `AxisMap` over the source system's axes.

    By substitution, axis name by axis name, so a path may change rank on the
    way. An axis a step reads from one an earlier step stopped stating is
    dropped: once a path has let go of an axis, nothing downstream takes hold of
    it again.
    """
    source = tuple(source_axes)
    current = AxisMap(source, source, np.eye(len(source) + 1))
    for step in steps:
        edge = _edge_axis_map(step)
        rows: list[np.ndarray] = []
        stated: list[str] = []
        for out_axis, form in zip(edge.output_axes, edge.matrix[:-1]):
            row = np.zeros(len(source) + 1)
            row[-1] = form[-1]
            for in_axis, factor in zip(edge.input_axes, form[:-1]):
                if factor == 0.0:
                    continue
                if in_axis not in current.output_axes:
                    break
                row += factor * current.matrix[current.output_axes.index(in_axis)]
            else:
                rows.append(row)
                stated.append(out_axis)
        bottom = np.zeros(len(source) + 1)
        bottom[-1] = 1.0
        current = AxisMap(source, tuple(stated), np.vstack([*rows, bottom]))
    return current


class PathStep(NamedTuple):
    """One edge of a composable path between coordinate systems.

    `inverted` is True when the edge is traversed output-to-input, in which
    case its matrix must be inverted before composing.
    """

    transformation: TransformationTrait
    inverted: bool


class TransformationTrait:
    """A trait for transformation edges between coordinate systems.

    Turns the per-kind parameters (scale, translation, affine, ...) into
    homogeneous numpy matrices and applies them to points. The matrix maps
    points given in the *input* system's axis order to points in the *output*
    system's axis order; the server guarantees positional correspondence, and
    explicit axis reordering only ever happens through MAP_AXIS edges.
    """

    #: Re-exported for callers that branch on it; the vocabulary itself lives
    #: in `mikro.vocabulary`.
    MATRIX_KINDS: ClassVar[frozenset[ResolvedTransformKind]] = MATRIX_KINDS

    def ndim_in(self) -> int | None:
        """Number of input axes, if the input system was selected in the query."""
        system = getattr(self, "input", None)
        axes = getattr(system, "axes", None) if system is not None else None
        return len(axes) if axes is not None else None

    def ndim_out(self) -> int | None:
        """Number of output axes, if the output system was selected in the query."""
        system = getattr(self, "output", None)
        axes = getattr(system, "axes", None) if system is not None else None
        return len(axes) if axes is not None else None

    def as_matrix(self) -> NDArray[np.float64]:
        """This transformation as a homogeneous (M+1) x (N+1) numpy matrix.

        IDENTITY, SCALE, TRANSLATION, AFFINE, ROTATION and MAP_AXIS have a
        closed-form matrix, and so does a SEQUENCE of them: it carries its steps,
        which compose first to last. The remaining kinds have no matrix.
        """
        kind = _normalize_kind(get_attributes_or_error(self, "kind"))

        if kind == "IDENTITY":
            n = self.ndim_in() or self.ndim_out()
            if n is None:
                raise ValueError(
                    "Cannot determine the dimensionality of an IDENTITY transformation: "
                    "neither the input nor the output coordinate system (with axes) was "
                    "selected in the query"
                )
            return np.eye(n + 1)

        if kind == "SCALE":
            scale = get_attributes_or_error(self, "scale")
            return np.diag([float(s) for s in scale] + [1.0])

        if kind == "TRANSLATION":
            translation = get_attributes_or_error(self, "translation")
            n = len(translation)
            matrix = np.eye(n + 1)
            matrix[:n, n] = [float(t) for t in translation]
            return matrix

        if kind in ("AFFINE", "ROTATION"):
            affine = get_attributes_or_error(self, "affine")
            return _homogeneous_from_rows(
                np.asarray(affine, dtype=float), self.ndim_in()
            )

        if kind == "MAP_AXIS":
            input_axes, output_axes = get_attributes_or_error(
                self, "input_axes", "output_axes"
            )
            input_system = getattr(self, "input", None)
            output_system = getattr(self, "output", None)
            if input_system is None or output_system is None:
                raise ValueError(
                    "Building a MAP_AXIS matrix requires the input and output "
                    "coordinate systems (with axes) to be selected in the query"
                )
            in_names = _axis_names_in_order(input_system)
            out_names = _axis_names_in_order(output_system)
            matrix = np.zeros((len(out_names) + 1, len(in_names) + 1))
            matrix[len(out_names), len(in_names)] = 1.0
            for in_name, out_name in zip(input_axes, output_axes):
                if in_name not in in_names:
                    raise KeyError(
                        f"MAP_AXIS input axis {in_name!r} not in input system axes {in_names}"
                    )
                if out_name not in out_names:
                    raise KeyError(
                        f"MAP_AXIS output axis {out_name!r} not in output system axes {out_names}"
                    )
                matrix[out_names.index(out_name), in_names.index(in_name)] = 1.0
            return matrix

        if kind == "SEQUENCE":
            steps = get_attributes_or_error(self, "steps")
            if not steps:
                raise ValueError(
                    f"SEQUENCE transformation {getattr(self, 'id', '?')} has no steps"
                )
            matrix = _step_matrix(steps[0], self.ndim_in())
            for step in steps[1:]:
                # Applied first to last, so each later step multiplies from the left.
                # A step's input rank is the previous step's output rank.
                matrix = _step_matrix(step, matrix.shape[0] - 1) @ matrix
            return matrix
        if kind == "UNMAPPABLE":
            raise NotImplementedError(
                "An UNMAPPABLE transformation is a declared non-correspondence between "
                "two coordinate systems; it has no matrix by definition"
            )
        raise NotImplementedError(
            f"Transformations of kind {kind} have no closed-form matrix"
        )

    def inverse_matrix(self) -> NDArray[np.float64]:
        """The inverse of `as_matrix()`; raises ValueError if not invertible."""
        matrix = self.as_matrix()
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(
                f"Cannot invert transformation {getattr(self, 'id', '?')}: it maps "
                f"{matrix.shape[1] - 1} -> {matrix.shape[0] - 1} dimensions"
            )
        try:
            return np.linalg.inv(matrix).astype(np.float64)
        except np.linalg.LinAlgError as e:
            kind = _normalize_kind(get_attributes_or_error(self, "kind"))
            raise ValueError(
                f"Transformation {getattr(self, 'id', '?')} ({kind}) is singular "
                f"and cannot be inverted"
            ) from e

    def apply(self, points: PointsLike) -> NDArray[np.float64]:
        """Map points from the input system to the output system.

        Accepts a (K, N) array or a single (N,) point in the input system's
        axis order; returns the matching shape in the output system's order.
        """
        return _apply_homogeneous(self.as_matrix(), points)

    def apply_inverse(self, points: PointsLike) -> NDArray[np.float64]:
        """Map points from the output system back to the input system."""
        return _apply_homogeneous(self.inverse_matrix(), points)


def _step_matrix(step: object, ndim_in: int | None) -> NDArray[np.float64]:
    """One step of a SEQUENCE as a homogeneous matrix.

    A step is a kind and that kind's parameters, in the axis order of the
    sequence's input -- not an edge, so it has no systems of its own and its rank
    is read off its parameters (or, for an identity, off what came before it).
    """
    kind = _normalize_kind(get_attributes_or_error(step, "kind"))
    if kind == "IDENTITY":
        if ndim_in is None:
            raise ValueError(
                "Cannot determine the dimensionality of an IDENTITY step: the sequence's "
                "input coordinate system (with axes) was not selected in the query"
            )
        return np.eye(ndim_in + 1)
    if kind == "SCALE":
        return np.diag([float(s) for s in get_attributes_or_error(step, "scale")] + [1.0])
    if kind == "TRANSLATION":
        translation = get_attributes_or_error(step, "translation")
        n = len(translation)
        matrix = np.eye(n + 1)
        matrix[:n, n] = [float(t) for t in translation]
        return matrix
    if kind in ("AFFINE", "ROTATION"):
        return _homogeneous_from_rows(
            np.asarray(get_attributes_or_error(step, "affine"), dtype=float), ndim_in
        )
    raise NotImplementedError(f"A SEQUENCE step of kind {kind} has no closed-form matrix")


def _bfs_path(
    transformations: Sequence[object],
    start_id: str,
    target_id: str,
) -> list[PathStep]:
    """Find the shortest composable path between two coordinate systems.

    Edges are walked forward (input -> output) and backward (output -> input,
    flagged inverted). Only composable kinds are walkable: those with a
    closed-form matrix -- a SEQUENCE among them when every one of its steps has
    one -- and BY_DIMENSION, which composes by axis name.

    The graph query returns a heterogeneous union, and a kind this client does
    not model comes back as a fieldless catch-all that carries no trait — hence
    `object` here, and the narrowing below. Such an edge is not walkable for the
    same reason a key is not (a BY_DIMENSION whose FIELD part dereferences a
    mask's ids): nothing about it yields a position. A placing FIELD part is
    walked forwards only, the axes its array gives left out of the composed map,
    and so is a part that changes rank.
    """
    adjacency: dict[str, list[tuple[PathStep, str]]] = {}
    for t in transformations:
        if not isinstance(t, TransformationTrait):
            continue
        kind = _normalize_kind(get_attributes_or_error(t, "kind"))
        if kind not in COMPOSABLE_KINDS:
            continue
        parts = list(getattr(t, "parts", ()) or ())
        if any(part.field is not None and part.field.dereference for part in parts):
            continue
        if kind == "SEQUENCE" and not all(
            _normalize_kind(step.kind) in TransformationTrait.MATRIX_KINDS
            for step in getattr(t, "steps", ())
        ):
            continue
        input_system = getattr(t, "input", None)
        output_system = getattr(t, "output", None)
        if input_system is None or output_system is None:
            continue
        in_id, out_id = str(input_system.id), str(output_system.id)
        adjacency.setdefault(in_id, []).append((PathStep(t, False), out_id))
        if all(_normalize_kind(part.kind) != "FIELD" and len(part.input_axes) == len(part.output_axes) for part in parts):
            adjacency.setdefault(out_id, []).append((PathStep(t, True), in_id))

    if start_id == target_id:
        return []

    queue = deque([start_id])
    predecessor: dict[str, tuple[str, PathStep]] = {}
    visited = {start_id}
    while queue:
        node = queue.popleft()
        for step, neighbor in adjacency.get(node, []):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            predecessor[neighbor] = (node, step)
            if neighbor == target_id:
                path: list[PathStep] = []
                current = neighbor
                while current != start_id:
                    current, prev_step = predecessor[current]
                    path.append(prev_step)
                return list(reversed(path))
            queue.append(neighbor)

    raise ValueError(
        f"No composable transformation path from coordinate system {start_id} to "
        f"{target_id}. Reachable systems: {sorted(visited)}"
    )


class SceneTrait:
    """A trait for scenes: a *composition* of layers over a world space.

    A scene is not a space. It adopts one — many scenes can share a world, the
    world outlives each of them, and deleting a scene never deletes it. What a
    scene owns is view state: its layers, its snapshots, its animations, its
    camera preference, its background colour.

    So a scene has no way to place anything. A layer carries no affine, and
    where data sits is an edge of the coordinate graph landing in the world —
    a claim that belongs to the *space*, which is why every scene composing
    over that world sees it. Register through the world instead::

        scene.world.register(dataset, x=288.0)
    """

    @property
    def world(self) -> CoordinateSystem:
        """The shared coordinate system this scene composes its layers over.

        Adopted, never owned: many scenes can compose over this same space, it
        outlives each of them, and deleting a scene never deletes it. Read
        straight off the scene — the same mutation that created it already
        returned this.
        """
        return get_attributes_or_error(self, "world_coordinate_system")

    def place(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Removed: a scene composes, it does not place.

        Raises:
            AttributeError: Always, pointing at `scene.world.register`.
        """
        raise AttributeError(
            "a scene composes, it does not place: scene.world.register(dataset, "
            "x=...) authors the edge, and every scene over that world sees it"
        )

    def grid_cell(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Removed: a scene composes, it does not place.

        Raises:
            AttributeError: Always, pointing at `scene.world.grid_cell`.
        """
        raise AttributeError(
            "a scene composes, it does not place: scene.world.grid_cell(dataset, "
            "index, cols, pitch) authors the edge, and every scene over that "
            "world sees it"
        )

    def clear(self, mikro: "Mikro | None" = None) -> Scene:
        """Delete every layer of this scene, keeping the scene itself.

        A pure view-state reset: no coordinate system, registration or dataset
        is touched, and other scenes over the same world never notice.

        Args:
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            This scene, now empty.
        """
        pass

        return client_of(self, mikro).clear_scene(id=get_attributes_or_error(self, "id"))

    def delete(self, mikro: "Mikro | None" = None) -> ID:
        """Delete this scene.

        Its world survives — a scene adopts a space, never owns it. Sweep the
        spaces nothing is left over with `delete_orphaned_coordinate_systems`.

        Args:
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            The id of the deleted scene.
        """
        pass

        return client_of(self, mikro).delete_scene(id=get_attributes_or_error(self, "id"))


class ChartTrait:
    """A trait for charts: a *composition* of layers along one metric axis.

    The second composition beside a scene, and its equal: a scene is a place, a
    chart is an axis with values read off it. It adopts a world with exactly one
    metric, unit-carrying axis and owns only view state, its layers.

    So a chart places nothing either. Which of a source's axes runs along the
    chart, and by what scale and shift, is the edge landing in the world::

        chart.world.register(traces, scale={"t": 0.05})
    """

    @property
    def world(self) -> CoordinateSystem:
        """The shared one-axis coordinate system this chart is laid out along.

        Adopted, never owned: many charts can share it, it outlives each of
        them, and deleting a chart never deletes it.
        """
        return get_attributes_or_error(self, "world_coordinate_system")

    def delete(self, mikro: "Mikro | None" = None) -> ID:
        """Delete this chart and its layers.

        Nothing a layer drew is touched, and the world survives.

        Args:
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            The id of the deleted chart.
        """
        return client_of(self, mikro).delete_chart(id=get_attributes_or_error(self, "id"))


class CoordinateSystemTrait:
    """A trait for coordinate systems: a *space*, a node of the coordinate graph.

    A space belongs to nobody. It does not know what lives in it (ask it for its
    residents and it answers by looking at who points at it), it owns no scene,
    and it carries no classification — a space with no residents simply is a
    pure reference frame, a world or an atlas.

    What lands in a space is a registration: an edge claiming that some source
    is placed here. Those edges belong to the space, not to any composition over
    it, so every scene sharing this world sees the same ones — which is why
    `register`, `grid_cell` and `unregister` live here rather than on a scene.

    Also provides axis utilities and client-side navigation of the coordinate
    graph (the server returns edges; composing and inverting them is the
    client's job). SCALE and TRANSLATION parameters are positional in the input
    system's axis order; explicit axis reordering only ever happens through
    MAP_AXIS edges.
    """

    def register(
        self,
        source: Registrable,
        *,
        scale: Mapping[str, float] | Sequence[float] | None = None,
        field: "Mapping[str, DatasetTrait] | None" = None,
        field_units: Mapping[str, str] | None = None,
        name: str | None = None,
        validity: PlacementValidity | None = None,
        mikro: "Mikro | None" = None,
        **offsets: float,
    ) -> CreatedTransformation:
        """Register `source` into this space, scaled and translated.

        `source` is anything that lives in a space — a dataset, a table dataset,
        a mesh collection, an annotation collection, or a coordinate system
        given directly.

        The edge is a BY_DIMENSION naming the axes the two spaces share, because
        that is the only shape that can say "these axes correspond one to one,
        and I claim nothing about the rest". A square edge cannot: a default
        world is ``(t, z, y, x)`` and a photograph is ``(c, y, x)``, so a plain
        translation sized to the source would be silently read positionally —
        mapping its ``c`` onto the world's ``t`` and its ``y`` onto ``z`` — and
        the rank check cannot catch it, because the vector length is right. It
        is also what lets an unshared axis simply not be claimed: a channel axis
        is not a position, and a physical world has no business naming it.

        `scale` is where a pixel size lives. It is a property of the edge, not
        of either space: the source's grid is in unitless indices, this space is
        in whatever its axes carry, and the factor between them is the claim.
        Give it per axis name (missing axes default to 1.0) or as a sequence
        positional against the shared axes.

        Offsets are given per axis name and default to 0, so registering at the
        origin needs no arguments. They are read against this space's axes, so
        what a unit means here is whatever those axes carry.

            world.register(dataset)                              # at the origin
            world.register(dataset, x=288.0)                     # shifted along x
            world.register(dataset, scale={"z": 1.0, "y": 0.2, "x": 0.2})
            world.register(table_dataset, y=144.0)               # any source with a space
            world.register(movie, scale={"y": 0.5, "x": 0.5}, field={"t": frame_times})

        The edge is a BY_DIMENSION with one part over the shared axes -- an
        IDENTITY, SCALE, TRANSLATION or (both) diagonal AFFINE, whichever the
        numbers given are -- and a FIELD part per `field` entry. An axis no part
        names is one the edge says nothing about.

        `field` reads an axis from a 1-D dataset's values instead of scaling it:
        the frames of an event-triggered movie were taken at uneven instants, so
        frame `i` sits at ``frame_times[i]``. The values are ABSOLUTE coordinates
        in this space -- seconds since its ``epoch`` when it has one
        (``create_space(..., epoch=datetime(...))``), which is the reference that
        makes them wall-clock times; nothing is offset or derived. The dataset holds one value per
        position along that axis, strictly increasing, alone in its own space.
        The values are read once here, to check that and to declare their range
        (the server never reads array contents). `field_units` names the unit
        of those values per axis; it defaults to this space's unit for the axis.

        Args:
            source: Anything that lives in a space.
            scale: The per-axis factor from the source's coordinates into this
                space's, by axis name or positional against the shared axes.
            name: An optional name for the edge.
            validity: How far the claim is to be trusted.
            mikro: The client to call through; defaults to the one that fetched this object.
            field: Axes read from 1-D datasets' values, by axis name.
            field_units: The unit of each field's values, by axis name.
            **offsets: The per-axis offset in this space's coordinates.

        Returns:
            The created registration edge.

        Raises:
            ValueError: If the two spaces share no axis, if a scale or an offset
                names an unshared one, if a positional scale is the wrong
                length, or if a field is not one strictly increasing value per
                position.
        """
        space = _space_of(source)

        axis_names = _axis_names_in_order(space)
        my_names = _axis_names_in_order(self)

        fields = _field_parts(source, self, field or {}, field_units or {}, axis_names, my_names)

        # In the source's own axis order: the part's parameters are positional
        # against its axes, so the two lists have to agree. An axis a field gives
        # is not among them: the array, not a factor, is its map.
        looked_up = {axis for part in fields for axis in part.input_axes}
        shared = [axis for axis in axis_names if axis in my_names and axis not in looked_up]
        if not shared and not fields:
            raise ValueError(
                f"{getattr(source, 'name', source)} has axes {axis_names} and the "
                f"space '{getattr(self, 'name', '?')}' has {my_names}: they share "
                f"none, so there is no correspondence to register. Create the space "
                f"over axes the source actually has "
                f"(create_coordinate_system(axes=[...]))."
            )

        named = set(offsets) | (set(scale) if isinstance(scale, Mapping) else set())
        both = sorted(named & looked_up)
        if both:
            raise ValueError(f"{both} is given by `field`, so it takes no scale or offset: an axis has one map")
        unplaceable = sorted(named - set(shared))
        if unplaceable:
            raise ValueError(
                f"Cannot scale or offset along {unplaceable}: the axis is not shared "
                f"between {getattr(source, 'name', source)} {axis_names} and the space "
                f"{my_names}, so a claim along it has nowhere to land."
            )

        # Both vectors are positional against `shared`, so they are built the
        # same way — a per-axis read in that one order — and cannot drift.
        if scale is None:
            factors = None
        elif isinstance(scale, Mapping):
            factors = [float(scale.get(axis, 1.0)) for axis in shared]
        else:
            factors = [float(s) for s in scale]
            if len(factors) != len(shared):
                raise ValueError(
                    f"scale has {len(factors)} entries but the edge acts on the "
                    f"shared axes {shared}. Pass a mapping of axis name to factor "
                    f"to say which is which."
                )

        parts = [_shared_part(shared, factors, [float(offsets.get(axis, 0.0)) for axis in shared])] if shared else []
        return space.transform_to(
            self,
            kind="BY_DIMENSION",
            parts=[*parts, *fields],
            name=name
            or f"{getattr(source, 'name', 'source')} -> {getattr(self, 'name', 'space')}",
            validity=validity,
            mikro=mikro,
        )

    def grid_cell(
        self,
        source: Registrable,
        index: int,
        cols: int,
        pitch: float,
        *,
        scale: Mapping[str, float] | Sequence[float] | None = None,
        name: str | None = None,
        validity: PlacementValidity | None = None,
    ) -> CreatedTransformation:
        """Register `source` into this space at grid cell `index`.

        Cells fill in reading order. `pitch` is the centre-to-centre spacing in
        this space's own units — at one unit per voxel that is the array's width
        plus whatever gutter you want. For laying variants of the same data out
        next to each other, which needs one source (and one edge) per cell.

        Args:
            source: Anything that lives in a space.
            index: Which cell to place it in, counting in reading order.
            cols: How many cells make a row.
            pitch: The centre-to-centre spacing, in this space's units.
            scale: Passed through to `register`.
            name: Passed through to `register`.
            validity: Passed through to `register`.

        Returns:
            The created registration edge.

        Raises:
            ValueError: If `cols` is less than 1.
        """
        if cols < 1:
            raise ValueError(f"cols must be at least 1, got {cols}")
        row, col = divmod(index, cols)
        return self.register(
            source,
            scale=scale,
            name=name,
            validity=validity,
            x=col * pitch,
            y=row * pitch,
        )

    def unregister(
        self,
        *,
        dataset: IDCoercible | None = None,
        table_dataset: IDCoercible | None = None,
        mesh_collection: IDCoercible | None = None,
        annotation_collection: IDCoercible | None = None,
        coordinate_system: IDCoercible | None = None,
        mikro: "Mikro | None" = None,
    ) -> tuple[ID, ...]:
        """Un-register a source from this space, by naming the source.

        Deletes every edge from the source's space into this one — rival claims
        are allowed, so there is no single edge to mean — and returns their ids.
        An UNMAPPABLE declaration is not a placement and is never matched.

        Exactly one source must be named. The kind is not inferred: the models
        carry no ``__typename``, so a guess could be silently wrong.

        Args:
            dataset: The dataset to un-register.
            table_dataset: The table dataset to un-register.
            mesh_collection: The mesh collection to un-register.
            annotation_collection: The annotation collection to un-register.
            coordinate_system: The coordinate system to un-register.
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            The ids of the deleted edges.

        Raises:
            ValueError: If other than exactly one source is named.
        """
        pass

        sources: dict[str, IDCoercible | None] = {
            "dataset": dataset,
            "table_dataset": table_dataset,
            "mesh_collection": mesh_collection,
            "annotation_collection": annotation_collection,
            "coordinate_system": coordinate_system,
        }
        named = {k: v for k, v in sources.items() if v is not None}
        if len(named) != 1:
            raise ValueError(
                f"Name exactly one source to un-register, got {sorted(named) or 'none'}. "
                f"Choose from {sorted(sources)}."
            )

        return client_of(self, mikro).delete_registration(
            world=get_attributes_or_error(self, "id"), **named
        )

    def stage(
        self,
        *,
        name: str | None = None,
        policy: ScenePolicyInput | None = None,
        mikro: "Mikro | None" = None,
    ) -> Scene:
        """Bootstrap a renderable scene over this space.

        The scene adopts this system as its world and no edges are authored —
        which is the whole point: what can be drawn here was decided when the
        sources were registered, so staging only composes. Over an ownerless
        shared space the sources already registered into it become layers, up to
        the policy's ``nchildren``; over an owned system (a dataset's intrinsic
        grid, a physical space, a collection's space) the container's own data
        becomes the layer.

        Rerunning makes another scene over this same space, which outlives them
        all.

        Args:
            name: An optional name for the scene.
            policy: A `ScenePolicyInput`. Omit to let the server choose.
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            The created scene.
        """
        from mikro.api.schema import UNSET, ScenePolicyInput

        return client_of(self, mikro).create_scene_from_coordinate_system(
            coordinate_system=get_attributes_or_error(self, "id"),
            policy=policy if policy is not None else ScenePolicyInput(),
            name=name if name is not None else UNSET,
        )

    def chart(
        self,
        *,
        name: str | None = None,
        policy: ChartPolicyInput | None = None,
        mikro: "Mikro | None" = None,
    ) -> Chart:
        """Bootstrap a chart over this space, drawing what is laid along its axis.

        The sibling of `stage`: the chart adopts this system as its world and no
        edges are authored. Every array registered into it that is a trace, every
        table that is a series and every annotation collection becomes a layer,
        up to the policy's ``nchildren``; what no layer kind reads is left out.

        The space must have exactly one axis, metric and carrying a unit.

        Args:
            name: An optional name for the chart. Defaults to the space's name.
            policy: A `ChartPolicyInput`. Omit to let the server choose.
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            The created chart.
        """
        from mikro.api.schema import UNSET, ChartPolicyInput

        return client_of(self, mikro).create_chart_from_coordinate_system(
            coordinate_system=get_attributes_or_error(self, "id"),
            policy=policy if policy is not None else ChartPolicyInput(),
            name=name if name is not None else UNSET,
        )

    def clear(self, mikro: "Mikro | None" = None) -> tuple[ID, ...]:
        """Delete every registration *into* this space, returning the edge ids.

        The space itself survives, so do the scenes composing over it (their
        layers drop to UNREGISTERED) and so do this space's own claims into
        wider spaces. Shared spaces only, and guarded by the space's creator:
        clearing a space is the space-owner's act.

        Args:
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            The ids of the deleted edges.
        """
        pass

        return client_of(self, mikro).clear_coordinate_system(
            id=get_attributes_or_error(self, "id")
        )

    @property
    def space(self) -> CoordinateSystem:
        """A coordinate system is its own space."""
        return cast("CoordinateSystem", self)

    @property
    def ndim(self) -> int:
        """The number of axes of this coordinate system."""
        return len(get_attributes_or_error(self, "axes"))

    @property
    def axis_names(self) -> list[str]:
        """The axis names, ordered by their `order` field."""
        return _axis_names_in_order(self)

    @property
    def units(self) -> dict[str, str | None]:
        """A mapping of axis name to its unit (None for uncalibrated axes)."""
        axes = get_attributes_or_error(self, "axes")
        return {a.name: a.unit for a in sorted(axes, key=lambda a: a.order)}

    def get_axis(self, name: str) -> Axis:
        """Get an axis by its name or long name."""
        axes = get_attributes_or_error(self, "axes")
        for axis in axes:
            if axis.name == name or getattr(axis, "long_name", None) == name:
                return axis
        raise KeyError(
            f"No axis {name!r} in coordinate system "
            f"{get_attributes_or_error(self, 'name')!r}. "
            f"Available axes: {[a.name for a in axes]}"
        )

    def transform_to(
        self,
        other: IDCoercible | CoordinateSystemTrait,
        *,
        scale: Sequence[float] | None = None,
        translation: Sequence[float] | None = None,
        affine: Sequence[Sequence[float]] | None = None,
        kind: TransformKind | None = None,
        name: str | None = None,
        input_axes: Sequence[str] | None = None,
        output_axes: Sequence[str] | None = None,
        reason: str | None = None,
        parts: Sequence["DimensionPartInput"] | None = None,
        validity: PlacementValidity | None = None,
        mikro: "Mikro | None" = None,
    ) -> CreatedTransformation:
        """Create a transformation edge from this system to `other`.

        The kind is inferred from which parameters are given: `affine` ->
        AFFINE, `scale` -> SCALE, `translation` -> TRANSLATION (scale and
        translation together fold into one AFFINE), `input_axes` -> MAP_AXIS.
        Pass `kind` explicitly to override. IDENTITY is authorable, but only
        when *asked for* by name: inference reaches it whenever no parameter is
        given at all, and "I passed nothing" is not the same statement as
        "these two spaces are the same grid". `reason` is recorded only on an
        UNMAPPABLE edge.
        """
        from mikro.api.schema import UNSET

        other_id = (
            other if isinstance(other, str) else get_attributes_or_error(other, "id")
        )

        if kind is None:
            kind, scale, translation, affine = _infer_transform_kind(
                scale, translation, affine, input_axes
            )
            # Inference lands on IDENTITY for an empty parameter set, which here
            # would turn a call that simply forgot its arguments into the claim
            # that the two systems are the same grid. A derivation may be handed
            # nothing and mean it — the data is in its source's space as-is —
            # but an edge between two named systems has no such default.
            if kind == "IDENTITY":
                raise ValueError(
                    "transform_to() was given no transformation parameters, which "
                    "would make this edge an IDENTITY: a claim that the two systems "
                    "are the same grid. Say kind='IDENTITY' if that is the claim; "
                    "otherwise pass scale=, translation=, affine= or input_axes=."
                )

        # Parameters are positional against the axes the edge acts on. Naming
        # `input_axes` is what narrows that to a subset — the whole point of
        # naming them — so the rank they answer to is the subset's, not the
        # system's.
        if input_axes is not None:
            expected, against = len(list(input_axes)), f"input_axes {list(input_axes)}"
        else:
            expected, against = self.ndim, f"{self.ndim} axes ({self.axis_names})"

        for field, vector in (("scale", scale), ("translation", translation)):
            if vector is not None and len(vector) != expected:
                raise ValueError(
                    f"{field} has {len(vector)} entries but this transformation acts "
                    f"on {against}"
                )

        transform = _transform_member(
            kind,
            scale=scale,
            translation=translation,
            affine=affine,
            input_axes=input_axes,
            output_axes=output_axes,
            reason=reason,
            parts=parts,
        )

        return client_of(self, mikro).create_transformation(
            input=get_attributes_or_error(self, "id"),
            output=other_id,
            transform=transform,
            name=name if name is not None else UNSET,
            validity=validity if validity is not None else UNSET,
        )

    def graph(
        self, max_depth: int | None = None, mikro: "Mikro | None" = None
    ) -> GetCoordinateGraphQueryCoordinateGraph:
        """Fetch the coordinate graph reachable from this system.

        Args:
            max_depth: How many edges out to walk. Omit for the server's default.
            mikro: The client to call through; defaults to the one that fetched this object.

        Returns:
            The reachable systems and the edges between them.
        """
        from mikro.api.schema import UNSET

        return client_of(self, mikro).get_coordinate_graph(
            coordinate_system=get_attributes_or_error(self, "id"),
            max_depth=max_depth if max_depth is not None else UNSET,
        )

    def path_to(
        self,
        other: IDCoercible | CoordinateSystemTrait,
        *,
        max_depth: int | None = None,
        graph: GetCoordinateGraphQueryCoordinateGraph | None = None,
        mikro: "Mikro | None" = None,
    ) -> list[PathStep]:
        """The shortest composable path of transformation edges to `other`.

        Fetches the coordinate graph (or uses a pre-fetched `graph`) and walks
        it client-side; edges traversed against their stored direction are
        flagged inverted. Empty when `other` is this system.
        """
        my_id = str(get_attributes_or_error(self, "id"))
        other_id = str(
            other if isinstance(other, str) else get_attributes_or_error(other, "id")
        )
        if my_id == other_id:
            return []
        if graph is None:
            graph = self.graph(max_depth=max_depth, mikro=mikro)
        return _bfs_path(graph.transformations, my_id, other_id)

    def axis_map_to(
        self,
        other: IDCoercible | CoordinateSystemTrait,
        *,
        max_depth: int | None = None,
        graph: GetCoordinateGraphQueryCoordinateGraph | None = None,
        mikro: "Mikro | None" = None,
    ) -> AxisMap:
        """The path to `other` composed into one map, keyed by axis name.

        What `matrix_to` cannot say: a path may cross a registration or a
        scene's drawing space, which relate systems of different rank, and then
        states only some of `other`'s axes. The map names the ones it states.
        """
        steps = self.path_to(other, max_depth=max_depth, graph=graph, mikro=mikro)
        return _compose_axis_maps(steps, self.axis_names)

    def matrix_to(
        self,
        other: IDCoercible | CoordinateSystemTrait,
        *,
        max_depth: int | None = None,
        graph: GetCoordinateGraphQueryCoordinateGraph | None = None,
        mikro: "Mikro | None" = None,
    ) -> NDArray[np.float64]:
        """The composed homogeneous matrix mapping points of this system into
        `other`, found via the coordinate graph.

        Raises when the path leaves an axis of `other` unstated, since a matrix
        has no way to say so; `axis_map_to` is the question to ask then.
        """
        steps = self.path_to(other, max_depth=max_depth, graph=graph, mikro=mikro)
        if not steps:
            return np.eye(self.ndim + 1)
        composed = _compose_axis_maps(steps, self.axis_names)
        target = _axis_names_in_order(steps[-1].transformation.input if steps[-1].inverted else steps[-1].transformation.output)
        unstated = [axis for axis in target if axis not in composed.output_axes]
        if unstated:
            raise ValueError(
                f"The path from {self.axis_names} states nothing about {unstated} of the "
                f"target's axes {target}, so it has no matrix. Use axis_map_to(), or "
                "transform_points_to(..., axes=...) naming the axes you need."
            )
        return composed.matrix

    def transform_points_to(
        self,
        other: IDCoercible | CoordinateSystemTrait,
        points: PointsLike,
        *,
        axes: Sequence[str] | None = None,
        max_depth: int | None = None,
        graph: GetCoordinateGraphQueryCoordinateGraph | None = None,
        mikro: "Mikro | None" = None,
    ) -> NDArray[np.float64]:
        """Map points given in this system's axis order into `other`.

        Accepts a (K, N) array or a single (N,) point; returns the matching
        shape in `other`'s axis order. `axes` asks for a subset of `other`'s
        axes instead, in the order given -- the way across a path that does not
        state all of them (a shape drawn in space, mapped onto an image with
        channels).
        """
        if axes is None:
            matrix = self.matrix_to(other, max_depth=max_depth, graph=graph, mikro=mikro)
            return _apply_homogeneous(matrix, points)
        mapped = self.axis_map_to(other, max_depth=max_depth, graph=graph, mikro=mikro)
        return mapped.apply(points, output_axes=axes)
