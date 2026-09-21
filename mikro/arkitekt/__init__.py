"""The mikro service of an arkitekt app, and the types it sends by id.

Declared on one registry: the service first, then the structures whose expanders
ask for the ``Mikro`` it returns. Each type is declared once -- the class, the
identifier it travels under, the widget a user picks one with, and how to fetch it
back. An app takes all of it in with ``App(services=[mikro_service])``.

Fetching *many* ids is not declared: the ``Mikro`` client answers a batch in one
federated ``_entities`` request, and binding routes through that when it can.

The registry only covers what the backend still models. `Image`, `ROI`, `Stage`,
`Era`, `Snapshot`, `RGBContext`, `Table`/`TableCell`/`TableRow` and the view types
were removed from the schema, so the structures that stood for them are gone with
them; `ADataset` is now `ArrayDataset` and travels as `@mikro/arraydataset`.
"""

from pathlib import Path
from typing import Annotated

from fakts import Alias, Require, TokenLoader
from fakts.contrib.rath.auth import FaktsAuthLink
from graphql import OperationType
from rath.links.aiohttp import AIOHttpLink
from rath.links.compose import compose
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.graphql_ws import GraphQLWSLink
from rath.links.split import SplitLink

from rekuest.app import AppRegistry
from rekuest.widgets import SearchWidget

from mikro.api.schema import (
    Animation,
    Annotation,
    AnnotationCollection,
    ArrayDataset,
    CoordinateSystem,
    File,
    Folder,
    Lens,
    MeshCollection,
    Scene,
    SceneSnapshot,
    SearchAnimationsQuery,
    SearchAnnotationCollectionsQuery,
    SearchArrayDatasetsQuery,
    SearchCoordinateSystemsQuery,
    SearchFilesQuery,
    SearchFoldersQuery,
    SearchMeshCollectionsQuery,
    SearchSceneSnapshotsQuery,
    SearchScenesQuery,
    TableDataset,
)

from mikro.datalayer import DataLayer
from mikro.middleware.upload import UploadMiddleware
from mikro.mikro import Mikro
from mikro.rath import MikroRath


def build_relative_path(*path: str) -> str:
    """Build a path relative to this file, for the files shipped beside it."""
    return str(Path(__file__).parent.joinpath(*path))


registry = AppRegistry()
"""What mikro brings to an app: its service, and the types it can send by id."""


@registry.service(
    schema=build_relative_path("api", "schema.graphql"),
    turms=build_relative_path("api", "project.json"),
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
                    left=AIOHttpLink(endpoint_url=mikro.to_http_path("graphql")),
                    right=GraphQLWSLink(ws_endpoint_url=mikro.to_ws_path("graphql")),
                    split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                ),
            ),
            middlewares=[UploadMiddleware(datalayer=datalayer)],
        ),
        datalayer=datalayer,
    )


def _search(query: object) -> SearchWidget:
    """The widget that picks one of these out of the deployment."""
    return SearchWidget(query=query.Meta.document, ward="mikro")  # type: ignore[attr-defined]


@registry.structure("@mikro/arraydataset", widget=_search(SearchArrayDatasetsQuery)
)
async def expand_array_dataset(id: str, mikro: Mikro) -> ArrayDataset:
    """An array dataset, by id."""
    return await mikro.aget_array_dataset(id)


async def shrink_table_dataset(dataset: TableDataset) -> str:
    """A table dataset, as the id it travels by."""
    return dataset.id


@registry.structure("@mikro/tabledataset", shrink=shrink_table_dataset
)
async def expand_table_dataset(id: str, mikro: Mikro) -> TableDataset:
    """A table dataset, by id."""
    return await mikro.aget_table_dataset(id)


@registry.structure("@mikro/meshcollection", widget=_search(SearchMeshCollectionsQuery)
)
async def expand_mesh_collection(id: str, mikro: Mikro) -> MeshCollection:
    """A mesh collection, by id."""
    return await mikro.aget_mesh_collection(id)


@registry.structure("@mikro/annotationcollection",
    widget=_search(SearchAnnotationCollectionsQuery),
)
async def expand_annotation_collection(id: str, mikro: Mikro) -> AnnotationCollection:
    """An annotation collection, by id."""
    return await mikro.aget_annotation_collection(id)


# The annotations themselves have no search query: one is picked through its
# collection, not out of every shape in the deployment.
@registry.structure("@mikro/annotation")
async def expand_annotation(id: str, mikro: Mikro) -> Annotation:
    """One annotation, by id."""
    return await mikro.aget_annotation(id)


@registry.structure("@mikro/lens")
async def expand_lens(id: str, mikro: Mikro) -> Lens:
    """A lens, by id."""
    return await mikro.aget_lens(id)


@registry.structure("@mikro/coordinatesystem",
    widget=_search(SearchCoordinateSystemsQuery),
)
async def expand_coordinate_system(id: str, mikro: Mikro) -> CoordinateSystem:
    """A coordinate system, by id."""
    return await mikro.aget_coordinate_system(id)


@registry.structure("@mikro/scene", widget=_search(SearchScenesQuery))
async def expand_scene(id: str, mikro: Mikro) -> Scene:
    """A scene, by id."""
    return await mikro.aget_scene(id)


@registry.structure("@mikro/scenesnapshot", widget=_search(SearchSceneSnapshotsQuery)
)
async def expand_scene_snapshot(id: str, mikro: Mikro) -> SceneSnapshot:
    """A scene snapshot, by id."""
    return await mikro.aget_scene_snapshot(id)


@registry.structure("@mikro/animation", widget=_search(SearchAnimationsQuery))
async def expand_animation(id: str, mikro: Mikro) -> Animation:
    """An animation, by id."""
    return await mikro.aget_animation(id)


# `@mikro/dataset` rather than `@mikro/folder`: the identifier a folder already
# travels under, kept because it is a wire contract with every deployed app.
@registry.structure("@mikro/dataset", widget=_search(SearchFoldersQuery))
async def expand_folder(id: str, mikro: Mikro) -> Folder:
    """A folder, by id -- it travels as `@mikro/dataset`."""
    return await mikro.aget_folder(id)


@registry.structure("@mikro/file", widget=_search(SearchFilesQuery))
async def expand_file(id: str, mikro: Mikro) -> File:
    """A file, by id."""
    return await mikro.aget_file(id)
