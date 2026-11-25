"""The types mikro sends by id: each expanded by the ``Mikro`` client.

Imported by ``mikro/__init__``, so each class is marked whenever mikro is.
"""

from typing import TypeVar

from arkitekt_spec.declare.structures.declare import structure
from arkitekt_spec.declare.widgets import SearchWidget

from mikro.api.schema import (
    Animation,
    Annotation,
    AnnotationCollection,
    AnnotationLens,
    ArrayDataset,
    ArrayLens,
    Chart,
    CoordinateSystem,
    File,
    Folder,
    MeshCollection,
    MeshLens,
    Metric,
    NetworkCollection,
    NetworkLens,
    Scene,
    SceneSnapshot,
    SearchAnimationsQuery,
    SearchAnnotationCollectionsQuery,
    SearchAnnotationLensesQuery,
    SearchAnnotationsQuery,
    SearchArrayDatasetsQuery,
    SearchArrayLensesQuery,
    SearchChartsQuery,
    SearchCoordinateSystemsQuery,
    SearchFilesQuery,
    SearchFoldersQuery,
    SearchMeshCollectionsQuery,
    SearchMeshLensesQuery,
    SearchMetricsQuery,
    SearchNetworkCollectionsQuery,
    SearchNetworkLensesQuery,
    SearchSceneSnapshotsQuery,
    SearchScenesQuery,
    SearchSparseDatasetsQuery,
    SearchSparseLensesQuery,
    SearchTableLensesQuery,
    SparseDataset,
    SparseLens,
    TableDataset,
    TableLens,
    TransformationBase,
)
from mikro.arkitekt.specs import descriptors_of
from mikro.mikro import Mikro


def _search(query: object) -> SearchWidget:
    """The widget that picks one of these out of the deployment.

    A query that declares ``$requires`` is handed the port's own constraints by the
    frontend, so one widget per structure serves every port typed on it.
    """
    return SearchWidget(query=query.Meta.document, ward="mikro")  # type: ignore[attr-defined]


@structure(
    "@mikro/arraydataset",
    widget=_search(SearchArrayDatasetsQuery),
    describe=descriptors_of,
)
async def expand_array_dataset(id: str, mikro: Mikro) -> ArrayDataset:
    """An array dataset, by id."""
    return await mikro.aget_array_dataset(id)


async def shrink_table_dataset(dataset: TableDataset) -> str:
    """A table dataset, as the id it travels by."""
    return dataset.id


@structure("@mikro/tabledataset", shrink=shrink_table_dataset, describe=descriptors_of)
async def expand_table_dataset(id: str, mikro: Mikro) -> TableDataset:
    """A table dataset, by id."""
    return await mikro.aget_table_dataset(id)


@structure(
    "@mikro/meshcollection",
    widget=_search(SearchMeshCollectionsQuery),
    describe=descriptors_of,
)
async def expand_mesh_collection(id: str, mikro: Mikro) -> MeshCollection:
    """A mesh collection, by id."""
    return await mikro.aget_mesh_collection(id)


@structure(
    "@mikro/networkcollection",
    widget=_search(SearchNetworkCollectionsQuery),
    describe=descriptors_of,
)
async def expand_network_collection(id: str, mikro: Mikro) -> NetworkCollection:
    """A network collection, by id."""
    return await mikro.aget_network_collection(id)


@structure(
    "@mikro/sparsedataset",
    widget=_search(SearchSparseDatasetsQuery),
    describe=descriptors_of,
)
async def expand_sparse_dataset(id: str, mikro: Mikro) -> SparseDataset:
    """A sparse dataset, by id."""
    return await mikro.aget_sparse_dataset(id)


@structure(
    "@mikro/annotationcollection",
    widget=_search(SearchAnnotationCollectionsQuery),
    describe=descriptors_of,
)
async def expand_annotation_collection(id: str, mikro: Mikro) -> AnnotationCollection:
    """An annotation collection, by id."""
    return await mikro.aget_annotation_collection(id)


# Searched across the deployment, narrowed by what the port requires: a port typed
# `PathAnnotation` is offered the paths.
@structure(
    "@mikro/annotation", widget=_search(SearchAnnotationsQuery), describe=descriptors_of
)
async def expand_annotation(id: str, mikro: Mikro) -> Annotation:
    """One annotation, by id."""
    return await mikro.aget_annotation(id)


_L = TypeVar("_L")


# One structure per lens kind, as the mikro service declares them: a port typed on
# pixels is never handed rows. `lens(id)` answers with whichever kind the id is, so
# each expander says which one it was promised.
async def _expand_lens(id: str, mikro: Mikro, kind: type[_L]) -> _L:
    lens = await mikro.aget_lens(id)
    if not isinstance(lens, kind):
        raise TypeError(
            f"Lens {id} is a {type(lens).__mro__[1].__name__}, not the {kind.__name__} this port takes"
        )
    return lens


@structure(
    "@mikro/arraylens", widget=_search(SearchArrayLensesQuery), describe=descriptors_of
)
async def expand_lens(id: str, mikro: Mikro) -> ArrayLens:
    """An array lens, by id: a selection over an array dataset by slices."""
    return await _expand_lens(id, mikro, ArrayLens)


@structure(
    "@mikro/tablelens", widget=_search(SearchTableLensesQuery), describe=descriptors_of
)
async def expand_table_lens(id: str, mikro: Mikro) -> TableLens:
    """A table lens, by id: the rows its windows keep."""
    return await _expand_lens(id, mikro, TableLens)


@structure(
    "@mikro/sparselens",
    widget=_search(SearchSparseLensesQuery),
    describe=descriptors_of,
)
async def expand_sparse_lens(id: str, mikro: Mikro) -> SparseLens:
    """A sparse lens, by id: the positions its windows keep."""
    return await _expand_lens(id, mikro, SparseLens)


@structure(
    "@mikro/meshlens", widget=_search(SearchMeshLensesQuery), describe=descriptors_of
)
async def expand_mesh_lens(id: str, mikro: Mikro) -> MeshLens:
    """A mesh lens, by id."""
    return await _expand_lens(id, mikro, MeshLens)


@structure(
    "@mikro/networklens",
    widget=_search(SearchNetworkLensesQuery),
    describe=descriptors_of,
)
async def expand_network_lens(id: str, mikro: Mikro) -> NetworkLens:
    """A network lens, by id."""
    return await _expand_lens(id, mikro, NetworkLens)


@structure(
    "@mikro/annotationlens",
    widget=_search(SearchAnnotationLensesQuery),
    describe=descriptors_of,
)
async def expand_annotation_lens(id: str, mikro: Mikro) -> AnnotationLens:
    """An annotation lens, by id."""
    return await _expand_lens(id, mikro, AnnotationLens)


@structure(
    "@mikro/coordinatesystem",
    widget=_search(SearchCoordinateSystemsQuery),
)
async def expand_coordinate_system(id: str, mikro: Mikro) -> CoordinateSystem:
    """A coordinate system, by id."""
    return await mikro.aget_coordinate_system(id)


# An edge of the coordinate graph has no search query: one is reached from the
# systems it joins. `Transformation` is an interface, so the structure is the base
# every kind of edge shares, and there is no one fragment to batch it by.
@structure("@mikro/transformation")
async def expand_transformation(id: str, mikro: Mikro) -> TransformationBase:
    """A transformation, by id: whichever kind of edge it is."""
    return await mikro.aget_transformation(id)  # type: ignore[return-value]


@structure("@mikro/scene", widget=_search(SearchScenesQuery), describe=descriptors_of)
async def expand_scene(id: str, mikro: Mikro) -> Scene:
    """A scene, by id."""
    return await mikro.aget_scene(id)


@structure("@mikro/chart", widget=_search(SearchChartsQuery), describe=descriptors_of)
async def expand_chart(id: str, mikro: Mikro) -> Chart:
    """A chart, by id."""
    return await mikro.aget_chart(id)


# Searched by key, narrowed by what the port requires: a port typed on one key is
# offered the metrics of that key.
@structure("@mikro/metric", widget=_search(SearchMetricsQuery), describe=descriptors_of)
async def expand_metric(id: str, mikro: Mikro) -> Metric:
    """A metric, by id."""
    return await mikro.aget_metric(id)


@structure(
    "@mikro/scenesnapshot",
    widget=_search(SearchSceneSnapshotsQuery),
    describe=descriptors_of,
)
async def expand_scene_snapshot(id: str, mikro: Mikro) -> SceneSnapshot:
    """A scene snapshot, by id."""
    return await mikro.aget_scene_snapshot(id)


@structure(
    "@mikro/animation", widget=_search(SearchAnimationsQuery), describe=descriptors_of
)
async def expand_animation(id: str, mikro: Mikro) -> Animation:
    """An animation, by id."""
    return await mikro.aget_animation(id)


# `@mikro/folder`, the identifier the mikro service declares it hosts. (A folder
# used to travel as `@mikro/dataset`; an app registered with that identifier has
# to re-register.)
@structure("@mikro/folder", widget=_search(SearchFoldersQuery), describe=descriptors_of)
async def expand_folder(id: str, mikro: Mikro) -> Folder:
    """A folder, by id."""
    return await mikro.aget_folder(id)


@structure("@mikro/file", widget=_search(SearchFilesQuery), describe=descriptors_of)
async def expand_file(id: str, mikro: Mikro) -> File:
    """A file, by id."""
    return await mikro.aget_file(id)
