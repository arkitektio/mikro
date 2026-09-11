"""Registers mikro's structures with rekuest, so they can cross a node boundary.

Every entity a node can take or return is registered here with the identifier it
travels under, the query that expands an id back into the object, and — where the
schema has a search query for it — the widget that lets a user pick one.

The registry only covers what the backend still models. `Image`, `ROI`, `Stage`,
`Era`, `Snapshot`, `RGBContext`, `Table`/`TableCell`/`TableRow` and the view types
were removed from the schema, so the structures that stood for them are gone with
them; `ADataset` is now `ArrayDataset` and travels as `@mikro/arraydataset`.
"""

from rekuest_next.structures.default import (
    get_default_structure_registry,
    id_shrink,
)
from rekuest_next.widgets import SearchWidget

from mikro_next.api.schema import (
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
    aget_animation,
    aget_annotation,
    aget_annotation_collection,
    aget_array_dataset,
    aget_coordinate_system,
    aget_file,
    aget_folder,
    aget_lens,
    aget_mesh_collection,
    aget_scene,
    aget_scene_snapshot,
    aget_table_dataset,
)

structure_reg = get_default_structure_registry()

structure_reg.register_as_structure(
    ArrayDataset,
    identifier="@mikro/arraydataset",
    aexpand=aget_array_dataset,
    ashrink=id_shrink,
    default_widget=SearchWidget(
        query=SearchArrayDatasetsQuery.Meta.document, ward="mikro"
    ),
)

structure_reg.register_as_structure(
    TableDataset,
    identifier="@mikro/tabledataset",
    aexpand=aget_table_dataset,
    ashrink=id_shrink,
)

structure_reg.register_as_structure(
    MeshCollection,
    identifier="@mikro/meshcollection",
    aexpand=aget_mesh_collection,
    ashrink=id_shrink,
    default_widget=SearchWidget(
        query=SearchMeshCollectionsQuery.Meta.document, ward="mikro"
    ),
)

structure_reg.register_as_structure(
    AnnotationCollection,
    identifier="@mikro/annotationcollection",
    aexpand=aget_annotation_collection,
    ashrink=id_shrink,
    default_widget=SearchWidget(
        query=SearchAnnotationCollectionsQuery.Meta.document, ward="mikro"
    ),
)

# The annotations themselves have no search query: one is picked through its
# collection, not out of every shape in the deployment.
structure_reg.register_as_structure(
    Annotation,
    identifier="@mikro/annotation",
    aexpand=aget_annotation,
    ashrink=id_shrink,
)

structure_reg.register_as_structure(
    Lens,
    identifier="@mikro/lens",
    aexpand=aget_lens,
    ashrink=id_shrink,
)

structure_reg.register_as_structure(
    CoordinateSystem,
    identifier="@mikro/coordinatesystem",
    aexpand=aget_coordinate_system,
    ashrink=id_shrink,
    default_widget=SearchWidget(
        query=SearchCoordinateSystemsQuery.Meta.document, ward="mikro"
    ),
)

structure_reg.register_as_structure(
    Scene,
    identifier="@mikro/scene",
    aexpand=aget_scene,
    ashrink=id_shrink,
    default_widget=SearchWidget(query=SearchScenesQuery.Meta.document, ward="mikro"),
)

structure_reg.register_as_structure(
    SceneSnapshot,
    identifier="@mikro/scenesnapshot",
    aexpand=aget_scene_snapshot,
    ashrink=id_shrink,
    default_widget=SearchWidget(
        query=SearchSceneSnapshotsQuery.Meta.document, ward="mikro"
    ),
)

structure_reg.register_as_structure(
    Animation,
    identifier="@mikro/animation",
    aexpand=aget_animation,
    ashrink=id_shrink,
    default_widget=SearchWidget(query=SearchAnimationsQuery.Meta.document, ward="mikro"),
)

# `@mikro/dataset` rather than `@mikro/folder`: the identifier a folder already
# travels under, kept because it is a wire contract with every deployed app.
structure_reg.register_as_structure(
    Folder,
    identifier="@mikro/dataset",
    aexpand=aget_folder,
    ashrink=id_shrink,
    default_widget=SearchWidget(query=SearchFoldersQuery.Meta.document, ward="mikro"),
)

structure_reg.register_as_structure(
    File,
    identifier="@mikro/file",
    aexpand=aget_file,
    ashrink=id_shrink,
    default_widget=SearchWidget(query=SearchFilesQuery.Meta.document, ward="mikro"),
)
