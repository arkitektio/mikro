from mikro.scalars import (
    FeatureValue,
    File,
    Parquet,
    Store,
    ModelFile,
    MetricValue,
    ModelData,
    XArrayInput,
    ParquetInput,
)
from mikro.traits import (
    ROI,
    Omero,
    Objective,
    Table,
    Vectorizable,
    Representation,
    Position,
    Stage,
)
from mikro.funcs import aexecute, asubscribe, execute, subscribe
from mikro.rath import MikroRath
from enum import Enum
from typing import Dict, Literal, Iterator, AsyncIterator, List, Tuple, Optional
from rath.scalars import ID
from pydantic import Field, BaseModel
from datetime import datetime


class CommentableModels(str, Enum):
    GRUNNLAG_USERMETA = "GRUNNLAG_USERMETA"
    GRUNNLAG_ANTIBODY = "GRUNNLAG_ANTIBODY"
    GRUNNLAG_OBJECTIVE = "GRUNNLAG_OBJECTIVE"
    GRUNNLAG_INSTRUMENT = "GRUNNLAG_INSTRUMENT"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_CONTEXT = "GRUNNLAG_CONTEXT"
    GRUNNLAG_DATALINK = "GRUNNLAG_DATALINK"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_MODEL = "GRUNNLAG_MODEL"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_STAGE = "GRUNNLAG_STAGE"
    GRUNNLAG_POSITION = "GRUNNLAG_POSITION"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_ROI = "GRUNNLAG_ROI"
    GRUNNLAG_LABEL = "GRUNNLAG_LABEL"
    GRUNNLAG_FEATURE = "GRUNNLAG_FEATURE"
    BORD_TABLE = "BORD_TABLE"


class SharableModels(str, Enum):
    """Sharable Models are models that can be shared amongst users and groups. They representent the models of the DB"""

    GRUNNLAG_USERMETA = "GRUNNLAG_USERMETA"
    GRUNNLAG_ANTIBODY = "GRUNNLAG_ANTIBODY"
    GRUNNLAG_OBJECTIVE = "GRUNNLAG_OBJECTIVE"
    GRUNNLAG_INSTRUMENT = "GRUNNLAG_INSTRUMENT"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_CONTEXT = "GRUNNLAG_CONTEXT"
    GRUNNLAG_DATALINK = "GRUNNLAG_DATALINK"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_MODEL = "GRUNNLAG_MODEL"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_STAGE = "GRUNNLAG_STAGE"
    GRUNNLAG_POSITION = "GRUNNLAG_POSITION"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_ROI = "GRUNNLAG_ROI"
    GRUNNLAG_LABEL = "GRUNNLAG_LABEL"
    GRUNNLAG_FEATURE = "GRUNNLAG_FEATURE"
    BORD_TABLE = "BORD_TABLE"


class LokClientGrantType(str, Enum):
    """An enumeration."""

    CLIENT_CREDENTIALS = "CLIENT_CREDENTIALS"
    "Backend (Client Credentials)"
    IMPLICIT = "IMPLICIT"
    "Implicit Grant"
    AUTHORIZATION_CODE = "AUTHORIZATION_CODE"
    "Authorization Code"
    PASSWORD = "PASSWORD"
    "Password"
    SESSION = "SESSION"
    "Django Session"


class AcquisitionKind(str, Enum):
    """What do the multiple positions in this acquistion represent?"""

    POSTION_IS_SAMPLE = "POSTION_IS_SAMPLE"
    POSITION_IS_ROI = "POSITION_IS_ROI"
    UNKNOWN = "UNKNOWN"


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
    FRAME = "FRAME"
    "Frame"
    SLICE = "SLICE"
    "Slice"
    POINT = "POINT"
    "Point"


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


class PandasDType(str, Enum):
    OBJECT = "OBJECT"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    BOOL = "BOOL"
    CATEGORY = "CATEGORY"
    DATETIME65 = "DATETIME65"
    TIMEDELTA = "TIMEDELTA"
    UNICODE = "UNICODE"


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
    FRAME = "FRAME"
    "Frame"
    SLICE = "SLICE"
    "Slice"
    POINT = "POINT"
    "Point"


class Medium(str, Enum):
    """The medium of the imaging environment

    Important for the objective settings"""

    AIR = "AIR"
    GLYCEROL = "GLYCEROL"
    OIL = "OIL"
    OTHER = "OTHER"
    WATER = "WATER"


class LinkableModels(str, Enum):
    """LinkableModels Models are models that can be shared amongst users and groups. They representent the models of the DB"""

    ADMIN_LOGENTRY = "ADMIN_LOGENTRY"
    AUTH_PERMISSION = "AUTH_PERMISSION"
    AUTH_GROUP = "AUTH_GROUP"
    CONTENTTYPES_CONTENTTYPE = "CONTENTTYPES_CONTENTTYPE"
    SESSIONS_SESSION = "SESSIONS_SESSION"
    TAGGIT_TAG = "TAGGIT_TAG"
    TAGGIT_TAGGEDITEM = "TAGGIT_TAGGEDITEM"
    KOMMENT_COMMENT = "KOMMENT_COMMENT"
    DB_TESTMODEL = "DB_TESTMODEL"
    LOK_LOKUSER = "LOK_LOKUSER"
    LOK_LOKAPP = "LOK_LOKAPP"
    LOK_LOKCLIENT = "LOK_LOKCLIENT"
    GUARDIAN_USEROBJECTPERMISSION = "GUARDIAN_USEROBJECTPERMISSION"
    GUARDIAN_GROUPOBJECTPERMISSION = "GUARDIAN_GROUPOBJECTPERMISSION"
    GRUNNLAG_USERMETA = "GRUNNLAG_USERMETA"
    GRUNNLAG_ANTIBODY = "GRUNNLAG_ANTIBODY"
    GRUNNLAG_OBJECTIVE = "GRUNNLAG_OBJECTIVE"
    GRUNNLAG_INSTRUMENT = "GRUNNLAG_INSTRUMENT"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_CONTEXT = "GRUNNLAG_CONTEXT"
    GRUNNLAG_DATALINK = "GRUNNLAG_DATALINK"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_MODEL = "GRUNNLAG_MODEL"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_STAGE = "GRUNNLAG_STAGE"
    GRUNNLAG_POSITION = "GRUNNLAG_POSITION"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_ROI = "GRUNNLAG_ROI"
    GRUNNLAG_LABEL = "GRUNNLAG_LABEL"
    GRUNNLAG_FEATURE = "GRUNNLAG_FEATURE"
    BORD_TABLE = "BORD_TABLE"
    PLOTQL_PLOT = "PLOTQL_PLOT"


class ModelKind(str, Enum):
    """What format is the model in?"""

    ONNX = "ONNX"
    TENSORFLOW = "TENSORFLOW"
    PYTORCH = "PYTORCH"
    UNKNOWN = "UNKNOWN"


class DescendendInput(BaseModel):
    children: Optional[Tuple[Optional["DescendendInput"], ...]]
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

    class Config:
        frozen = True


class GroupAssignmentInput(BaseModel):
    permissions: Tuple[Optional[str], ...]
    group: ID

    class Config:
        frozen = True


class UserAssignmentInput(BaseModel):
    permissions: Tuple[Optional[str], ...]
    user: str
    "The user id"

    class Config:
        frozen = True


class OmeroRepresentationInput(BaseModel):
    """The Omero Meta Data of an Image

    Follows closely the omexml model. With a few alterations:
    - The data model of the datasets and experimenters is
    part of the mikro datamodel and are not accessed here.
    - Some parameters are ommited as they are not really used"""

    planes: Optional[Tuple[Optional["PlaneInput"], ...]]
    channels: Optional[Tuple[Optional["ChannelInput"], ...]]
    physical_size: Optional["PhysicalSizeInput"] = Field(alias="physicalSize")
    scale: Optional[Tuple[Optional[float], ...]]
    position: Optional[ID]
    acquisition_date: Optional[datetime] = Field(alias="acquisitionDate")
    objective_settings: Optional["ObjectiveSettingsInput"] = Field(
        alias="objectiveSettings"
    )
    imaging_environment: Optional["ImagingEnvironmentInput"] = Field(
        alias="imagingEnvironment"
    )
    instrument: Optional[ID]
    objective: Optional[ID]

    class Config:
        frozen = True


class PlaneInput(BaseModel):
    """ " A plane in an image

    Plane follows the convention of the OME model, where the first index is the
    Z axis, the second is the Y axis, the third is the X axis, the fourth is the
    C axis, and the fifth is the T axis.

    It attached the image at the indicated index to the image and gives information
    about the plane (e.g. exposure time, delta t to the origin, etc.)"""

    z: Optional[int]
    "Z index of the plane"
    y: Optional[int]
    "Y index of the plane"
    x: Optional[int]
    "X index of the plane"
    c: Optional[int]
    "C index of the plane"
    t: Optional[int]
    "Z index of the plane"
    position_x: Optional[float] = Field(alias="positionX")
    "The planes X position on the stage of the microscope"
    position_y: Optional[float] = Field(alias="positionY")
    "The planes Y position on the stage of the microscope"
    position_z: Optional[float] = Field(alias="positionZ")
    "The planes Z position on the stage of the microscope"
    exposure_time: Optional[float] = Field(alias="exposureTime")
    "The exposure time of the plane (e.g. Laser exposure)"
    delta_t: Optional[float] = Field(alias="deltaT")
    "The Delta T to the origin of the image acqusition"

    class Config:
        frozen = True


class ChannelInput(BaseModel):
    """A channel in an image

    Channels can be highly variable in their properties. This class is a
    representation of the most common properties of a channel."""

    name: Optional[str]
    "The name of the channel"
    emmission_wavelength: Optional[float] = Field(alias="emmissionWavelength")
    "The emmission wavelength of the fluorophore in nm"
    excitation_wavelength: Optional[float] = Field(alias="excitationWavelength")
    "The excitation wavelength of the fluorophore in nm"
    acquisition_mode: Optional[str] = Field(alias="acquisitionMode")
    "The acquisition mode of the channel"
    color: Optional[str]
    "The default color for the channel (might be ommited by the rendered)"

    class Config:
        frozen = True


class PhysicalSizeInput(BaseModel):
    """Physical size of the image

    Each dimensions of the image has a physical size. This is the size of the
    pixel in the image. The physical size is given in micrometers on a PIXEL
    basis. This means that the physical size of the image is the size of the
    pixel in the image * the number of pixels in the image. For example, if
    the image is 1000x1000 pixels and the physical size of the image is 3 (x params) x 3 (y params),
    micrometer, the physical size of the image is 3000x3000 micrometer. If the image

    The t dimension is given in ms, since the time is given in ms.
    The C dimension is given in nm, since the wavelength is given in nm."""

    x: Optional[float]
    "Physical size of *one* Pixel in the x dimension (in µm)"
    y: Optional[float]
    "Physical size of *one* Pixel in the t dimension (in µm)"
    z: Optional[float]
    "Physical size of *one* Pixel in the z dimension (in µm)"
    t: Optional[float]
    "Physical size of *one* Pixel in the t dimension (in ms)"
    c: Optional[float]
    "Physical size of *one* Pixel in the c dimension (in nm)"

    class Config:
        frozen = True


class ObjectiveSettingsInput(BaseModel):
    """Settings of the objective used to acquire the image

    Follows the OME model for objective settings"""

    correction_collar: Optional[float] = Field(alias="correctionCollar")
    "The correction collar of the objective"
    medium: Optional[Medium]
    "The medium of the objective"
    numerical_aperture: Optional[float] = Field(alias="numericalAperture")
    "The numerical aperture of the objective"
    working_distance: Optional[float] = Field(alias="workingDistance")
    "The working distance of the objective"

    class Config:
        frozen = True


class ImagingEnvironmentInput(BaseModel):
    """The imaging environment during the acquisition

    Follows the OME model for imaging environment"""

    air_pressure: Optional[float] = Field(alias="airPressure")
    "The air pressure during the acquisition"
    co2_percent: Optional[float] = Field(alias="co2Percent")
    "The CO2 percentage in the environment"
    humidity: Optional[float]
    "The humidity of the imaging environment"
    temperature: Optional[float]
    "The temperature of the imaging environment"
    map: Optional[Dict]
    "A map of the imaging environment. Key value based"

    class Config:
        frozen = True


class InputVector(Vectorizable, BaseModel):
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

    class Config:
        frozen = True


class LabelFragmentRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    name: Optional[str]
    "Cleartext name"

    class Config:
        frozen = True


class LabelFragment(BaseModel):
    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    instance: int
    "The instance value of the representation (pixel value). Must be a value of the image array"
    id: ID
    representation: Optional[LabelFragmentRepresentation]
    "The Representation this Label instance belongs to"

    class Config:
        frozen = True


class ContextFragmentLinks(BaseModel):
    """DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)"""

    typename: Optional[Literal["DataLink"]] = Field(alias="__typename")
    x_id: int = Field(alias="xId")
    y_id: int = Field(alias="yId")
    left_type: Optional[LinkableModels] = Field(alias="leftType")
    "Left Type"
    right_type: Optional[LinkableModels] = Field(alias="rightType")
    "Left Type"

    class Config:
        frozen = True


class ContextFragment(BaseModel):
    typename: Optional[Literal["Context"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the context"
    links: Tuple[ContextFragmentLinks, ...]

    class Config:
        frozen = True


class ListContextFragment(BaseModel):
    typename: Optional[Literal["Context"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the context"

    class Config:
        frozen = True


class ThumbnailFragment(BaseModel):
    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    id: ID
    image: Optional[str]

    class Config:
        frozen = True


class TableFragmentCreator(BaseModel):
    """User

    This object represents a user in the system. Users are used to
    control access to different parts of the system. Users are assigned
    to groups. A user has access to a part of the system if the user is
    a member of a group that has the permission assigned to it.

    Users can be be "creator" of objects. This means that the user has
    created the object. This is used to control access to objects. A user
    can only access objects that they have created, or objects that they
    have access to through a group that they are a member of.

    See the documentation for "Object Level Permissions" for more information."""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class TableFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class TableFragmentReporigins(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class TableFragmentExperiment(BaseModel):
    """
    An experiment is a collection of samples and their representations.
    It mimics the concept of an experiment in the lab and is the top level
    object in the data model.

    You can use the experiment to group samples and representations likewise
    to how you would group files into folders in a file system.





    """

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class TableFragment(Table, BaseModel):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: ID
    name: str
    tags: Optional[Tuple[Optional[str], ...]]
    "A comma-separated list of tags."
    store: Optional[Parquet]
    "The parquet store for the table"
    creator: Optional[TableFragmentCreator]
    "The creator of the Table"
    sample: Optional[TableFragmentSample]
    "Sample this table belongs to"
    rep_origins: Tuple[TableFragmentReporigins, ...] = Field(alias="repOrigins")
    "The Representation this Table belongs to"
    experiment: Optional[TableFragmentExperiment]
    "The Experiment this Table belongs to."

    class Config:
        frozen = True


class ListLinkFragment(BaseModel):
    typename: Optional[Literal["DataLink"]] = Field(alias="__typename")
    relation: Optional[str]
    "Relation"
    id: ID

    class Config:
        frozen = True


class LinkFragment(BaseModel):
    typename: Optional[Literal["DataLink"]] = Field(alias="__typename")
    relation: Optional[str]
    "Relation"
    id: ID
    x_id: int = Field(alias="xId")
    y_id: int = Field(alias="yId")
    left_type: Optional[LinkableModels] = Field(alias="leftType")
    "Left Type"
    right_type: Optional[LinkableModels] = Field(alias="rightType")
    "Left Type"

    class Config:
        frozen = True


class StageFragment(Stage, BaseModel):
    typename: Optional[Literal["Stage"]] = Field(alias="__typename")
    id: ID
    kind: Optional[AcquisitionKind]
    "The kind of acquisition"
    name: str
    "The name of the stage"
    physical_size: Optional[Tuple[Optional[float], ...]] = Field(alias="physicalSize")
    "The physical size of the stage"

    class Config:
        frozen = True


class ListStageFragment(Stage, BaseModel):
    typename: Optional[Literal["Stage"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the stage"
    kind: Optional[AcquisitionKind]
    "The kind of acquisition"
    physical_size: Optional[Tuple[Optional[float], ...]] = Field(alias="physicalSize")
    "The physical size of the stage"

    class Config:
        frozen = True


class SampleFragmentRepresentations(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class SampleFragmentExperiments(BaseModel):
    """
    An experiment is a collection of samples and their representations.
    It mimics the concept of an experiment in the lab and is the top level
    object in the data model.

    You can use the experiment to group samples and representations likewise
    to how you would group files into folders in a file system.





    """

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class SampleFragment(BaseModel):
    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    "The name of the sample"
    id: ID
    representations: Optional[Tuple[Optional[SampleFragmentRepresentations], ...]]
    "Associated representations of this Sample"
    experiments: Tuple[SampleFragmentExperiments, ...]
    "The experiments this sample belongs to"

    class Config:
        frozen = True


class ROIFragmentVectors(BaseModel):
    typename: Optional[Literal["Vector"]] = Field(alias="__typename")
    x: Optional[float]
    "X-coordinate"
    y: Optional[float]
    "Y-coordinate"
    t: Optional[float]
    "T-coordinate"
    c: Optional[float]
    "C-coordinate"
    z: Optional[float]
    "Z-coordinate"

    class Config:
        frozen = True


class ROIFragmentRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class ROIFragmentDerivedrepresentations(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class ROIFragmentCreator(BaseModel):
    """User

    This object represents a user in the system. Users are used to
    control access to different parts of the system. Users are assigned
    to groups. A user has access to a part of the system if the user is
    a member of a group that has the permission assigned to it.

    Users can be be "creator" of objects. This means that the user has
    created the object. This is used to control access to objects. A user
    can only access objects that they have created, or objects that they
    have access to through a group that they are a member of.

    See the documentation for "Object Level Permissions" for more information."""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str
    id: ID
    color: str
    "The prefered color of the user"

    class Config:
        frozen = True


class ROIFragment(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    id: ID
    label: Optional[str]
    "The label of the ROI (for UI)"
    vectors: Optional[Tuple[Optional[ROIFragmentVectors], ...]]
    "The vectors of the ROI"
    type: ROIType
    "The Roi can have varying types, consult your API"
    representation: Optional[ROIFragmentRepresentation]
    "The Representation this ROI was original used to create (drawn on)"
    derived_representations: Tuple[ROIFragmentDerivedrepresentations, ...] = Field(
        alias="derivedRepresentations"
    )
    creator: ROIFragmentCreator
    "The user that created the ROI"

    class Config:
        frozen = True


class ListROIFragmentVectors(BaseModel):
    typename: Optional[Literal["Vector"]] = Field(alias="__typename")
    x: Optional[float]
    "X-coordinate"
    y: Optional[float]
    "Y-coordinate"
    t: Optional[float]
    "T-coordinate"
    c: Optional[float]
    "C-coordinate"
    z: Optional[float]
    "Z-coordinate"

    class Config:
        frozen = True


class ListROIFragmentRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class ListROIFragmentCreator(BaseModel):
    """User

    This object represents a user in the system. Users are used to
    control access to different parts of the system. Users are assigned
    to groups. A user has access to a part of the system if the user is
    a member of a group that has the permission assigned to it.

    Users can be be "creator" of objects. This means that the user has
    created the object. This is used to control access to objects. A user
    can only access objects that they have created, or objects that they
    have access to through a group that they are a member of.

    See the documentation for "Object Level Permissions" for more information."""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str
    id: ID
    color: str
    "The prefered color of the user"

    class Config:
        frozen = True


class ListROIFragment(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    id: ID
    label: Optional[str]
    "The label of the ROI (for UI)"
    vectors: Optional[Tuple[Optional[ListROIFragmentVectors], ...]]
    "The vectors of the ROI"
    type: ROIType
    "The Roi can have varying types, consult your API"
    representation: Optional[ListROIFragmentRepresentation]
    "The Representation this ROI was original used to create (drawn on)"
    creator: ListROIFragmentCreator
    "The user that created the ROI"

    class Config:
        frozen = True


class FeatureFragmentLabelRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class FeatureFragmentLabel(BaseModel):
    """A Label is a trough model for image and features.

    Its map an instance value of a representation
    (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
    class instance.

    There can only be one label per representation and class instance. You can then attach
    features to the label.


    """

    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    instance: int
    "The instance value of the representation (pixel value). Must be a value of the image array"
    representation: Optional[FeatureFragmentLabelRepresentation]
    "The Representation this Label instance belongs to"

    class Config:
        frozen = True


class FeatureFragment(BaseModel):
    typename: Optional[Literal["Feature"]] = Field(alias="__typename")
    label: Optional[FeatureFragmentLabel]
    "The Label this Feature belongs to"
    id: ID
    key: str
    "The key of the feature"
    value: Optional[FeatureValue]
    "Value"

    class Config:
        frozen = True


class InstrumentFragment(BaseModel):
    typename: Optional[Literal["Instrument"]] = Field(alias="__typename")
    id: ID
    dichroics: Optional[Dict]
    detectors: Optional[Dict]
    filters: Optional[Dict]
    name: str
    lot_number: Optional[str] = Field(alias="lotNumber")
    serial_number: Optional[str] = Field(alias="serialNumber")
    manufacturer: Optional[str]
    model: Optional[str]

    class Config:
        frozen = True


class ExperimentFragmentCreator(BaseModel):
    """User

    This object represents a user in the system. Users are used to
    control access to different parts of the system. Users are assigned
    to groups. A user has access to a part of the system if the user is
    a member of a group that has the permission assigned to it.

    Users can be be "creator" of objects. This means that the user has
    created the object. This is used to control access to objects. A user
    can only access objects that they have created, or objects that they
    have access to through a group that they are a member of.

    See the documentation for "Object Level Permissions" for more information."""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class ExperimentFragment(BaseModel):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the experiment"
    creator: Optional[ExperimentFragmentCreator]
    "The user that created the experiment"

    class Config:
        frozen = True


class RepresentationFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the sample"

    class Config:
        frozen = True


class RepresentationFragmentOmeroPhysicalsize(BaseModel):
    """Physical size of the image

    Each dimensions of the image has a physical size. This is the size of the
    pixel in the image. The physical size is given in micrometers on a PIXEL
    basis. This means that the physical size of the image is the size of the
    pixel in the image * the number of pixels in the image. For example, if
    the image is 1000x1000 pixels and the physical size of the image is 3 (x params) x 3 (y params),
    micrometer, the physical size of the image is 3000x3000 micrometer. If the image

    The t dimension is given in ms, since the time is given in ms.
    The C dimension is given in nm, since the wavelength is given in nm."""

    typename: Optional[Literal["PhysicalSize"]] = Field(alias="__typename")
    x: Optional[float]
    "Physical size of *one* Pixel in the x dimension (in µm)"
    y: Optional[float]
    "Physical size of *one* Pixel in the t dimension (in µm)"
    z: Optional[float]
    "Physical size of *one* Pixel in the z dimension (in µm)"
    t: Optional[float]
    "Physical size of *one* Pixel in the t dimension (in ms)"
    c: Optional[float]
    "Physical size of *one* Pixel in the c dimension (in µm)"

    class Config:
        frozen = True


class RepresentationFragmentOmeroPosition(Position, BaseModel):
    """The relative position of a sample on a microscope stage"""

    typename: Optional[Literal["Position"]] = Field(alias="__typename")
    id: ID
    x: Optional[float]
    y: Optional[float]

    class Config:
        frozen = True


class RepresentationFragmentOmeroChannels(BaseModel):
    """A channel in an image

    Channels can be highly variable in their properties. This class is a
    representation of the most common properties of a channel."""

    typename: Optional[Literal["Channel"]] = Field(alias="__typename")
    name: Optional[str]
    "The name of the channel"
    color: Optional[str]
    "The default color for the channel (might be ommited by the rendered)"

    class Config:
        frozen = True


class RepresentationFragmentOmero(Omero, BaseModel):
    """Omero is a through model that stores the real world context of an image

    This means that it stores the position (corresponding to the relative displacement to
    a stage (Both are models)), objective and other meta data of the image.

    """

    typename: Optional[Literal["Omero"]] = Field(alias="__typename")
    scale: Optional[Tuple[Optional[float], ...]]
    physical_size: Optional[RepresentationFragmentOmeroPhysicalsize] = Field(
        alias="physicalSize"
    )
    position: Optional[RepresentationFragmentOmeroPosition]
    channels: Optional[Tuple[Optional[RepresentationFragmentOmeroChannels], ...]]

    class Config:
        frozen = True


class RepresentationFragmentOrigins(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"

    class Config:
        frozen = True


class RepresentationFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    sample: Optional[RepresentationFragmentSample]
    "The Sample this representation belosngs to"
    shape: Optional[Tuple[int, ...]]
    "The arrays shape"
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"
    name: Optional[str]
    "Cleartext name"
    omero: Optional[RepresentationFragmentOmero]
    origins: Tuple[RepresentationFragmentOrigins, ...]

    class Config:
        frozen = True


class ListRepresentationFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    shape: Optional[Tuple[int, ...]]
    "The arrays shape"
    name: Optional[str]
    "Cleartext name"
    store: Optional[Store]

    class Config:
        frozen = True


class ModelFragmentContexts(BaseModel):
    """Context(id, created_by, created_through, name, created_at, experiment, creator)"""

    typename: Optional[Literal["Context"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the context"

    class Config:
        frozen = True


class ModelFragment(BaseModel):
    typename: Optional[Literal["Model"]] = Field(alias="__typename")
    id: ID
    data: Optional[ModelData]
    "The model data"
    kind: Optional[ModelKind]
    "The kind of model"
    name: str
    "The name of the model"
    contexts: Tuple[ModelFragmentContexts, ...]
    "The contexts this model is valid for"

    class Config:
        frozen = True


class MetricFragmentRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class MetricFragmentCreator(BaseModel):
    """User

    This object represents a user in the system. Users are used to
    control access to different parts of the system. Users are assigned
    to groups. A user has access to a part of the system if the user is
    a member of a group that has the permission assigned to it.

    Users can be be "creator" of objects. This means that the user has
    created the object. This is used to control access to objects. A user
    can only access objects that they have created, or objects that they
    have access to through a group that they are a member of.

    See the documentation for "Object Level Permissions" for more information."""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class MetricFragment(BaseModel):
    typename: Optional[Literal["Metric"]] = Field(alias="__typename")
    id: ID
    representation: Optional[MetricFragmentRepresentation]
    "The Representatoin this Metric belongs to"
    key: str
    "The Key"
    value: Optional[MetricValue]
    "Value"
    creator: Optional[MetricFragmentCreator]
    created_at: datetime = Field(alias="createdAt")

    class Config:
        frozen = True


class OmeroFileFragmentExperiments(BaseModel):
    """
    An experiment is a collection of samples and their representations.
    It mimics the concept of an experiment in the lab and is the top level
    object in the data model.

    You can use the experiment to group samples and representations likewise
    to how you would group files into folders in a file system.





    """

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class OmeroFileFragment(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the file"
    file: Optional[File]
    "The file"
    type: OmeroFileType
    "The type of the file"
    experiments: Tuple[OmeroFileFragmentExperiments, ...]
    "The experiment this file belongs to"

    class Config:
        frozen = True


class PositionFragmentOmeros(Omero, BaseModel):
    """Omero is a through model that stores the real world context of an image

    This means that it stores the position (corresponding to the relative displacement to
    a stage (Both are models)), objective and other meta data of the image.

    """

    typename: Optional[Literal["Omero"]] = Field(alias="__typename")
    representation: ListRepresentationFragment

    class Config:
        frozen = True


class PositionFragment(Position, BaseModel):
    typename: Optional[Literal["Position"]] = Field(alias="__typename")
    id: ID
    stage: ListStageFragment
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    omeros: Optional[Tuple[Optional[PositionFragmentOmeros], ...]]
    "Associated images through Omero"

    class Config:
        frozen = True


class ObjectiveFragment(Objective, BaseModel):
    typename: Optional[Literal["Objective"]] = Field(alias="__typename")
    id: ID
    name: str
    magnification: float

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesUpdateExperiments(BaseModel):
    """
    An experiment is a collection of samples and their representations.
    It mimics the concept of an experiment in the lab and is the top level
    object in the data model.

    You can use the experiment to group samples and representations likewise
    to how you would group files into folders in a file system.





    """

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str
    "The name of the experiment"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesUpdate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the sample"
    experiments: Tuple[Watch_samplesSubscriptionMysamplesUpdateExperiments, ...]
    "The experiments this sample belongs to"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesCreateExperiments(BaseModel):
    """
    An experiment is a collection of samples and their representations.
    It mimics the concept of an experiment in the lab and is the top level
    object in the data model.

    You can use the experiment to group samples and representations likewise
    to how you would group files into folders in a file system.





    """

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    name: str
    "The name of the experiment"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesCreate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    "The name of the sample"
    experiments: Tuple[Watch_samplesSubscriptionMysamplesCreateExperiments, ...]
    "The experiments this sample belongs to"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamples(BaseModel):
    typename: Optional[Literal["SamplesEvent"]] = Field(alias="__typename")
    update: Optional[Watch_samplesSubscriptionMysamplesUpdate]
    create: Optional[Watch_samplesSubscriptionMysamplesCreate]

    class Config:
        frozen = True


class Watch_samplesSubscription(BaseModel):
    my_samples: Optional[Watch_samplesSubscriptionMysamples] = Field(alias="mySamples")

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "subscription watch_samples {\n  mySamples {\n    update {\n      id\n      name\n      experiments {\n        name\n      }\n    }\n    create {\n      name\n      experiments {\n        name\n      }\n    }\n  }\n}"


class Watch_roisSubscriptionRois(BaseModel):
    typename: Optional[Literal["RoiEvent"]] = Field(alias="__typename")
    update: Optional[ListROIFragment]
    delete: Optional[ID]
    create: Optional[ListROIFragment]

    class Config:
        frozen = True


class Watch_roisSubscription(BaseModel):
    rois: Optional[Watch_roisSubscriptionRois]

    class Arguments(BaseModel):
        representation: ID

    class Meta:
        document = "fragment ListROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nsubscription watch_rois($representation: ID!) {\n  rois(representation: $representation) {\n    update {\n      ...ListROI\n    }\n    delete\n    create {\n      ...ListROI\n    }\n  }\n}"


class Create_labelMutationCreatelabel(BaseModel):
    """A Label is a trough model for image and features.

    Its map an instance value of a representation
    (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
    class instance.

    There can only be one label per representation and class instance. You can then attach
    features to the label.


    """

    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    id: ID
    instance: int
    "The instance value of the representation (pixel value). Must be a value of the image array"

    class Config:
        frozen = True


class Create_labelMutation(BaseModel):
    create_label: Optional[Create_labelMutationCreatelabel] = Field(alias="createLabel")
    "Creates a Label\n    \n    This mutation creates a Label and returns the created Label.\n    We require a reference to the image pixel value that the label belongs to.\n    (Labels can be created for any pixel in an image, no matter if this image\n    is a mask or not). However labels can only be created for pixels that are\n    integer values.\n\n    \n\n    "

    class Arguments(BaseModel):
        instance: int
        representation: ID
        creator: Optional[ID] = None
        name: Optional[str] = None

    class Meta:
        document = "mutation create_label($instance: Int!, $representation: ID!, $creator: ID, $name: String) {\n  createLabel(\n    instance: $instance\n    representation: $representation\n    creator: $creator\n    name: $name\n  ) {\n    id\n    instance\n  }\n}"


class Create_contextMutation(BaseModel):
    create_context: Optional[ContextFragment] = Field(alias="createContext")
    "Create an Experiment\n    \n    This mutation creates an Experiment and returns the created Experiment.\n    "

    class Arguments(BaseModel):
        name: str
        experiment: Optional[ID] = None

    class Meta:
        document = "fragment Context on Context {\n  id\n  name\n  links {\n    xId\n    yId\n    leftType\n    rightType\n  }\n}\n\nmutation create_context($name: String!, $experiment: ID) {\n  createContext(name: $name, experiment: $experiment) {\n    ...Context\n  }\n}"


class Create_thumbnailMutation(BaseModel):
    upload_thumbnail: Optional[ThumbnailFragment] = Field(alias="uploadThumbnail")

    class Arguments(BaseModel):
        rep: ID
        file: File
        major_color: Optional[str] = None
        blurhash: Optional[str] = None

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nmutation create_thumbnail($rep: ID!, $file: ImageFile!, $major_color: String, $blurhash: String) {\n  uploadThumbnail(\n    rep: $rep\n    file: $file\n    majorColor: $major_color\n    blurhash: $blurhash\n  ) {\n    ...Thumbnail\n  }\n}"


class NegotiateMutation(BaseModel):
    negotiate: Optional[Dict]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "mutation negotiate {\n  negotiate\n}"


class From_dfMutation(BaseModel):
    from_df: Optional[TableFragment] = Field(alias="fromDf")
    "Creates a Representation"

    class Arguments(BaseModel):
        df: ParquetInput
        name: str
        rep_origins: Optional[List[Optional[ID]]] = None

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  repOrigins {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nmutation from_df($df: ParquetInput!, $name: String!, $rep_origins: [ID]) {\n  fromDf(df: $df, name: $name, repOrigins: $rep_origins) {\n    ...Table\n  }\n}"


class LinkMutation(BaseModel):
    link: Optional[ListLinkFragment]
    "Create an Comment \n    \n    This mutation creates a comment. It takes a commentable_id and a commentable_type.\n    If this is the first comment on the commentable, it will create a new comment thread.\n    If there is already a comment thread, it will add the comment to the thread (by setting\n    it's parent to the last parent comment in the thread).\n\n    CreateComment takes a list of Descendents, which are the comment tree. The Descendents\n    are a recursive structure, where each Descendent can have a list of Descendents as children.\n    The Descendents are either a Leaf, which is a text node, or a MentionDescendent, which is a\n    reference to another user on the platform.\n\n    Please convert your comment tree to a list of Descendents before sending it to the server.\n    TODO: Add a converter from a comment tree to a list of Descendents.\n\n    \n    (only signed in users)"

    class Arguments(BaseModel):
        relation: str
        x_type: LinkableModels
        x_id: ID
        y_type: LinkableModels
        y_id: ID
        context: Optional[ID] = None

    class Meta:
        document = "fragment ListLink on DataLink {\n  relation\n  id\n}\n\nmutation link($relation: String!, $x_type: LinkableModels!, $x_id: ID!, $y_type: LinkableModels!, $y_id: ID!, $context: ID) {\n  link(\n    relation: $relation\n    xType: $x_type\n    xId: $x_id\n    yType: $y_type\n    yId: $y_id\n    context: $context\n  ) {\n    ...ListLink\n  }\n}"


class Link_rep_to_repMutation(BaseModel):
    link: Optional[ListLinkFragment]
    "Create an Comment \n    \n    This mutation creates a comment. It takes a commentable_id and a commentable_type.\n    If this is the first comment on the commentable, it will create a new comment thread.\n    If there is already a comment thread, it will add the comment to the thread (by setting\n    it's parent to the last parent comment in the thread).\n\n    CreateComment takes a list of Descendents, which are the comment tree. The Descendents\n    are a recursive structure, where each Descendent can have a list of Descendents as children.\n    The Descendents are either a Leaf, which is a text node, or a MentionDescendent, which is a\n    reference to another user on the platform.\n\n    Please convert your comment tree to a list of Descendents before sending it to the server.\n    TODO: Add a converter from a comment tree to a list of Descendents.\n\n    \n    (only signed in users)"

    class Arguments(BaseModel):
        relation: str
        left_rep: ID
        right_rep: ID
        context: Optional[ID] = None

    class Meta:
        document = "fragment ListLink on DataLink {\n  relation\n  id\n}\n\nmutation link_rep_to_rep($relation: String!, $left_rep: ID!, $right_rep: ID!, $context: ID) {\n  link(\n    relation: $relation\n    xType: GRUNNLAG_REPRESENTATION\n    xId: $left_rep\n    yType: GRUNNLAG_REPRESENTATION\n    yId: $right_rep\n    context: $context\n  ) {\n    ...ListLink\n  }\n}"


class Create_stageMutation(BaseModel):
    create_stage: Optional[StageFragment] = Field(alias="createStage")
    "Creates a Stage\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        name: str
        creator: Optional[ID] = None
        tags: Optional[List[Optional[str]]] = None
        physical_size: List[Optional[float]]

    class Meta:
        document = "fragment Stage on Stage {\n  id\n  kind\n  name\n  physicalSize\n}\n\nmutation create_stage($name: String!, $creator: ID, $tags: [String], $physical_size: [Float]!) {\n  createStage(\n    name: $name\n    creator: $creator\n    tags: $tags\n    physicalSize: $physical_size\n  ) {\n    ...Stage\n  }\n}"


class Create_sampleMutationCreatesampleCreator(BaseModel):
    """User

    This object represents a user in the system. Users are used to
    control access to different parts of the system. Users are assigned
    to groups. A user has access to a part of the system if the user is
    a member of a group that has the permission assigned to it.

    Users can be be "creator" of objects. This means that the user has
    created the object. This is used to control access to objects. A user
    can only access objects that they have created, or objects that they
    have access to through a group that they are a member of.

    See the documentation for "Object Level Permissions" for more information."""

    typename: Optional[Literal["User"]] = Field(alias="__typename")
    email: str

    class Config:
        frozen = True


class Create_sampleMutationCreatesample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the sample"
    creator: Optional[Create_sampleMutationCreatesampleCreator]
    "The user that created the sample"

    class Config:
        frozen = True


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


class Create_roiMutation(BaseModel):
    create_roi: Optional[ROIFragment] = Field(alias="createROI")
    "Creates a Sample"

    class Arguments(BaseModel):
        representation: ID
        vectors: List[Optional[InputVector]]
        creator: Optional[ID] = None
        type: RoiTypeInput
        label: Optional[str] = None
        tags: Optional[List[Optional[str]]] = None

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n  }\n  derivedRepresentations {\n    id\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nmutation create_roi($representation: ID!, $vectors: [InputVector]!, $creator: ID, $type: RoiTypeInput!, $label: String, $tags: [String]) {\n  createROI(\n    representation: $representation\n    vectors: $vectors\n    type: $type\n    creator: $creator\n    label: $label\n    tags: $tags\n  ) {\n    ...ROI\n  }\n}"


class Create_featureMutationCreatefeatureLabelRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID

    class Config:
        frozen = True


class Create_featureMutationCreatefeatureLabel(BaseModel):
    """A Label is a trough model for image and features.

    Its map an instance value of a representation
    (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
    class instance.

    There can only be one label per representation and class instance. You can then attach
    features to the label.


    """

    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    id: ID
    representation: Optional[Create_featureMutationCreatefeatureLabelRepresentation]
    "The Representation this Label instance belongs to"

    class Config:
        frozen = True


class Create_featureMutationCreatefeature(BaseModel):
    """A Feature is a numerical key value pair that is attached to a Label.

    You can model it for example as a key value pair of a class instance of a segmentation mask.
    Representation -> Label0 -> Feature0
                             -> Feature1
                   -> Label1 -> Feature0

    Features can be used to store any numerical value that is attached to a class instance.
    THere can only ever be one key per label. If you want to store multiple values for a key, you can
    store them as a list in the value field.

    Feature are analogous to metrics on a representation, but for a specific class instance (Label)

    """

    typename: Optional[Literal["Feature"]] = Field(alias="__typename")
    id: ID
    key: str
    "The key of the feature"
    value: Optional[FeatureValue]
    "Value"
    label: Optional[Create_featureMutationCreatefeatureLabel]
    "The Label this Feature belongs to"

    class Config:
        frozen = True


class Create_featureMutation(BaseModel):
    createfeature: Optional[Create_featureMutationCreatefeature]
    "Creates a Feature\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        label: ID
        key: Optional[str] = None
        value: FeatureValue
        creator: Optional[ID] = None

    class Meta:
        document = "mutation create_feature($label: ID!, $key: String, $value: FeatureValue!, $creator: ID) {\n  createfeature(label: $label, key: $key, value: $value, creator: $creator) {\n    id\n    key\n    value\n    label {\n      id\n      representation {\n        id\n      }\n    }\n  }\n}"


class Create_instrumentMutation(BaseModel):
    create_instrument: Optional[InstrumentFragment] = Field(alias="createInstrument")
    "Creates an Instrument\n    \n    This mutation creates an Instrument and returns the created Instrument.\n    The serial number is required and the manufacturer is inferred from the serial number.\n    "

    class Arguments(BaseModel):
        detectors: Optional[List[Optional[Dict]]] = None
        dichroics: Optional[List[Optional[Dict]]] = None
        filters: Optional[List[Optional[Dict]]] = None
        name: str
        objectives: Optional[List[Optional[ID]]] = None
        lot_number: Optional[str] = None
        serial_number: Optional[str] = None
        model: Optional[str] = None
        manufacturer: Optional[str] = None

    class Meta:
        document = "fragment Instrument on Instrument {\n  id\n  dichroics\n  detectors\n  filters\n  name\n  lotNumber\n  serialNumber\n  manufacturer\n  model\n}\n\nmutation create_instrument($detectors: [GenericScalar], $dichroics: [GenericScalar], $filters: [GenericScalar], $name: String!, $objectives: [ID], $lotNumber: String, $serialNumber: String, $model: String, $manufacturer: String) {\n  createInstrument(\n    detectors: $detectors\n    dichroics: $dichroics\n    filters: $filters\n    name: $name\n    lotNumber: $lotNumber\n    objectives: $objectives\n    serialNumber: $serialNumber\n    model: $model\n    manufacturer: $manufacturer\n  ) {\n    ...Instrument\n  }\n}"


class Create_experimentMutation(BaseModel):
    create_experiment: Optional[ExperimentFragment] = Field(alias="createExperiment")
    "Create an Experiment\n    \n    This mutation creates an Experiment and returns the created Experiment.\n    "

    class Arguments(BaseModel):
        name: str
        creator: Optional[str] = None
        description: Optional[str] = None
        tags: Optional[List[Optional[str]]] = None

    class Meta:
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n}\n\nmutation create_experiment($name: String!, $creator: String, $description: String, $tags: [String]) {\n  createExperiment(\n    name: $name\n    creator: $creator\n    description: $description\n    tags: $tags\n  ) {\n    ...Experiment\n  }\n}"


class From_xarrayMutation(BaseModel):
    """Creates a Representation from an xarray dataset."""

    from_x_array: Optional[RepresentationFragment] = Field(alias="fromXArray")
    "Creates a Representation"

    class Arguments(BaseModel):
        xarray: XArrayInput
        name: Optional[str] = None
        variety: Optional[RepresentationVarietyInput] = None
        origins: Optional[List[Optional[ID]]] = None
        file_origins: Optional[List[Optional[ID]]] = None
        roi_origins: Optional[List[Optional[ID]]] = None
        tags: Optional[List[Optional[str]]] = None
        experiments: Optional[List[Optional[ID]]] = None
        sample: Optional[ID] = None
        omero: Optional[OmeroRepresentationInput] = None

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    position {\n      id\n      x\n      y\n    }\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nmutation from_xarray($xarray: XArrayInput!, $name: String, $variety: RepresentationVarietyInput, $origins: [ID], $file_origins: [ID], $roi_origins: [ID], $tags: [String], $experiments: [ID], $sample: ID, $omero: OmeroRepresentationInput) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n    fileOrigins: $file_origins\n    roiOrigins: $roi_origins\n    experiments: $experiments\n    variety: $variety\n  ) {\n    ...Representation\n  }\n}"


class Double_uploadMutationX(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    store: Optional[Store]

    class Config:
        frozen = True


class Double_uploadMutationY(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    store: Optional[Store]

    class Config:
        frozen = True


class Double_uploadMutation(BaseModel):
    x: Optional[Double_uploadMutationX]
    "Creates a Representation"
    y: Optional[Double_uploadMutationY]
    "Creates a Representation"

    class Arguments(BaseModel):
        xarray: XArrayInput
        name: Optional[str] = None
        origins: Optional[List[Optional[ID]]] = None
        tags: Optional[List[Optional[str]]] = None
        sample: Optional[ID] = None
        omero: Optional[OmeroRepresentationInput] = None

    class Meta:
        document = "mutation double_upload($xarray: XArrayInput!, $name: String, $origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  x: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n  y: fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n  ) {\n    id\n    store\n  }\n}"


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
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    position {\n      id\n      x\n      y\n    }\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nmutation update_representation($id: ID!, $tags: [String], $sample: ID, $variety: RepresentationVarietyInput) {\n  updateRepresentation(rep: $id, tags: $tags, sample: $sample, variety: $variety) {\n    ...Representation\n  }\n}"


class Create_modelMutation(BaseModel):
    create_model: Optional[ModelFragment] = Field(alias="createModel")
    "Creates an Instrument\n    \n    This mutation creates an Instrument and returns the created Instrument.\n    The serial number is required and the manufacturer is inferred from the serial number.\n    "

    class Arguments(BaseModel):
        data: ModelFile
        kind: ModelKind
        name: str
        contexts: Optional[List[Optional[ID]]] = None
        experiments: Optional[List[Optional[ID]]] = None

    class Meta:
        document = "fragment Model on Model {\n  id\n  data\n  kind\n  name\n  contexts {\n    id\n    name\n  }\n}\n\nmutation create_model($data: ModelFile!, $kind: ModelKind!, $name: String!, $contexts: [ID], $experiments: [ID]) {\n  createModel(\n    data: $data\n    kind: $kind\n    name: $name\n    contexts: $contexts\n    experiments: $experiments\n  ) {\n    ...Model\n  }\n}"


class Create_metricMutation(BaseModel):
    create_metric: Optional[MetricFragment] = Field(alias="createMetric")
    "Create a metric\n\n    This mutation creates a metric and returns the created metric.\n    \n    "

    class Arguments(BaseModel):
        representation: Optional[ID] = None
        sample: Optional[ID] = None
        experiment: Optional[ID] = None
        key: str
        value: MetricValue

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  representation {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nmutation create_metric($representation: ID, $sample: ID, $experiment: ID, $key: String!, $value: MetricValue!) {\n  createMetric(\n    representation: $representation\n    sample: $sample\n    experiment: $experiment\n    key: $key\n    value: $value\n  ) {\n    ...Metric\n  }\n}"


class Create_positionMutation(BaseModel):
    create_position: Optional[PositionFragment] = Field(alias="createPosition")
    "Creates a Feature\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        stage: ID
        x: float
        y: float
        z: float
        name: Optional[str] = None
        tags: Optional[List[Optional[str]]] = None

    class Meta:
        document = 'fragment ListRepresentation on Representation {\n  id\n  shape\n  name\n  store\n}\n\nfragment ListStage on Stage {\n  id\n  name\n  kind\n  physicalSize\n}\n\nfragment Position on Position {\n  id\n  stage {\n    ...ListStage\n  }\n  x\n  y\n  z\n  omeros(order: "-acquired") {\n    representation {\n      ...ListRepresentation\n    }\n  }\n}\n\nmutation create_position($stage: ID!, $x: Float!, $y: Float!, $z: Float!, $name: String, $tags: [String]) {\n  createPosition(stage: $stage, x: $x, y: $y, z: $z, tags: $tags, name: $name) {\n    ...Position\n  }\n}'


class Create_objectiveMutation(BaseModel):
    create_objective: Optional[ObjectiveFragment] = Field(alias="createObjective")
    "Creates an Instrument\n    \n    This mutation creates an Instrument and returns the created Instrument.\n    The serial number is required and the manufacturer is inferred from the serial number.\n    "

    class Arguments(BaseModel):
        serial_number: str
        name: str
        magnification: float

    class Meta:
        document = "fragment Objective on Objective {\n  id\n  name\n  magnification\n}\n\nmutation create_objective($serial_number: String!, $name: String!, $magnification: Float!) {\n  createObjective(\n    name: $name\n    serialNumber: $serial_number\n    magnification: $magnification\n  ) {\n    ...Objective\n  }\n}"


class Upload_bioimageMutationUploadomerofile(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: ID
    file: Optional[File]
    "The file"
    type: OmeroFileType
    "The type of the file"
    name: str
    "The name of the file"

    class Config:
        frozen = True


class Upload_bioimageMutation(BaseModel):
    upload_omero_file: Optional[Upload_bioimageMutationUploadomerofile] = Field(
        alias="uploadOmeroFile"
    )
    "Upload a file to Mikro\n\n    This mutation uploads a file to Omero and returns the created OmeroFile.\n    "

    class Arguments(BaseModel):
        file: File
        name: Optional[str] = None

    class Meta:
        document = "mutation upload_bioimage($file: ImageFile!, $name: String) {\n  uploadOmeroFile(file: $file, name: $name) {\n    id\n    file\n    type\n    name\n  }\n}"


class Get_labelQueryLabelforFeatures(BaseModel):
    """A Feature is a numerical key value pair that is attached to a Label.

    You can model it for example as a key value pair of a class instance of a segmentation mask.
    Representation -> Label0 -> Feature0
                             -> Feature1
                   -> Label1 -> Feature0

    Features can be used to store any numerical value that is attached to a class instance.
    THere can only ever be one key per label. If you want to store multiple values for a key, you can
    store them as a list in the value field.

    Feature are analogous to metrics on a representation, but for a specific class instance (Label)

    """

    typename: Optional[Literal["Feature"]] = Field(alias="__typename")
    id: ID
    key: str
    "The key of the feature"
    value: Optional[FeatureValue]
    "Value"

    class Config:
        frozen = True


class Get_labelQueryLabelfor(BaseModel):
    """A Label is a trough model for image and features.

    Its map an instance value of a representation
    (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
    class instance.

    There can only be one label per representation and class instance. You can then attach
    features to the label.


    """

    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    id: ID
    features: Optional[Tuple[Optional[Get_labelQueryLabelforFeatures], ...]]
    "Features attached to this Label"

    class Config:
        frozen = True


class Get_labelQuery(BaseModel):
    label_for: Optional[Get_labelQueryLabelfor] = Field(alias="labelFor")
    "Get a label for a specific instance on a specific representation\n    \n    "

    class Arguments(BaseModel):
        representation: ID
        instance: int

    class Meta:
        document = "query get_label($representation: ID!, $instance: Int!) {\n  labelFor(representation: $representation, instance: $instance) {\n    id\n    features {\n      id\n      key\n      value\n    }\n  }\n}"


class Expand_labelQuery(BaseModel):
    label: Optional[LabelFragment]
    "Get a single label by ID\n    \n    Returns a single label by ID. If the user does not have access\n    to the label, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Label on Label {\n  instance\n  id\n  representation {\n    id\n    name\n  }\n}\n\nquery expand_label($id: ID!) {\n  label(id: $id) {\n    ...Label\n  }\n}"


class Search_labelsQueryOptions(BaseModel):
    """A Label is a trough model for image and features.

    Its map an instance value of a representation
    (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
    class instance.

    There can only be one label per representation and class instance. You can then attach
    features to the label.


    """

    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    label: Optional[str]
    "The name of the instance"
    value: ID

    class Config:
        frozen = True


class Search_labelsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_labelsQueryOptions], ...]]
    "All Labels\n    \n    This query returns all Labels that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Labels that the user has access to. If the user is an amdin\n    or superuser, all Labels will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_labels($search: String) {\n  options: labels(name: $search, limit: 20) {\n    label: name\n    value: id\n  }\n}"


class Get_contextQuery(BaseModel):
    context: Optional[ContextFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Context on Context {\n  id\n  name\n  links {\n    xId\n    yId\n    leftType\n    rightType\n  }\n}\n\nquery get_context($id: ID!) {\n  context(id: $id) {\n    ...Context\n  }\n}"


class Get_mycontextsQuery(BaseModel):
    mycontexts: Optional[Tuple[Optional[ListContextFragment], ...]]
    "My Experiments runs a fast query on the database to return all\n    Experiments that the user has created. This query is faster than\n    the `experiments` query, but it does not return all Experiments that\n    the user has access to."

    class Arguments(BaseModel):
        limit: Optional[int] = None
        offset: Optional[int] = None

    class Meta:
        document = "fragment ListContext on Context {\n  id\n  name\n}\n\nquery get_mycontexts($limit: Int, $offset: Int) {\n  mycontexts(limit: $limit, offset: $offset) {\n    ...ListContext\n  }\n}"


class Expand_contextQuery(BaseModel):
    context: Optional[ContextFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Context on Context {\n  id\n  name\n  links {\n    xId\n    yId\n    leftType\n    rightType\n  }\n}\n\nquery expand_context($id: ID!) {\n  context(id: $id) {\n    ...Context\n  }\n}"


class Search_contextsQueryOptions(BaseModel):
    """Context(id, created_by, created_through, name, created_at, experiment, creator)"""

    typename: Optional[Literal["Context"]] = Field(alias="__typename")
    value: ID
    label: str
    "The name of the context"

    class Config:
        frozen = True


class Search_contextsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_contextsQueryOptions], ...]]
    "My Experiments runs a fast query on the database to return all\n    Experiments that the user has created. This query is faster than\n    the `experiments` query, but it does not return all Experiments that\n    the user has access to."

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_contexts($search: String) {\n  options: mycontexts(name: $search, limit: 30) {\n    value: id\n    label: name\n  }\n}"


class ThumbnailQuery(BaseModel):
    thumbnail: Optional[ThumbnailFragment]
    "Get a single Thumbnail by ID\n    \n    Get a single Thumbnail by ID. If the user does not have access\n    to the Thumbnail, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery Thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"


class Expand_thumbnailQuery(BaseModel):
    thumbnail: Optional[ThumbnailFragment]
    "Get a single Thumbnail by ID\n    \n    Get a single Thumbnail by ID. If the user does not have access\n    to the Thumbnail, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nquery expand_thumbnail($id: ID!) {\n  thumbnail(id: $id) {\n    ...Thumbnail\n  }\n}"


class Search_thumbnailsQueryOptions(BaseModel):
    """A Thumbnail is a render of a representation that is used to display the representation in the UI.

    Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.
    """

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    value: ID
    label: Optional[str]

    class Config:
        frozen = True


class Search_thumbnailsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_thumbnailsQueryOptions], ...]]
    "All Thumbnails\n    \n    This query returns all Thumbnails that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Thumbnails that the user has access to. If the user is an amdin\n    or superuser, all Thumbnails will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_thumbnails($search: String) {\n  options: thumbnails(name: $search, limit: 20) {\n    value: id\n    label: image\n  }\n}"


class Image_for_thumbnailQueryImage(BaseModel):
    """A Thumbnail is a render of a representation that is used to display the representation in the UI.

    Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.
    """

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    path: Optional[str]
    label: Optional[str]

    class Config:
        frozen = True


class Image_for_thumbnailQuery(BaseModel):
    image: Optional[Image_for_thumbnailQueryImage]
    "Get a single Thumbnail by ID\n    \n    Get a single Thumbnail by ID. If the user does not have access\n    to the Thumbnail, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "query image_for_thumbnail($id: ID!) {\n  image: thumbnail(id: $id) {\n    path: image\n    label: image\n  }\n}"


class Get_tableQuery(BaseModel):
    table: Optional[TableFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  repOrigins {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery get_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


class Expand_tableQuery(BaseModel):
    table: Optional[TableFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  repOrigins {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery expand_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


class Search_tablesQueryOptions(Table, BaseModel):
    """A Table is a collection of tabular data.

    It provides a way to store data in a tabular format and associate it with a Representation,
    Sample or Experiment. It is a way to store data that might be to large to store in a
    Feature or Metric on this Experiments. Or it might be data that is not easily represented
    as a Feature or Metric.

    Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
    Its columns are defined by the columns of the DataFrame.


    """

    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    value: ID
    label: str

    class Config:
        frozen = True


class Search_tablesQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_tablesQueryOptions], ...]]
    "My samples return all of the users samples attached to the current user"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "query search_tables {\n  options: tables {\n    value: id\n    label: name\n  }\n}"


class LinksQueryLinksRepresentationInlineFragment(Representation):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    store: Optional[Store]

    class Config:
        frozen = True


class LinksQueryLinksRepresentationInlineFragment(Representation):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    id: ID
    store: Optional[Store]

    class Config:
        frozen = True


class LinksQueryLinks(BaseModel):
    """DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)"""

    typename: Optional[Literal["DataLink"]] = Field(alias="__typename")
    relation: Optional[str]
    "Relation"
    x: LinksQueryLinksRepresentationInlineFragment
    "X"
    y: LinksQueryLinksRepresentationInlineFragment
    "Y"

    class Config:
        frozen = True


class LinksQuery(BaseModel):
    links: Optional[Tuple[Optional[LinksQueryLinks], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        x_type: LinkableModels
        y_type: LinkableModels
        relation: str
        context: Optional[ID] = None
        limit: Optional[int] = 10

    class Meta:
        document = "query Links($x_type: LinkableModels!, $y_type: LinkableModels!, $relation: String!, $context: ID, $limit: Int = 10) {\n  links(\n    xType: $x_type\n    yType: $y_type\n    relation: $relation\n    context: $context\n    limit: $limit\n  ) {\n    relation\n    x {\n      ... on Representation {\n        id\n        store\n      }\n    }\n    y {\n      ... on Representation {\n        id\n        store\n      }\n    }\n  }\n}"


class Get_linkQuery(BaseModel):
    link: Optional[LinkFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Link on DataLink {\n  relation\n  id\n  xId\n  yId\n  leftType\n  rightType\n}\n\nquery get_link($id: ID!) {\n  link(id: $id) {\n    ...Link\n  }\n}"


class Expand_linkQuery(BaseModel):
    link: Optional[LinkFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Link on DataLink {\n  relation\n  id\n  xId\n  yId\n  leftType\n  rightType\n}\n\nquery expand_link($id: ID!) {\n  link(id: $id) {\n    ...Link\n  }\n}"


class Search_linksQueryOptions(BaseModel):
    """DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)"""

    typename: Optional[Literal["DataLink"]] = Field(alias="__typename")
    value: ID
    label: Optional[str]
    "Relation"

    class Config:
        frozen = True


class Search_linksQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_linksQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_links($search: String) {\n  options: links(relation: $search, limit: 30) {\n    value: id\n    label: relation\n  }\n}"


class Get_stageQuery(BaseModel):
    stage: Optional[StageFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Stage on Stage {\n  id\n  kind\n  name\n  physicalSize\n}\n\nquery get_stage($id: ID!) {\n  stage(id: $id) {\n    ...Stage\n  }\n}"


class Expand_stageQuery(BaseModel):
    stage: Optional[StageFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Stage on Stage {\n  id\n  kind\n  name\n  physicalSize\n}\n\nquery expand_stage($id: ID!) {\n  stage(id: $id) {\n    ...Stage\n  }\n}"


class Search_stagesQueryOptions(Stage, BaseModel):
    """An Stage is a set of positions that share a common space on a microscope and can
    be use to translate.


    """

    typename: Optional[Literal["Stage"]] = Field(alias="__typename")
    value: ID
    label: str
    "The name of the stage"

    class Config:
        frozen = True


class Search_stagesQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_stagesQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_stages($search: String) {\n  options: stages(name: $search, limit: 30) {\n    value: id\n    label: name\n  }\n}"


class Get_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a Sample by ID\n    \n    Returns a single Sample by ID. If the user does not have access\n    to the Sample, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  experiments {\n    id\n  }\n}\n\nquery get_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class Search_sampleQueryOptions(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    value: ID
    label: str
    "The name of the sample"

    class Config:
        frozen = True


class Search_sampleQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_sampleQueryOptions], ...]]
    "All Samples\n    \n    This query returns all Samples that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Samples that the user has access to. If the user is an amdin\n    or superuser, all Samples will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_sample($search: String) {\n  options: samples(name: $search, limit: 20) {\n    value: id\n    label: name\n  }\n}"


class Expand_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a Sample by ID\n    \n    Returns a single Sample by ID. If the user does not have access\n    to the Sample, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  experiments {\n    id\n  }\n}\n\nquery expand_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class Get_roisQuery(BaseModel):
    rois: Optional[Tuple[Optional[ListROIFragment], ...]]
    "All Rois\n    \n    This query returns all Rois that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Rois that the user has access to. If the user is an amdin\n    or superuser, all Rois will be returned."

    class Arguments(BaseModel):
        representation: ID
        type: Optional[List[Optional[RoiTypeInput]]] = None

    class Meta:
        document = "fragment ListROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nquery get_rois($representation: ID!, $type: [RoiTypeInput]) {\n  rois(representation: $representation, type: $type) {\n    ...ListROI\n  }\n}"


class Expand_roiQuery(BaseModel):
    roi: Optional[ROIFragment]
    'Get a single Roi by ID"\n    \n    Returns a single Roi by ID. If the user does not have access\n    to the Roi, an error will be raised.'

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n  }\n  derivedRepresentations {\n    id\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nquery expand_roi($id: ID!) {\n  roi(id: $id) {\n    ...ROI\n  }\n}"


class Get_roiQuery(BaseModel):
    roi: Optional[ROIFragment]
    'Get a single Roi by ID"\n    \n    Returns a single Roi by ID. If the user does not have access\n    to the Roi, an error will be raised.'

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n  }\n  derivedRepresentations {\n    id\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nquery get_roi($id: ID!) {\n  roi(id: $id) {\n    ...ROI\n  }\n}"


class Search_roisQueryOptions(ROI, BaseModel):
    """A ROI is a region of interest in a representation.

    This region is to be regarded as a view on the representation. Depending
    on the implementatoin (type) of the ROI, the view can be constructed
    differently. For example, a rectangular ROI can be constructed by cropping
    the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
    representation with the polygon.

    The ROI can also store a name and a description. This is used to display the ROI in the UI.

    """

    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    label: ID
    value: ID

    class Config:
        frozen = True


class Search_roisQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_roisQueryOptions], ...]]
    "All Rois\n    \n    This query returns all Rois that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Rois that the user has access to. If the user is an amdin\n    or superuser, all Rois will be returned."

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_rois($search: String) {\n  options: rois(repname: $search) {\n    label: id\n    value: id\n  }\n}"


class Expand_featureQuery(BaseModel):
    feature: Optional[FeatureFragment]
    "Get a single feature by ID\n    \n    Returns a single feature by ID. If the user does not have access\n    to the feature, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Feature on Feature {\n  label {\n    instance\n    representation {\n      id\n    }\n  }\n  id\n  key\n  value\n}\n\nquery expand_feature($id: ID!) {\n  feature(id: $id) {\n    ...Feature\n  }\n}"


class Search_featuresQueryOptions(BaseModel):
    """A Feature is a numerical key value pair that is attached to a Label.

    You can model it for example as a key value pair of a class instance of a segmentation mask.
    Representation -> Label0 -> Feature0
                             -> Feature1
                   -> Label1 -> Feature0

    Features can be used to store any numerical value that is attached to a class instance.
    THere can only ever be one key per label. If you want to store multiple values for a key, you can
    store them as a list in the value field.

    Feature are analogous to metrics on a representation, but for a specific class instance (Label)

    """

    typename: Optional[Literal["Feature"]] = Field(alias="__typename")
    label: str
    "The key of the feature"
    value: ID

    class Config:
        frozen = True


class Search_featuresQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_featuresQueryOptions], ...]]
    "All features\n    \n    This query returns all features that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all features that the user has access to. If the user is an amdin\n    or superuser, all features will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_features($search: String) {\n  options: features(substring: $search, limit: 20) {\n    label: key\n    value: id\n  }\n}"


class RequestQueryRequest(BaseModel):
    typename: Optional[Literal["Credentials"]] = Field(alias="__typename")
    access_key: Optional[str] = Field(alias="accessKey")
    status: Optional[str]
    secret_key: Optional[str] = Field(alias="secretKey")

    class Config:
        frozen = True


class RequestQuery(BaseModel):
    request: Optional[RequestQueryRequest]
    "Requets a new set of credentials from the S3 server\n    encompassing the users credentials and the access key and secret key"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "query Request {\n  request {\n    accessKey\n    status\n    secretKey\n  }\n}"


class Get_instrumentQuery(BaseModel):
    instrument: Optional[InstrumentFragment]
    "Get a single instrumes by ID\n    \n    Returns a single instrument by ID. If the user does not have access\n    to the instrument, an error will be raised."

    class Arguments(BaseModel):
        id: Optional[ID] = None
        name: Optional[str] = None

    class Meta:
        document = "fragment Instrument on Instrument {\n  id\n  dichroics\n  detectors\n  filters\n  name\n  lotNumber\n  serialNumber\n  manufacturer\n  model\n}\n\nquery get_instrument($id: ID, $name: String) {\n  instrument(id: $id, name: $name) {\n    ...Instrument\n  }\n}"


class Expand_instrumentQuery(BaseModel):
    instrument: Optional[InstrumentFragment]
    "Get a single instrumes by ID\n    \n    Returns a single instrument by ID. If the user does not have access\n    to the instrument, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Instrument on Instrument {\n  id\n  dichroics\n  detectors\n  filters\n  name\n  lotNumber\n  serialNumber\n  manufacturer\n  model\n}\n\nquery expand_instrument($id: ID!) {\n  instrument(id: $id) {\n    ...Instrument\n  }\n}"


class Search_instrumentsQueryOptions(BaseModel):
    """Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)"""

    typename: Optional[Literal["Instrument"]] = Field(alias="__typename")
    value: ID
    label: str

    class Config:
        frozen = True


class Search_instrumentsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_instrumentsQueryOptions], ...]]
    "All Instruments\n    \n    This query returns all Instruments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Instruments that the user has access to. If the user is an amdin\n    or superuser, all Instruments will be returned."

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_instruments($search: String) {\n  options: instruments(name: $search, limit: 30) {\n    value: id\n    label: name\n  }\n}"


class Get_experimentQuery(BaseModel):
    experiment: Optional[ExperimentFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n}\n\nquery get_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"


class Expand_experimentQuery(BaseModel):
    experiment: Optional[ExperimentFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n}\n\nquery expand_experiment($id: ID!) {\n  experiment(id: $id) {\n    ...Experiment\n  }\n}"


class Search_experimentQueryOptions(BaseModel):
    """
    An experiment is a collection of samples and their representations.
    It mimics the concept of an experiment in the lab and is the top level
    object in the data model.

    You can use the experiment to group samples and representations likewise
    to how you would group files into folders in a file system.





    """

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    value: ID
    label: str
    "The name of the experiment"

    class Config:
        frozen = True


class Search_experimentQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_experimentQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_experiment($search: String) {\n  options: experiments(name: $search, limit: 30) {\n    value: id\n    label: name\n  }\n}"


class Expand_representationQuery(BaseModel):
    """Creates a new representation"""

    representation: Optional[RepresentationFragment]
    "Get a single Representation by ID\n    \n    Returns a single Representation by ID. If the user does not have access\n    to the Representation, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    position {\n      id\n      x\n      y\n    }\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Get_representationQuery(BaseModel):
    representation: Optional[RepresentationFragment]
    "Get a single Representation by ID\n    \n    Returns a single Representation by ID. If the user does not have access\n    to the Representation, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    position {\n      id\n      x\n      y\n    }\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery get_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Search_representationQueryOptions(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as a 5-dimensional representation. The dimensions are:
    - t: time
    - c: channel
    - z: z-stack
    - x: x-dimension
    - y: y-dimension

    This ensures a unified api for all images, regardless of their original dimensions. Another main
    determining factor for a representation is its variety:
    A representation can be a raw image representating voxels (VOXEL)
    or a segmentation mask representing instances of a class. (MASK)
    It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

    # Meta

    Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


    #Origins and Derivations

    Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
    Both are encapsulaed in the origins and derived fields.

    Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
    Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
    File and Rois that are used to create images are saved in the file origins and roi origins repectively.


    """

    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    value: ID
    label: Optional[str]
    "Cleartext name"

    class Config:
        frozen = True


class Search_representationQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_representationQueryOptions], ...]]
    "All Representations\n    \n    This query returns all Representations that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Representations that the user has access to. If the user is an amdin\n    or superuser, all Representations will be returned."

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
    "Get a random Representation\n    \n    Gets a random Representation from the database. This is used for\n    testing purposes\n    \n    "

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    position {\n      id\n      x\n      y\n    }\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"


class My_accessiblesQuery(BaseModel):
    accessiblerepresentations: Optional[Tuple[Optional[RepresentationFragment], ...]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    position {\n      id\n      x\n      y\n    }\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery my_accessibles {\n  accessiblerepresentations {\n    ...Representation\n  }\n}"


class Search_tagsQueryOptions(BaseModel):
    typename: Optional[Literal["Tag"]] = Field(alias="__typename")
    value: str
    label: str

    class Config:
        frozen = True


class Search_tagsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_tagsQueryOptions], ...]]
    "All Tags\n    \n    Returns all Tags that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Tags that the user has access to. If the user is an amdin\n    or superuser, all Tags will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_tags($search: String) {\n  options: tags(name: $search) {\n    value: slug\n    label: name\n  }\n}"


class Get_modelQuery(BaseModel):
    model: Optional[ModelFragment]
    "Get a single label by ID\n    \n    Returns a single label by ID. If the user does not have access\n    to the label, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Model on Model {\n  id\n  data\n  kind\n  name\n  contexts {\n    id\n    name\n  }\n}\n\nquery get_model($id: ID!) {\n  model(id: $id) {\n    ...Model\n  }\n}"


class Expand_modelQuery(BaseModel):
    model: Optional[ModelFragment]
    "Get a single label by ID\n    \n    Returns a single label by ID. If the user does not have access\n    to the label, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Model on Model {\n  id\n  data\n  kind\n  name\n  contexts {\n    id\n    name\n  }\n}\n\nquery expand_model($id: ID!) {\n  model(id: $id) {\n    ...Model\n  }\n}"


class Search_modelsQueryOptions(BaseModel):
    """A

    Mikro uses the omero-meta data to create representations of the file. See Representation for more information."""

    typename: Optional[Literal["Model"]] = Field(alias="__typename")
    label: str
    "The name of the model"
    value: ID

    class Config:
        frozen = True


class Search_modelsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_modelsQueryOptions], ...]]
    "All Labels\n    \n    This query returns all Labels that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Labels that the user has access to. If the user is an amdin\n    or superuser, all Labels will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_models($search: String) {\n  options: models(name: $search, limit: 20) {\n    label: name\n    value: id\n  }\n}"


class Expand_metricQuery(BaseModel):
    """Creates a new representation"""

    metric: Optional[MetricFragment]
    "Get a single Metric by ID\n    \n    Returns a single Metric by ID. If the user does not have access\n    to the Metric, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  representation {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nquery expand_metric($id: ID!) {\n  metric(id: $id) {\n    ...Metric\n  }\n}"


class Get_positionQuery(BaseModel):
    position: Optional[PositionFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = 'fragment ListRepresentation on Representation {\n  id\n  shape\n  name\n  store\n}\n\nfragment ListStage on Stage {\n  id\n  name\n  kind\n  physicalSize\n}\n\nfragment Position on Position {\n  id\n  stage {\n    ...ListStage\n  }\n  x\n  y\n  z\n  omeros(order: "-acquired") {\n    representation {\n      ...ListRepresentation\n    }\n  }\n}\n\nquery get_position($id: ID!) {\n  position(id: $id) {\n    ...Position\n  }\n}'


class Expand_positionQuery(BaseModel):
    position: Optional[PositionFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = 'fragment ListRepresentation on Representation {\n  id\n  shape\n  name\n  store\n}\n\nfragment ListStage on Stage {\n  id\n  name\n  kind\n  physicalSize\n}\n\nfragment Position on Position {\n  id\n  stage {\n    ...ListStage\n  }\n  x\n  y\n  z\n  omeros(order: "-acquired") {\n    representation {\n      ...ListRepresentation\n    }\n  }\n}\n\nquery expand_position($id: ID!) {\n  position(id: $id) {\n    ...Position\n  }\n}'


class Search_positionsQueryOptions(Position, BaseModel):
    """The relative position of a sample on a microscope stage"""

    typename: Optional[Literal["Position"]] = Field(alias="__typename")
    value: ID
    label: str
    "The name of the possition"

    class Config:
        frozen = True


class Search_positionsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_positionsQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str] = None
        stage: Optional[ID] = None

    class Meta:
        document = "query search_positions($search: String, $stage: ID) {\n  options: positions(name: $search, limit: 30, stage: $stage) {\n    value: id\n    label: name\n  }\n}"


class Get_objectiveQuery(BaseModel):
    objective: Optional[ObjectiveFragment]
    "Get a single instrumes by ID\n    \n    Returns a single instrument by ID. If the user does not have access\n    to the instrument, an error will be raised."

    class Arguments(BaseModel):
        id: Optional[ID] = None
        name: Optional[str] = None

    class Meta:
        document = "fragment Objective on Objective {\n  id\n  name\n  magnification\n}\n\nquery get_objective($id: ID, $name: String) {\n  objective(id: $id, name: $name) {\n    ...Objective\n  }\n}"


class Expand_objectiveQuery(BaseModel):
    objective: Optional[ObjectiveFragment]
    "Get a single instrumes by ID\n    \n    Returns a single instrument by ID. If the user does not have access\n    to the instrument, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Objective on Objective {\n  id\n  name\n  magnification\n}\n\nquery expand_objective($id: ID!) {\n  objective(id: $id) {\n    ...Objective\n  }\n}"


class Search_objectivesQueryOptions(Objective, BaseModel):
    """Objective(id, created_by, created_through, serial_number, name, magnification)"""

    typename: Optional[Literal["Objective"]] = Field(alias="__typename")
    value: ID
    label: str

    class Config:
        frozen = True


class Search_objectivesQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_objectivesQueryOptions], ...]]
    "All Instruments\n    \n    This query returns all Instruments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Instruments that the user has access to. If the user is an amdin\n    or superuser, all Instruments will be returned."

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_objectives($search: String) {\n  options: objectives(search: $search) {\n    value: id\n    label: name\n  }\n}"


class Get_omero_fileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single Omero File by ID\n    \n    Returns a single Omero File by ID. If the user does not have access\n    to the Omero File, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n  type\n  experiments {\n    id\n  }\n}\n\nquery get_omero_file($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Expand_omerofileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single Omero File by ID\n    \n    Returns a single Omero File by ID. If the user does not have access\n    to the Omero File, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n  type\n  experiments {\n    id\n  }\n}\n\nquery expand_omerofile($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Search_omerofileQueryOptions(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    value: ID
    label: str
    "The name of the file"

    class Config:
        frozen = True


class Search_omerofileQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_omerofileQueryOptions], ...]]
    "All OmeroFiles\n\n    This query returns all OmeroFiles that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all OmeroFiles that the user has access to. If the user is an amdin\n    or superuser, all OmeroFiles will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: str

    class Meta:
        document = "query search_omerofile($search: String!) {\n  options: omerofiles(name: $search) {\n    value: id\n    label: name\n  }\n}"


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


async def acreate_label(
    instance: int,
    representation: ID,
    creator: Optional[ID] = None,
    name: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[Create_labelMutationCreatelabel]:
    """create_label


     createLabel: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





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


     createLabel: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





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


async def acreate_context(
    name: str, experiment: Optional[ID] = None, rath: MikroRath = None
) -> Optional[ContextFragment]:
    """create_context


     createContext: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        name (str): name
        experiment (Optional[ID], optional): experiment.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return (
        await aexecute(
            Create_contextMutation, {"name": name, "experiment": experiment}, rath=rath
        )
    ).create_context


def create_context(
    name: str, experiment: Optional[ID] = None, rath: MikroRath = None
) -> Optional[ContextFragment]:
    """create_context


     createContext: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        name (str): name
        experiment (Optional[ID], optional): experiment.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return execute(
        Create_contextMutation, {"name": name, "experiment": experiment}, rath=rath
    ).create_context


async def acreate_thumbnail(
    rep: ID,
    file: File,
    major_color: Optional[str] = None,
    blurhash: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[ThumbnailFragment]:
    """create_thumbnail


     uploadThumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        rep (ID): rep
        file (File): file
        major_color (Optional[str], optional): major_color.
        blurhash (Optional[str], optional): blurhash.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return (
        await aexecute(
            Create_thumbnailMutation,
            {
                "rep": rep,
                "file": file,
                "major_color": major_color,
                "blurhash": blurhash,
            },
            rath=rath,
        )
    ).upload_thumbnail


def create_thumbnail(
    rep: ID,
    file: File,
    major_color: Optional[str] = None,
    blurhash: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[ThumbnailFragment]:
    """create_thumbnail


     uploadThumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        rep (ID): rep
        file (File): file
        major_color (Optional[str], optional): major_color.
        blurhash (Optional[str], optional): blurhash.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return execute(
        Create_thumbnailMutation,
        {"rep": rep, "file": file, "major_color": major_color, "blurhash": blurhash},
        rath=rath,
    ).upload_thumbnail


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


async def afrom_df(
    df: ParquetInput,
    name: str,
    rep_origins: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[TableFragment]:
    """from_df


     fromDf:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





    Arguments:
        df (ParquetInput): df
        name (str): name
        rep_origins (Optional[List[Optional[ID]]], optional): rep_origins.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return (
        await aexecute(
            From_dfMutation,
            {"df": df, "name": name, "rep_origins": rep_origins},
            rath=rath,
        )
    ).from_df


def from_df(
    df: ParquetInput,
    name: str,
    rep_origins: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[TableFragment]:
    """from_df


     fromDf:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





    Arguments:
        df (ParquetInput): df
        name (str): name
        rep_origins (Optional[List[Optional[ID]]], optional): rep_origins.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return execute(
        From_dfMutation, {"df": df, "name": name, "rep_origins": rep_origins}, rath=rath
    ).from_df


async def alink(
    relation: str,
    x_type: LinkableModels,
    x_id: ID,
    y_type: LinkableModels,
    y_id: ID,
    context: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[ListLinkFragment]:
    """link


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (str): relation
        x_type (LinkableModels): x_type
        x_id (ID): x_id
        y_type (LinkableModels): y_type
        y_id (ID): y_id
        context (Optional[ID], optional): context.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ListLinkFragment]"""
    return (
        await aexecute(
            LinkMutation,
            {
                "relation": relation,
                "x_type": x_type,
                "x_id": x_id,
                "y_type": y_type,
                "y_id": y_id,
                "context": context,
            },
            rath=rath,
        )
    ).link


def link(
    relation: str,
    x_type: LinkableModels,
    x_id: ID,
    y_type: LinkableModels,
    y_id: ID,
    context: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[ListLinkFragment]:
    """link


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (str): relation
        x_type (LinkableModels): x_type
        x_id (ID): x_id
        y_type (LinkableModels): y_type
        y_id (ID): y_id
        context (Optional[ID], optional): context.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ListLinkFragment]"""
    return execute(
        LinkMutation,
        {
            "relation": relation,
            "x_type": x_type,
            "x_id": x_id,
            "y_type": y_type,
            "y_id": y_id,
            "context": context,
        },
        rath=rath,
    ).link


async def alink_rep_to_rep(
    relation: str,
    left_rep: ID,
    right_rep: ID,
    context: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[ListLinkFragment]:
    """link_rep_to_rep


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (str): relation
        left_rep (ID): left_rep
        right_rep (ID): right_rep
        context (Optional[ID], optional): context.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ListLinkFragment]"""
    return (
        await aexecute(
            Link_rep_to_repMutation,
            {
                "relation": relation,
                "left_rep": left_rep,
                "right_rep": right_rep,
                "context": context,
            },
            rath=rath,
        )
    ).link


def link_rep_to_rep(
    relation: str,
    left_rep: ID,
    right_rep: ID,
    context: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[ListLinkFragment]:
    """link_rep_to_rep


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (str): relation
        left_rep (ID): left_rep
        right_rep (ID): right_rep
        context (Optional[ID], optional): context.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ListLinkFragment]"""
    return execute(
        Link_rep_to_repMutation,
        {
            "relation": relation,
            "left_rep": left_rep,
            "right_rep": right_rep,
            "context": context,
        },
        rath=rath,
    ).link


async def acreate_stage(
    name: str,
    physical_size: List[Optional[float]],
    creator: Optional[ID] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[StageFragment]:
    """create_stage


     createStage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        name (str): name
        physical_size (List[Optional[float]]): physical_size
        creator (Optional[ID], optional): creator.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return (
        await aexecute(
            Create_stageMutation,
            {
                "name": name,
                "creator": creator,
                "tags": tags,
                "physical_size": physical_size,
            },
            rath=rath,
        )
    ).create_stage


def create_stage(
    name: str,
    physical_size: List[Optional[float]],
    creator: Optional[ID] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[StageFragment]:
    """create_stage


     createStage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        name (str): name
        physical_size (List[Optional[float]]): physical_size
        creator (Optional[ID], optional): creator.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return execute(
        Create_stageMutation,
        {
            "name": name,
            "creator": creator,
            "tags": tags,
            "physical_size": physical_size,
        },
        rath=rath,
    ).create_stage


async def acreate_sample(
    name: Optional[str] = None,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[Create_sampleMutationCreatesample]:
    """create_sample


     createSample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


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


     createSample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


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


async def acreate_roi(
    representation: ID,
    vectors: List[Optional[InputVector]],
    type: RoiTypeInput,
    creator: Optional[ID] = None,
    label: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[ROIFragment]:
    """create_roi


     createROI: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        representation (ID): representation
        vectors (List[Optional[InputVector]]): vectors
        type (RoiTypeInput): type
        creator (Optional[ID], optional): creator.
        label (Optional[str], optional): label.
        tags (Optional[List[Optional[str]]], optional): tags.
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
                "label": label,
                "tags": tags,
            },
            rath=rath,
        )
    ).create_roi


def create_roi(
    representation: ID,
    vectors: List[Optional[InputVector]],
    type: RoiTypeInput,
    creator: Optional[ID] = None,
    label: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[ROIFragment]:
    """create_roi


     createROI: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        representation (ID): representation
        vectors (List[Optional[InputVector]]): vectors
        type (RoiTypeInput): type
        creator (Optional[ID], optional): creator.
        label (Optional[str], optional): label.
        tags (Optional[List[Optional[str]]], optional): tags.
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
            "label": label,
            "tags": tags,
        },
        rath=rath,
    ).create_roi


async def acreate_feature(
    label: ID,
    value: FeatureValue,
    key: Optional[str] = None,
    creator: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[Create_featureMutationCreatefeature]:
    """create_feature


     createfeature: A Feature is a numerical key value pair that is attached to a Label.

        You can model it for example as a key value pair of a class instance of a segmentation mask.
        Representation -> Label0 -> Feature0
                                 -> Feature1
                       -> Label1 -> Feature0

        Features can be used to store any numerical value that is attached to a class instance.
        THere can only ever be one key per label. If you want to store multiple values for a key, you can
        store them as a list in the value field.

        Feature are analogous to metrics on a representation, but for a specific class instance (Label)




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


     createfeature: A Feature is a numerical key value pair that is attached to a Label.

        You can model it for example as a key value pair of a class instance of a segmentation mask.
        Representation -> Label0 -> Feature0
                                 -> Feature1
                       -> Label1 -> Feature0

        Features can be used to store any numerical value that is attached to a class instance.
        THere can only ever be one key per label. If you want to store multiple values for a key, you can
        store them as a list in the value field.

        Feature are analogous to metrics on a representation, but for a specific class instance (Label)




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


async def acreate_instrument(
    name: str,
    detectors: Optional[List[Optional[Dict]]] = None,
    dichroics: Optional[List[Optional[Dict]]] = None,
    filters: Optional[List[Optional[Dict]]] = None,
    objectives: Optional[List[Optional[ID]]] = None,
    lot_number: Optional[str] = None,
    serial_number: Optional[str] = None,
    model: Optional[str] = None,
    manufacturer: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[InstrumentFragment]:
    """create_instrument


     createInstrument: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        name (str): name
        detectors (Optional[List[Optional[Dict]]], optional): detectors.
        dichroics (Optional[List[Optional[Dict]]], optional): dichroics.
        filters (Optional[List[Optional[Dict]]], optional): filters.
        objectives (Optional[List[Optional[ID]]], optional): objectives.
        lot_number (Optional[str], optional): lotNumber.
        serial_number (Optional[str], optional): serialNumber.
        model (Optional[str], optional): model.
        manufacturer (Optional[str], optional): manufacturer.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return (
        await aexecute(
            Create_instrumentMutation,
            {
                "detectors": detectors,
                "dichroics": dichroics,
                "filters": filters,
                "name": name,
                "objectives": objectives,
                "lotNumber": lot_number,
                "serialNumber": serial_number,
                "model": model,
                "manufacturer": manufacturer,
            },
            rath=rath,
        )
    ).create_instrument


def create_instrument(
    name: str,
    detectors: Optional[List[Optional[Dict]]] = None,
    dichroics: Optional[List[Optional[Dict]]] = None,
    filters: Optional[List[Optional[Dict]]] = None,
    objectives: Optional[List[Optional[ID]]] = None,
    lot_number: Optional[str] = None,
    serial_number: Optional[str] = None,
    model: Optional[str] = None,
    manufacturer: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[InstrumentFragment]:
    """create_instrument


     createInstrument: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        name (str): name
        detectors (Optional[List[Optional[Dict]]], optional): detectors.
        dichroics (Optional[List[Optional[Dict]]], optional): dichroics.
        filters (Optional[List[Optional[Dict]]], optional): filters.
        objectives (Optional[List[Optional[ID]]], optional): objectives.
        lot_number (Optional[str], optional): lotNumber.
        serial_number (Optional[str], optional): serialNumber.
        model (Optional[str], optional): model.
        manufacturer (Optional[str], optional): manufacturer.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return execute(
        Create_instrumentMutation,
        {
            "detectors": detectors,
            "dichroics": dichroics,
            "filters": filters,
            "name": name,
            "objectives": objectives,
            "lotNumber": lot_number,
            "serialNumber": serial_number,
            "model": model,
            "manufacturer": manufacturer,
        },
        rath=rath,
    ).create_instrument


async def acreate_experiment(
    name: str,
    creator: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[ExperimentFragment]:
    """create_experiment


     createExperiment:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








    Arguments:
        name (str): name
        creator (Optional[str], optional): creator.
        description (Optional[str], optional): description.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return (
        await aexecute(
            Create_experimentMutation,
            {
                "name": name,
                "creator": creator,
                "description": description,
                "tags": tags,
            },
            rath=rath,
        )
    ).create_experiment


def create_experiment(
    name: str,
    creator: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[ExperimentFragment]:
    """create_experiment


     createExperiment:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








    Arguments:
        name (str): name
        creator (Optional[str], optional): creator.
        description (Optional[str], optional): description.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return execute(
        Create_experimentMutation,
        {"name": name, "creator": creator, "description": description, "tags": tags},
        rath=rath,
    ).create_experiment


async def afrom_xarray(
    xarray: XArrayInput,
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[ID]]] = None,
    file_origins: Optional[List[Optional[ID]]] = None,
    roi_origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """from_xarray

     Creates a Representation from an xarray dataset.

    Arguments:
        xarray (XArrayInput): xarray
        name (Optional[str], optional): name.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        origins (Optional[List[Optional[ID]]], optional): origins.
        file_origins (Optional[List[Optional[ID]]], optional): file_origins.
        roi_origins (Optional[List[Optional[ID]]], optional): roi_origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
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
                "file_origins": file_origins,
                "roi_origins": roi_origins,
                "tags": tags,
                "experiments": experiments,
                "sample": sample,
                "omero": omero,
            },
            rath=rath,
        )
    ).from_x_array


def from_xarray(
    xarray: XArrayInput,
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[ID]]] = None,
    file_origins: Optional[List[Optional[ID]]] = None,
    roi_origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """from_xarray

     Creates a Representation from an xarray dataset.

    Arguments:
        xarray (XArrayInput): xarray
        name (Optional[str], optional): name.
        variety (Optional[RepresentationVarietyInput], optional): variety.
        origins (Optional[List[Optional[ID]]], optional): origins.
        file_origins (Optional[List[Optional[ID]]], optional): file_origins.
        roi_origins (Optional[List[Optional[ID]]], optional): roi_origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
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
            "file_origins": file_origins,
            "roi_origins": roi_origins,
            "tags": tags,
            "experiments": experiments,
            "sample": sample,
            "omero": omero,
        },
        rath=rath,
    ).from_x_array


async def adouble_upload(
    xarray: XArrayInput,
    name: Optional[str] = None,
    origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Double_uploadMutation:
    """double_upload


     x: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.




     y: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





    Arguments:
        xarray (XArrayInput): xarray
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
    xarray: XArrayInput,
    name: Optional[str] = None,
    origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    rath: MikroRath = None,
) -> Double_uploadMutation:
    """double_upload


     x: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.




     y: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





    Arguments:
        xarray (XArrayInput): xarray
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


     updateRepresentation: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





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


     updateRepresentation: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





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


async def acreate_model(
    data: ModelFile,
    kind: ModelKind,
    name: str,
    contexts: Optional[List[Optional[ID]]] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[ModelFragment]:
    """create_model


     createModel: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        data (ModelFile): data
        kind (ModelKind): kind
        name (str): name
        contexts (Optional[List[Optional[ID]]], optional): contexts.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ModelFragment]"""
    return (
        await aexecute(
            Create_modelMutation,
            {
                "data": data,
                "kind": kind,
                "name": name,
                "contexts": contexts,
                "experiments": experiments,
            },
            rath=rath,
        )
    ).create_model


def create_model(
    data: ModelFile,
    kind: ModelKind,
    name: str,
    contexts: Optional[List[Optional[ID]]] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[ModelFragment]:
    """create_model


     createModel: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        data (ModelFile): data
        kind (ModelKind): kind
        name (str): name
        contexts (Optional[List[Optional[ID]]], optional): contexts.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ModelFragment]"""
    return execute(
        Create_modelMutation,
        {
            "data": data,
            "kind": kind,
            "name": name,
            "contexts": contexts,
            "experiments": experiments,
        },
        rath=rath,
    ).create_model


async def acreate_metric(
    key: str,
    value: MetricValue,
    representation: Optional[ID] = None,
    sample: Optional[ID] = None,
    experiment: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[MetricFragment]:
    """create_metric



    Arguments:
        key (str): key
        value (MetricValue): value
        representation (Optional[ID], optional): representation.
        sample (Optional[ID], optional): sample.
        experiment (Optional[ID], optional): experiment.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[MetricFragment]"""
    return (
        await aexecute(
            Create_metricMutation,
            {
                "representation": representation,
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
    representation: Optional[ID] = None,
    sample: Optional[ID] = None,
    experiment: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[MetricFragment]:
    """create_metric



    Arguments:
        key (str): key
        value (MetricValue): value
        representation (Optional[ID], optional): representation.
        sample (Optional[ID], optional): sample.
        experiment (Optional[ID], optional): experiment.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[MetricFragment]"""
    return execute(
        Create_metricMutation,
        {
            "representation": representation,
            "sample": sample,
            "experiment": experiment,
            "key": key,
            "value": value,
        },
        rath=rath,
    ).create_metric


async def acreate_position(
    stage: ID,
    x: float,
    y: float,
    z: float,
    name: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[PositionFragment]:
    """create_position


     createPosition: The relative position of a sample on a microscope stage


    Arguments:
        stage (ID): stage
        x (float): x
        y (float): y
        z (float): z
        name (Optional[str], optional): name.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return (
        await aexecute(
            Create_positionMutation,
            {"stage": stage, "x": x, "y": y, "z": z, "name": name, "tags": tags},
            rath=rath,
        )
    ).create_position


def create_position(
    stage: ID,
    x: float,
    y: float,
    z: float,
    name: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    rath: MikroRath = None,
) -> Optional[PositionFragment]:
    """create_position


     createPosition: The relative position of a sample on a microscope stage


    Arguments:
        stage (ID): stage
        x (float): x
        y (float): y
        z (float): z
        name (Optional[str], optional): name.
        tags (Optional[List[Optional[str]]], optional): tags.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return execute(
        Create_positionMutation,
        {"stage": stage, "x": x, "y": y, "z": z, "name": name, "tags": tags},
        rath=rath,
    ).create_position


async def acreate_objective(
    serial_number: str, name: str, magnification: float, rath: MikroRath = None
) -> Optional[ObjectiveFragment]:
    """create_objective


     createObjective: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        serial_number (str): serial_number
        name (str): name
        magnification (float): magnification
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return (
        await aexecute(
            Create_objectiveMutation,
            {
                "serial_number": serial_number,
                "name": name,
                "magnification": magnification,
            },
            rath=rath,
        )
    ).create_objective


def create_objective(
    serial_number: str, name: str, magnification: float, rath: MikroRath = None
) -> Optional[ObjectiveFragment]:
    """create_objective


     createObjective: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        serial_number (str): serial_number
        name (str): name
        magnification (float): magnification
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return execute(
        Create_objectiveMutation,
        {"serial_number": serial_number, "name": name, "magnification": magnification},
        rath=rath,
    ).create_objective


async def aupload_bioimage(
    file: File, name: Optional[str] = None, rath: MikroRath = None
) -> Optional[Upload_bioimageMutationUploadomerofile]:
    """upload_bioimage



    Arguments:
        file (File): file
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Upload_bioimageMutationUploadomerofile]"""
    return (
        await aexecute(Upload_bioimageMutation, {"file": file, "name": name}, rath=rath)
    ).upload_omero_file


def upload_bioimage(
    file: File, name: Optional[str] = None, rath: MikroRath = None
) -> Optional[Upload_bioimageMutationUploadomerofile]:
    """upload_bioimage



    Arguments:
        file (File): file
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Upload_bioimageMutationUploadomerofile]"""
    return execute(
        Upload_bioimageMutation, {"file": file, "name": name}, rath=rath
    ).upload_omero_file


async def aget_label(
    representation: ID, instance: int, rath: MikroRath = None
) -> Optional[Get_labelQueryLabelfor]:
    """get_label


     labelFor: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





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


     labelFor: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





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


async def aexpand_label(id: ID, rath: MikroRath = None) -> Optional[LabelFragment]:
    """expand_label


     label: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LabelFragment]"""
    return (await aexecute(Expand_labelQuery, {"id": id}, rath=rath)).label


def expand_label(id: ID, rath: MikroRath = None) -> Optional[LabelFragment]:
    """expand_label


     label: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LabelFragment]"""
    return execute(Expand_labelQuery, {"id": id}, rath=rath).label


async def asearch_labels(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_labelsQueryOptions]]]:
    """search_labels


     options: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_labelsQueryLabels]]]"""
    return (await aexecute(Search_labelsQuery, {"search": search}, rath=rath)).labels


def search_labels(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_labelsQueryOptions]]]:
    """search_labels


     options: A Label is a trough model for image and features.

        Its map an instance value of a representation
        (e.g. a pixel value of a segmentation mask) to a set of corresponding features of the segmented
        class instance.

        There can only be one label per representation and class instance. You can then attach
        features to the label.





    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_labelsQueryLabels]]]"""
    return execute(Search_labelsQuery, {"search": search}, rath=rath).labels


async def aget_context(id: ID, rath: MikroRath = None) -> Optional[ContextFragment]:
    """get_context


     context: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return (await aexecute(Get_contextQuery, {"id": id}, rath=rath)).context


def get_context(id: ID, rath: MikroRath = None) -> Optional[ContextFragment]:
    """get_context


     context: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return execute(Get_contextQuery, {"id": id}, rath=rath).context


async def aget_mycontexts(
    limit: Optional[int] = None, offset: Optional[int] = None, rath: MikroRath = None
) -> Optional[List[Optional[ListContextFragment]]]:
    """get_mycontexts


     mycontexts: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        limit (Optional[int], optional): limit.
        offset (Optional[int], optional): offset.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListContextFragment]]]"""
    return (
        await aexecute(
            Get_mycontextsQuery, {"limit": limit, "offset": offset}, rath=rath
        )
    ).mycontexts


def get_mycontexts(
    limit: Optional[int] = None, offset: Optional[int] = None, rath: MikroRath = None
) -> Optional[List[Optional[ListContextFragment]]]:
    """get_mycontexts


     mycontexts: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        limit (Optional[int], optional): limit.
        offset (Optional[int], optional): offset.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListContextFragment]]]"""
    return execute(
        Get_mycontextsQuery, {"limit": limit, "offset": offset}, rath=rath
    ).mycontexts


async def aexpand_context(id: ID, rath: MikroRath = None) -> Optional[ContextFragment]:
    """expand_context


     context: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return (await aexecute(Expand_contextQuery, {"id": id}, rath=rath)).context


def expand_context(id: ID, rath: MikroRath = None) -> Optional[ContextFragment]:
    """expand_context


     context: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return execute(Expand_contextQuery, {"id": id}, rath=rath).context


async def asearch_contexts(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_contextsQueryOptions]]]:
    """search_contexts


     options: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_contextsQueryMycontexts]]]"""
    return (
        await aexecute(Search_contextsQuery, {"search": search}, rath=rath)
    ).mycontexts


def search_contexts(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_contextsQueryOptions]]]:
    """search_contexts


     options: Context(id, created_by, created_through, name, created_at, experiment, creator)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_contextsQueryMycontexts]]]"""
    return execute(Search_contextsQuery, {"search": search}, rath=rath).mycontexts


async def athumbnail(id: ID, rath: MikroRath = None) -> Optional[ThumbnailFragment]:
    """Thumbnail


     thumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return (await aexecute(ThumbnailQuery, {"id": id}, rath=rath)).thumbnail


def thumbnail(id: ID, rath: MikroRath = None) -> Optional[ThumbnailFragment]:
    """Thumbnail


     thumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



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


     thumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return (await aexecute(Expand_thumbnailQuery, {"id": id}, rath=rath)).thumbnail


def expand_thumbnail(id: ID, rath: MikroRath = None) -> Optional[ThumbnailFragment]:
    """expand_thumbnail


     thumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return execute(Expand_thumbnailQuery, {"id": id}, rath=rath).thumbnail


async def asearch_thumbnails(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_thumbnailsQueryOptions]]]:
    """search_thumbnails


     options: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



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
) -> Optional[List[Optional[Search_thumbnailsQueryOptions]]]:
    """search_thumbnails


     options: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



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


     image: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



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


     image: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Image_for_thumbnailQueryThumbnail]"""
    return execute(Image_for_thumbnailQuery, {"id": id}, rath=rath).thumbnail


async def aget_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """get_table


     table:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return (await aexecute(Get_tableQuery, {"id": id}, rath=rath)).table


def get_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """get_table


     table:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return execute(Get_tableQuery, {"id": id}, rath=rath).table


async def aexpand_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """expand_table


     table:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return (await aexecute(Expand_tableQuery, {"id": id}, rath=rath)).table


def expand_table(id: ID, rath: MikroRath = None) -> Optional[TableFragment]:
    """expand_table


     table:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





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


     options:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tablesQueryTables]]]"""
    return (await aexecute(Search_tablesQuery, {}, rath=rath)).tables


def search_tables(
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_tablesQueryOptions]]]:
    """search_tables


     options:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tablesQueryTables]]]"""
    return execute(Search_tablesQuery, {}, rath=rath).tables


async def alinks(
    x_type: LinkableModels,
    y_type: LinkableModels,
    relation: str,
    context: Optional[ID] = None,
    limit: Optional[int] = 10,
    rath: MikroRath = None,
) -> Optional[List[Optional[LinksQueryLinks]]]:
    """Links


     links: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        x_type (LinkableModels): x_type
        y_type (LinkableModels): y_type
        relation (str): relation
        context (Optional[ID], optional): context.
        limit (Optional[int], optional): limit. Defaults to 10
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[LinksQueryLinks]]]"""
    return (
        await aexecute(
            LinksQuery,
            {
                "x_type": x_type,
                "y_type": y_type,
                "relation": relation,
                "context": context,
                "limit": limit,
            },
            rath=rath,
        )
    ).links


def links(
    x_type: LinkableModels,
    y_type: LinkableModels,
    relation: str,
    context: Optional[ID] = None,
    limit: Optional[int] = 10,
    rath: MikroRath = None,
) -> Optional[List[Optional[LinksQueryLinks]]]:
    """Links


     links: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        x_type (LinkableModels): x_type
        y_type (LinkableModels): y_type
        relation (str): relation
        context (Optional[ID], optional): context.
        limit (Optional[int], optional): limit. Defaults to 10
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[LinksQueryLinks]]]"""
    return execute(
        LinksQuery,
        {
            "x_type": x_type,
            "y_type": y_type,
            "relation": relation,
            "context": context,
            "limit": limit,
        },
        rath=rath,
    ).links


async def aget_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """get_link


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return (await aexecute(Get_linkQuery, {"id": id}, rath=rath)).link


def get_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """get_link


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return execute(Get_linkQuery, {"id": id}, rath=rath).link


async def aexpand_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """expand_link


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return (await aexecute(Expand_linkQuery, {"id": id}, rath=rath)).link


def expand_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """expand_link


     link: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return execute(Expand_linkQuery, {"id": id}, rath=rath).link


async def asearch_links(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_linksQueryOptions]]]:
    """search_links


     options: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_linksQueryLinks]]]"""
    return (await aexecute(Search_linksQuery, {"search": search}, rath=rath)).links


def search_links(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_linksQueryOptions]]]:
    """search_links


     options: DataLink(id, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_linksQueryLinks]]]"""
    return execute(Search_linksQuery, {"search": search}, rath=rath).links


async def aget_stage(id: ID, rath: MikroRath = None) -> Optional[StageFragment]:
    """get_stage


     stage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return (await aexecute(Get_stageQuery, {"id": id}, rath=rath)).stage


def get_stage(id: ID, rath: MikroRath = None) -> Optional[StageFragment]:
    """get_stage


     stage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return execute(Get_stageQuery, {"id": id}, rath=rath).stage


async def aexpand_stage(id: ID, rath: MikroRath = None) -> Optional[StageFragment]:
    """expand_stage


     stage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return (await aexecute(Expand_stageQuery, {"id": id}, rath=rath)).stage


def expand_stage(id: ID, rath: MikroRath = None) -> Optional[StageFragment]:
    """expand_stage


     stage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return execute(Expand_stageQuery, {"id": id}, rath=rath).stage


async def asearch_stages(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_stagesQueryOptions]]]:
    """search_stages


     options: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_stagesQueryStages]]]"""
    return (await aexecute(Search_stagesQuery, {"search": search}, rath=rath)).stages


def search_stages(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_stagesQueryOptions]]]:
    """search_stages


     options: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_stagesQueryStages]]]"""
    return execute(Search_stagesQuery, {"search": search}, rath=rath).stages


async def aget_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """get_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[SampleFragment]"""
    return (await aexecute(Get_sampleQuery, {"id": id}, rath=rath)).sample


def get_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """get_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


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


     options: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


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


     options: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_sampleQuerySamples]]]"""
    return execute(Search_sampleQuery, {"search": search}, rath=rath).samples


async def aexpand_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """expand_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[SampleFragment]"""
    return (await aexecute(Expand_sampleQuery, {"id": id}, rath=rath)).sample


def expand_sample(id: ID, rath: MikroRath = None) -> Optional[SampleFragment]:
    """expand_sample


     sample: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[SampleFragment]"""
    return execute(Expand_sampleQuery, {"id": id}, rath=rath).sample


async def aget_rois(
    representation: ID,
    type: Optional[List[Optional[RoiTypeInput]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[ListROIFragment]]]:
    """get_rois


     rois: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        representation (ID): representation
        type (Optional[List[Optional[RoiTypeInput]]], optional): type.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListROIFragment]]]"""
    return (
        await aexecute(
            Get_roisQuery, {"representation": representation, "type": type}, rath=rath
        )
    ).rois


def get_rois(
    representation: ID,
    type: Optional[List[Optional[RoiTypeInput]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[ListROIFragment]]]:
    """get_rois


     rois: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        representation (ID): representation
        type (Optional[List[Optional[RoiTypeInput]]], optional): type.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListROIFragment]]]"""
    return execute(
        Get_roisQuery, {"representation": representation, "type": type}, rath=rath
    ).rois


async def aexpand_roi(id: ID, rath: MikroRath = None) -> Optional[ROIFragment]:
    """expand_roi


     roi: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return (await aexecute(Expand_roiQuery, {"id": id}, rath=rath)).roi


def expand_roi(id: ID, rath: MikroRath = None) -> Optional[ROIFragment]:
    """expand_roi


     roi: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return execute(Expand_roiQuery, {"id": id}, rath=rath).roi


async def aget_roi(id: ID, rath: MikroRath = None) -> Optional[ROIFragment]:
    """get_roi


     roi: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return (await aexecute(Get_roiQuery, {"id": id}, rath=rath)).roi


def get_roi(id: ID, rath: MikroRath = None) -> Optional[ROIFragment]:
    """get_roi


     roi: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ROIFragment]"""
    return execute(Get_roiQuery, {"id": id}, rath=rath).roi


async def asearch_rois(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_roisQueryOptions]]]:
    """search_rois


     options: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_roisQueryRois]]]"""
    return (await aexecute(Search_roisQuery, {"search": search}, rath=rath)).rois


def search_rois(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_roisQueryOptions]]]:
    """search_rois


     options: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_roisQueryRois]]]"""
    return execute(Search_roisQuery, {"search": search}, rath=rath).rois


async def aexpand_feature(id: ID, rath: MikroRath = None) -> Optional[FeatureFragment]:
    """expand_feature


     feature: A Feature is a numerical key value pair that is attached to a Label.

        You can model it for example as a key value pair of a class instance of a segmentation mask.
        Representation -> Label0 -> Feature0
                                 -> Feature1
                       -> Label1 -> Feature0

        Features can be used to store any numerical value that is attached to a class instance.
        THere can only ever be one key per label. If you want to store multiple values for a key, you can
        store them as a list in the value field.

        Feature are analogous to metrics on a representation, but for a specific class instance (Label)




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[FeatureFragment]"""
    return (await aexecute(Expand_featureQuery, {"id": id}, rath=rath)).feature


def expand_feature(id: ID, rath: MikroRath = None) -> Optional[FeatureFragment]:
    """expand_feature


     feature: A Feature is a numerical key value pair that is attached to a Label.

        You can model it for example as a key value pair of a class instance of a segmentation mask.
        Representation -> Label0 -> Feature0
                                 -> Feature1
                       -> Label1 -> Feature0

        Features can be used to store any numerical value that is attached to a class instance.
        THere can only ever be one key per label. If you want to store multiple values for a key, you can
        store them as a list in the value field.

        Feature are analogous to metrics on a representation, but for a specific class instance (Label)




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[FeatureFragment]"""
    return execute(Expand_featureQuery, {"id": id}, rath=rath).feature


async def asearch_features(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_featuresQueryOptions]]]:
    """search_features


     options: A Feature is a numerical key value pair that is attached to a Label.

        You can model it for example as a key value pair of a class instance of a segmentation mask.
        Representation -> Label0 -> Feature0
                                 -> Feature1
                       -> Label1 -> Feature0

        Features can be used to store any numerical value that is attached to a class instance.
        THere can only ever be one key per label. If you want to store multiple values for a key, you can
        store them as a list in the value field.

        Feature are analogous to metrics on a representation, but for a specific class instance (Label)




    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_featuresQueryFeatures]]]"""
    return (
        await aexecute(Search_featuresQuery, {"search": search}, rath=rath)
    ).features


def search_features(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_featuresQueryOptions]]]:
    """search_features


     options: A Feature is a numerical key value pair that is attached to a Label.

        You can model it for example as a key value pair of a class instance of a segmentation mask.
        Representation -> Label0 -> Feature0
                                 -> Feature1
                       -> Label1 -> Feature0

        Features can be used to store any numerical value that is attached to a class instance.
        THere can only ever be one key per label. If you want to store multiple values for a key, you can
        store them as a list in the value field.

        Feature are analogous to metrics on a representation, but for a specific class instance (Label)




    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_featuresQueryFeatures]]]"""
    return execute(Search_featuresQuery, {"search": search}, rath=rath).features


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


async def aget_instrument(
    id: Optional[ID] = None, name: Optional[str] = None, rath: MikroRath = None
) -> Optional[InstrumentFragment]:
    """get_instrument


     instrument: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        id (Optional[ID], optional): id.
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return (
        await aexecute(Get_instrumentQuery, {"id": id, "name": name}, rath=rath)
    ).instrument


def get_instrument(
    id: Optional[ID] = None, name: Optional[str] = None, rath: MikroRath = None
) -> Optional[InstrumentFragment]:
    """get_instrument


     instrument: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        id (Optional[ID], optional): id.
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return execute(Get_instrumentQuery, {"id": id, "name": name}, rath=rath).instrument


async def aexpand_instrument(
    id: ID, rath: MikroRath = None
) -> Optional[InstrumentFragment]:
    """expand_instrument


     instrument: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return (await aexecute(Expand_instrumentQuery, {"id": id}, rath=rath)).instrument


def expand_instrument(id: ID, rath: MikroRath = None) -> Optional[InstrumentFragment]:
    """expand_instrument


     instrument: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return execute(Expand_instrumentQuery, {"id": id}, rath=rath).instrument


async def asearch_instruments(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_instrumentsQueryOptions]]]:
    """search_instruments


     options: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_instrumentsQueryInstruments]]]"""
    return (
        await aexecute(Search_instrumentsQuery, {"search": search}, rath=rath)
    ).instruments


def search_instruments(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_instrumentsQueryOptions]]]:
    """search_instruments


     options: Instrument(id, created_by, created_through, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_instrumentsQueryInstruments]]]"""
    return execute(Search_instrumentsQuery, {"search": search}, rath=rath).instruments


async def aget_experiment(
    id: ID, rath: MikroRath = None
) -> Optional[ExperimentFragment]:
    """get_experiment


     experiment:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return (await aexecute(Get_experimentQuery, {"id": id}, rath=rath)).experiment


def get_experiment(id: ID, rath: MikroRath = None) -> Optional[ExperimentFragment]:
    """get_experiment


     experiment:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








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


     experiment:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return (await aexecute(Expand_experimentQuery, {"id": id}, rath=rath)).experiment


def expand_experiment(id: ID, rath: MikroRath = None) -> Optional[ExperimentFragment]:
    """expand_experiment


     experiment:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








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


     options:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








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


     options:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.








    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_experimentQueryExperiments]]]"""
    return execute(Search_experimentQuery, {"search": search}, rath=rath).experiments


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


     representation: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





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


     representation: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





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


     options: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





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


     options: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





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


     accessiblerepresentations: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





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


     accessiblerepresentations: A Representation is 5-dimensional representation of an image

        Mikro stores each image as a 5-dimensional representation. The dimensions are:
        - t: time
        - c: channel
        - z: z-stack
        - x: x-dimension
        - y: y-dimension

        This ensures a unified api for all images, regardless of their original dimensions. Another main
        determining factor for a representation is its variety:
        A representation can be a raw image representating voxels (VOXEL)
        or a segmentation mask representing instances of a class. (MASK)
        It can also representate a human perception of the image (RGB) or a human perception of the mask (RGBMASK)

        # Meta

        Meta information is stored in the omero field which gives access to the omero-meta data. Refer to the omero documentation for more information.


        #Origins and Derivations

        Images can be filtered, which means that a new representation is created from the other (original) representations. This new representation is then linked to the original representations. This way, we can always trace back to the original representation.
        Both are encapsulaed in the origins and derived fields.

        Representations belong to *one* sample. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample
        Each iamge has also a name, which is used to identify the image. The name is unique within a sample.
        File and Rois that are used to create images are saved in the file origins and roi origins repectively.





    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[RepresentationFragment]]]"""
    return execute(My_accessiblesQuery, {}, rath=rath).accessiblerepresentations


async def asearch_tags(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_tagsQueryOptions]]]:
    """search_tags



    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tagsQueryTags]]]"""
    return (await aexecute(Search_tagsQuery, {"search": search}, rath=rath)).tags


def search_tags(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_tagsQueryOptions]]]:
    """search_tags



    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tagsQueryTags]]]"""
    return execute(Search_tagsQuery, {"search": search}, rath=rath).tags


async def aget_model(id: ID, rath: MikroRath = None) -> Optional[ModelFragment]:
    """get_model


     model: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ModelFragment]"""
    return (await aexecute(Get_modelQuery, {"id": id}, rath=rath)).model


def get_model(id: ID, rath: MikroRath = None) -> Optional[ModelFragment]:
    """get_model


     model: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ModelFragment]"""
    return execute(Get_modelQuery, {"id": id}, rath=rath).model


async def aexpand_model(id: ID, rath: MikroRath = None) -> Optional[ModelFragment]:
    """expand_model


     model: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ModelFragment]"""
    return (await aexecute(Expand_modelQuery, {"id": id}, rath=rath)).model


def expand_model(id: ID, rath: MikroRath = None) -> Optional[ModelFragment]:
    """expand_model


     model: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ModelFragment]"""
    return execute(Expand_modelQuery, {"id": id}, rath=rath).model


async def asearch_models(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_modelsQueryOptions]]]:
    """search_models


     options: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_modelsQueryModels]]]"""
    return (await aexecute(Search_modelsQuery, {"search": search}, rath=rath)).models


def search_models(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_modelsQueryOptions]]]:
    """search_models


     options: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_modelsQueryModels]]]"""
    return execute(Search_modelsQuery, {"search": search}, rath=rath).models


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


async def aget_position(id: ID, rath: MikroRath = None) -> Optional[PositionFragment]:
    """get_position


     position: The relative position of a sample on a microscope stage


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return (await aexecute(Get_positionQuery, {"id": id}, rath=rath)).position


def get_position(id: ID, rath: MikroRath = None) -> Optional[PositionFragment]:
    """get_position


     position: The relative position of a sample on a microscope stage


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return execute(Get_positionQuery, {"id": id}, rath=rath).position


async def aexpand_position(
    id: ID, rath: MikroRath = None
) -> Optional[PositionFragment]:
    """expand_position


     position: The relative position of a sample on a microscope stage


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return (await aexecute(Expand_positionQuery, {"id": id}, rath=rath)).position


def expand_position(id: ID, rath: MikroRath = None) -> Optional[PositionFragment]:
    """expand_position


     position: The relative position of a sample on a microscope stage


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return execute(Expand_positionQuery, {"id": id}, rath=rath).position


async def asearch_positions(
    search: Optional[str] = None, stage: Optional[ID] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_positionsQueryOptions]]]:
    """search_positions


     options: The relative position of a sample on a microscope stage


    Arguments:
        search (Optional[str], optional): search.
        stage (Optional[ID], optional): stage.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_positionsQueryPositions]]]"""
    return (
        await aexecute(
            Search_positionsQuery, {"search": search, "stage": stage}, rath=rath
        )
    ).positions


def search_positions(
    search: Optional[str] = None, stage: Optional[ID] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_positionsQueryOptions]]]:
    """search_positions


     options: The relative position of a sample on a microscope stage


    Arguments:
        search (Optional[str], optional): search.
        stage (Optional[ID], optional): stage.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_positionsQueryPositions]]]"""
    return execute(
        Search_positionsQuery, {"search": search, "stage": stage}, rath=rath
    ).positions


async def aget_objective(
    id: Optional[ID] = None, name: Optional[str] = None, rath: MikroRath = None
) -> Optional[ObjectiveFragment]:
    """get_objective


     objective: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        id (Optional[ID], optional): id.
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return (
        await aexecute(Get_objectiveQuery, {"id": id, "name": name}, rath=rath)
    ).objective


def get_objective(
    id: Optional[ID] = None, name: Optional[str] = None, rath: MikroRath = None
) -> Optional[ObjectiveFragment]:
    """get_objective


     objective: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        id (Optional[ID], optional): id.
        name (Optional[str], optional): name.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return execute(Get_objectiveQuery, {"id": id, "name": name}, rath=rath).objective


async def aexpand_objective(
    id: ID, rath: MikroRath = None
) -> Optional[ObjectiveFragment]:
    """expand_objective


     objective: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return (await aexecute(Expand_objectiveQuery, {"id": id}, rath=rath)).objective


def expand_objective(id: ID, rath: MikroRath = None) -> Optional[ObjectiveFragment]:
    """expand_objective


     objective: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return execute(Expand_objectiveQuery, {"id": id}, rath=rath).objective


async def asearch_objectives(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_objectivesQueryOptions]]]:
    """search_objectives


     options: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_objectivesQueryObjectives]]]"""
    return (
        await aexecute(Search_objectivesQuery, {"search": search}, rath=rath)
    ).objectives


def search_objectives(
    search: Optional[str] = None, rath: MikroRath = None
) -> Optional[List[Optional[Search_objectivesQueryOptions]]]:
    """search_objectives


     options: Objective(id, created_by, created_through, serial_number, name, magnification)


    Arguments:
        search (Optional[str], optional): search.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_objectivesQueryObjectives]]]"""
    return execute(Search_objectivesQuery, {"search": search}, rath=rath).objectives


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


DescendendInput.update_forward_refs()
OmeroRepresentationInput.update_forward_refs()
