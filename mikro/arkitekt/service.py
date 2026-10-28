"""The mikro service of an arkitekt app, and the types it sends by id.

Declared on one registry: the service first, then the structures whose expanders
ask for the ``Mikro`` it returns. Each type is declared once -- the class, the
identifier it travels under, the widget a user picks one with, and how to fetch it
back. An app takes all of it in with ``App(services=[mikro_service])``.
"""

from pathlib import Path
from typing import Annotated, TypeVar

from fakts import Alias, Require, TokenLoader
from fakts.contrib.rath.auth import FaktsAuthLink
from graphql import OperationType
from rath.links.aiohttp import AIOHttpLink
from rath.links.compose import compose
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.graphql_ws import GraphQLWSLink
from rath.links.split import SplitLink

from arkitekt_spec.declare.app import AppRegistry
from arkitekt_spec.declare.widgets import SearchWidget

from mikro.api.schema import (
    SCOPES,
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
    SearchArrayLensesQuery,
    SearchArrayDatasetsQuery,
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

from mikro.arkitekt.specs import annotation_descriptors, lens_descriptors, metric_descriptors
from mikro.datalayer import DataLayer
from mikro.middleware.upload import UploadMiddleware
from mikro.mikro import Mikro
from mikro.rath import MikroRath


def _package_path(*path: str) -> str:
    """A path inside the ``mikro`` package, for the files shipped with it."""
    return str(Path(__file__).parent.parent.joinpath(*path))


registry = AppRegistry()
"""What mikro brings to an app: its service, and the types it can send by id."""


@registry.service(
    schema=_package_path("api", "schema.graphql"),
    turms=_package_path("api", "project.json"),
    # The server this release of the client is written against: what a hub made for
    # an app's tests runs. Moves with the server's major, not with this package's.
    image="jhnnsrs/mikro:12",
    # What the client's operations need at mikro, as turms gathered it from the schema: every
    # app using mikro asks for it.
    scopes=SCOPES,
)
def mikro(
    mikro: Annotated[
        Alias,
        Require("live.arkitekt.mikro", "Where the user's images and their metadata live"),
    ],
    s3: Annotated[
        Alias,
        Require("live.arkitekt.s3", "Where the user's files are stored"),
    ],
    tokens: TokenLoader,
) -> Mikro:
    """Mikro: the user's images, files and metadata."""
    datalayer = DataLayer.from_alias(s3)

    return Mikro(
        rath=MikroRath(
            link=compose(
                FileExtraction(),
                DictingLink(),
                FaktsAuthLink(token_loader=tokens),
                SplitLink(
                    left=AIOHttpLink(endpoint_url=mikro.to_http_path("graphql"), proxy=mikro.proxy, ssl_context=mikro.ssl_context()),
                    right=GraphQLWSLink(ws_endpoint_url=mikro.to_ws_path("graphql"), proxy=mikro.proxy, ssl_context=mikro.ssl_context()),
                    split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                ),
            ),
            middlewares=[UploadMiddleware(datalayer=datalayer)],
        ),
        datalayer=datalayer,
    )


def _search(query: object) -> SearchWidget:
    """The widget that picks one of these out of the deployment.

    A query that declares ``$requires`` is handed the port's own constraints by the
    frontend, so one widget per structure serves every port typed on it.
    """
    return SearchWidget(query=query.Meta.document, ward="mikro")  # type: ignore[attr-defined]


@registry.structure(
    "@mikro/arraydataset",
    widget=_search(SearchArrayDatasetsQuery),
    describe=lens_descriptors,
)
async def expand_array_dataset(id: str, mikro: Mikro) -> ArrayDataset:
    """An array dataset, by id."""
    return await mikro.aget_array_dataset(id)


async def shrink_table_dataset(dataset: TableDataset) -> str:
    """A table dataset, as the id it travels by."""
    return dataset.id


@registry.structure("@mikro/tabledataset", shrink=shrink_table_dataset)
async def expand_table_dataset(id: str, mikro: Mikro) -> TableDataset:
    """A table dataset, by id."""
    return await mikro.aget_table_dataset(id)


@registry.structure("@mikro/meshcollection", widget=_search(SearchMeshCollectionsQuery))
async def expand_mesh_collection(id: str, mikro: Mikro) -> MeshCollection:
    """A mesh collection, by id."""
    return await mikro.aget_mesh_collection(id)


@registry.structure("@mikro/networkcollection", widget=_search(SearchNetworkCollectionsQuery))
async def expand_network_collection(id: str, mikro: Mikro) -> NetworkCollection:
    """A network collection, by id."""
    return await mikro.aget_network_collection(id)


@registry.structure("@mikro/sparsedataset", widget=_search(SearchSparseDatasetsQuery))
async def expand_sparse_dataset(id: str, mikro: Mikro) -> SparseDataset:
    """A sparse dataset, by id."""
    return await mikro.aget_sparse_dataset(id)


@registry.structure(
    "@mikro/annotationcollection",
    widget=_search(SearchAnnotationCollectionsQuery),
)
async def expand_annotation_collection(id: str, mikro: Mikro) -> AnnotationCollection:
    """An annotation collection, by id."""
    return await mikro.aget_annotation_collection(id)


# Searched across the deployment, narrowed by what the port requires: a port typed
# `PathAnnotation` is offered the paths.
@registry.structure("@mikro/annotation", widget=_search(SearchAnnotationsQuery), describe=annotation_descriptors)
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


@registry.structure("@mikro/arraylens", widget=_search(SearchArrayLensesQuery), describe=lens_descriptors)
async def expand_lens(id: str, mikro: Mikro) -> ArrayLens:
    """An array lens, by id: a selection over an array dataset by slices."""
    return await _expand_lens(id, mikro, ArrayLens)


@registry.structure("@mikro/tablelens", widget=_search(SearchTableLensesQuery))
async def expand_table_lens(id: str, mikro: Mikro) -> TableLens:
    """A table lens, by id: the rows its windows keep."""
    return await _expand_lens(id, mikro, TableLens)


@registry.structure("@mikro/sparselens", widget=_search(SearchSparseLensesQuery))
async def expand_sparse_lens(id: str, mikro: Mikro) -> SparseLens:
    """A sparse lens, by id: the positions its windows keep."""
    return await _expand_lens(id, mikro, SparseLens)


@registry.structure("@mikro/meshlens", widget=_search(SearchMeshLensesQuery))
async def expand_mesh_lens(id: str, mikro: Mikro) -> MeshLens:
    """A mesh lens, by id."""
    return await _expand_lens(id, mikro, MeshLens)


@registry.structure("@mikro/networklens", widget=_search(SearchNetworkLensesQuery))
async def expand_network_lens(id: str, mikro: Mikro) -> NetworkLens:
    """A network lens, by id."""
    return await _expand_lens(id, mikro, NetworkLens)


@registry.structure("@mikro/annotationlens", widget=_search(SearchAnnotationLensesQuery))
async def expand_annotation_lens(id: str, mikro: Mikro) -> AnnotationLens:
    """An annotation lens, by id."""
    return await _expand_lens(id, mikro, AnnotationLens)


@registry.structure(
    "@mikro/coordinatesystem",
    widget=_search(SearchCoordinateSystemsQuery),
)
async def expand_coordinate_system(id: str, mikro: Mikro) -> CoordinateSystem:
    """A coordinate system, by id."""
    return await mikro.aget_coordinate_system(id)


# An edge of the coordinate graph has no search query: one is reached from the
# systems it joins. `Transformation` is an interface, so the structure is the base
# every kind of edge shares, and there is no one fragment to batch it by.
@registry.structure("@mikro/transformation")
async def expand_transformation(id: str, mikro: Mikro) -> TransformationBase:
    """A transformation, by id: whichever kind of edge it is."""
    return await mikro.aget_transformation(id)  # type: ignore[return-value]


@registry.structure("@mikro/scene", widget=_search(SearchScenesQuery))
async def expand_scene(id: str, mikro: Mikro) -> Scene:
    """A scene, by id."""
    return await mikro.aget_scene(id)


@registry.structure("@mikro/chart", widget=_search(SearchChartsQuery))
async def expand_chart(id: str, mikro: Mikro) -> Chart:
    """A chart, by id."""
    return await mikro.aget_chart(id)


# Searched by key, narrowed by what the port requires: a port typed on one key is
# offered the metrics of that key.
@registry.structure("@mikro/metric", widget=_search(SearchMetricsQuery), describe=metric_descriptors)
async def expand_metric(id: str, mikro: Mikro) -> Metric:
    """A metric, by id."""
    return await mikro.aget_metric(id)


@registry.structure("@mikro/scenesnapshot", widget=_search(SearchSceneSnapshotsQuery))
async def expand_scene_snapshot(id: str, mikro: Mikro) -> SceneSnapshot:
    """A scene snapshot, by id."""
    return await mikro.aget_scene_snapshot(id)


@registry.structure("@mikro/animation", widget=_search(SearchAnimationsQuery))
async def expand_animation(id: str, mikro: Mikro) -> Animation:
    """An animation, by id."""
    return await mikro.aget_animation(id)


# `@mikro/folder`, the identifier the mikro service declares it hosts. (A folder
# used to travel as `@mikro/dataset`; an app registered with that identifier has
# to re-register.)
@registry.structure("@mikro/folder", widget=_search(SearchFoldersQuery))
async def expand_folder(id: str, mikro: Mikro) -> Folder:
    """A folder, by id."""
    return await mikro.aget_folder(id)


@registry.structure("@mikro/file", widget=_search(SearchFilesQuery))
async def expand_file(id: str, mikro: Mikro) -> File:
    """A file, by id."""
    return await mikro.aget_file(id)
