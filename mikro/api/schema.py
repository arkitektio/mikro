from mikro.scalars import File, Upload, XArray, DataFrame, Store
from mikro.traits import Table, Thumbnail, Experiment, Sample, Representation, OmeroFile
from typing import Dict, AsyncIterator, List, Iterator, Literal, Optional
from pydantic import Field, BaseModel
from mikro.funcs import aexecute, subscribe, asubscribe, execute
from rath.turms.object import GraphQLObject
from mikro.mikro import MikroRath
from enum import Enum


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
    RGB = "RGB"
    "RGB (First three channel represent RGB)"
    UNKNOWN = "UNKNOWN"
    "Unknown"


class RepresentationVarietyInput(str, Enum):
    """Variety expresses the Type of Representation we are dealing with"""

    MASK = "MASK"
    "Mask (Value represent Labels)"
    VOXEL = "VOXEL"
    "Voxel (Value represent Intensity)"
    RGB = "RGB"
    "RGB (First three channel represent RGB)"
    UNKNOWN = "UNKNOWN"
    "Unknown"


class ROIType(str, Enum):
    """An enumeration."""

    ELLIPSE = "ELLIPSE"
    "Ellipse"
    POLYGON = "POLYGON"
    "POLYGON"
    LINE = "LINE"
    "Line"
    RECTANGLE = "RECTANGLE"
    "Rectangle"
    PATH = "PATH"
    "Path"
    UNKNOWN = "UNKNOWN"
    "Unknown"


class RoiTypeInput(str, Enum):
    """An enumeration."""

    ELLIPSIS = "ELLIPSIS"
    "Ellipse"
    POLYGON = "POLYGON"
    "POLYGON"
    LINE = "LINE"
    "Line"
    RECTANGLE = "RECTANGLE"
    "Rectangle"
    PATH = "PATH"
    "Path"
    UNKNOWN = "UNKNOWN"
    "Unknown"


class OmeroRepresentationInput(BaseModel):
    planes: Optional[List[Optional["PlaneInput"]]]
    channels: Optional[List[Optional["ChannelInput"]]]
    physicalSize: Optional["PhysicalSizeInput"]
    scale: Optional[List[Optional[float]]]


class PlaneInput(BaseModel):
    zIndex: Optional[int]
    yIndex: Optional[int]
    xIndex: Optional[int]
    cIndex: Optional[int]
    tIndex: Optional[int]
    exposureTime: Optional[float]
    deltaT: Optional[float]


class ChannelInput(BaseModel):
    name: Optional[str]
    emmissionWavelength: Optional[float]
    excitationWavelength: Optional[float]
    acquisitionMode: Optional[str]
    color: Optional[str]


class PhysicalSizeInput(BaseModel):
    x: Optional[int]
    y: Optional[int]
    z: Optional[int]
    t: Optional[int]
    c: Optional[int]


class InputVector(BaseModel):
    x: Optional[float]
    "X-coordinate"
    y: Optional[float]
    "Y-coordinate"
    z: Optional[float]
    "Z-coordinate"


OmeroRepresentationInput.update_forward_refs()


class RepresentationFragmentSample(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str

    class Config:
        frozen = True


class RepresentationFragment(Representation, GraphQLObject):
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

    class Config:
        frozen = True


class ThumbnailFragment(Thumbnail, GraphQLObject):
    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    id: str
    image: Optional[str]

    class Config:
        frozen = True


class ROIFragmentVectors(GraphQLObject):
    typename: Optional[Literal["Vector"]] = Field(alias="__typename")
    x: Optional[float]
    "X-coordinate"
    y: Optional[float]
    "Y-coordinate"
    z: Optional[float]
    "Z-coordinate"

    class Config:
        frozen = True


class ROIFragmentRepresentation(Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class ROIFragment(GraphQLObject):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    id: str
    vectors: Optional[List[Optional[ROIFragmentVectors]]]
    type: ROIType
    "The Representation can have varying types, consult your API"
    representation: Optional[ROIFragmentRepresentation]

    class Config:
        frozen = True


class TableFragmentCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class TableFragmentSample(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class TableFragmentRepresentation(Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class TableFragmentExperiment(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


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

    class Config:
        frozen = True


class SampleFragmentRepresentations(Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class SampleFragmentExperiments(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class SampleFragment(Sample, GraphQLObject):
    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    id: str
    representations: Optional[List[Optional[SampleFragmentRepresentations]]]
    meta: Optional[Dict]
    experiments: List[SampleFragmentExperiments]

    class Config:
        frozen = True


class OmeroFileFragment(OmeroFile, GraphQLObject):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    name: str
    file: Optional[File]

    class Config:
        frozen = True


class ExperimentFragmentCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class ExperimentFragment(Experiment, GraphQLObject):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str
    name: str
    creator: Optional[ExperimentFragmentCreator]
    meta: Optional[Dict]

    class Config:
        frozen = True


class Get_omero_fileQuery(GraphQLObject):
    omerofile: Optional[OmeroFileFragment]

    class Meta:
        domain = "mikro"
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n}\n\nquery get_omero_file($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"

    class Config:
        frozen = True


class Expand_omerofileQuery(GraphQLObject):
    omerofile: Optional[OmeroFileFragment]

    class Meta:
        domain = "mikro"
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n}\n\nquery expand_omerofile($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"

    class Config:
        frozen = True


class Search_omerofileQueryOmerofiles(OmeroFile, GraphQLObject):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    label: str

    class Config:
        frozen = True


class Search_omerofileQuery(GraphQLObject):
    omerofiles: Optional[List[Optional[Search_omerofileQueryOmerofiles]]]

    class Meta:
        domain = "mikro"
        document = "query search_omerofile($search: String!) {\n  omerofiles(name: $search) {\n    id: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Expand_representationQuery(GraphQLObject):
    representation: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class Get_representationQuery(GraphQLObject):
    representation: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery get_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class Search_representationQueryRepresentations(Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    value: str
    label: Optional[str]
    "Cleartext name"

    class Config:
        frozen = True


class Search_representationQuery(GraphQLObject):
    representations: Optional[List[Optional[Search_representationQueryRepresentations]]]

    class Meta:
        domain = "mikro"
        document = "query search_representation($search: String) {\n  representations(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Get_random_repQuery(GraphQLObject):
    randomRepresentation: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class ThumbnailQuery(GraphQLObject):
    thumbnail: Optional[ThumbnailFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery Thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"

    class Config:
        frozen = True


class Expand_thumbnailQuery(GraphQLObject):
    thumbnail: Optional[ThumbnailFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery expand_thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"

    class Config:
        frozen = True


class Get_roisQuery(GraphQLObject):
    rois: Optional[List[Optional[ROIFragment]]]

    class Meta:
        domain = "mikro"
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n}\n\nquery get_rois($representation: ID!, $type: [RoiTypeInput]) {\n  rois(representation: $representation, type: $type) {\n    ...ROI\n  }\n}"

    class Config:
        frozen = True


class TableQuery(GraphQLObject):
    table: Optional[TableFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery Table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"

    class Config:
        frozen = True


class Expand_tableQuery(GraphQLObject):
    table: Optional[TableFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery expand_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"

    class Config:
        frozen = True


class Search_tablesQueryTables(Table, GraphQLObject):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: str
    label: str

    class Config:
        frozen = True


class Search_tablesQuery(GraphQLObject):
    tables: Optional[List[Optional[Search_tablesQueryTables]]]

    class Meta:
        domain = "mikro"
        document = (
            "query search_tables {\n  tables {\n    id: id\n    label: name\n  }\n}"
        )

    class Config:
        frozen = True


class Get_sampleQuery(GraphQLObject):
    sample: Optional[SampleFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery get_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"

    class Config:
        frozen = True


class Search_sampleQuerySamples(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    value: str
    label: str

    class Config:
        frozen = True


class Search_sampleQuery(GraphQLObject):
    samples: Optional[List[Optional[Search_sampleQuerySamples]]]

    class Meta:
        domain = "mikro"
        document = "query search_sample($search: String) {\n  samples(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Expand_sampleQuery(GraphQLObject):
    sample: Optional[SampleFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery expand_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"

    class Config:
        frozen = True


class Get_experimentQuery(GraphQLObject):
    experiment: Optional[ExperimentFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery get_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"

    class Config:
        frozen = True


class Expand_experimentQuery(GraphQLObject):
    experiment: Optional[ExperimentFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery expand_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"

    class Config:
        frozen = True


class Search_experimentQueryExperiments(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str
    label: str

    class Config:
        frozen = True


class Search_experimentQuery(GraphQLObject):
    experiments: Optional[List[Optional[Search_experimentQueryExperiments]]]

    class Meta:
        domain = "mikro"
        document = "query search_experiment($search: String) {\n  experiments(name: $search, limit: 30) {\n    id: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Watch_roisSubscriptionRois(GraphQLObject):
    typename: Optional[Literal["RoiEvent"]] = Field(alias="__typename")
    update: Optional[ROIFragment]
    delete: Optional[str]
    create: Optional[ROIFragment]

    class Config:
        frozen = True


class Watch_roisSubscription(GraphQLObject):
    rois: Optional[Watch_roisSubscriptionRois]

    class Meta:
        domain = "mikro"
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n}\n\nsubscription watch_rois($representation: ID!) {\n  rois(representation: $representation) {\n    update {\n      ...ROI\n    }\n    delete\n    create {\n      ...ROI\n    }\n  }\n}"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesUpdateExperiments(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesUpdate(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str
    name: str
    experiments: List[Watch_samplesSubscriptionMysamplesUpdateExperiments]

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesCreateExperiments(Experiment, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesCreate(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    experiments: List[Watch_samplesSubscriptionMysamplesCreateExperiments]

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamples(GraphQLObject):
    typename: Optional[Literal["SamplesEvent"]] = Field(alias="__typename")
    update: Optional[Watch_samplesSubscriptionMysamplesUpdate]
    create: Optional[Watch_samplesSubscriptionMysamplesCreate]

    class Config:
        frozen = True


class Watch_samplesSubscription(GraphQLObject):
    mySamples: Optional[Watch_samplesSubscriptionMysamples]

    class Meta:
        domain = "mikro"
        document = "subscription watch_samples {\n  mySamples {\n    update {\n      id\n      name\n      experiments {\n        name\n      }\n    }\n    create {\n      name\n      experiments {\n        name\n      }\n    }\n  }\n}"

    class Config:
        frozen = True


class NegotiateMutation(GraphQLObject):
    negotiate: Optional[Dict]

    class Meta:
        domain = "mikro"
        document = "mutation negotiate {\n  negotiate\n}"

    class Config:
        frozen = True


class Upload_bioimageMutationUploadomerofile(OmeroFile, GraphQLObject):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    file: Optional[File]
    type: OmeroFileType
    name: str

    class Config:
        frozen = True


class Upload_bioimageMutation(GraphQLObject):
    uploadOmeroFile: Optional[Upload_bioimageMutationUploadomerofile]

    class Meta:
        domain = "mikro"
        document = "mutation upload_bioimage($file: Upload!) {\n  uploadOmeroFile(file: $file) {\n    id\n    file\n    type\n    name\n  }\n}"

    class Config:
        frozen = True


class From_xarrayMutation(GraphQLObject):
    fromXArray: Optional[RepresentationFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nmutation from_xarray($xarray: XArray!, $name: String, $variety: RepresentationVarietyInput, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n    variety: $variety\n  ) {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class Double_uploadMutationX(Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[Store]

    class Config:
        frozen = True


class Double_uploadMutationY(Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[Store]

    class Config:
        frozen = True


class Double_uploadMutation(GraphQLObject):
    x: Optional[Double_uploadMutationX]
    y: Optional[Double_uploadMutationY]

    class Meta:
        domain = "mikro"
        document = "mutation double_upload($xarray: XArray!, $name: String, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  x: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n  y: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n}"

    class Config:
        frozen = True


class Create_thumbnailMutation(GraphQLObject):
    uploadThumbnail: Optional[ThumbnailFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nmutation create_thumbnail($rep: ID!, $file: ImageFile!) {\n  uploadThumbnail(rep: $rep, file: $file) {\n    ...Thumbnail\n  }\n}"

    class Config:
        frozen = True


class Create_metricMutationCreatemetricRep(Representation, GraphQLObject):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class Create_metricMutationCreatemetricCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


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

    class Config:
        frozen = True


class Create_metricMutation(GraphQLObject):
    createMetric: Optional[Create_metricMutationCreatemetric]

    class Meta:
        domain = "mikro"
        document = "mutation create_metric($rep: ID, $sample: ID, $experiment: ID, $key: String!, $value: GenericScalar!) {\n  createMetric(\n    rep: $rep\n    sample: $sample\n    experiment: $experiment\n    key: $key\n    value: $value\n  ) {\n    id\n    rep {\n      id\n    }\n    key\n    value\n    creator {\n      id\n    }\n    createdAt\n  }\n}"

    class Config:
        frozen = True


class Create_roiMutation(GraphQLObject):
    createROI: Optional[ROIFragment]

    class Meta:
        domain = "mikro"
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n}\n\nmutation create_roi($representation: ID!, $vectors: [InputVector]!, $creator: ID, $type: RoiTypeInput) {\n  createROI(\n    representation: $representation\n    vectors: $vectors\n    type: $type\n    creator: $creator\n  ) {\n    ...ROI\n  }\n}"

    class Config:
        frozen = True


class From_dfMutation(GraphQLObject):
    fromDf: Optional[TableFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nmutation from_df($df: DataFrame!) {\n  fromDf(df: $df) {\n    ...Table\n  }\n}"

    class Config:
        frozen = True


class Create_sampleMutationCreatesampleCreator(GraphQLObject):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class Create_sampleMutationCreatesample(Sample, GraphQLObject):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str
    name: str
    creator: Optional[Create_sampleMutationCreatesampleCreator]

    class Config:
        frozen = True


class Create_sampleMutation(GraphQLObject):
    createSample: Optional[Create_sampleMutationCreatesample]

    class Meta:
        domain = "mikro"
        document = "mutation create_sample($name: String, $creator: String, $meta: GenericScalar, $experiments: [ID]) {\n  createSample(\n    name: $name\n    creator: $creator\n    meta: $meta\n    experiments: $experiments\n  ) {\n    id\n    name\n    creator {\n      email\n    }\n  }\n}"

    class Config:
        frozen = True


class Create_experimentMutation(GraphQLObject):
    createExperiment: Optional[ExperimentFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nmutation create_experiment($name: String!, $creator: String, $meta: GenericScalar, $description: String) {\n  createExperiment(\n    name: $name\n    creator: $creator\n    description: $description\n    meta: $meta\n  ) {\n    ...Experiment\n  }\n}"

    class Config:
        frozen = True


async def aget_omero_file(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> OmeroFileFragment:
    """get_omero_file

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return (
        await aexecute(
            Get_omero_fileQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).omerofile


def get_omero_file(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> OmeroFileFragment:
    """get_omero_file

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return execute(
        Get_omero_fileQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).omerofile


async def aexpand_omerofile(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> OmeroFileFragment:
    """expand_omerofile

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return (
        await aexecute(
            Expand_omerofileQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).omerofile


def expand_omerofile(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> OmeroFileFragment:
    """expand_omerofile

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        OmeroFileFragment: The returned Mutation"""
    return execute(
        Expand_omerofileQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).omerofile


async def asearch_omerofile(
    search: str, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_omerofileQueryOmerofiles]:
    """search_omerofile

    My samples return all of the users samples attached to the current user

    Arguments:
        search (String): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_omerofileQueryOmerofiles: The returned Mutation"""
    return (
        await aexecute(
            Search_omerofileQuery,
            {"search": search},
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).omerofiles


def search_omerofile(
    search: str, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_omerofileQueryOmerofiles]:
    """search_omerofile

    My samples return all of the users samples attached to the current user

    Arguments:
        search (String): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_omerofileQueryOmerofiles: The returned Mutation"""
    return execute(
        Search_omerofileQuery, {"search": search}, mikrorath=mikrorath, as_task=as_task
    ).omerofiles


async def aexpand_representation(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> RepresentationFragment:
    """expand_representation

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return (
        await aexecute(
            Expand_representationQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).representation


def expand_representation(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> RepresentationFragment:
    """expand_representation

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return execute(
        Expand_representationQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).representation


async def aget_representation(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> RepresentationFragment:
    """get_representation

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return (
        await aexecute(
            Get_representationQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).representation


def get_representation(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> RepresentationFragment:
    """get_representation

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return execute(
        Get_representationQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).representation


async def asearch_representation(
    search: str = None, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_representationQueryRepresentations]:
    """search_representation

    All represetations

    Arguments:
        search (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_representationQueryRepresentations: The returned Mutation"""
    return (
        await aexecute(
            Search_representationQuery,
            {"search": search},
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).representations


def search_representation(
    search: str = None, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_representationQueryRepresentations]:
    """search_representation

    All represetations

    Arguments:
        search (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_representationQueryRepresentations: The returned Mutation"""
    return execute(
        Search_representationQuery,
        {"search": search},
        mikrorath=mikrorath,
        as_task=as_task,
    ).representations


async def aget_random_rep(
    mikrorath: MikroRath = None, as_task: bool = False
) -> RepresentationFragment:
    """get_random_rep

    Get a single representation by ID

    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return (
        await aexecute(Get_random_repQuery, {}, mikrorath=mikrorath, as_task=as_task)
    ).randomRepresentation


def get_random_rep(
    mikrorath: MikroRath = None, as_task: bool = False
) -> RepresentationFragment:
    """get_random_rep

    Get a single representation by ID

    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return execute(
        Get_random_repQuery, {}, mikrorath=mikrorath, as_task=as_task
    ).randomRepresentation


async def athumbnail(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ThumbnailFragment:
    """Thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return (
        await aexecute(ThumbnailQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task)
    ).thumbnail


def thumbnail(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ThumbnailFragment:
    """Thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return execute(
        ThumbnailQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).thumbnail


async def aexpand_thumbnail(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ThumbnailFragment:
    """expand_thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return (
        await aexecute(
            Expand_thumbnailQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).thumbnail


def expand_thumbnail(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ThumbnailFragment:
    """expand_thumbnail

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return execute(
        Expand_thumbnailQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).thumbnail


async def aget_rois(
    representation: str,
    type: List[RoiTypeInput] = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> List[ROIFragment]:
    """get_rois

    All represetations

    Arguments:
        representation (ID): ID
        type (List[RoiTypeInput], Optional): RoiTypeInput
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ROIFragment: The returned Mutation"""
    return (
        await aexecute(
            Get_roisQuery,
            {"representation": representation, "type": type},
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).rois


def get_rois(
    representation: str,
    type: List[RoiTypeInput] = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> List[ROIFragment]:
    """get_rois

    All represetations

    Arguments:
        representation (ID): ID
        type (List[RoiTypeInput], Optional): RoiTypeInput
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ROIFragment: The returned Mutation"""
    return execute(
        Get_roisQuery,
        {"representation": representation, "type": type},
        mikrorath=mikrorath,
        as_task=as_task,
    ).rois


async def atable(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> TableFragment:
    """Table

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        TableFragment: The returned Mutation"""
    return (
        await aexecute(TableQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task)
    ).table


def table(id: str, mikrorath: MikroRath = None, as_task: bool = False) -> TableFragment:
    """Table

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        TableFragment: The returned Mutation"""
    return execute(TableQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task).table


async def aexpand_table(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> TableFragment:
    """expand_table

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        TableFragment: The returned Mutation"""
    return (
        await aexecute(
            Expand_tableQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).table


def expand_table(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> TableFragment:
    """expand_table

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        TableFragment: The returned Mutation"""
    return execute(
        Expand_tableQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).table


async def asearch_tables(
    mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_tablesQueryTables]:
    """search_tables

    My samples return all of the users samples attached to the current user

    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_tablesQueryTables: The returned Mutation"""
    return (
        await aexecute(Search_tablesQuery, {}, mikrorath=mikrorath, as_task=as_task)
    ).tables


def search_tables(
    mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_tablesQueryTables]:
    """search_tables

    My samples return all of the users samples attached to the current user

    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_tablesQueryTables: The returned Mutation"""
    return execute(Search_tablesQuery, {}, mikrorath=mikrorath, as_task=as_task).tables


async def aget_sample(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> SampleFragment:
    """get_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        SampleFragment: The returned Mutation"""
    return (
        await aexecute(
            Get_sampleQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).sample


def get_sample(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> SampleFragment:
    """get_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        SampleFragment: The returned Mutation"""
    return execute(
        Get_sampleQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).sample


async def asearch_sample(
    search: str = None, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_sampleQuerySamples]:
    """search_sample

    All Samples

    Arguments:
        search (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_sampleQuerySamples: The returned Mutation"""
    return (
        await aexecute(
            Search_sampleQuery, {"search": search}, mikrorath=mikrorath, as_task=as_task
        )
    ).samples


def search_sample(
    search: str = None, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_sampleQuerySamples]:
    """search_sample

    All Samples

    Arguments:
        search (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_sampleQuerySamples: The returned Mutation"""
    return execute(
        Search_sampleQuery, {"search": search}, mikrorath=mikrorath, as_task=as_task
    ).samples


async def aexpand_sample(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> SampleFragment:
    """expand_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        SampleFragment: The returned Mutation"""
    return (
        await aexecute(
            Expand_sampleQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).sample


def expand_sample(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> SampleFragment:
    """expand_sample

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        SampleFragment: The returned Mutation"""
    return execute(
        Expand_sampleQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).sample


async def aget_experiment(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ExperimentFragment:
    """get_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ExperimentFragment: The returned Mutation"""
    return (
        await aexecute(
            Get_experimentQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).experiment


def get_experiment(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ExperimentFragment:
    """get_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ExperimentFragment: The returned Mutation"""
    return execute(
        Get_experimentQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).experiment


async def aexpand_experiment(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ExperimentFragment:
    """expand_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ExperimentFragment: The returned Mutation"""
    return (
        await aexecute(
            Expand_experimentQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
        )
    ).experiment


def expand_experiment(
    id: str, mikrorath: MikroRath = None, as_task: bool = False
) -> ExperimentFragment:
    """expand_experiment

    Get a single representation by ID

    Arguments:
        id (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ExperimentFragment: The returned Mutation"""
    return execute(
        Expand_experimentQuery, {"id": id}, mikrorath=mikrorath, as_task=as_task
    ).experiment


async def asearch_experiment(
    search: str = None, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_experimentQueryExperiments]:
    """search_experiment

    All Samples

    Arguments:
        search (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_experimentQueryExperiments: The returned Mutation"""
    return (
        await aexecute(
            Search_experimentQuery,
            {"search": search},
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).experiments


def search_experiment(
    search: str = None, mikrorath: MikroRath = None, as_task: bool = False
) -> List[Search_experimentQueryExperiments]:
    """search_experiment

    All Samples

    Arguments:
        search (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Search_experimentQueryExperiments: The returned Mutation"""
    return execute(
        Search_experimentQuery, {"search": search}, mikrorath=mikrorath, as_task=as_task
    ).experiments


async def awatch_rois(
    representation: str, mikrorath: MikroRath = None, as_task: bool = False
) -> AsyncIterator[Watch_roisSubscriptionRois]:
    """watch_rois



    Arguments:
        representation (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Watch_roisSubscriptionRois: The returned Mutation"""
    async for event in asubscribe(
        Watch_roisSubscription,
        {"representation": representation},
        mikrorath=mikrorath,
        as_task=as_task,
    ):
        yield event.rois


def watch_rois(
    representation: str, mikrorath: MikroRath = None, as_task: bool = False
) -> Iterator[Watch_roisSubscriptionRois]:
    """watch_rois



    Arguments:
        representation (ID): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Watch_roisSubscriptionRois: The returned Mutation"""
    for event in subscribe(
        Watch_roisSubscription,
        {"representation": representation},
        mikrorath=mikrorath,
        as_task=as_task,
    ):
        yield event.rois


async def awatch_samples(
    mikrorath: MikroRath = None, as_task: bool = False
) -> AsyncIterator[Watch_samplesSubscriptionMysamples]:
    """watch_samples



    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Watch_samplesSubscriptionMysamples: The returned Mutation"""
    async for event in asubscribe(
        Watch_samplesSubscription, {}, mikrorath=mikrorath, as_task=as_task
    ):
        yield event.mySamples


def watch_samples(
    mikrorath: MikroRath = None, as_task: bool = False
) -> Iterator[Watch_samplesSubscriptionMysamples]:
    """watch_samples



    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Watch_samplesSubscriptionMysamples: The returned Mutation"""
    for event in subscribe(
        Watch_samplesSubscription, {}, mikrorath=mikrorath, as_task=as_task
    ):
        yield event.mySamples


async def anegotiate(mikrorath: MikroRath = None, as_task: bool = False) -> Dict:
    """negotiate



    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Dict: The returned Mutation"""
    return (
        await aexecute(NegotiateMutation, {}, mikrorath=mikrorath, as_task=as_task)
    ).negotiate


def negotiate(mikrorath: MikroRath = None, as_task: bool = False) -> Dict:
    """negotiate



    Arguments:
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Dict: The returned Mutation"""
    return execute(
        NegotiateMutation, {}, mikrorath=mikrorath, as_task=as_task
    ).negotiate


async def aupload_bioimage(
    file: Upload, mikrorath: MikroRath = None, as_task: bool = False
) -> Upload_bioimageMutationUploadomerofile:
    """upload_bioimage



    Arguments:
        file (Upload): Upload
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Upload_bioimageMutationUploadomerofile: The returned Mutation"""
    return (
        await aexecute(
            Upload_bioimageMutation,
            {"file": file},
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).uploadOmeroFile


def upload_bioimage(
    file: Upload, mikrorath: MikroRath = None, as_task: bool = False
) -> Upload_bioimageMutationUploadomerofile:
    """upload_bioimage



    Arguments:
        file (Upload): Upload
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Upload_bioimageMutationUploadomerofile: The returned Mutation"""
    return execute(
        Upload_bioimageMutation, {"file": file}, mikrorath=mikrorath, as_task=as_task
    ).uploadOmeroFile


async def afrom_xarray(
    xarray: XArray,
    name: str = None,
    variety: RepresentationVarietyInput = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> RepresentationFragment:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        variety (RepresentationVarietyInput, Optional): RepresentationVarietyInput
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID
        omero (OmeroRepresentationInput, Optional): OmeroRepresentationInput
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return (
        await aexecute(
            From_xarrayMutation,
            {
                "xarray": xarray,
                "name": name,
                "variety": variety,
                "origins": origins,
                "tags": tags,
                "sample": sample,
                "omero": omero,
            },
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).fromXArray


def from_xarray(
    xarray: XArray,
    name: str = None,
    variety: RepresentationVarietyInput = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> RepresentationFragment:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): XArray
        name (String, Optional): String
        variety (RepresentationVarietyInput, Optional): RepresentationVarietyInput
        origins (List[ID], Optional): ID
        tags (List[String], Optional): String
        sample (ID, Optional): ID
        omero (OmeroRepresentationInput, Optional): OmeroRepresentationInput
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        RepresentationFragment: The returned Mutation"""
    return execute(
        From_xarrayMutation,
        {
            "xarray": xarray,
            "name": name,
            "variety": variety,
            "origins": origins,
            "tags": tags,
            "sample": sample,
            "omero": omero,
        },
        mikrorath=mikrorath,
        as_task=as_task,
    ).fromXArray


async def adouble_upload(
    xarray: XArray,
    name: str = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> Double_uploadMutation:
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
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Double_uploadMutation: The returned Mutation"""
    return await aexecute(
        Double_uploadMutation,
        {
            "xarray": xarray,
            "name": name,
            "origins": origins,
            "tags": tags,
            "sample": sample,
            "omero": omero,
        },
        mikrorath=mikrorath,
        as_task=as_task,
    )


def double_upload(
    xarray: XArray,
    name: str = None,
    origins: List[str] = None,
    tags: List[str] = None,
    sample: str = None,
    omero: OmeroRepresentationInput = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> Double_uploadMutation:
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
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Double_uploadMutation: The returned Mutation"""
    return execute(
        Double_uploadMutation,
        {
            "xarray": xarray,
            "name": name,
            "origins": origins,
            "tags": tags,
            "sample": sample,
            "omero": omero,
        },
        mikrorath=mikrorath,
        as_task=as_task,
    )


async def acreate_thumbnail(
    rep: str, file: File, mikrorath: MikroRath = None, as_task: bool = False
) -> ThumbnailFragment:
    """create_thumbnail



    Arguments:
        rep (ID): ID
        file (ImageFile): ImageFile
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return (
        await aexecute(
            Create_thumbnailMutation,
            {"rep": rep, "file": file},
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).uploadThumbnail


def create_thumbnail(
    rep: str, file: File, mikrorath: MikroRath = None, as_task: bool = False
) -> ThumbnailFragment:
    """create_thumbnail



    Arguments:
        rep (ID): ID
        file (ImageFile): ImageFile
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ThumbnailFragment: The returned Mutation"""
    return execute(
        Create_thumbnailMutation,
        {"rep": rep, "file": file},
        mikrorath=mikrorath,
        as_task=as_task,
    ).uploadThumbnail


async def acreate_metric(
    key: str,
    value: Dict,
    rep: str = None,
    sample: str = None,
    experiment: str = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> Create_metricMutationCreatemetric:
    """create_metric

    Creates a Representation

    Arguments:
        key (String): String
        value (GenericScalar): GenericScalar
        rep (ID, Optional): ID
        sample (ID, Optional): ID
        experiment (ID, Optional): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Create_metricMutationCreatemetric: The returned Mutation"""
    return (
        await aexecute(
            Create_metricMutation,
            {
                "key": key,
                "value": value,
                "rep": rep,
                "sample": sample,
                "experiment": experiment,
            },
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).createMetric


def create_metric(
    key: str,
    value: Dict,
    rep: str = None,
    sample: str = None,
    experiment: str = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> Create_metricMutationCreatemetric:
    """create_metric

    Creates a Representation

    Arguments:
        key (String): String
        value (GenericScalar): GenericScalar
        rep (ID, Optional): ID
        sample (ID, Optional): ID
        experiment (ID, Optional): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Create_metricMutationCreatemetric: The returned Mutation"""
    return execute(
        Create_metricMutation,
        {
            "key": key,
            "value": value,
            "rep": rep,
            "sample": sample,
            "experiment": experiment,
        },
        mikrorath=mikrorath,
        as_task=as_task,
    ).createMetric


async def acreate_roi(
    representation: str,
    vectors: List[InputVector],
    creator: str = None,
    type: RoiTypeInput = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> ROIFragment:
    """create_roi

    Creates a Sample

    Arguments:
        representation (ID): ID
        vectors (List[InputVector]): InputVector
        creator (ID, Optional): ID
        type (RoiTypeInput, Optional): RoiTypeInput
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ROIFragment: The returned Mutation"""
    return (
        await aexecute(
            Create_roiMutation,
            {
                "representation": representation,
                "vectors": vectors,
                "creator": creator,
                "type": type,
            },
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).createROI


def create_roi(
    representation: str,
    vectors: List[InputVector],
    creator: str = None,
    type: RoiTypeInput = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> ROIFragment:
    """create_roi

    Creates a Sample

    Arguments:
        representation (ID): ID
        vectors (List[InputVector]): InputVector
        creator (ID, Optional): ID
        type (RoiTypeInput, Optional): RoiTypeInput
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ROIFragment: The returned Mutation"""
    return execute(
        Create_roiMutation,
        {
            "representation": representation,
            "vectors": vectors,
            "creator": creator,
            "type": type,
        },
        mikrorath=mikrorath,
        as_task=as_task,
    ).createROI


async def afrom_df(
    df: DataFrame, mikrorath: MikroRath = None, as_task: bool = False
) -> TableFragment:
    """from_df

    Creates a Representation

    Arguments:
        df (DataFrame): DataFrame
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        TableFragment: The returned Mutation"""
    return (
        await aexecute(
            From_dfMutation, {"df": df}, mikrorath=mikrorath, as_task=as_task
        )
    ).fromDf


def from_df(
    df: DataFrame, mikrorath: MikroRath = None, as_task: bool = False
) -> TableFragment:
    """from_df

    Creates a Representation

    Arguments:
        df (DataFrame): DataFrame
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        TableFragment: The returned Mutation"""
    return execute(
        From_dfMutation, {"df": df}, mikrorath=mikrorath, as_task=as_task
    ).fromDf


async def acreate_sample(
    name: str = None,
    creator: str = None,
    meta: Dict = None,
    experiments: List[str] = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> Create_sampleMutationCreatesample:
    """create_sample

    Creates a Sample


    Arguments:
        name (String, Optional): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        experiments (List[ID], Optional): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Create_sampleMutationCreatesample: The returned Mutation"""
    return (
        await aexecute(
            Create_sampleMutation,
            {
                "name": name,
                "creator": creator,
                "meta": meta,
                "experiments": experiments,
            },
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).createSample


def create_sample(
    name: str = None,
    creator: str = None,
    meta: Dict = None,
    experiments: List[str] = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> Create_sampleMutationCreatesample:
    """create_sample

    Creates a Sample


    Arguments:
        name (String, Optional): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        experiments (List[ID], Optional): ID
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        Create_sampleMutationCreatesample: The returned Mutation"""
    return execute(
        Create_sampleMutation,
        {"name": name, "creator": creator, "meta": meta, "experiments": experiments},
        mikrorath=mikrorath,
        as_task=as_task,
    ).createSample


async def acreate_experiment(
    name: str,
    creator: str = None,
    meta: Dict = None,
    description: str = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> ExperimentFragment:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (String): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        description (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ExperimentFragment: The returned Mutation"""
    return (
        await aexecute(
            Create_experimentMutation,
            {
                "name": name,
                "creator": creator,
                "meta": meta,
                "description": description,
            },
            mikrorath=mikrorath,
            as_task=as_task,
        )
    ).createExperiment


def create_experiment(
    name: str,
    creator: str = None,
    meta: Dict = None,
    description: str = None,
    mikrorath: MikroRath = None,
    as_task: bool = False,
) -> ExperimentFragment:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (String): String
        creator (String, Optional): String
        meta (GenericScalar, Optional): GenericScalar
        description (String, Optional): String
        mikrorath (mikro.mikro.MikroRath): The mikro rath client
        as_task (bool): Should we return a task

    Returns:
        ExperimentFragment: The returned Mutation"""
    return execute(
        Create_experimentMutation,
        {"name": name, "creator": creator, "meta": meta, "description": description},
        mikrorath=mikrorath,
        as_task=as_task,
    ).createExperiment
