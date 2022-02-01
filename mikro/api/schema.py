from mikro.structure import Thumbnail
from mikro.array import Array
from mikro.structure import Representation
from mikro.structure import Experiment
from mikro.structure import Sample
from mikro.structure import Table
from mikro.structure import OmeroFile
from mikro.scalars import XArray
from mikro.scalars import File
from mikro.scalars import File
from mikro.scalars import Upload
from mikro.scalars import DataFrame
from mikro.scalars import Store
from turms.types.object import GraphQLObject
from turms.types.object import GraphQLObject
from pydantic.fields import Field
from typing import Optional, List, Dict, Union, Literal
from enum import Enum
from turms.types.object import GraphQLInputObject
from turms.types.object import GraphQLObject
from turms.types.herre import GraphQLQuery
from turms.types.herre import GraphQLMutation
from turms.types.herre import GraphQLSubscription


class OmeroFileType(str, Enum):
    """An enumeration."""

    TIFF = "TIFF"
    "Tiff"
    JPEG = "JPEG"
    "Jpeg"
    MSR = "MSR"
    "MSR File"
    CZI = "CZI"
    "Zeiss Microscopy File"
    UNKNOWN = "UNKNOWN"
    "Unwknon File Format"


class RepresentationVariety(str, Enum):
    """An enumeration."""

    MASK = "MASK"
    "Mask (Value represent Labels)"
    VOXEL = "VOXEL"
    "Voxel (Value represent Intensity)"
    UNKNOWN = "UNKNOWN"
    "Unknown"


class RepresentationVarietyInput(str, Enum):
    """Variety expresses the Type of Representation we are dealing with"""

    MASK = "MASK"
    "Mask (Value represent Labels)"
    VOXEL = "VOXEL"
    "Voxel (Value represent Intensity)"
    UNKNOWN = "UNKNOWN"
    "Unknown"


class OmeroRepresentationInput(GraphQLInputObject):
    None
    planes: Optional[List[Optional["PlaneInput"]]]
    channels: Optional[List[Optional["ChannelInput"]]]
    physicalSize: Optional["PhysicalSizeInput"]
    scale: Optional[List[Optional[float]]]


class PlaneInput(GraphQLInputObject):
    None
    zIndex: Optional[int]
    yIndex: Optional[int]
    xIndex: Optional[int]
    cIndex: Optional[int]
    tIndex: Optional[int]
    exposureTime: Optional[float]
    deltaT: Optional[float]


class ChannelInput(GraphQLInputObject):
    None
    name: Optional[str]
    emmissionWavelength: Optional[float]
    excitationWavelength: Optional[float]
    acquisitionMode: Optional[str]
    color: Optional[str]


class PhysicalSizeInput(GraphQLInputObject):
    None
    x: Optional[int]
    y: Optional[int]
    z: Optional[int]
    t: Optional[int]
    c: Optional[int]


OmeroRepresentationInput.update_forward_refs()


class RepresentationFragmentSample(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str


class RepresentationFragment(Array, Representation, GraphQLObject):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    sample: Optional[RepresentationFragmentSample]
    "The Sample this representation belongs to"
    type: Optional[str]
    "The Representation can have varying types, consult your API"
    id: str
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have varying types, consult your API"
    name: Optional[str]
    "Cleartext name"


class ThumbnailFragment(Thumbnail, GraphQLObject):
    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    id: str
    image: Optional[str]


class TableFragmentCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str


class TableFragmentSample(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str


class TableFragmentRepresentation(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str


class TableFragmentExperiment(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str


class TableFragment(Table, GraphQLObject):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: str
    name: str
    tags: Optional[List[Optional[str]]]
    "A comma-separated list of tags."
    store: Optional[str]
    "The location of the Parquet on the Storage System (S3 or Media-URL)"
    creator: Optional[TableFragmentCreator]
    sample: Optional[TableFragmentSample]
    representation: Optional[TableFragmentRepresentation]
    experiment: Optional[TableFragmentExperiment]


class SampleFragmentRepresentations(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str


class SampleFragmentExperiments(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str


class SampleFragment(Sample, GraphQLObject):
    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    id: str
    representations: Optional[List[Optional[SampleFragmentRepresentations]]]
    meta: Optional[Dict]
    experiments: List[SampleFragmentExperiments]


class OmeroFileFragment(OmeroFile, GraphQLObject):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    name: str
    file: Optional[File]


class ExperimentFragmentCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str


class ExperimentFragment(Experiment, GraphQLObject):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str
    name: str
    creator: Optional[ExperimentFragmentCreator]
    meta: Optional[Dict]


class Get_omero_fileQuery(GraphQLQuery):
    omerofile: Optional[OmeroFileFragment]

    class Meta:
        domain = "mikro"
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n}\n\nquery get_omero_file($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Expand_omerofileQuery(GraphQLQuery):
    omerofile: Optional[OmeroFileFragment]

    class Meta:
        domain = "mikro"
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n}\n\nquery expand_omerofile($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Search_omerofileQueryOmerofiles(OmeroFile, GraphQLObject):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    label: str


class Search_omerofileQuery(GraphQLQuery):
    omerofiles: Optional[List[Optional[Search_omerofileQueryOmerofiles]]]

    class Meta:
        domain = "mikro"
        document = "query search_omerofile($search: String!) {\n  omerofiles(name: $search) {\n    id: id\n    label: name\n  }\n}"


class Expand_representationQuery(GraphQLQuery):
    representation: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Search_representationQueryRepresentations(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    value: str
    label: Optional[str]
    "Cleartext name"


class Search_representationQuery(GraphQLQuery):
    representations: Optional[List[Optional[Search_representationQueryRepresentations]]]

    class Meta:
        domain = "mikro"
        document = "query search_representation($search: String) {\n  representations(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"


class Get_random_repQuery(GraphQLQuery):
    randomRepresentation: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"


class ThumbnailQuery(GraphQLQuery):
    thumbnail: Optional[ThumbnailFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery Thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"


class Expand_thumbnailQuery(GraphQLQuery):
    thumbnail: Optional[ThumbnailFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery expand_thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"


class TableQuery(GraphQLQuery):
    table: Optional[TableFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery Table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


class Expand_tableQuery(GraphQLQuery):
    table: Optional[TableFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery expand_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


class Search_tablesQueryTables(Table, GraphQLObject):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: str
    label: str


class Search_tablesQuery(GraphQLQuery):
    tables: Optional[List[Optional[Search_tablesQueryTables]]]

    class Meta:
        domain = "mikro"
        document = (
            "query search_tables {\n  tables {\n    id: id\n    label: name\n  }\n}"
        )


class Get_sampleQuery(GraphQLQuery):
    sample: Optional[SampleFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery get_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class Search_sampleQuerySamples(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    value: str
    label: str


class Search_sampleQuery(GraphQLQuery):
    samples: Optional[List[Optional[Search_sampleQuerySamples]]]

    class Meta:
        domain = "mikro"
        document = "query search_sample($search: String) {\n  samples(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"


class Expand_sampleQuery(GraphQLQuery):
    sample: Optional[SampleFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery expand_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class Get_experimentQuery(GraphQLQuery):
    experiment: Optional[ExperimentFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery get_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"


class Expand_experimentQuery(GraphQLQuery):
    experiment: Optional[ExperimentFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery expand_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"


class Search_experimentQueryExperiments(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str
    label: str


class Search_experimentQuery(GraphQLQuery):
    experiments: Optional[List[Optional[Search_experimentQueryExperiments]]]

    class Meta:
        domain = "mikro"
        document = "query search_experiment($search: String) {\n  experiments(name: $search, limit: 20) {\n    id: id\n    label: name\n  }\n}"


class NegotiateMutation(GraphQLMutation):
    negotiate: Optional[Dict]

    class Meta:
        domain = "mikro"
        document = "mutation negotiate {\n  negotiate\n}"


class Upload_bioimageMutationUploadomerofile(OmeroFile, GraphQLObject):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    file: Optional[File]
    type: OmeroFileType
    name: str


class Upload_bioimageMutation(GraphQLMutation):
    uploadOmeroFile: Optional[Upload_bioimageMutationUploadomerofile]

    class Meta:
        domain = "mikro"
        document = "mutation upload_bioimage($file: Upload!) {\n  uploadOmeroFile(file: $file) {\n    id\n    file\n    type\n    name\n  }\n}"


class From_xarrayMutationFromxarraySampleExperiments(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str


class From_xarrayMutationFromxarraySample(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    experiments: List[From_xarrayMutationFromxarraySampleExperiments]


class From_xarrayMutationFromxarrayOrigins(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    name: Optional[str]
    "Cleartext name"


class From_xarrayMutationFromxarrayOmeroPlanes(GraphQLObject):
    typename: Optional[Literal["Plane"]] = Field(alias="__typename")
    exposureTime: Optional[float]
    zIndex: Optional[int]
    yIndex: Optional[int]
    tIndex: Optional[int]


class From_xarrayMutationFromxarrayOmero(GraphQLObject):
    typename: Optional[Literal["OmeroRepresentation"]] = Field(alias="__typename")
    planes: Optional[List[Optional[From_xarrayMutationFromxarrayOmeroPlanes]]]


class From_xarrayMutationFromxarray(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[Store]
    sample: Optional[From_xarrayMutationFromxarraySample]
    "The Sample this representation belongs to"
    origins: List[From_xarrayMutationFromxarrayOrigins]
    tags: Optional[List[Optional[str]]]
    "A comma-separated list of tags."
    omero: Optional[From_xarrayMutationFromxarrayOmero]
    "Metadata in Omero-compliant format"


class From_xarrayMutation(GraphQLMutation):
    fromXArray: Optional[From_xarrayMutationFromxarray]

    class Meta:
        domain = "mikro"
        document = "mutation from_xarray($xarray: XArray!, $name: String, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n    sample {\n      experiments {\n        name\n      }\n    }\n    origins {\n      id\n      name\n    }\n    tags\n    omero {\n      planes {\n        exposureTime\n        zIndex\n        yIndex\n        tIndex\n      }\n    }\n  }\n}"


class Double_uploadMutationX(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[Store]


class Double_uploadMutationY(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[Store]


class Double_uploadMutation(GraphQLMutation):
    x: Optional[Double_uploadMutationX]
    y: Optional[Double_uploadMutationY]

    class Meta:
        domain = "mikro"
        document = "mutation double_upload($xarray: XArray!, $name: String, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  x: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n  y: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n}"


class Create_thumbnailMutation(GraphQLMutation):
    uploadThumbnail: Optional[ThumbnailFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nmutation create_thumbnail($rep: ID!, $file: ImageFile!) {\n  uploadThumbnail(rep: $rep, file: $file) {\n    ...Thumbnail\n  }\n}"


class Create_metricMutationCreatemetricRep(Array, Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str


class Create_metricMutationCreatemetricCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    id: str


class Create_metricMutationCreatemetric(GraphQLObject):
    typename: Optional[Literal["Metric"]] = Field(alias="__typename")
    id: str
    rep: Optional[Create_metricMutationCreatemetricRep]
    "The Representatoin this Metric belongs to"
    key: str
    "The Key"
    value: Optional[Dict]
    creator: Optional[Create_metricMutationCreatemetricCreator]
    createdAt: str


class Create_metricMutation(GraphQLMutation):
    createMetric: Optional[Create_metricMutationCreatemetric]

    class Meta:
        domain = "mikro"
        document = "mutation create_metric($rep: ID, $sample: ID, $experiment: ID, $key: String!, $value: GenericScalar!) {\n  createMetric(\n    rep: $rep\n    sample: $sample\n    experiment: $experiment\n    key: $key\n    value: $value\n  ) {\n    id\n    rep {\n      id\n    }\n    key\n    value\n    creator {\n      id\n    }\n    createdAt\n  }\n}"


class From_dfMutation(GraphQLMutation):
    fromDf: Optional[TableFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nmutation from_df($df: DataFrame!) {\n  fromDf(df: $df) {\n    ...Table\n  }\n}"


class Create_sampleMutationCreatesampleCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str


class Create_sampleMutationCreatesample(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str
    name: str
    creator: Optional[Create_sampleMutationCreatesampleCreator]


class Create_sampleMutation(GraphQLMutation):
    createSample: Optional[Create_sampleMutationCreatesample]

    class Meta:
        domain = "mikro"
        document = "mutation create_sample($name: String, $creator: String, $meta: GenericScalar, $experiments: [ID]) {\n  createSample(\n    name: $name\n    creator: $creator\n    meta: $meta\n    experiments: $experiments\n  ) {\n    id\n    name\n    creator {\n      email\n    }\n  }\n}"


class Create_experimentMutation(GraphQLMutation):
    createExperiment: Optional[ExperimentFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nmutation create_experiment($name: String!, $creator: String, $meta: GenericScalar, $description: String) {\n  createExperiment(\n    name: $name\n    creator: $creator\n    description: $description\n    meta: $meta\n  ) {\n    ...Experiment\n  }\n}"


async def aget_omero_file(id: str) -> OmeroFileFragment:
    """get_omero_file

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return (await Get_omero_fileQuery.aexecute({"id": id})).omerofile


def get_omero_file(id: str) -> OmeroFileFragment:
    """get_omero_file

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return Get_omero_fileQuery.execute({"id": id}).omerofile


async def aexpand_omerofile(id: str) -> OmeroFileFragment:
    """expand_omerofile

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return (await Expand_omerofileQuery.aexecute({"id": id})).omerofile


def expand_omerofile(id: str) -> OmeroFileFragment:
    """expand_omerofile

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return Expand_omerofileQuery.execute({"id": id}).omerofile


async def asearch_omerofile(search: str) -> List[Search_omerofileQueryOmerofiles]:
    """search_omerofile

    My samples return all of the users samples attached to the current user

    Arguments:
        search (String): String

    Returns:
        Search_omerofileQueryOmerofiles: The returned Mutation"""
    return (await Search_omerofileQuery.aexecute({"search": search})).omerofiles


def search_omerofile(search: str) -> List[Search_omerofileQueryOmerofiles]:
    """search_omerofile

    My samples return all of the users samples attached to the current user

    Arguments:
        search (String): String

    Returns:
        Search_omerofileQueryOmerofiles: The returned Mutation"""
    return Search_omerofileQuery.execute({"search": search}).omerofiles


async def aexpand_representation(id: str) -> RepresentationFragment:
    """expand_representation

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        RepresentationFragment: The returned Mutation"""
    return (await Expand_representationQuery.aexecute({"id": id})).representation


def expand_representation(id: str) -> RepresentationFragment:
    """expand_representation

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        RepresentationFragment: The returned Mutation"""
    return Expand_representationQuery.execute({"id": id}).representation


async def asearch_representation(
    search: str = None,
) -> List[Search_representationQueryRepresentations]:
    """search_representation

    All represetations

    Arguments:
        search (String, Optional): String

    Returns:
        Search_representationQueryRepresentations: The returned Mutation"""
    return (
        await Search_representationQuery.aexecute({"search": search})
    ).representations


def search_representation(
    search: str = None,
) -> List[Search_representationQueryRepresentations]:
    """search_representation

    All represetations

    Arguments:
        search (String, Optional): String

    Returns:
        Search_representationQueryRepresentations: The returned Mutation"""
    return Search_representationQuery.execute({"search": search}).representations


async def aget_random_rep() -> RepresentationFragment:
    """get_random_rep

    Get a single representation by ID

    Arguments:

    Returns:
        RepresentationFragment: The returned Mutation"""
    return (await Get_random_repQuery.aexecute({})).randomRepresentation


def get_random_rep() -> RepresentationFragment:
    """get_random_rep

    Get a single representation by ID

    Arguments:

    Returns:
        RepresentationFragment: The returned Mutation"""
    return Get_random_repQuery.execute({}).randomRepresentation


async def aThumbnail(id: str) -> ThumbnailFragment:
    """Thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return (await ThumbnailQuery.aexecute({"id": id})).thumbnail


def Thumbnail(id: str) -> ThumbnailFragment:
    """Thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return ThumbnailQuery.execute({"id": id}).thumbnail


async def aexpand_thumbnail(id: str) -> ThumbnailFragment:
    """expand_thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return (await Expand_thumbnailQuery.aexecute({"id": id})).thumbnail


def expand_thumbnail(id: str) -> ThumbnailFragment:
    """expand_thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return Expand_thumbnailQuery.execute({"id": id}).thumbnail


async def aTable(id: str) -> TableFragment:
    """Table

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        TableFragment: The returned Mutation"""
    return (await TableQuery.aexecute({"id": id})).table


def Table(id: str) -> TableFragment:
    """Table

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        TableFragment: The returned Mutation"""
    return TableQuery.execute({"id": id}).table


async def aexpand_table(id: str) -> TableFragment:
    """expand_table

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        TableFragment: The returned Mutation"""
    return (await Expand_tableQuery.aexecute({"id": id})).table


def expand_table(id: str) -> TableFragment:
    """expand_table

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        TableFragment: The returned Mutation"""
    return Expand_tableQuery.execute({"id": id}).table


async def asearch_tables() -> List[Search_tablesQueryTables]:
    """search_tables

    My samples return all of the users samples attached to the current user

    Arguments:

    Returns:
        Search_tablesQueryTables: The returned Mutation"""
    return (await Search_tablesQuery.aexecute({})).tables


def search_tables() -> List[Search_tablesQueryTables]:
    """search_tables

    My samples return all of the users samples attached to the current user

    Arguments:

    Returns:
        Search_tablesQueryTables: The returned Mutation"""
    return Search_tablesQuery.execute({}).tables


async def aget_sample(id: str) -> SampleFragment:
    """get_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        SampleFragment: The returned Mutation"""
    return (await Get_sampleQuery.aexecute({"id": id})).sample


def get_sample(id: str) -> SampleFragment:
    """get_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        SampleFragment: The returned Mutation"""
    return Get_sampleQuery.execute({"id": id}).sample


async def asearch_sample(search: str = None) -> List[Search_sampleQuerySamples]:
    """search_sample

    All Samples

    Arguments:
        search (String, Optional): String

    Returns:
        Search_sampleQuerySamples: The returned Mutation"""
    return (await Search_sampleQuery.aexecute({"search": search})).samples


def search_sample(search: str = None) -> List[Search_sampleQuerySamples]:
    """search_sample

    All Samples

    Arguments:
        search (String, Optional): String

    Returns:
        Search_sampleQuerySamples: The returned Mutation"""
    return Search_sampleQuery.execute({"search": search}).samples


async def aexpand_sample(id: str) -> SampleFragment:
    """expand_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        SampleFragment: The returned Mutation"""
    return (await Expand_sampleQuery.aexecute({"id": id})).sample


def expand_sample(id: str) -> SampleFragment:
    """expand_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        SampleFragment: The returned Mutation"""
    return Expand_sampleQuery.execute({"id": id}).sample


async def aget_experiment(id: str) -> ExperimentFragment:
    """get_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ExperimentFragment: The returned Mutation"""
    return (await Get_experimentQuery.aexecute({"id": id})).experiment


def get_experiment(id: str) -> ExperimentFragment:
    """get_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ExperimentFragment: The returned Mutation"""
    return Get_experimentQuery.execute({"id": id}).experiment


async def aexpand_experiment(id: str) -> ExperimentFragment:
    """expand_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ExperimentFragment: The returned Mutation"""
    return (await Expand_experimentQuery.aexecute({"id": id})).experiment


def expand_experiment(id: str) -> ExperimentFragment:
    """expand_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID

    Returns:
        ExperimentFragment: The returned Mutation"""
    return Expand_experimentQuery.execute({"id": id}).experiment


async def asearch_experiment(
    search: str = None,
) -> List[Search_experimentQueryExperiments]:
    """search_experiment

    All Samples

    Arguments:
        search (String, Optional): String

    Returns:
        Search_experimentQueryExperiments: The returned Mutation"""
    return (await Search_experimentQuery.aexecute({"search": search})).experiments


def search_experiment(search: str = None) -> List[Search_experimentQueryExperiments]:
    """search_experiment

    All Samples

    Arguments:
        search (String, Optional): String

    Returns:
        Search_experimentQueryExperiments: The returned Mutation"""
    return Search_experimentQuery.execute({"search": search}).experiments


async def anegotiate() -> Dict:
    """negotiate



    Arguments:

    Returns:
        Dict: The returned Mutation"""
    return (await NegotiateMutation.aexecute({})).negotiate


def negotiate() -> Dict:
    """negotiate



    Arguments:

    Returns:
        Dict: The returned Mutation"""
    return NegotiateMutation.execute({}).negotiate


async def aupload_bioimage(file: Upload) -> Upload_bioimageMutationUploadomerofile:
    """upload_bioimage



    Arguments:
        file (Upload): Upload

    Returns:
        Upload_bioimageMutationUploadomerofile: The returned Mutation"""
    return (await Upload_bioimageMutation.aexecute({"file": file})).uploadOmeroFile


def upload_bioimage(file: Upload) -> Upload_bioimageMutationUploadomerofile:
    """upload_bioimage



    Arguments:
        file (Upload): Upload

    Returns:
        Upload_bioimageMutationUploadomerofile: The returned Mutation"""
    return Upload_bioimageMutation.execute({"file": file}).uploadOmeroFile


async def afrom_xarray(
    xarray: XArray,
    name: str = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
) -> From_xarrayMutationFromxarray:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID
        omero (OmeroRepresentationInput, Optional): OmeroRepresentationInput

    Returns:
        From_xarrayMutationFromxarray: The returned Mutation"""
    return (
        await From_xarrayMutation.aexecute(
            {
                "xarray": xarray,
                "name": name,
                "origins": origins,
                "tags": tags,
                "sample": sample,
                "omero": omero,
            }
        )
    ).fromXArray


def from_xarray(
    xarray: XArray,
    name: str = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
) -> From_xarrayMutationFromxarray:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID
        omero (OmeroRepresentationInput, Optional): OmeroRepresentationInput

    Returns:
        From_xarrayMutationFromxarray: The returned Mutation"""
    return From_xarrayMutation.execute(
        {
            "xarray": xarray,
            "name": name,
            "origins": origins,
            "tags": tags,
            "sample": sample,
            "omero": omero,
        }
    ).fromXArray


async def adouble_upload(
    xarray: XArray,
    name: str = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
) -> List[Double_uploadMutation]:
    """double_upload


     x: Creates a Representation
     y: Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID
        omero (OmeroRepresentationInput, Optional): OmeroRepresentationInput

    Returns:
        Double_uploadMutation: The returned Mutation"""
    return await Double_uploadMutation.aexecute(
        {
            "xarray": xarray,
            "name": name,
            "origins": origins,
            "tags": tags,
            "sample": sample,
            "omero": omero,
        }
    )


def double_upload(
    xarray: XArray,
    name: str = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
) -> List[Double_uploadMutation]:
    """double_upload


     x: Creates a Representation
     y: Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID
        omero (OmeroRepresentationInput, Optional): OmeroRepresentationInput

    Returns:
        Double_uploadMutation: The returned Mutation"""
    return Double_uploadMutation.execute(
        {
            "xarray": xarray,
            "name": name,
            "origins": origins,
            "tags": tags,
            "sample": sample,
            "omero": omero,
        }
    )


async def acreate_thumbnail(rep: str, file: File) -> ThumbnailFragment:
    """create_thumbnail



    Arguments:
        rep (ID): ID
        file (ImageFile): ImageFile

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return (
        await Create_thumbnailMutation.aexecute({"rep": rep, "file": file})
    ).uploadThumbnail


def create_thumbnail(rep: str, file: File) -> ThumbnailFragment:
    """create_thumbnail



    Arguments:
        rep (ID): ID
        file (ImageFile): ImageFile

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return Create_thumbnailMutation.execute({"rep": rep, "file": file}).uploadThumbnail


async def acreate_metric(
    key: str, value: Dict, rep: str = None, sample: str = None, experiment: str = None
) -> Create_metricMutationCreatemetric:
    """create_metric

    Creates a Representation

    Arguments:
        key (String): String
        value (GenericScalar): GenericScalar
        rep (ID, Optional): ID
        sample (ID, Optional): ID
        experiment (ID, Optional): ID

    Returns:
        Create_metricMutationCreatemetric: The returned Mutation"""
    return (
        await Create_metricMutation.aexecute(
            {
                "key": key,
                "value": value,
                "rep": rep,
                "sample": sample,
                "experiment": experiment,
            }
        )
    ).createMetric


def create_metric(
    key: str, value: Dict, rep: str = None, sample: str = None, experiment: str = None
) -> Create_metricMutationCreatemetric:
    """create_metric

    Creates a Representation

    Arguments:
        key (String): String
        value (GenericScalar): GenericScalar
        rep (ID, Optional): ID
        sample (ID, Optional): ID
        experiment (ID, Optional): ID

    Returns:
        Create_metricMutationCreatemetric: The returned Mutation"""
    return Create_metricMutation.execute(
        {
            "key": key,
            "value": value,
            "rep": rep,
            "sample": sample,
            "experiment": experiment,
        }
    ).createMetric


async def afrom_df(df: DataFrame) -> TableFragment:
    """from_df

    Creates a Representation

    Arguments:
        df (DataFrame): DataFrame

    Returns:
        TableFragment: The returned Mutation"""
    return (await From_dfMutation.aexecute({"df": df})).fromDf


def from_df(df: DataFrame) -> TableFragment:
    """from_df

    Creates a Representation

    Arguments:
        df (DataFrame): DataFrame

    Returns:
        TableFragment: The returned Mutation"""
    return From_dfMutation.execute({"df": df}).fromDf


async def acreate_sample(
    name: str = None,
    creator: str = None,
    meta: Dict = None,
    experiments: List[str] = None,
) -> Create_sampleMutationCreatesample:
    """create_sample

    Creates a Sample


    Arguments:
        name (String, Optional): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        experiments (List[ID], Optional): ID

    Returns:
        Create_sampleMutationCreatesample: The returned Mutation"""
    return (
        await Create_sampleMutation.aexecute(
            {"name": name, "creator": creator, "meta": meta, "experiments": experiments}
        )
    ).createSample


def create_sample(
    name: str = None,
    creator: str = None,
    meta: Dict = None,
    experiments: List[str] = None,
) -> Create_sampleMutationCreatesample:
    """create_sample

    Creates a Sample


    Arguments:
        name (String, Optional): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        experiments (List[ID], Optional): ID

    Returns:
        Create_sampleMutationCreatesample: The returned Mutation"""
    return Create_sampleMutation.execute(
        {"name": name, "creator": creator, "meta": meta, "experiments": experiments}
    ).createSample


async def acreate_experiment(
    name: str, creator: str = None, meta: Dict = None, description: str = None
) -> ExperimentFragment:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (String): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        description (String, Optional): String

    Returns:
        ExperimentFragment: The returned Mutation"""
    return (
        await Create_experimentMutation.aexecute(
            {"name": name, "creator": creator, "meta": meta, "description": description}
        )
    ).createExperiment


def create_experiment(
    name: str, creator: str = None, meta: Dict = None, description: str = None
) -> ExperimentFragment:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (String): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        description (String, Optional): String

    Returns:
        ExperimentFragment: The returned Mutation"""
    return Create_experimentMutation.execute(
        {"name": name, "creator": creator, "meta": meta, "description": description}
    ).createExperiment
