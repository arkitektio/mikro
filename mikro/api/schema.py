from enum import Enum
from mikro.scalars import File, XArray, DataFrame, Upload, Store
from typing import Optional, List, AsyncIterator, Literal, Iterator, Dict
from pydantic import BaseModel, Field
from mikro.funcs import execute, aexecute, subscribe, asubscribe
from mikro.mikro import MikroRath
from mikro.traits import OmeroFile, Thumbnail, Experiment, Representation, Sample, Table


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


class RepresentationFragmentSample(Sample, BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str

    class Config:
        frozen = True


class RepresentationFragment(Representation, BaseModel):
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


class ThumbnailFragment(Thumbnail, BaseModel):
    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    id: str
    image: Optional[str]

    class Config:
        frozen = True


class ROIFragmentVectors(BaseModel):
    typename: Optional[Literal["Vector"]] = Field(alias="__typename")
    x: Optional[float]
    "X-coordinate"
    y: Optional[float]
    "Y-coordinate"
    z: Optional[float]
    "Z-coordinate"

    class Config:
        frozen = True


class ROIFragmentRepresentation(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class ROIFragment(BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    id: str
    vectors: Optional[List[Optional[ROIFragmentVectors]]]
    type: ROIType
    "The Representation can have varying types, consult your API"
    representation: Optional[ROIFragmentRepresentation]

    class Config:
        frozen = True


class TableFragmentCreator(BaseModel):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class TableFragmentSample(Sample, BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class TableFragmentRepresentation(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class TableFragmentExperiment(Experiment, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class TableFragment(Table, BaseModel):
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


class SampleFragmentRepresentations(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class SampleFragmentExperiments(Experiment, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class SampleFragment(Sample, BaseModel):
    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    id: str
    representations: Optional[List[Optional[SampleFragmentRepresentations]]]
    meta: Optional[Dict]
    experiments: List[SampleFragmentExperiments]

    class Config:
        frozen = True


class OmeroFileFragment(OmeroFile, BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    name: str
    file: Optional[File]

    class Config:
        frozen = True


class ExperimentFragmentCreator(BaseModel):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class ExperimentFragment(Experiment, BaseModel):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str
    name: str
    creator: Optional[ExperimentFragmentCreator]
    meta: Optional[Dict]

    class Config:
        frozen = True


class Get_omero_fileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n}\n\nquery get_omero_file($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"

    class Config:
        frozen = True


class Expand_omerofileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n}\n\nquery expand_omerofile($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"

    class Config:
        frozen = True


class Search_omerofileQueryOmerofiles(OmeroFile, BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    label: str

    class Config:
        frozen = True


class Search_omerofileQuery(BaseModel):
    omerofiles: Optional[List[Optional[Search_omerofileQueryOmerofiles]]]
    "My samples return all of the users samples attached to the current user"

    class Meta:
        domain = "mikro"
        document = "query search_omerofile($search: String!) {\n  omerofiles(name: $search) {\n    id: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Expand_representationQuery(BaseModel):
    representation: Optional[RepresentationFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class Get_representationQuery(BaseModel):
    representation: Optional[RepresentationFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery get_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class Search_representationQueryRepresentations(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    value: str
    label: Optional[str]
    "Cleartext name"

    class Config:
        frozen = True


class Search_representationQuery(BaseModel):
    representations: Optional[List[Optional[Search_representationQueryRepresentations]]]
    "All represetations"

    class Meta:
        domain = "mikro"
        document = "query search_representation($search: String) {\n  representations(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Get_random_repQuery(BaseModel):
    randomRepresentation: Optional[RepresentationFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class ThumbnailQuery(BaseModel):
    thumbnail: Optional[ThumbnailFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery Thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"

    class Config:
        frozen = True


class Expand_thumbnailQuery(BaseModel):
    thumbnail: Optional[ThumbnailFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery expand_thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"

    class Config:
        frozen = True


class Get_roisQuery(BaseModel):
    rois: Optional[List[Optional[ROIFragment]]]
    "All represetations"

    class Meta:
        domain = "mikro"
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n}\n\nquery get_rois($representation: ID!, $type: [RoiTypeInput]) {\n  rois(representation: $representation, type: $type) {\n    ...ROI\n  }\n}"

    class Config:
        frozen = True


class TableQuery(BaseModel):
    table: Optional[TableFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery Table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"

    class Config:
        frozen = True


class Expand_tableQuery(BaseModel):
    table: Optional[TableFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery expand_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"

    class Config:
        frozen = True


class Search_tablesQueryTables(Table, BaseModel):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: str
    label: str

    class Config:
        frozen = True


class Search_tablesQuery(BaseModel):
    tables: Optional[List[Optional[Search_tablesQueryTables]]]
    "My samples return all of the users samples attached to the current user"

    class Meta:
        domain = "mikro"
        document = (
            "query search_tables {\n  tables {\n    id: id\n    label: name\n  }\n}"
        )

    class Config:
        frozen = True


class Get_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery get_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"

    class Config:
        frozen = True


class Search_sampleQuerySamples(Sample, BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    value: str
    label: str

    class Config:
        frozen = True


class Search_sampleQuery(BaseModel):
    samples: Optional[List[Optional[Search_sampleQuerySamples]]]
    "All Samples"

    class Meta:
        domain = "mikro"
        document = "query search_sample($search: String) {\n  samples(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Expand_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery expand_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"

    class Config:
        frozen = True


class Get_experimentQuery(BaseModel):
    experiment: Optional[ExperimentFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery get_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"

    class Config:
        frozen = True


class Expand_experimentQuery(BaseModel):
    experiment: Optional[ExperimentFragment]
    "Get a single representation by ID"

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery expand_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"

    class Config:
        frozen = True


class Search_experimentQueryExperiments(Experiment, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: str
    label: str

    class Config:
        frozen = True


class Search_experimentQuery(BaseModel):
    experiments: Optional[List[Optional[Search_experimentQueryExperiments]]]
    "All Samples"

    class Meta:
        domain = "mikro"
        document = "query search_experiment($search: String) {\n  experiments(name: $search, limit: 30) {\n    id: id\n    label: name\n  }\n}"

    class Config:
        frozen = True


class Watch_roisSubscriptionRois(BaseModel):
    typename: Optional[Literal["RoiEvent"]] = Field(alias="__typename")
    update: Optional[ROIFragment]
    delete: Optional[str]
    create: Optional[ROIFragment]

    class Config:
        frozen = True


class Watch_roisSubscription(BaseModel):
    rois: Optional[Watch_roisSubscriptionRois]

    class Meta:
        domain = "mikro"
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n}\n\nsubscription watch_rois($representation: ID!) {\n  rois(representation: $representation) {\n    update {\n      ...ROI\n    }\n    delete\n    create {\n      ...ROI\n    }\n  }\n}"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesUpdateExperiments(Experiment, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesUpdate(Sample, BaseModel):
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


class Watch_samplesSubscriptionMysamplesCreateExperiments(Experiment, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesCreate(Sample, BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    experiments: List[Watch_samplesSubscriptionMysamplesCreateExperiments]

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamples(BaseModel):
    typename: Optional[Literal["SamplesEvent"]] = Field(alias="__typename")
    update: Optional[Watch_samplesSubscriptionMysamplesUpdate]
    create: Optional[Watch_samplesSubscriptionMysamplesCreate]

    class Config:
        frozen = True


class Watch_samplesSubscription(BaseModel):
    mySamples: Optional[Watch_samplesSubscriptionMysamples]

    class Meta:
        domain = "mikro"
        document = "subscription watch_samples {\n  mySamples {\n    update {\n      id\n      name\n      experiments {\n        name\n      }\n    }\n    create {\n      name\n      experiments {\n        name\n      }\n    }\n  }\n}"

    class Config:
        frozen = True


class NegotiateMutation(BaseModel):
    negotiate: Optional[Dict]

    class Meta:
        domain = "mikro"
        document = "mutation negotiate {\n  negotiate\n}"

    class Config:
        frozen = True


class Upload_bioimageMutationUploadomerofile(OmeroFile, BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: str
    file: Optional[File]
    type: OmeroFileType
    name: str

    class Config:
        frozen = True


class Upload_bioimageMutation(BaseModel):
    uploadOmeroFile: Optional[Upload_bioimageMutationUploadomerofile]

    class Meta:
        domain = "mikro"
        document = "mutation upload_bioimage($file: Upload!) {\n  uploadOmeroFile(file: $file) {\n    id\n    file\n    type\n    name\n  }\n}"

    class Config:
        frozen = True


class From_xarrayMutation(BaseModel):
    fromXArray: Optional[RepresentationFragment]
    "Creates a Representation"

    class Meta:
        domain = "mikro"
        document = "fragment Representation on Representation {\n  sample {\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n}\n\nmutation from_xarray($xarray: XArray!, $name: String, $variety: RepresentationVarietyInput, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n    variety: $variety\n  ) {\n    ...Representation\n  }\n}"

    class Config:
        frozen = True


class Double_uploadMutationX(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[Store]

    class Config:
        frozen = True


class Double_uploadMutationY(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str
    store: Optional[Store]

    class Config:
        frozen = True


class Double_uploadMutation(BaseModel):
    x: Optional[Double_uploadMutationX]
    "Creates a Representation"
    y: Optional[Double_uploadMutationY]
    "Creates a Representation"

    class Meta:
        domain = "mikro"
        document = "mutation double_upload($xarray: XArray!, $name: String, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  x: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n  y: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n}"

    class Config:
        frozen = True


class Create_thumbnailMutation(BaseModel):
    uploadThumbnail: Optional[ThumbnailFragment]

    class Meta:
        domain = "mikro"
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nmutation create_thumbnail($rep: ID!, $file: ImageFile!) {\n  uploadThumbnail(rep: $rep, file: $file) {\n    ...Thumbnail\n  }\n}"

    class Config:
        frozen = True


class Create_metricMutationCreatemetricRep(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class Create_metricMutationCreatemetricCreator(BaseModel):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    id: str

    class Config:
        frozen = True


class Create_metricMutationCreatemetric(BaseModel):
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


class Create_metricMutation(BaseModel):
    createMetric: Optional[Create_metricMutationCreatemetric]
    "Creates a Representation"

    class Meta:
        domain = "mikro"
        document = "mutation create_metric($rep: ID, $sample: ID, $experiment: ID, $key: String!, $value: GenericScalar!) {\n  createMetric(\n    rep: $rep\n    sample: $sample\n    experiment: $experiment\n    key: $key\n    value: $value\n  ) {\n    id\n    rep {\n      id\n    }\n    key\n    value\n    creator {\n      id\n    }\n    createdAt\n  }\n}"

    class Config:
        frozen = True


class Create_roiMutation(BaseModel):
    createROI: Optional[ROIFragment]
    "Creates a Sample"

    class Meta:
        domain = "mikro"
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n}\n\nmutation create_roi($representation: ID!, $vectors: [InputVector]!, $creator: ID, $type: RoiTypeInput) {\n  createROI(\n    representation: $representation\n    vectors: $vectors\n    type: $type\n    creator: $creator\n  ) {\n    ...ROI\n  }\n}"

    class Config:
        frozen = True


class From_dfMutation(BaseModel):
    fromDf: Optional[TableFragment]
    "Creates a Representation"

    class Meta:
        domain = "mikro"
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nmutation from_df($df: DataFrame!) {\n  fromDf(df: $df) {\n    ...Table\n  }\n}"

    class Config:
        frozen = True


class Create_sampleMutationCreatesampleCreator(BaseModel):
    """A reflection on the real User"""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class Create_sampleMutationCreatesample(Sample, BaseModel):
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


class Create_sampleMutation(BaseModel):
    createSample: Optional[Create_sampleMutationCreatesample]
    "Creates a Sample\n    "

    class Meta:
        domain = "mikro"
        document = "mutation create_sample($name: String, $creator: String, $meta: GenericScalar, $experiments: [ID]) {\n  createSample(\n    name: $name\n    creator: $creator\n    meta: $meta\n    experiments: $experiments\n  ) {\n    id\n    name\n    creator {\n      email\n    }\n  }\n}"

    class Config:
        frozen = True


class Create_experimentMutation(BaseModel):
    createExperiment: Optional[ExperimentFragment]
    "Create an experiment (only signed in users)"

    class Meta:
        domain = "mikro"
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nmutation create_experiment($name: String!, $creator: String, $meta: GenericScalar, $description: String) {\n  createExperiment(\n    name: $name\n    creator: $creator\n    description: $description\n    meta: $meta\n  ) {\n    ...Experiment\n  }\n}"

    class Config:
        frozen = True


async def aget_omero_file(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[OmeroFileFragment]:
    """get_omero_file

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        OmeroFileFragment"""
    return (
        await aexecute(Get_omero_fileQuery, {"id": id}, mikrorath=mikrorath)
    ).omerofile


def get_omero_file(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[OmeroFileFragment]:
    """get_omero_file

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        OmeroFileFragment"""
    return execute(Get_omero_fileQuery, {"id": id}, mikrorath=mikrorath).omerofile


async def aexpand_omerofile(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[OmeroFileFragment]:
    """expand_omerofile

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        OmeroFileFragment"""
    return (
        await aexecute(Expand_omerofileQuery, {"id": id}, mikrorath=mikrorath)
    ).omerofile


def expand_omerofile(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[OmeroFileFragment]:
    """expand_omerofile

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        OmeroFileFragment"""
    return execute(Expand_omerofileQuery, {"id": id}, mikrorath=mikrorath).omerofile


async def asearch_omerofile(
    search: Optional[str], mikrorath: MikroRath = None
) -> Optional[List[Search_omerofileQueryOmerofiles]]:
    """search_omerofile

    My samples return all of the users samples attached to the current user

    Arguments:
        search (str): search
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_omerofileQueryOmerofiles"""
    return (
        await aexecute(Search_omerofileQuery, {"search": search}, mikrorath=mikrorath)
    ).omerofiles


def search_omerofile(
    search: Optional[str], mikrorath: MikroRath = None
) -> Optional[List[Search_omerofileQueryOmerofiles]]:
    """search_omerofile

    My samples return all of the users samples attached to the current user

    Arguments:
        search (str): search
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_omerofileQueryOmerofiles"""
    return execute(
        Search_omerofileQuery, {"search": search}, mikrorath=mikrorath
    ).omerofiles


async def aexpand_representation(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """expand_representation

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
    return (
        await aexecute(Expand_representationQuery, {"id": id}, mikrorath=mikrorath)
    ).representation


def expand_representation(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """expand_representation

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
    return execute(
        Expand_representationQuery, {"id": id}, mikrorath=mikrorath
    ).representation


async def aget_representation(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """get_representation

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
    return (
        await aexecute(Get_representationQuery, {"id": id}, mikrorath=mikrorath)
    ).representation


def get_representation(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """get_representation

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
    return execute(
        Get_representationQuery, {"id": id}, mikrorath=mikrorath
    ).representation


async def asearch_representation(
    search: Optional[str] = None, mikrorath: MikroRath = None
) -> Optional[List[Search_representationQueryRepresentations]]:
    """search_representation

    All represetations

    Arguments:
        search (Optional[str], optional): search.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_representationQueryRepresentations"""
    return (
        await aexecute(
            Search_representationQuery, {"search": search}, mikrorath=mikrorath
        )
    ).representations


def search_representation(
    search: Optional[str] = None, mikrorath: MikroRath = None
) -> Optional[List[Search_representationQueryRepresentations]]:
    """search_representation

    All represetations

    Arguments:
        search (Optional[str], optional): search.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_representationQueryRepresentations"""
    return execute(
        Search_representationQuery, {"search": search}, mikrorath=mikrorath
    ).representations


async def aget_random_rep(
    mikrorath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """get_random_rep

    Get a single representation by ID

    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
    return (
        await aexecute(Get_random_repQuery, {}, mikrorath=mikrorath)
    ).randomRepresentation


def get_random_rep(mikrorath: MikroRath = None) -> Optional[RepresentationFragment]:
    """get_random_rep

    Get a single representation by ID

    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
    return execute(Get_random_repQuery, {}, mikrorath=mikrorath).randomRepresentation


async def athumbnail(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """Thumbnail

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ThumbnailFragment"""
    return (await aexecute(ThumbnailQuery, {"id": id}, mikrorath=mikrorath)).thumbnail


def thumbnail(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """Thumbnail

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ThumbnailFragment"""
    return execute(ThumbnailQuery, {"id": id}, mikrorath=mikrorath).thumbnail


async def aexpand_thumbnail(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """expand_thumbnail

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ThumbnailFragment"""
    return (
        await aexecute(Expand_thumbnailQuery, {"id": id}, mikrorath=mikrorath)
    ).thumbnail


def expand_thumbnail(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """expand_thumbnail

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ThumbnailFragment"""
    return execute(Expand_thumbnailQuery, {"id": id}, mikrorath=mikrorath).thumbnail


async def aget_rois(
    representation: Optional[str],
    type: Optional[List[Optional[RoiTypeInput]]] = None,
    mikrorath: MikroRath = None,
) -> Optional[List[ROIFragment]]:
    """get_rois

    All represetations

    Arguments:
        representation (str): representation
        type (Optional[List[Optional[RoiTypeInput]]], optional): type.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ROIFragment"""
    return (
        await aexecute(
            Get_roisQuery,
            {"representation": representation, "type": type},
            mikrorath=mikrorath,
        )
    ).rois


def get_rois(
    representation: Optional[str],
    type: Optional[List[Optional[RoiTypeInput]]] = None,
    mikrorath: MikroRath = None,
) -> Optional[List[ROIFragment]]:
    """get_rois

    All represetations

    Arguments:
        representation (str): representation
        type (Optional[List[Optional[RoiTypeInput]]], optional): type.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ROIFragment"""
    return execute(
        Get_roisQuery,
        {"representation": representation, "type": type},
        mikrorath=mikrorath,
    ).rois


async def atable(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[TableFragment]:
    """Table

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        TableFragment"""
    return (await aexecute(TableQuery, {"id": id}, mikrorath=mikrorath)).table


def table(id: Optional[str], mikrorath: MikroRath = None) -> Optional[TableFragment]:
    """Table

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        TableFragment"""
    return execute(TableQuery, {"id": id}, mikrorath=mikrorath).table


async def aexpand_table(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[TableFragment]:
    """expand_table

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        TableFragment"""
    return (await aexecute(Expand_tableQuery, {"id": id}, mikrorath=mikrorath)).table


def expand_table(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[TableFragment]:
    """expand_table

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        TableFragment"""
    return execute(Expand_tableQuery, {"id": id}, mikrorath=mikrorath).table


async def asearch_tables(
    mikrorath: MikroRath = None,
) -> Optional[List[Search_tablesQueryTables]]:
    """search_tables

    My samples return all of the users samples attached to the current user

    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_tablesQueryTables"""
    return (await aexecute(Search_tablesQuery, {}, mikrorath=mikrorath)).tables


def search_tables(
    mikrorath: MikroRath = None,
) -> Optional[List[Search_tablesQueryTables]]:
    """search_tables

    My samples return all of the users samples attached to the current user

    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_tablesQueryTables"""
    return execute(Search_tablesQuery, {}, mikrorath=mikrorath).tables


async def aget_sample(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[SampleFragment]:
    """get_sample

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        SampleFragment"""
    return (await aexecute(Get_sampleQuery, {"id": id}, mikrorath=mikrorath)).sample


def get_sample(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[SampleFragment]:
    """get_sample

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        SampleFragment"""
    return execute(Get_sampleQuery, {"id": id}, mikrorath=mikrorath).sample


async def asearch_sample(
    search: Optional[str] = None, mikrorath: MikroRath = None
) -> Optional[List[Search_sampleQuerySamples]]:
    """search_sample

    All Samples

    Arguments:
        search (Optional[str], optional): search.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_sampleQuerySamples"""
    return (
        await aexecute(Search_sampleQuery, {"search": search}, mikrorath=mikrorath)
    ).samples


def search_sample(
    search: Optional[str] = None, mikrorath: MikroRath = None
) -> Optional[List[Search_sampleQuerySamples]]:
    """search_sample

    All Samples

    Arguments:
        search (Optional[str], optional): search.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_sampleQuerySamples"""
    return execute(Search_sampleQuery, {"search": search}, mikrorath=mikrorath).samples


async def aexpand_sample(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[SampleFragment]:
    """expand_sample

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        SampleFragment"""
    return (await aexecute(Expand_sampleQuery, {"id": id}, mikrorath=mikrorath)).sample


def expand_sample(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[SampleFragment]:
    """expand_sample

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        SampleFragment"""
    return execute(Expand_sampleQuery, {"id": id}, mikrorath=mikrorath).sample


async def aget_experiment(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ExperimentFragment]:
    """get_experiment

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ExperimentFragment"""
    return (
        await aexecute(Get_experimentQuery, {"id": id}, mikrorath=mikrorath)
    ).experiment


def get_experiment(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ExperimentFragment]:
    """get_experiment

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ExperimentFragment"""
    return execute(Get_experimentQuery, {"id": id}, mikrorath=mikrorath).experiment


async def aexpand_experiment(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ExperimentFragment]:
    """expand_experiment

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ExperimentFragment"""
    return (
        await aexecute(Expand_experimentQuery, {"id": id}, mikrorath=mikrorath)
    ).experiment


def expand_experiment(
    id: Optional[str], mikrorath: MikroRath = None
) -> Optional[ExperimentFragment]:
    """expand_experiment

    Get a single representation by ID

    Arguments:
        id (str): id
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ExperimentFragment"""
    return execute(Expand_experimentQuery, {"id": id}, mikrorath=mikrorath).experiment


async def asearch_experiment(
    search: Optional[str] = None, mikrorath: MikroRath = None
) -> Optional[List[Search_experimentQueryExperiments]]:
    """search_experiment

    All Samples

    Arguments:
        search (Optional[str], optional): search.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_experimentQueryExperiments"""
    return (
        await aexecute(Search_experimentQuery, {"search": search}, mikrorath=mikrorath)
    ).experiments


def search_experiment(
    search: Optional[str] = None, mikrorath: MikroRath = None
) -> Optional[List[Search_experimentQueryExperiments]]:
    """search_experiment

    All Samples

    Arguments:
        search (Optional[str], optional): search.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Search_experimentQueryExperiments"""
    return execute(
        Search_experimentQuery, {"search": search}, mikrorath=mikrorath
    ).experiments


async def awatch_rois(
    representation: Optional[str], mikrorath: MikroRath = None
) -> AsyncIterator[Optional[Watch_roisSubscriptionRois]]:
    """watch_rois



    Arguments:
        representation (str): representation
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Watch_roisSubscriptionRois"""
    async for event in asubscribe(
        Watch_roisSubscription, {"representation": representation}, mikrorath=mikrorath
    ):
        yield event.rois


def watch_rois(
    representation: Optional[str], mikrorath: MikroRath = None
) -> Iterator[Optional[Watch_roisSubscriptionRois]]:
    """watch_rois



    Arguments:
        representation (str): representation
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Watch_roisSubscriptionRois"""
    for event in subscribe(
        Watch_roisSubscription, {"representation": representation}, mikrorath=mikrorath
    ):
        yield event.rois


async def awatch_samples(
    mikrorath: MikroRath = None,
) -> AsyncIterator[Optional[Watch_samplesSubscriptionMysamples]]:
    """watch_samples



    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Watch_samplesSubscriptionMysamples"""
    async for event in asubscribe(Watch_samplesSubscription, {}, mikrorath=mikrorath):
        yield event.mySamples


def watch_samples(
    mikrorath: MikroRath = None,
) -> Iterator[Optional[Watch_samplesSubscriptionMysamples]]:
    """watch_samples



    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Watch_samplesSubscriptionMysamples"""
    for event in subscribe(Watch_samplesSubscription, {}, mikrorath=mikrorath):
        yield event.mySamples


async def anegotiate(mikrorath: MikroRath = None) -> Optional[Dict]:
    """negotiate



    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Dict"""
    return (await aexecute(NegotiateMutation, {}, mikrorath=mikrorath)).negotiate


def negotiate(mikrorath: MikroRath = None) -> Optional[Dict]:
    """negotiate



    Arguments:
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Dict"""
    return execute(NegotiateMutation, {}, mikrorath=mikrorath).negotiate


async def aupload_bioimage(
    file: Optional[Upload], mikrorath: MikroRath = None
) -> Optional[Upload_bioimageMutationUploadomerofile]:
    """upload_bioimage



    Arguments:
        file (Upload): file
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Upload_bioimageMutationUploadomerofile"""
    return (
        await aexecute(Upload_bioimageMutation, {"file": file}, mikrorath=mikrorath)
    ).uploadOmeroFile


def upload_bioimage(
    file: Optional[Upload], mikrorath: MikroRath = None
) -> Optional[Upload_bioimageMutationUploadomerofile]:
    """upload_bioimage



    Arguments:
        file (Upload): file
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Upload_bioimageMutationUploadomerofile"""
    return execute(
        Upload_bioimageMutation, {"file": file}, mikrorath=mikrorath
    ).uploadOmeroFile


async def afrom_xarray(
    xarray: Optional[XArray],
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[str]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[str] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    mikrorath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): xarray
        name (Optional[str], optional): name.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        origins (Optional[List[Optional[str]]], optional): origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[str], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
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
        )
    ).fromXArray


def from_xarray(
    xarray: Optional[XArray],
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[str]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[str] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    mikrorath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """from_xarray

    Creates a Representation

    Arguments:
        xarray (XArray): xarray
        name (Optional[str], optional): name.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        origins (Optional[List[Optional[str]]], optional): origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[str], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        RepresentationFragment"""
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
    ).fromXArray


async def adouble_upload(
    xarray: Optional[XArray],
    name: Optional[str] = None,
    origins: Optional[List[Optional[str]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[str] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    mikrorath: MikroRath = None,
) -> Double_uploadMutation:
    """double_upload


     x: Creates a Representation
     y: Creates a Representation

    Arguments:
        xarray (XArray): xarray
        name (Optional[str], optional): name.
        origins (Optional[List[Optional[str]]], optional): origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[str], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Double_uploadMutation"""
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
    )


def double_upload(
    xarray: Optional[XArray],
    name: Optional[str] = None,
    origins: Optional[List[Optional[str]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[str] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    mikrorath: MikroRath = None,
) -> Double_uploadMutation:
    """double_upload


     x: Creates a Representation
     y: Creates a Representation

    Arguments:
        xarray (XArray): xarray
        name (Optional[str], optional): name.
        origins (Optional[List[Optional[str]]], optional): origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[str], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Double_uploadMutation"""
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
    )


async def acreate_thumbnail(
    rep: Optional[str], file: Optional[File], mikrorath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """create_thumbnail



    Arguments:
        rep (str): rep
        file (File): file
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ThumbnailFragment"""
    return (
        await aexecute(
            Create_thumbnailMutation, {"rep": rep, "file": file}, mikrorath=mikrorath
        )
    ).uploadThumbnail


def create_thumbnail(
    rep: Optional[str], file: Optional[File], mikrorath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """create_thumbnail



    Arguments:
        rep (str): rep
        file (File): file
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ThumbnailFragment"""
    return execute(
        Create_thumbnailMutation, {"rep": rep, "file": file}, mikrorath=mikrorath
    ).uploadThumbnail


async def acreate_metric(
    key: Optional[str],
    value: Optional[Dict],
    rep: Optional[str] = None,
    sample: Optional[str] = None,
    experiment: Optional[str] = None,
    mikrorath: MikroRath = None,
) -> Optional[Create_metricMutationCreatemetric]:
    """create_metric

    Creates a Representation

    Arguments:
        key (str): key
        value (Dict): value
        rep (Optional[str], optional): rep.
        sample (Optional[str], optional): sample.
        experiment (Optional[str], optional): experiment.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Create_metricMutationCreatemetric"""
    return (
        await aexecute(
            Create_metricMutation,
            {
                "rep": rep,
                "sample": sample,
                "experiment": experiment,
                "key": key,
                "value": value,
            },
            mikrorath=mikrorath,
        )
    ).createMetric


def create_metric(
    key: Optional[str],
    value: Optional[Dict],
    rep: Optional[str] = None,
    sample: Optional[str] = None,
    experiment: Optional[str] = None,
    mikrorath: MikroRath = None,
) -> Optional[Create_metricMutationCreatemetric]:
    """create_metric

    Creates a Representation

    Arguments:
        key (str): key
        value (Dict): value
        rep (Optional[str], optional): rep.
        sample (Optional[str], optional): sample.
        experiment (Optional[str], optional): experiment.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Create_metricMutationCreatemetric"""
    return execute(
        Create_metricMutation,
        {
            "rep": rep,
            "sample": sample,
            "experiment": experiment,
            "key": key,
            "value": value,
        },
        mikrorath=mikrorath,
    ).createMetric


async def acreate_roi(
    representation: Optional[str],
    vectors: Optional[List[Optional[InputVector]]],
    creator: Optional[str] = None,
    type: Optional[RoiTypeInput] = None,
    mikrorath: MikroRath = None,
) -> Optional[ROIFragment]:
    """create_roi

    Creates a Sample

    Arguments:
        representation (str): representation
        vectors (List[Optional[InputVector]]): vectors
        creator (Optional[str], optional): creator.
        type (Optional[RoiTypeInput], optional): type.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ROIFragment"""
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
        )
    ).createROI


def create_roi(
    representation: Optional[str],
    vectors: Optional[List[Optional[InputVector]]],
    creator: Optional[str] = None,
    type: Optional[RoiTypeInput] = None,
    mikrorath: MikroRath = None,
) -> Optional[ROIFragment]:
    """create_roi

    Creates a Sample

    Arguments:
        representation (str): representation
        vectors (List[Optional[InputVector]]): vectors
        creator (Optional[str], optional): creator.
        type (Optional[RoiTypeInput], optional): type.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ROIFragment"""
    return execute(
        Create_roiMutation,
        {
            "representation": representation,
            "vectors": vectors,
            "creator": creator,
            "type": type,
        },
        mikrorath=mikrorath,
    ).createROI


async def afrom_df(
    df: Optional[DataFrame], mikrorath: MikroRath = None
) -> Optional[TableFragment]:
    """from_df

    Creates a Representation

    Arguments:
        df (DataFrame): df
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        TableFragment"""
    return (await aexecute(From_dfMutation, {"df": df}, mikrorath=mikrorath)).fromDf


def from_df(
    df: Optional[DataFrame], mikrorath: MikroRath = None
) -> Optional[TableFragment]:
    """from_df

    Creates a Representation

    Arguments:
        df (DataFrame): df
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        TableFragment"""
    return execute(From_dfMutation, {"df": df}, mikrorath=mikrorath).fromDf


async def acreate_sample(
    name: Optional[str] = None,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    experiments: Optional[List[Optional[str]]] = None,
    mikrorath: MikroRath = None,
) -> Optional[Create_sampleMutationCreatesample]:
    """create_sample

    Creates a Sample


    Arguments:
        name (Optional[str], optional): name.
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        experiments (Optional[List[Optional[str]]], optional): experiments.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Create_sampleMutationCreatesample"""
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
        )
    ).createSample


def create_sample(
    name: Optional[str] = None,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    experiments: Optional[List[Optional[str]]] = None,
    mikrorath: MikroRath = None,
) -> Optional[Create_sampleMutationCreatesample]:
    """create_sample

    Creates a Sample


    Arguments:
        name (Optional[str], optional): name.
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        experiments (Optional[List[Optional[str]]], optional): experiments.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        Create_sampleMutationCreatesample"""
    return execute(
        Create_sampleMutation,
        {"name": name, "creator": creator, "meta": meta, "experiments": experiments},
        mikrorath=mikrorath,
    ).createSample


async def acreate_experiment(
    name: Optional[str],
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    description: Optional[str] = None,
    mikrorath: MikroRath = None,
) -> Optional[ExperimentFragment]:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (str): name
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        description (Optional[str], optional): description.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ExperimentFragment"""
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
        )
    ).createExperiment


def create_experiment(
    name: Optional[str],
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    description: Optional[str] = None,
    mikrorath: MikroRath = None,
) -> Optional[ExperimentFragment]:
    """create_experiment

    Create an experiment (only signed in users)

    Arguments:
        name (str): name
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        description (Optional[str], optional): description.
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        ExperimentFragment"""
    return execute(
        Create_experimentMutation,
        {"name": name, "creator": creator, "meta": meta, "description": description},
        mikrorath=mikrorath,
    ).createExperiment
