from datetime import datetime
from typing import Iterator, AsyncIterator, Literal, Optional, List, Dict
from enum import Enum
from mikro.scalars import (
    ArrayInput,
    DataFrame,
    FeatureValue,
    File,
    MetricValue,
    Parquet,
    Store,
)
from mikro.funcs import subscribe, asubscribe, execute, aexecute
from mikro.traits import Representation, Table, ROI, Vectorizable
from pydantic import Field, BaseModel
from mikro.rath import MikroRath
from rath.scalars import ID


class CommentableModels(str, Enum):
    GRUNNLAG_USERMETA = "GRUNNLAG_USERMETA"
    GRUNNLAG_ANTIBODY = "GRUNNLAG_ANTIBODY"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_ROI = "GRUNNLAG_ROI"
    GRUNNLAG_LABEL = "GRUNNLAG_LABEL"
    GRUNNLAG_FEATURE = "GRUNNLAG_FEATURE"
    BORD_TABLE = "BORD_TABLE"


class SharableModels(str, Enum):
    GRUNNLAG_USERMETA = "GRUNNLAG_USERMETA"
    GRUNNLAG_ANTIBODY = "GRUNNLAG_ANTIBODY"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_ROI = "GRUNNLAG_ROI"
    GRUNNLAG_LABEL = "GRUNNLAG_LABEL"
    GRUNNLAG_FEATURE = "GRUNNLAG_FEATURE"
    BORD_TABLE = "BORD_TABLE"


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


class PandasDType(str, Enum):
    OBJECT = "OBJECT"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    BOOL = "BOOL"
    CATEGORY = "CATEGORY"
    DATETIME65 = "DATETIME65"
    TIMEDELTA = "TIMEDELTA"
    UNICODE = "UNICODE"


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


class DescendendInput(BaseModel):
    children: Optional[List[Optional["DescendendInput"]]]
    typename: Optional[str]
    "The type of the descendent"
    user: Optional[str]
    "The user that is mentioned"
    bold: Optional[bool]
    "Is this a bold leaf?"
    italic: Optional[bool]
    "Is this a italic leaf?"
    code: Optional[bool]
    "Is this a code leaf?"
    text: Optional[str]
    "The text of the leaf"


class GroupAssignmentInput(BaseModel):
    permissions: List[Optional[str]]
    group: ID


class UserAssignmentInput(BaseModel):
    permissions: List[Optional[str]]
    user: str
    "The user email"


class OmeroRepresentationInput(BaseModel):
    planes: Optional[List[Optional["PlaneInput"]]]
    channels: Optional[List[Optional["ChannelInput"]]]
    physical_size: Optional["PhysicalSizeInput"] = Field(alias="physicalSize")
    scale: Optional[List[Optional[float]]]
    acquisition_date: Optional[datetime] = Field(alias="acquisitionDate")


class PlaneInput(BaseModel):
    z_index: Optional[int] = Field(alias="zIndex")
    y_index: Optional[int] = Field(alias="yIndex")
    x_index: Optional[int] = Field(alias="xIndex")
    c_index: Optional[int] = Field(alias="cIndex")
    t_index: Optional[int] = Field(alias="tIndex")
    exposure_time: Optional[float] = Field(alias="exposureTime")
    delta_t: Optional[float] = Field(alias="deltaT")


class ChannelInput(BaseModel):
    name: Optional[str]
    emmission_wavelength: Optional[float] = Field(alias="emmissionWavelength")
    excitation_wavelength: Optional[float] = Field(alias="excitationWavelength")
    acquisition_mode: Optional[str] = Field(alias="acquisitionMode")
    color: Optional[str]


class PhysicalSizeInput(BaseModel):
    x: Optional[int]
    y: Optional[int]
    z: Optional[int]
    t: Optional[int]
    c: Optional[int]


class InputVector(BaseModel, Vectorizable):
    x: Optional[float]
    "X-coordinate"
    y: Optional[float]
    "Y-coordinate"
    z: Optional[float]
    "Z-coordinate"
    c: Optional[float]
    "C-coordinate"
    t: Optional[float]
    "T-coordinate"


class RepresentationFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str


class RepresentationFragmentOmero(BaseModel):
    typename: Optional[Literal["Omero"]] = Field(alias="__typename")
    scale: Optional[List[Optional[float]]]


class RepresentationFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    sample: Optional[RepresentationFragmentSample]
    "The Sample this representation belongs to"
    type: Optional[str]
    "The Representation can have varying types, consult your API"
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have varying types, consult your API"
    name: Optional[str]
    "Cleartext name"
    omero: Optional[RepresentationFragmentOmero]


class ThumbnailFragment(BaseModel):
    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    id: ID
    image: Optional[str]


class MetricFragmentRep(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID


class MetricFragmentCreator(BaseModel):
    typename: Optional[Literal["User"]] = Field(alias="__typename")
    id: ID


class MetricFragment(BaseModel):
    typename: Optional[Literal["Metric"]] = Field(alias="__typename")
    id: ID
    rep: Optional[MetricFragmentRep]
    "The Representatoin this Metric belongs to"
    key: str
    "The Key"
    value: Optional[MetricValue]
    "Value"
    creator: Optional[MetricFragmentCreator]
    created_at: datetime = Field(alias="createdAt")


class ROIFragmentVectors(BaseModel):
    typename: Optional[Literal["Vector"]] = Field(alias="__typename")
    x: Optional[float]
    "X-coordinate"
    y: Optional[float]
    "Y-coordinate"
    z: Optional[float]
    "Z-coordinate"


class ROIFragmentRepresentation(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID


class ROIFragmentCreator(BaseModel):
    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str
    color: str
    "The color of the user"


class ROIFragment(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    id: ID
    vectors: Optional[List[Optional[ROIFragmentVectors]]]
    type: ROIType
    "The Representation can have varying types, consult your API"
    representation: Optional[ROIFragmentRepresentation]
    creator: ROIFragmentCreator


class TableFragmentCreator(BaseModel):
    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str


class TableFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID


class TableFragmentRepresentation(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID


class TableFragmentExperiment(BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID


class TableFragment(Table, BaseModel):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: ID
    name: str
    tags: Optional[List[Optional[str]]]
    "A comma-separated list of tags."
    store: Optional[Parquet]
    creator: Optional[TableFragmentCreator]
    sample: Optional[TableFragmentSample]
    representation: Optional[TableFragmentRepresentation]
    experiment: Optional[TableFragmentExperiment]


class SampleFragmentRepresentations(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID


class SampleFragmentExperiments(BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID


class SampleFragment(BaseModel):
    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    id: ID
    representations: Optional[List[Optional[SampleFragmentRepresentations]]]
    meta: Optional[Dict]
    experiments: List[SampleFragmentExperiments]


class OmeroFileFragment(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: ID
    name: str
    file: Optional[File]
    type: OmeroFileType


class ExperimentFragmentCreator(BaseModel):
    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str


class ExperimentFragment(BaseModel):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID
    name: str
    creator: Optional[ExperimentFragmentCreator]
    meta: Optional[Dict]


class RequestQueryRequest(BaseModel):
    typename: Optional[Literal["Credentials"]] = Field(alias="__typename")
    access_key: Optional[str] = Field(alias="accessKey")
    status: Optional[str]
    secret_key: Optional[str] = Field(alias="secretKey")


class RequestQuery(BaseModel):
    request: Optional[RequestQueryRequest]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "query Request {\n  request {\n    accessKey\n    status\n    secretKey\n  }\n}"


class Get_omero_fileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n  type\n}\n\nquery get_omero_file($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Expand_omerofileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n  type\n}\n\nquery expand_omerofile($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Search_omerofileQueryOptions(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    value: ID
    label: str


class Search_omerofileQuery(BaseModel):
    options: Optional[List[Optional[Search_omerofileQueryOptions]]]
    "My samples return all of the users samples attached to the current user"

    class Arguments(BaseModel):
        search: str

    class Meta:
        document = "query search_omerofile($search: String!) {\n  options: omerofiles(name: $search) {\n    value: id\n    label: name\n  }\n}"


class Get_labelQueryLabelforFeatures(BaseModel):
    typename: Optional[Literal["Feature"]] = Field(alias="__typename")
    id: ID
    key: str
    "The sKesyss"
    value: Optional[FeatureValue]
    "Value"


class Get_labelQueryLabelfor(BaseModel):
    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    id: ID
    features: Optional[List[Optional[Get_labelQueryLabelforFeatures]]]
    "Features attached to this Label"


class Get_labelQuery(BaseModel):
    label_for: Optional[Get_labelQueryLabelfor] = Field(alias="labelFor")
    "Get a label for a specific instance on a specific representation"

    class Arguments(BaseModel):
        representation: ID
        instance: int

    class Meta:
        document = "query get_label($representation: ID!, $instance: Int!) {\n  labelFor(representation: $representation, instance: $instance) {\n    id\n    features {\n      id\n      key\n      value\n    }\n  }\n}"


class Expand_representationQuery(BaseModel):
    """Creates a new representation"""

    representation: Optional[RepresentationFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n  }\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Get_representationQuery(BaseModel):
    representation: Optional[RepresentationFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n  }\n}\n\nquery get_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Search_representationQueryOptions(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    value: ID
    label: Optional[str]
    "Cleartext name"


class Search_representationQuery(BaseModel):
    options: Optional[List[Optional[Search_representationQueryOptions]]]
    "All represetations"

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_representation($search: String) {\n  options: representations(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"


class Get_random_repQuery(BaseModel):
    """Queries the database for a random representation
    This is used to generate a random representation for the user to play with
    The random representation is generated by taking a random representation from the database"""

    random_representation: Optional[RepresentationFragment] = Field(
        alias="randomRepresentation"
    )
    "Get a single representation by ID"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n  }\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"


class My_accessiblesQuery(BaseModel):
    accessiblerepresentations: Optional[List[Optional[RepresentationFragment]]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n  }\n}\n\nquery my_accessibles {\n  accessiblerepresentations {\n    ...Representation\n  }\n}"


class ThumbnailQuery(BaseModel):
    thumbnail: Optional[ThumbnailFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery Thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"


class Expand_thumbnailQuery(BaseModel):
    thumbnail: Optional[ThumbnailFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery expand_thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"


class Search_thumbnailsQueryThumbnails(BaseModel):
    """Thumbnail(id, representation, image)"""

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    value: ID
    label: Optional[str]


class Search_thumbnailsQuery(BaseModel):
    thumbnails: Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]
    "All represetations"

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_thumbnails($search: String) {\n  thumbnails(name: $search, limit: 20) {\n    value: id\n    label: image\n  }\n}"


class Image_for_thumbnailQueryImage(BaseModel):
    """Thumbnail(id, representation, image)"""

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    path: Optional[str]
    label: Optional[str]


class Image_for_thumbnailQuery(BaseModel):
    image: Optional[Image_for_thumbnailQueryImage]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "query image_for_thumbnail($id: ID!) {\n  image: thumbnail(id: $id) {\n    path: image\n    label: image\n  }\n}"


class Expand_metricQuery(BaseModel):
    """Creates a new representation"""

    metric: Optional[MetricFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  rep {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nquery expand_metric($id: ID!) {\n  metric(id: $id) {\n    ...Metric\n  }\n}"


class Get_roisQuery(BaseModel):
    rois: Optional[List[Optional[ROIFragment]]]
    "All represetations"

    class Arguments(BaseModel):
        representation: ID
        type: Optional[List[Optional[RoiTypeInput]]] = None

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n  creator {\n    email\n    color\n  }\n}\n\nquery get_rois($representation: ID!, $type: [RoiTypeInput]) {\n  rois(representation: $representation, type: $type) {\n    ...ROI\n  }\n}"


class Get_tableQuery(BaseModel):
    table: Optional[TableFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery get_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


class Expand_tableQuery(BaseModel):
    table: Optional[TableFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery expand_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


class Search_tablesQueryOptions(Table, BaseModel):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    value: ID
    label: str


class Search_tablesQuery(BaseModel):
    options: Optional[List[Optional[Search_tablesQueryOptions]]]
    "My samples return all of the users samples attached to the current user"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "query search_tables {\n  options: tables {\n    value: id\n    label: name\n  }\n}"


class Get_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery get_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class Search_sampleQueryOptions(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    value: ID
    label: str


class Search_sampleQuery(BaseModel):
    options: Optional[List[Optional[Search_sampleQueryOptions]]]
    "All Samples"

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_sample($search: String) {\n  options: samples(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"


class Expand_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  meta\n  experiments {\n    id\n  }\n}\n\nquery expand_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class Get_experimentQuery(BaseModel):
    experiment: Optional[ExperimentFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery get_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"


class Expand_experimentQuery(BaseModel):
    experiment: Optional[ExperimentFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nquery expand_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"


class Search_experimentQueryOptions(BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID
    label: str


class Search_experimentQuery(BaseModel):
    options: Optional[List[Optional[Search_experimentQueryOptions]]]
    "All Samples"

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_experiment($search: String) {\n  options: experiments(name: $search, limit: 30) {\n    id: id\n    label: name\n  }\n}"


class Watch_roisSubscriptionRois(BaseModel):
    typename: Optional[Literal["RoiEvent"]] = Field(alias="__typename")
    update: Optional[ROIFragment]
    delete: Optional[ID]
    create: Optional[ROIFragment]


class Watch_roisSubscription(BaseModel):
    rois: Optional[Watch_roisSubscriptionRois]

    class Arguments(BaseModel):
        representation: ID

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n  creator {\n    email\n    color\n  }\n}\n\nsubscription watch_rois($representation: ID!) {\n  rois(representation: $representation) {\n    update {\n      ...ROI\n    }\n    delete\n    create {\n      ...ROI\n    }\n  }\n}"


class Watch_samplesSubscriptionMysamplesUpdateExperiments(BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str


class Watch_samplesSubscriptionMysamplesUpdate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    experiments: List[Watch_samplesSubscriptionMysamplesUpdateExperiments]


class Watch_samplesSubscriptionMysamplesCreateExperiments(BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment"""

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str


class Watch_samplesSubscriptionMysamplesCreate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    experiments: List[Watch_samplesSubscriptionMysamplesCreateExperiments]


class Watch_samplesSubscriptionMysamples(BaseModel):
    typename: Optional[Literal["SamplesEvent"]] = Field(alias="__typename")
    update: Optional[Watch_samplesSubscriptionMysamplesUpdate]
    create: Optional[Watch_samplesSubscriptionMysamplesCreate]


class Watch_samplesSubscription(BaseModel):
    my_samples: Optional[Watch_samplesSubscriptionMysamples] = Field(alias="mySamples")

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "subscription watch_samples {\n  mySamples {\n    update {\n      id\n      name\n      experiments {\n        name\n      }\n    }\n    create {\n      name\n      experiments {\n        name\n      }\n    }\n  }\n}"


class NegotiateMutation(BaseModel):
    negotiate: Optional[Dict]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "mutation negotiate {\n  negotiate\n}"


class Upload_bioimageMutationUploadomerofile(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: ID
    file: Optional[File]
    type: OmeroFileType
    name: str


class Upload_bioimageMutation(BaseModel):
    upload_omero_file: Optional[Upload_bioimageMutationUploadomerofile] = Field(
        alias="uploadOmeroFile"
    )

    class Arguments(BaseModel):
        file: File

    class Meta:
        document = "mutation upload_bioimage($file: ImageFile!) {\n  uploadOmeroFile(file: $file) {\n    id\n    file\n    type\n    name\n  }\n}"


class Create_featureMutationCreatefeatureLabelRepresentation(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID


class Create_featureMutationCreatefeatureLabel(BaseModel):
    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    id: ID
    representation: Optional[Create_featureMutationCreatefeatureLabelRepresentation]


class Create_featureMutationCreatefeature(BaseModel):
    typename: Optional[Literal["Feature"]] = Field(alias="__typename")
    id: ID
    key: str
    "The sKesyss"
    value: Optional[FeatureValue]
    "Value"
    label: Optional[Create_featureMutationCreatefeatureLabel]


class Create_featureMutation(BaseModel):
    createfeature: Optional[Create_featureMutationCreatefeature]
    "Creates a Sample"

    class Arguments(BaseModel):
        label: ID
        key: Optional[str] = None
        value: FeatureValue
        creator: Optional[ID] = None

    class Meta:
        document = "mutation create_feature($label: ID!, $key: String, $value: FeatureValue!, $creator: ID) {\n  createfeature(label: $label, key: $key, value: $value, creator: $creator) {\n    id\n    key\n    value\n    label {\n      id\n      representation {\n        id\n      }\n    }\n  }\n}"


class Create_labelMutationCreatelabel(BaseModel):
    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    id: ID
    instance: int


class Create_labelMutation(BaseModel):
    create_label: Optional[Create_labelMutationCreatelabel] = Field(alias="createLabel")
    "Creates a Sample"

    class Arguments(BaseModel):
        instance: int
        representation: ID
        creator: Optional[ID] = None
        name: Optional[str] = None

    class Meta:
        document = "mutation create_label($instance: Int!, $representation: ID!, $creator: ID, $name: String) {\n  createLabel(\n    instance: $instance\n    representation: $representation\n    creator: $creator\n    name: $name\n  ) {\n    id\n    instance\n  }\n}"


class From_xarrayMutation(BaseModel):
    """Creates a Representation from an xarray dataset."""

    from_x_array: Optional[RepresentationFragment] = Field(alias="fromXArray")
    "Creates a Representation"

    class Arguments(BaseModel):
        xarray: ArrayInput
        name: Optional[str] = None
        variety: Optional[RepresentationVarietyInput] = None
        origins: Optional[List[Optional[ID]]] = None
        files: Optional[List[Optional[ID]]] = None
        tags: Optional[List[Optional[str]]] = None
        sample: Optional[ID] = None
        omero: Optional[OmeroRepresentationInput] = None

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n  }\n}\n\nmutation from_xarray($xarray: XArray!, $name: String, $variety: RepresentationVarietyInput, $origins: [ID], $files: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n    files: $files\n    variety: $variety\n  ) {\n    ...Representation\n  }\n}"


class Double_uploadMutationX(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    store: Optional[Store]


class Double_uploadMutationY(Representation, BaseModel):
    """A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest"""

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    store: Optional[Store]


class Double_uploadMutation(BaseModel):
    x: Optional[Double_uploadMutationX]
    "Creates a Representation"
    y: Optional[Double_uploadMutationY]
    "Creates a Representation"

    class Arguments(BaseModel):
        xarray: ArrayInput
        name: Optional[str] = None
        origins: Optional[List[Optional[ID]]] = None
        tags: Optional[List[Optional[str]]] = None
        sample: Optional[ID] = None
        omero: Optional[OmeroRepresentationInput] = None

    class Meta:
        document = "mutation double_upload($xarray: XArray!, $name: String, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  x: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n  y: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n}"


class Update_representationMutation(BaseModel):
    update_representation: Optional[RepresentationFragment] = Field(
        alias="updateRepresentation"
    )
    "Updates an Representation (also retriggers meta-data retrieval from data stored in)"

    class Arguments(BaseModel):
        id: ID
        tags: Optional[List[Optional[str]]] = None
        sample: Optional[ID] = None
        variety: Optional[RepresentationVarietyInput] = None

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  type\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n  }\n}\n\nmutation update_representation($id: ID!, $tags: [String], $sample: ID, $variety: RepresentationVarietyInput) {\n  updateRepresentation(rep: $id, tags: $tags, sample: $sample, variety: $variety) {\n    ...Representation\n  }\n}"


class Create_thumbnailMutation(BaseModel):
    upload_thumbnail: Optional[ThumbnailFragment] = Field(alias="uploadThumbnail")

    class Arguments(BaseModel):
        rep: ID
        file: File

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nmutation create_thumbnail($rep: ID!, $file: ImageFile!) {\n  uploadThumbnail(rep: $rep, file: $file) {\n    ...Thumbnail\n  }\n}"


class Create_metricMutation(BaseModel):
    create_metric: Optional[MetricFragment] = Field(alias="createMetric")
    "Creates a Representation"

    class Arguments(BaseModel):
        rep: Optional[ID] = None
        sample: Optional[ID] = None
        experiment: Optional[ID] = None
        key: str
        value: MetricValue

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  rep {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nmutation create_metric($rep: ID, $sample: ID, $experiment: ID, $key: String!, $value: MetricValue!) {\n  createMetric(\n    rep: $rep\n    sample: $sample\n    experiment: $experiment\n    key: $key\n    value: $value\n  ) {\n    ...Metric\n  }\n}"


class Create_roiMutation(BaseModel):
    create_roi: Optional[ROIFragment] = Field(alias="createROI")
    "Creates a Sample"

    class Arguments(BaseModel):
        representation: ID
        vectors: List[Optional[InputVector]]
        creator: Optional[ID] = None
        type: RoiTypeInput

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n  creator {\n    email\n    color\n  }\n}\n\nmutation create_roi($representation: ID!, $vectors: [InputVector]!, $creator: ID, $type: RoiTypeInput!) {\n  createROI(\n    representation: $representation\n    vectors: $vectors\n    type: $type\n    creator: $creator\n  ) {\n    ...ROI\n  }\n}"


class Get_roiQuery(BaseModel):
    roi: Optional[ROIFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  vectors {\n    x\n    y\n    z\n  }\n  type\n  representation {\n    id\n  }\n  creator {\n    email\n    color\n  }\n}\n\nquery get_roi($id: ID!) {\n  roi(id: $id) {\n    ...ROI\n  }\n}"


class Search_roisQueryRois(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    label: ID
    value: ID


class Search_roisQuery(BaseModel):
    rois: Optional[List[Optional[Search_roisQueryRois]]]
    "All represetations"

    class Arguments(BaseModel):
        search: str

    class Meta:
        document = "query search_rois($search: String!) {\n  rois(repname: $search) {\n    label: id\n    value: id\n  }\n}"


class From_dfMutation(BaseModel):
    from_df: Optional[TableFragment] = Field(alias="fromDf")
    "Creates a Representation"

    class Arguments(BaseModel):
        df: DataFrame
        name: str

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nmutation from_df($df: DataFrame!, $name: String!) {\n  fromDf(df: $df, name: $name) {\n    ...Table\n  }\n}"


class Create_sampleMutationCreatesampleCreator(BaseModel):
    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str


class Create_sampleMutationCreatesample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
    was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
    the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    """

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    creator: Optional[Create_sampleMutationCreatesampleCreator]


class Create_sampleMutation(BaseModel):
    create_sample: Optional[Create_sampleMutationCreatesample] = Field(
        alias="createSample"
    )
    "Creates a Sample"

    class Arguments(BaseModel):
        name: Optional[str] = None
        creator: Optional[str] = None
        meta: Optional[Dict] = None
        experiments: Optional[List[Optional[ID]]] = None
        tags: Optional[List[Optional[str]]] = None

    class Meta:
        document = "mutation create_sample($name: String, $creator: String, $meta: GenericScalar, $experiments: [ID], $tags: [String]) {\n  createSample(\n    name: $name\n    creator: $creator\n    meta: $meta\n    experiments: $experiments\n    tags: $tags\n  ) {\n    id\n    name\n    creator {\n      email\n    }\n  }\n}"


class Create_experimentMutation(BaseModel):
    create_experiment: Optional[ExperimentFragment] = Field(alias="createExperiment")
    "Create an experiment (only signed in users)"

    class Arguments(BaseModel):
        name: str
        creator: Optional[str] = None
        meta: Optional[Dict] = None
        description: Optional[str] = None

    class Meta:
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n  meta\n}\n\nmutation create_experiment($name: String!, $creator: String, $meta: GenericScalar, $description: String) {\n  createExperiment(\n    name: $name\n    creator: $creator\n    description: $description\n    meta: $meta\n  ) {\n    ...Experiment\n  }\n}"


async def arequest(rath: MikroRath = None) -> Optional[RequestQueryRequest]:
    """Request



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RequestQueryRequest]"""
    return (await aexecute(RequestQuery, {}, rath=rath)).request


def request(rath: MikroRath = None) -> Optional[RequestQueryRequest]:
    """Request



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RequestQueryRequest]"""
    return execute(RequestQuery, {}, rath=rath).request


async def aget_omero_file(
    id: ID, rath: MikroRath = None
) -> Optional[OmeroFileFragment]:
    """get_omero_file



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[OmeroFileFragment]"""
    return (await aexecute(Get_omero_fileQuery, {"id": id}, rath=rath)).omerofile


def get_omero_file(id: ID, rath: MikroRath = None) -> Optional[OmeroFileFragment]:
    """get_omero_file



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[OmeroFileFragment]"""
    return execute(Get_omero_fileQuery, {"id": id}, rath=rath).omerofile


async def aexpand_omerofile(
    id: ID, rath: MikroRath = None
) -> Optional[OmeroFileFragment]:
    """expand_omerofile



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[OmeroFileFragment]"""
    return (await aexecute(Expand_omerofileQuery, {"id": id}, rath=rath)).omerofile


def expand_omerofile(id: ID, rath: MikroRath = None) -> Optional[OmeroFileFragment]:
    """expand_omerofile



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[OmeroFileFragment]"""
    return execute(Expand_omerofileQuery, {"id": id}, rath=rath).omerofile


async def asearch_omerofile(
    search: str, rath: MikroRath = None
) -> Optional[List[Optional[Search_omerofileQueryOptions]]]:
    """search_omerofile



    Arguments:
        search (str): search
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_omerofileQueryOmerofiles]]]"""
    return (
        await aexecute(Search_omerofileQuery, {"search": search}, rath=rath)
    ).omerofiles


def search_omerofile(
    search: str, rath: MikroRath = None
) -> Optional[List[Optional[Search_omerofileQueryOptions]]]:
    """search_omerofile



    Arguments:
        search (str): search
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_omerofileQueryOmerofiles]]]"""
    return execute(Search_omerofileQuery, {"search": search}, rath=rath).omerofiles


async def aget_label(
    representation: ID, instance: int, rath: MikroRath = None
) -> Optional[Get_labelQueryLabelfor]:
    """get_label



    Arguments:
        representation (ID): representation
        instance (int): instance
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Get_labelQueryLabelfor]"""
    return (
        await aexecute(
            Get_labelQuery,
            {"representation": representation, "instance": instance},
            rath=rath,
        )
    ).label_for


def get_label(
    representation: ID, instance: int, rath: MikroRath = None
) -> Optional[Get_labelQueryLabelfor]:
    """get_label



    Arguments:
        representation (ID): representation
        instance (int): instance
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Get_labelQueryLabelfor]"""
    return execute(
        Get_labelQuery,
        {"representation": representation, "instance": instance},
        rath=rath,
    ).label_for


async def aexpand_representation(
    id: ID, rath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """expand_representation

     Creates a new representation

    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return (
        await aexecute(Expand_representationQuery, {"id": id}, rath=rath)
    ).representation


def expand_representation(
    id: ID, rath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """expand_representation

     Creates a new representation

    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return execute(Expand_representationQuery, {"id": id}, rath=rath).representation


async def aget_representation(
    id: ID, rath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """get_representation


     representation: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return (
        await aexecute(Get_representationQuery, {"id": id}, rath=rath)
    ).representation


def get_representation(
    id: ID, rath: MikroRath = None
) -> Optional[RepresentationFragment]:
    """get_representation


     representation: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return execute(Get_representationQuery, {"id": id}, rath=rath).representation


async def asearch_representation(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_representationQueryOptions]]]:
    """search_representation


     options: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_representationQueryRepresentations]]]"""
    return (
        await aexecute(Search_representationQuery, {"search": search}, rath=rath)
    ).representations


def search_representation(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_representationQueryOptions]]]:
    """search_representation


     options: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_representationQueryRepresentations]]]"""
    return execute(
        Search_representationQuery, {"search": search}, rath=rath
    ).representations


async def aget_random_rep(rath: MikroRath = None) -> Optional[RepresentationFragment]:
    """get_random_rep

     Queries the database for a random representation
     This is used to generate a random representation for the user to play with
     The random representation is generated by taking a random representation from the database

    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return (await aexecute(Get_random_repQuery, {}, rath=rath)).random_representation


def get_random_rep(rath: MikroRath = None) -> Optional[RepresentationFragment]:
    """get_random_rep

     Queries the database for a random representation
     This is used to generate a random representation for the user to play with
     The random representation is generated by taking a random representation from the database

    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return execute(Get_random_repQuery, {}, rath=rath).random_representation


async def amy_accessibles(
    rath: MikroRath = None,
) -> Optional[List[Optional[RepresentationFragment]]]:
    """my_accessibles


     accessiblerepresentations: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[RepresentationFragment]]]"""
    return (
        await aexecute(My_accessiblesQuery, {}, rath=rath)
    ).accessiblerepresentations


def my_accessibles(
    rath: MikroRath = None,
) -> Optional[List[Optional[RepresentationFragment]]]:
    """my_accessibles


     accessiblerepresentations: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[RepresentationFragment]]]"""
    return execute(My_accessiblesQuery, {}, rath=rath).accessiblerepresentations


async def athumbnail(id: ID, rath: MikroRath = None) -> Optional[ThumbnailFragment]:
    """Thumbnail


     thumbnail: Thumbnail(id, representation, image)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return (await aexecute(ThumbnailQuery, {"id": id}, rath=rath)).thumbnail


def thumbnail(id: ID, rath: MikroRath = None) -> Optional[ThumbnailFragment]:
    """Thumbnail


     thumbnail: Thumbnail(id, representation, image)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return execute(ThumbnailQuery, {"id": id}, rath=rath).thumbnail


async def aexpand_thumbnail(
    id: ID, rath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """expand_thumbnail


     thumbnail: Thumbnail(id, representation, image)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return (await aexecute(Expand_thumbnailQuery, {"id": id}, rath=rath)).thumbnail


def expand_thumbnail(id: ID, rath: MikroRath = None) -> Optional[ThumbnailFragment]:
    """expand_thumbnail


     thumbnail: Thumbnail(id, representation, image)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return execute(Expand_thumbnailQuery, {"id": id}, rath=rath).thumbnail


async def asearch_thumbnails(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]:
    """search_thumbnails


     thumbnails: Thumbnail(id, representation, image)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]"""
    return (
        await aexecute(Search_thumbnailsQuery, {"search": search}, rath=rath)
    ).thumbnails


def search_thumbnails(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]:
    """search_thumbnails


     thumbnails: Thumbnail(id, representation, image)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]"""
    return execute(Search_thumbnailsQuery, {"search": search}, rath=rath).thumbnails


async def aimage_for_thumbnail(
    id: ID, rath: MikroRath = None
) -> Optional[Image_for_thumbnailQueryImage]:
    """image_for_thumbnail


     image: Thumbnail(id, representation, image)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Image_for_thumbnailQueryThumbnail]"""
    return (await aexecute(Image_for_thumbnailQuery, {"id": id}, rath=rath)).thumbnail


def image_for_thumbnail(
    id: ID, rath: MikroRath = None
) -> Optional[Image_for_thumbnailQueryImage]:
    """image_for_thumbnail


     image: Thumbnail(id, representation, image)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Image_for_thumbnailQueryThumbnail]"""
    return execute(Image_for_thumbnailQuery, {"id": id}, rath=rath).thumbnail


async def aexpand_metric(id: ID, rath: MikroRath = None) -> Optional[MetricFragment]:
    """expand_metric

     Creates a new representation

    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[MetricFragment]"""
    return (await aexecute(Expand_metricQuery, {"id": id}, rath=rath)).metric


def expand_metric(id: ID, rath: MikroRath = None) -> Optional[MetricFragment]:
    """expand_metric

     Creates a new representation

    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[MetricFragment]"""
    return execute(Expand_metricQuery, {"id": id}, rath=rath).metric


async def aget_rois(
    representation: ID,
    type: Optional[List[Optional[RoiTypeInput]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[ROIFragment]]]:
    """get_rois



    Arguments:
        representation (ID): representation
        type (Optional[List[Optional[RoiTypeInput]]], optional): type.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ROIFragment]]]"""
    return (
        await aexecute(
            Get_roisQuery, {"representation": representation, "type": type}, rath=rath
        )
    ).rois


def get_rois(
    representation: ID,
    type: Optional[List[Optional[RoiTypeInput]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[ROIFragment]]]:
    """get_rois



    Arguments:
        representation (ID): representation
        type (Optional[List[Optional[RoiTypeInput]]], optional): type.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ROIFragment]]]"""
    return execute(
        Get_roisQuery, {"representation": representation, "type": type}, rath=rath
    ).rois


async def aget_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """get_table



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return (await aexecute(Get_tableQuery, {"id": id}, rath=rath)).table


def get_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """get_table



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return execute(Get_tableQuery, {"id": id}, rath=rath).table


async def aexpand_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """expand_table



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return (await aexecute(Expand_tableQuery, {"id": id}, rath=rath)).table


def expand_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """expand_table



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return execute(Expand_tableQuery, {"id": id}, rath=rath).table


async def asearch_tables(
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_tablesQueryOptions]]]:
    """search_tables



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tablesQueryTables]]]"""
    return (await aexecute(Search_tablesQuery, {}, rath=rath)).tables


def search_tables(
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_tablesQueryOptions]]]:
    """search_tables



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tablesQueryTables]]]"""
    return execute(Search_tablesQuery, {}, rath=rath).tables


async def aget_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """get_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[SampleFragment]"""
    return (await aexecute(Get_sampleQuery, {"id": id}, rath=rath)).sample


def get_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """get_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[SampleFragment]"""
    return execute(Get_sampleQuery, {"id": id}, rath=rath).sample


async def asearch_sample(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_sampleQueryOptions]]]:
    """search_sample


     options: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_sampleQuerySamples]]]"""
    return (await aexecute(Search_sampleQuery, {"search": search}, rath=rath)).samples


def search_sample(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_sampleQueryOptions]]]:
    """search_sample


     options: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_sampleQuerySamples]]]"""
    return execute(Search_sampleQuery, {"search": search}, rath=rath).samples


async def aexpand_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """expand_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[SampleFragment]"""
    return (await aexecute(Expand_sampleQuery, {"id": id}, rath=rath)).sample


def expand_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """expand_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[SampleFragment]"""
    return execute(Expand_sampleQuery, {"id": id}, rath=rath).sample


async def aget_experiment(
    id: ID, rath: MikroRath = None
) -> Optional[ExperimentFragment]:
    """get_experiment


     experiment: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return (await aexecute(Get_experimentQuery, {"id": id}, rath=rath)).experiment


def get_experiment(id: ID, rath: MikroRath = None) -> Optional[ExperimentFragment]:
    """get_experiment


     experiment: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return execute(Get_experimentQuery, {"id": id}, rath=rath).experiment


async def aexpand_experiment(
    id: ID, rath: MikroRath = None
) -> Optional[ExperimentFragment]:
    """expand_experiment


     experiment: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return (await aexecute(Expand_experimentQuery, {"id": id}, rath=rath)).experiment


def expand_experiment(id: ID, rath: MikroRath = None) -> Optional[ExperimentFragment]:
    """expand_experiment


     experiment: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return execute(Expand_experimentQuery, {"id": id}, rath=rath).experiment


async def asearch_experiment(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_experimentQueryOptions]]]:
    """search_experiment


     options: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_experimentQueryExperiments]]]"""
    return (
        await aexecute(Search_experimentQuery, {"search": search}, rath=rath)
    ).experiments


def search_experiment(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_experimentQueryOptions]]]:
    """search_experiment


     options: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_experimentQueryExperiments]]]"""
    return execute(Search_experimentQuery, {"search": search}, rath=rath).experiments


async def awatch_rois(
    representation: ID, rath: MikroRath = None
) -> AsyncIterator[Optional[Watch_roisSubscriptionRois]]:
    """watch_rois



    Arguments:
        representation (ID): representation
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Watch_roisSubscriptionRois]"""
    async for event in asubscribe(
        Watch_roisSubscription, {"representation": representation}, rath=rath
    ):
        yield event.rois


def watch_rois(
    representation: ID, rath: MikroRath = None
) -> Iterator[Optional[Watch_roisSubscriptionRois]]:
    """watch_rois



    Arguments:
        representation (ID): representation
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Watch_roisSubscriptionRois]"""
    for event in subscribe(
        Watch_roisSubscription, {"representation": representation}, rath=rath
    ):
        yield event.rois


async def awatch_samples(
    rath: MikroRath = None,
) -> AsyncIterator[Optional[Watch_samplesSubscriptionMysamples]]:
    """watch_samples



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Watch_samplesSubscriptionMysamples]"""
    async for event in asubscribe(Watch_samplesSubscription, {}, rath=rath):
        yield event.my_samples


def watch_samples(
    rath: MikroRath = None,
) -> Iterator[Optional[Watch_samplesSubscriptionMysamples]]:
    """watch_samples



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Watch_samplesSubscriptionMysamples]"""
    for event in subscribe(Watch_samplesSubscription, {}, rath=rath):
        yield event.my_samples


async def anegotiate(rath: MikroRath = None) -> Optional[Dict]:
    """negotiate


     negotiate: The `GenericScalar` scalar type represents a generic
    GraphQL scalar value that could be:
    String, Boolean, Int, Float, List or Object.


    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Dict]"""
    return (await aexecute(NegotiateMutation, {}, rath=rath)).negotiate


def negotiate(rath: MikroRath = None) -> Optional[Dict]:
    """negotiate


     negotiate: The `GenericScalar` scalar type represents a generic
    GraphQL scalar value that could be:
    String, Boolean, Int, Float, List or Object.


    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Dict]"""
    return execute(NegotiateMutation, {}, rath=rath).negotiate


async def aupload_bioimage(
    file: File, rath: MikroRath = None
) -> Optional[Upload_bioimageMutationUploadomerofile]:
    """upload_bioimage



    Arguments:
        file (File): file
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Upload_bioimageMutationUploadomerofile]"""
    return (
        await aexecute(Upload_bioimageMutation, {"file": file}, rath=rath)
    ).upload_omero_file


def upload_bioimage(
    file: File, rath: MikroRath = None
) -> Optional[Upload_bioimageMutationUploadomerofile]:
    """upload_bioimage



    Arguments:
        file (File): file
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Upload_bioimageMutationUploadomerofile]"""
    return execute(Upload_bioimageMutation, {"file": file}, rath=rath).upload_omero_file


async def acreate_feature(
    label: ID,
    value: FeatureValue,
    key: Optional[str] = None,
    creator: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[Create_featureMutationCreatefeature]:
    """create_feature



    Arguments:
        label (ID): label
        value (FeatureValue): value
        key (Optional[str], optional): key.
        creator (Optional[ID], optional): creator.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_featureMutationCreatefeature]"""
    return (
        await aexecute(
            Create_featureMutation,
            {"label": label, "key": key, "value": value, "creator": creator},
            rath=rath,
        )
    ).createfeature


def create_feature(
    label: ID,
    value: FeatureValue,
    key: Optional[str] = None,
    creator: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[Create_featureMutationCreatefeature]:
    """create_feature



    Arguments:
        label (ID): label
        value (FeatureValue): value
        key (Optional[str], optional): key.
        creator (Optional[ID], optional): creator.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_featureMutationCreatefeature]"""
    return execute(
        Create_featureMutation,
        {"label": label, "key": key, "value": value, "creator": creator},
        rath=rath,
    ).createfeature


async def acreate_label(
    instance: int,
    representation: ID,
    creator: Optional[ID] = None,
    name: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[Create_labelMutationCreatelabel]:
    """create_label



    Arguments:
        instance (int): instance
        representation (ID): representation
        creator (Optional[ID], optional): creator.
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_labelMutationCreatelabel]"""
    return (
        await aexecute(
            Create_labelMutation,
            {
                "instance": instance,
                "representation": representation,
                "creator": creator,
                "name": name,
            },
            rath=rath,
        )
    ).create_label


def create_label(
    instance: int,
    representation: ID,
    creator: Optional[ID] = None,
    name: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[Create_labelMutationCreatelabel]:
    """create_label



    Arguments:
        instance (int): instance
        representation (ID): representation
        creator (Optional[ID], optional): creator.
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_labelMutationCreatelabel]"""
    return execute(
        Create_labelMutation,
        {
            "instance": instance,
            "representation": representation,
            "creator": creator,
            "name": name,
        },
        rath=rath,
    ).create_label


async def afrom_xarray(
    xarray: ArrayInput,
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[ID]]] = None,
    files: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """from_xarray

     Creates a Representation from an xarray dataset.

    Arguments:
        xarray (ArrayInput): xarray
        name (Optional[str], optional): name.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        origins (Optional[List[Optional[ID]]], optional): origins.
        files (Optional[List[Optional[ID]]], optional): files.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[ID], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return (
        await aexecute(
            From_xarrayMutation,
            {
                "xarray": xarray,
                "name": name,
                "variety": variety,
                "origins": origins,
                "files": files,
                "tags": tags,
                "sample": sample,
                "omero": omero,
            },
            rath=rath,
        )
    ).from_x_array


def from_xarray(
    xarray: ArrayInput,
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[ID]]] = None,
    files: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """from_xarray

     Creates a Representation from an xarray dataset.

    Arguments:
        xarray (ArrayInput): xarray
        name (Optional[str], optional): name.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        origins (Optional[List[Optional[ID]]], optional): origins.
        files (Optional[List[Optional[ID]]], optional): files.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[ID], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return execute(
        From_xarrayMutation,
        {
            "xarray": xarray,
            "name": name,
            "variety": variety,
            "origins": origins,
            "files": files,
            "tags": tags,
            "sample": sample,
            "omero": omero,
        },
        rath=rath,
    ).from_x_array


async def adouble_upload(
    xarray: ArrayInput,
    name: Optional[str] = None,
    origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Double_uploadMutation:
    """double_upload


     x: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest

     y: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        xarray (ArrayInput): xarray
        name (Optional[str], optional): name.
        origins (Optional[List[Optional[ID]]], optional): origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[ID], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

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
        rath=rath,
    )


def double_upload(
    xarray: ArrayInput,
    name: Optional[str] = None,
    origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Double_uploadMutation:
    """double_upload


     x: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest

     y: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        xarray (ArrayInput): xarray
        name (Optional[str], optional): name.
        origins (Optional[List[Optional[ID]]], optional): origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[ID], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

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
        rath=rath,
    )


async def aupdate_representation(
    id: ID,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    rath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """update_representation


     updateRepresentation: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        id (ID): id
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[ID], optional): sample.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return (
        await aexecute(
            Update_representationMutation,
            {"id": id, "tags": tags, "sample": sample, "variety": variety},
            rath=rath,
        )
    ).update_representation


def update_representation(
    id: ID,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    rath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """update_representation


     updateRepresentation: A Representation is a multi-dimensional Array that can do what ever it wants


    @elements/rep:latest


    Arguments:
        id (ID): id
        tags (Optional[List[Optional[str]]], optional): tags.
        sample (Optional[ID], optional): sample.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[RepresentationFragment]"""
    return execute(
        Update_representationMutation,
        {"id": id, "tags": tags, "sample": sample, "variety": variety},
        rath=rath,
    ).update_representation


async def acreate_thumbnail(
    rep: ID, file: File, rath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """create_thumbnail


     uploadThumbnail: Thumbnail(id, representation, image)


    Arguments:
        rep (ID): rep
        file (File): file
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return (
        await aexecute(Create_thumbnailMutation, {"rep": rep, "file": file}, rath=rath)
    ).upload_thumbnail


def create_thumbnail(
    rep: ID, file: File, rath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """create_thumbnail


     uploadThumbnail: Thumbnail(id, representation, image)


    Arguments:
        rep (ID): rep
        file (File): file
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return execute(
        Create_thumbnailMutation, {"rep": rep, "file": file}, rath=rath
    ).upload_thumbnail


async def acreate_metric(
    key: str,
    value: MetricValue,
    rep: Optional[ID] = None,
    sample: Optional[ID] = None,
    experiment: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[MetricFragment]:
    """create_metric



    Arguments:
        key (str): key
        value (MetricValue): value
        rep (Optional[ID], optional): rep.
        sample (Optional[ID], optional): sample.
        experiment (Optional[ID], optional): experiment.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[MetricFragment]"""
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
            rath=rath,
        )
    ).create_metric


def create_metric(
    key: str,
    value: MetricValue,
    rep: Optional[ID] = None,
    sample: Optional[ID] = None,
    experiment: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[MetricFragment]:
    """create_metric



    Arguments:
        key (str): key
        value (MetricValue): value
        rep (Optional[ID], optional): rep.
        sample (Optional[ID], optional): sample.
        experiment (Optional[ID], optional): experiment.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[MetricFragment]"""
    return execute(
        Create_metricMutation,
        {
            "rep": rep,
            "sample": sample,
            "experiment": experiment,
            "key": key,
            "value": value,
        },
        rath=rath,
    ).create_metric


async def acreate_roi(
    representation: ID,
    vectors: List[Optional[InputVector]],
    type: RoiTypeInput,
    creator: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[ROIFragment]:
    """create_roi



    Arguments:
        representation (ID): representation
        vectors (List[Optional[InputVector]]): vectors
        type (RoiTypeInput): type
        creator (Optional[ID], optional): creator.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return (
        await aexecute(
            Create_roiMutation,
            {
                "representation": representation,
                "vectors": vectors,
                "creator": creator,
                "type": type,
            },
            rath=rath,
        )
    ).create_roi


def create_roi(
    representation: ID,
    vectors: List[Optional[InputVector]],
    type: RoiTypeInput,
    creator: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[ROIFragment]:
    """create_roi



    Arguments:
        representation (ID): representation
        vectors (List[Optional[InputVector]]): vectors
        type (RoiTypeInput): type
        creator (Optional[ID], optional): creator.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return execute(
        Create_roiMutation,
        {
            "representation": representation,
            "vectors": vectors,
            "creator": creator,
            "type": type,
        },
        rath=rath,
    ).create_roi


async def aget_roi(id: ID, rath: MikroRath = None) -> Optional[ROIFragment]:
    """get_roi



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return (await aexecute(Get_roiQuery, {"id": id}, rath=rath)).roi


def get_roi(id: ID, rath: MikroRath = None) -> Optional[ROIFragment]:
    """get_roi



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return execute(Get_roiQuery, {"id": id}, rath=rath).roi


async def asearch_rois(
    search: str, rath: MikroRath = None
) -> Optional[List[Optional[Search_roisQueryRois]]]:
    """search_rois



    Arguments:
        search (str): search
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_roisQueryRois]]]"""
    return (await aexecute(Search_roisQuery, {"search": search}, rath=rath)).rois


def search_rois(
    search: str, rath: MikroRath = None
) -> Optional[List[Optional[Search_roisQueryRois]]]:
    """search_rois



    Arguments:
        search (str): search
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_roisQueryRois]]]"""
    return execute(Search_roisQuery, {"search": search}, rath=rath).rois


async def afrom_df(
    df: DataFrame, name: str, rath: MikroRath = None
) -> Optional[TableFragment]:
    """from_df



    Arguments:
        df (DataFrame): df
        name (str): name
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return (
        await aexecute(From_dfMutation, {"df": df, "name": name}, rath=rath)
    ).from_df


def from_df(
    df: DataFrame, name: str, rath: MikroRath = None
) -> Optional[TableFragment]:
    """from_df



    Arguments:
        df (DataFrame): df
        name (str): name
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return execute(From_dfMutation, {"df": df, "name": name}, rath=rath).from_df


async def acreate_sample(
    name: Optional[str] = None,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[Create_sampleMutationCreatesample]:
    """create_sample


     createSample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        name (Optional[str], optional): name.
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_sampleMutationCreatesample]"""
    return (
        await aexecute(
            Create_sampleMutation,
            {
                "name": name,
                "creator": creator,
                "meta": meta,
                "experiments": experiments,
                "tags": tags,
            },
            rath=rath,
        )
    ).create_sample


def create_sample(
    name: Optional[str] = None,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[Create_sampleMutationCreatesample]:
    """create_sample


     createSample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
        was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
        the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample



    Arguments:
        name (Optional[str], optional): name.
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_sampleMutationCreatesample]"""
    return execute(
        Create_sampleMutation,
        {
            "name": name,
            "creator": creator,
            "meta": meta,
            "experiments": experiments,
            "tags": tags,
        },
        rath=rath,
    ).create_sample


async def acreate_experiment(
    name: str,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    description: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[ExperimentFragment]:
    """create_experiment


     createExperiment: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        name (str): name
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        description (Optional[str], optional): description.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return (
        await aexecute(
            Create_experimentMutation,
            {
                "name": name,
                "creator": creator,
                "meta": meta,
                "description": description,
            },
            rath=rath,
        )
    ).create_experiment


def create_experiment(
    name: str,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    description: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[ExperimentFragment]:
    """create_experiment


     createExperiment: A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment


    Arguments:
        name (str): name
        creator (Optional[str], optional): creator.
        meta (Optional[Dict], optional): meta.
        description (Optional[str], optional): description.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return execute(
        Create_experimentMutation,
        {"name": name, "creator": creator, "meta": meta, "description": description},
        rath=rath,
    ).create_experiment


DescendendInput.update_forward_refs()
OmeroRepresentationInput.update_forward_refs()
