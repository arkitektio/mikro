from mikro.array import Array
from mikro.scalars import XArray
from mikro.scalars import File
from mikro.scalars import Upload
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


class RepresentationFragmentOriginsSample(GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str


class RepresentationFragmentOrigins(Array, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    sample: Optional[RepresentationFragmentOriginsSample]
    "The Sample this representation belongs to"


class RepresentationFragmentDerivedSampleTables(GraphQLObject):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: str


class RepresentationFragmentDerivedSample(GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    tables: List[RepresentationFragmentDerivedSampleTables]


class RepresentationFragmentDerived(Array, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    sample: Optional[RepresentationFragmentDerivedSample]
    "The Sample this representation belongs to"


class RepresentationFragment(Array, GraphQLObject):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    origins: List[RepresentationFragmentOrigins]
    type: Optional[str]
    "The Representation can have varying types, consult your API"
    id: str
    derived: Optional[List[Optional[RepresentationFragmentDerived]]]
    "Derived Images from this Image"


class Expand_representationQuery(GraphQLQuery):
    representation: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  origins {\n    sample {\n      id\n    }\n  }\n  type\n  id\n  derived {\n    sample {\n      tables {\n        id\n      }\n    }\n  }\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Get_random_repQuery(GraphQLQuery):
    randomRepresentation: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  origins {\n    sample {\n      id\n    }\n  }\n  type\n  id\n  derived {\n    sample {\n      tables {\n        id\n      }\n    }\n  }\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"


class Upload_bioimageMutationUploadomerofile(GraphQLObject):
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


class From_xarrayMutationFromxarraySampleExperiments(GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str


class From_xarrayMutationFromxarraySample(GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    experiments: List[From_xarrayMutationFromxarraySampleExperiments]


class From_xarrayMutationFromxarrayOrigins(Array, GraphQLObject):
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


class From_xarrayMutationFromxarray(Array, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[str]
    "The location of the Array on the Storage System (S3 or Media-URL)"
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
        document = "mutation from_xarray($xarray: XArray!, $name: String, $origins: [ID], $tags: [String], $sample: ID) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n  ) {\n    id\n    store\n    sample {\n      experiments {\n        name\n      }\n    }\n    origins {\n      id\n      name\n    }\n    tags\n    omero {\n      planes {\n        exposureTime\n        zIndex\n        yIndex\n        tIndex\n      }\n    }\n  }\n}"


class Get_samplesQuerySamplesCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    id: str
    username: str
    "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."


class Get_samplesQuerySamplesRepresentationsOriginsSampleTables(GraphQLObject):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    name: str


class Get_samplesQuerySamplesRepresentationsOriginsSample(GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    tables: List[Get_samplesQuerySamplesRepresentationsOriginsSampleTables]


class Get_samplesQuerySamplesRepresentationsOrigins(Array, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    sample: Optional[Get_samplesQuerySamplesRepresentationsOriginsSample]
    "The Sample this representation belongs to"


class Get_samplesQuerySamplesRepresentations(Array, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    name: Optional[str]
    "Cleartext name"
    origins: List[Get_samplesQuerySamplesRepresentationsOrigins]


class Get_samplesQuerySamples(GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    creator: Optional[Get_samplesQuerySamplesCreator]
    name: str
    representations: Optional[List[Optional[Get_samplesQuerySamplesRepresentations]]]


class Get_samplesQuery(GraphQLQuery):
    samples: Optional[List[Optional[Get_samplesQuerySamples]]]

    class Meta:
        domain = "mikro"
        document = "query get_samples {\n  samples {\n    creator {\n      id\n      username\n    }\n    name\n    representations {\n      name\n      origins {\n        sample {\n          tables {\n            name\n          }\n        }\n      }\n    }\n  }\n}"


class Create_sampleMutationCreatesample(GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str
    name: str


class Create_sampleMutation(GraphQLMutation):
    createSample: Optional[Create_sampleMutationCreatesample]

    class Meta:
        domain = "mikro"
        document = "mutation create_sample($name: String) {\n  createSample(name: $name) {\n    id\n    name\n  }\n}"


class Omero_filesQueryOmerofiles(GraphQLObject):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    file: Optional[File]
    id: str


class Omero_filesQuery(GraphQLQuery):
    omerofiles: Optional[List[Optional[Omero_filesQueryOmerofiles]]]

    class Meta:
        domain = "mikro"
        document = "query omero_files {\n  omerofiles {\n    file\n    id\n  }\n}"


class Create_metricMutationCreatemetricRep(Array, GraphQLObject):
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


class Create_experimentMutationCreateexperimentCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str


class Create_experimentMutationCreateexperiment(GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str
    name: str
    creator: Optional[Create_experimentMutationCreateexperimentCreator]
    meta: Optional[Dict]


class Create_experimentMutation(GraphQLMutation):
    createExperiment: Optional[Create_experimentMutationCreateexperiment]

    class Meta:
        domain = "mikro"
        document = "mutation create_experiment($name: String!, $creator: String, $meta: GenericScalar, $description: String) {\n  createExperiment(\n    name: $name\n    creator: $creator\n    description: $description\n    meta: $meta\n  ) {\n    id\n    name\n    creator {\n      email\n    }\n    meta\n  }\n}"


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
) -> From_xarrayMutationFromxarray:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID

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
            }
        )
    ).fromXArray


def from_xarray(
    xarray: XArray,
    name: str = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
) -> From_xarrayMutationFromxarray:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID

    Returns:
        From_xarrayMutationFromxarray: The returned Mutation"""
    return From_xarrayMutation.execute(
        {
            "xarray": xarray,
            "name": name,
            "origins": origins,
            "tags": tags,
            "sample": sample,
        }
    ).fromXArray


async def aget_samples() -> List[Get_samplesQuerySamples]:
    """get_samples

    All Samples

    Arguments:

    Returns:
        Get_samplesQuerySamples: The returned Mutation"""
    return (await Get_samplesQuery.aexecute({})).samples


def get_samples() -> List[Get_samplesQuerySamples]:
    """get_samples

    All Samples

    Arguments:

    Returns:
        Get_samplesQuerySamples: The returned Mutation"""
    return Get_samplesQuery.execute({}).samples


async def acreate_sample(name: str = None) -> Create_sampleMutationCreatesample:
    """create_sample

    Creates a Sample


    Arguments:
        name (String, Optional): String

    Returns:
        Create_sampleMutationCreatesample: The returned Mutation"""
    return (await Create_sampleMutation.aexecute({"name": name})).createSample


def create_sample(name: str = None) -> Create_sampleMutationCreatesample:
    """create_sample

    Creates a Sample


    Arguments:
        name (String, Optional): String

    Returns:
        Create_sampleMutationCreatesample: The returned Mutation"""
    return Create_sampleMutation.execute({"name": name}).createSample


async def aomero_files() -> List[Omero_filesQueryOmerofiles]:
    """omero_files

    My samples return all of the users samples attached to the current user

    Arguments:

    Returns:
        Omero_filesQueryOmerofiles: The returned Mutation"""
    return (await Omero_filesQuery.aexecute({})).omerofiles


def omero_files() -> List[Omero_filesQueryOmerofiles]:
    """omero_files

    My samples return all of the users samples attached to the current user

    Arguments:

    Returns:
        Omero_filesQueryOmerofiles: The returned Mutation"""
    return Omero_filesQuery.execute({}).omerofiles


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


async def acreate_experiment(
    name: str, creator: str = None, meta: Dict = None, description: str = None
) -> Create_experimentMutationCreateexperiment:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (String): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        description (String, Optional): String

    Returns:
        Create_experimentMutationCreateexperiment: The returned Mutation"""
    return (
        await Create_experimentMutation.aexecute(
            {"name": name, "creator": creator, "meta": meta, "description": description}
        )
    ).createExperiment


def create_experiment(
    name: str, creator: str = None, meta: Dict = None, description: str = None
) -> Create_experimentMutationCreateexperiment:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (String): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        description (String, Optional): String

    Returns:
        Create_experimentMutationCreateexperiment: The returned Mutation"""
    return Create_experimentMutation.execute(
        {"name": name, "creator": creator, "meta": meta, "description": description}
    ).createExperiment
