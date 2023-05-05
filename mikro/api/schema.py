from mikro.scalars import (
    ParquetInput,
    XArrayInput,
    AssignationID,
    MetricValue,
    AffineMatrix,
    FeatureValue,
    Parquet,
    File,
    ModelData,
    BigFile,
    Store,
    ModelFile,
    get_current_id,
)
from mikro.funcs import subscribe, asubscribe, aexecute, execute
from pydantic import validator, BaseModel, Field
from rath.scalars import ID
from typing import Tuple, AsyncIterator, Literal, Iterator, List, Dict, Optional
from mikro.traits import (
    Stage,
    Objective,
    ROI,
    Vectorizable,
    Position,
    Representation,
    Table,
    PhysicalSize,
    Omero,
)
from mikro.rath import MikroRath
from enum import Enum
from datetime import datetime


class CommentableModels(str, Enum):
    GRUNNLAG_USERMETA = "GRUNNLAG_USERMETA"
    GRUNNLAG_ANTIBODY = "GRUNNLAG_ANTIBODY"
    GRUNNLAG_OBJECTIVE = "GRUNNLAG_OBJECTIVE"
    GRUNNLAG_INSTRUMENT = "GRUNNLAG_INSTRUMENT"
    GRUNNLAG_DATASET = "GRUNNLAG_DATASET"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_CONTEXT = "GRUNNLAG_CONTEXT"
    GRUNNLAG_RELATION = "GRUNNLAG_RELATION"
    GRUNNLAG_DATALINK = "GRUNNLAG_DATALINK"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_MODEL = "GRUNNLAG_MODEL"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_STAGE = "GRUNNLAG_STAGE"
    GRUNNLAG_CHANNEL = "GRUNNLAG_CHANNEL"
    GRUNNLAG_POSITION = "GRUNNLAG_POSITION"
    GRUNNLAG_ERA = "GRUNNLAG_ERA"
    GRUNNLAG_TIMEPOINT = "GRUNNLAG_TIMEPOINT"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_DIMENSIONMAP = "GRUNNLAG_DIMENSIONMAP"
    GRUNNLAG_VIEW = "GRUNNLAG_VIEW"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_VIDEO = "GRUNNLAG_VIDEO"
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
    GRUNNLAG_DATASET = "GRUNNLAG_DATASET"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_CONTEXT = "GRUNNLAG_CONTEXT"
    GRUNNLAG_RELATION = "GRUNNLAG_RELATION"
    GRUNNLAG_DATALINK = "GRUNNLAG_DATALINK"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_MODEL = "GRUNNLAG_MODEL"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_STAGE = "GRUNNLAG_STAGE"
    GRUNNLAG_CHANNEL = "GRUNNLAG_CHANNEL"
    GRUNNLAG_POSITION = "GRUNNLAG_POSITION"
    GRUNNLAG_ERA = "GRUNNLAG_ERA"
    GRUNNLAG_TIMEPOINT = "GRUNNLAG_TIMEPOINT"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_DIMENSIONMAP = "GRUNNLAG_DIMENSIONMAP"
    GRUNNLAG_VIEW = "GRUNNLAG_VIEW"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_VIDEO = "GRUNNLAG_VIDEO"
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
    GRUNNLAG_DATASET = "GRUNNLAG_DATASET"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_CONTEXT = "GRUNNLAG_CONTEXT"
    GRUNNLAG_RELATION = "GRUNNLAG_RELATION"
    GRUNNLAG_DATALINK = "GRUNNLAG_DATALINK"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_MODEL = "GRUNNLAG_MODEL"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_STAGE = "GRUNNLAG_STAGE"
    GRUNNLAG_CHANNEL = "GRUNNLAG_CHANNEL"
    GRUNNLAG_POSITION = "GRUNNLAG_POSITION"
    GRUNNLAG_ERA = "GRUNNLAG_ERA"
    GRUNNLAG_TIMEPOINT = "GRUNNLAG_TIMEPOINT"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_OMERO = "GRUNNLAG_OMERO"
    GRUNNLAG_DIMENSIONMAP = "GRUNNLAG_DIMENSIONMAP"
    GRUNNLAG_VIEW = "GRUNNLAG_VIEW"
    GRUNNLAG_METRIC = "GRUNNLAG_METRIC"
    GRUNNLAG_THUMBNAIL = "GRUNNLAG_THUMBNAIL"
    GRUNNLAG_VIDEO = "GRUNNLAG_VIDEO"
    GRUNNLAG_ROI = "GRUNNLAG_ROI"
    GRUNNLAG_LABEL = "GRUNNLAG_LABEL"
    GRUNNLAG_FEATURE = "GRUNNLAG_FEATURE"
    BORD_TABLE = "BORD_TABLE"
    PLOTQL_PLOT = "PLOTQL_PLOT"


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
    DATETIME = "DATETIME"
    DATETIMEZ = "DATETIMEZ"
    DATETIMETZ = "DATETIMETZ"
    DATETIME64 = "DATETIME64"
    DATETIME64TZ = "DATETIME64TZ"
    DATETIME64NS = "DATETIME64NS"
    DATETIME64NSUTC = "DATETIME64NSUTC"
    DATETIME64NSZ = "DATETIME64NSZ"
    DATETIME64NSZUTC = "DATETIME64NSZUTC"


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


class Dimension(str, Enum):
    """The dimension of the data"""

    X = "X"
    Y = "Y"
    Z = "Z"
    T = "T"
    C = "C"


class Medium(str, Enum):
    """The medium of the imaging environment

    Important for the objective settings"""

    AIR = "AIR"
    GLYCEROL = "GLYCEROL"
    OIL = "OIL"
    OTHER = "OTHER"
    WATER = "WATER"


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


class ModelKind(str, Enum):
    """What format is the model in?"""

    ONNX = "ONNX"
    TENSORFLOW = "TENSORFLOW"
    PYTORCH = "PYTORCH"
    UNKNOWN = "UNKNOWN"


class AcquisitionKind(str, Enum):
    """What do the multiple positions in this acquistion represent?"""

    POSTION_IS_SAMPLE = "POSTION_IS_SAMPLE"
    POSITION_IS_ROI = "POSITION_IS_ROI"
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
        extra = "forbid"
        use_enum_values = True


class GroupAssignmentInput(BaseModel):
    permissions: Tuple[Optional[str], ...]
    group: ID

    class Config:
        frozen = True
        extra = "forbid"
        use_enum_values = True


class UserAssignmentInput(BaseModel):
    permissions: Tuple[Optional[str], ...]
    user: str
    "The user id"

    class Config:
        frozen = True
        extra = "forbid"
        use_enum_values = True


class OmeroRepresentationInput(BaseModel):
    """The Omero Meta Data of an Image

    Follows closely the omexml model. With a few alterations:
    - The data model of the datasets and experimenters is
    part of the mikro datamodel and are not accessed here.
    - Some parameters are ommited as they are not really used"""

    planes: Optional[Tuple[Optional["PlaneInput"], ...]]
    maps: Optional[Tuple[Optional[ID], ...]]
    timepoints: Optional[Tuple[Optional[ID], ...]]
    channels: Optional[Tuple[Optional["ChannelInput"], ...]]
    physical_size: Optional["PhysicalSizeInput"] = Field(alias="physicalSize")
    affine_transformation: Optional[AffineMatrix] = Field(alias="affineTransformation")
    scale: Optional[Tuple[Optional[float], ...]]
    positions: Optional[Tuple[Optional[ID], ...]]
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
        extra = "forbid"
        use_enum_values = True


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
        extra = "forbid"
        use_enum_values = True


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
        extra = "forbid"
        use_enum_values = True


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
        extra = "forbid"
        use_enum_values = True


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
        extra = "forbid"
        use_enum_values = True


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
        extra = "forbid"
        use_enum_values = True


class RepresentationViewInput(BaseModel):
    z_min: Optional[int] = Field(alias="zMin")
    "The x coord of the position (relative to origin)"
    z_max: Optional[int] = Field(alias="zMax")
    "The x coord of the position (relative to origin)"
    t_min: Optional[int] = Field(alias="tMin")
    "The x coord of the position (relative to origin)"
    t_max: Optional[int] = Field(alias="tMax")
    "The x coord of the position (relative to origin)"
    c_min: Optional[int] = Field(alias="cMin")
    "The x coord of the position (relative to origin)"
    c_max: Optional[int] = Field(alias="cMax")
    "The x coord of the position (relative to origin)"
    x_min: Optional[int] = Field(alias="xMin")
    "The x coord of the position (relative to origin)"
    x_max: Optional[int] = Field(alias="xMax")
    "The x coord of the position (relative to origin)"
    y_min: Optional[int] = Field(alias="yMin")
    "The x coord of the position (relative to origin)"
    y_max: Optional[int] = Field(alias="yMax")
    "The x coord of the position (relative to origin)"
    channel: Optional[ID]
    "The channel you want to associate with this map"
    position: Optional[ID]
    "The position you want to associate with this map"
    timepoint: Optional[ID]
    "The position you want to associate with this map"
    created_while: Optional[AssignationID] = Field(alias="createdWhile")
    "The assignation id"

    class Config:
        frozen = True
        extra = "forbid"
        use_enum_values = True


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
        extra = "forbid"
        use_enum_values = True


class ViewInput(BaseModel):
    omero: ID
    "The stage this position belongs to"
    z_min: Optional[int] = Field(alias="zMin")
    "The x coord of the position (relative to origin)"
    z_max: Optional[int] = Field(alias="zMax")
    "The x coord of the position (relative to origin)"
    t_min: Optional[int] = Field(alias="tMin")
    "The x coord of the position (relative to origin)"
    t_max: Optional[int] = Field(alias="tMax")
    "The x coord of the position (relative to origin)"
    c_min: Optional[int] = Field(alias="cMin")
    "The x coord of the position (relative to origin)"
    c_max: Optional[int] = Field(alias="cMax")
    "The x coord of the position (relative to origin)"
    x_min: Optional[int] = Field(alias="xMin")
    "The x coord of the position (relative to origin)"
    x_max: Optional[int] = Field(alias="xMax")
    "The x coord of the position (relative to origin)"
    y_min: Optional[int] = Field(alias="yMin")
    "The x coord of the position (relative to origin)"
    y_max: Optional[int] = Field(alias="yMax")
    "The x coord of the position (relative to origin)"
    channel: Optional[ID]
    "The channel you want to associate with this map"
    position: Optional[ID]
    "The position you want to associate with this map"
    timepoint: Optional[ID]
    "The position you want to associate with this map"
    created_while: Optional[AssignationID] = Field(alias="createdWhile")
    "The assignation id"

    class Config:
        frozen = True
        extra = "forbid"
        use_enum_values = True


class LabelFragmentRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    name: Optional[str]
    "Cleartext name"

    class Config:
        frozen = True


class LabelFragment(BaseModel):
    typename: Optional[Literal["Label"]] = Field(alias="__typename", exclude=True)
    instance: int
    "The instance value of the representation (pixel value). Must be a value of the image array"
    id: ID
    representation: Optional[LabelFragmentRepresentation]
    "The Representation this Label instance belongs to"

    class Config:
        frozen = True


class ContextFragmentLinks(BaseModel):
    """DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)"""

    typename: Optional[Literal["DataLink"]] = Field(alias="__typename", exclude=True)
    id: ID
    left_id: ID = Field(alias="leftId")
    "X"
    right_id: ID = Field(alias="rightId")
    "Y"
    left_type: Optional[LinkableModels] = Field(alias="leftType")
    "Left Type"
    right_type: Optional[LinkableModels] = Field(alias="rightType")
    "Left Type"

    class Config:
        frozen = True


class ContextFragment(BaseModel):
    typename: Optional[Literal["Context"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the context"
    links: Tuple[ContextFragmentLinks, ...]

    class Config:
        frozen = True


class ListContextFragment(BaseModel):
    typename: Optional[Literal["Context"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the context"

    class Config:
        frozen = True


class ThumbnailFragment(BaseModel):
    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename", exclude=True)
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

    typename: Optional[Literal["User"]] = Field(alias="__typename", exclude=True)
    email: str

    class Config:
        frozen = True


class TableFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class TableFragmentReporigins(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
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

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class TableFragment(Table, BaseModel):
    typename: Optional[Literal["Table"]] = Field(alias="__typename", exclude=True)
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


class ListLinkFragmentRelation(BaseModel):
    """Relation(id, created_by, created_through, created_while, name, description)"""

    typename: Optional[Literal["Relation"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the relation"

    class Config:
        frozen = True


class ListLinkFragment(BaseModel):
    typename: Optional[Literal["DataLink"]] = Field(alias="__typename", exclude=True)
    relation: ListLinkFragmentRelation
    "The relation between the two objects"
    id: ID
    left_id: ID = Field(alias="leftId")
    "X"
    right_id: ID = Field(alias="rightId")
    "Y"
    left_type: Optional[LinkableModels] = Field(alias="leftType")
    "Left Type"
    right_type: Optional[LinkableModels] = Field(alias="rightType")
    "Left Type"

    class Config:
        frozen = True


class LinkFragmentRelation(BaseModel):
    """Relation(id, created_by, created_through, created_while, name, description)"""

    typename: Optional[Literal["Relation"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the relation"

    class Config:
        frozen = True


class LinkFragment(BaseModel):
    typename: Optional[Literal["DataLink"]] = Field(alias="__typename", exclude=True)
    relation: LinkFragmentRelation
    "The relation between the two objects"
    id: ID
    left_id: ID = Field(alias="leftId")
    "X"
    right_id: ID = Field(alias="rightId")
    "Y"
    left_type: Optional[LinkableModels] = Field(alias="leftType")
    "Left Type"
    right_type: Optional[LinkableModels] = Field(alias="rightType")
    "Left Type"

    class Config:
        frozen = True


class StageFragment(Stage, BaseModel):
    typename: Optional[Literal["Stage"]] = Field(alias="__typename", exclude=True)
    id: ID
    kind: Optional[AcquisitionKind]
    "The kind of acquisition"
    name: str
    "The name of the stage"

    class Config:
        frozen = True


class ListStageFragment(Stage, BaseModel):
    typename: Optional[Literal["Stage"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the stage"
    kind: Optional[AcquisitionKind]
    "The kind of acquisition"

    class Config:
        frozen = True


class SampleFragmentRepresentations(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
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

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class SampleFragment(BaseModel):
    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
    name: str
    "The name of the sample"
    id: ID
    representations: Optional[Tuple[Optional[SampleFragmentRepresentations], ...]]
    "Associated representations of this Sample"
    experiments: Tuple[SampleFragmentExperiments, ...]
    "The experiments this sample belongs to"

    class Config:
        frozen = True


class ChannelFragmentDimensionmapsOmero(Omero, BaseModel):
    """Omero is a through model that stores the real world context of an image

    This means that it stores the position (corresponding to the relative displacement to
    a stage (Both are models)), objective and other meta data of the image.

    """

    typename: Optional[Literal["Omero"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class ChannelFragmentDimensionmaps(BaseModel):
    """DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)"""

    typename: Optional[Literal["DimensionMap"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    omero: ChannelFragmentDimensionmapsOmero

    class Config:
        frozen = True


class ChannelFragment(BaseModel):
    typename: Optional[Literal["Channel"]] = Field(alias="__typename", exclude=True)
    name: str
    "The name of the channel"
    id: ID
    dimension_maps: Optional[
        Tuple[Optional[ChannelFragmentDimensionmaps], ...]
    ] = Field(alias="dimensionMaps")
    "Associated maps of dimensions"

    class Config:
        frozen = True


class ROIFragmentVectors(BaseModel):
    typename: Optional[Literal["Vector"]] = Field(alias="__typename", exclude=True)
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

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    shape: Optional[Tuple[int, ...]]
    "The arrays shape format [c,t,z,y,x]"
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"

    class Config:
        frozen = True


class ROIFragmentDerivedrepresentations(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    store: Optional[Store]
    shape: Optional[Tuple[int, ...]]
    "The arrays shape format [c,t,z,y,x]"
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"

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

    typename: Optional[Literal["User"]] = Field(alias="__typename", exclude=True)
    email: str
    id: ID
    color: str
    "The prefered color of the user"

    class Config:
        frozen = True


class ROIFragment(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename", exclude=True)
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
    typename: Optional[Literal["Vector"]] = Field(alias="__typename", exclude=True)
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

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
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

    typename: Optional[Literal["User"]] = Field(alias="__typename", exclude=True)
    email: str
    id: ID
    color: str
    "The prefered color of the user"

    class Config:
        frozen = True


class ListROIFragment(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename", exclude=True)
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

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
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

    typename: Optional[Literal["Label"]] = Field(alias="__typename", exclude=True)
    instance: int
    "The instance value of the representation (pixel value). Must be a value of the image array"
    representation: Optional[FeatureFragmentLabelRepresentation]
    "The Representation this Label instance belongs to"

    class Config:
        frozen = True


class FeatureFragment(BaseModel):
    typename: Optional[Literal["Feature"]] = Field(alias="__typename", exclude=True)
    label: Optional[FeatureFragmentLabel]
    "The Label this Feature belongs to"
    id: ID
    key: str
    "The key of the feature"
    value: Optional[FeatureValue]
    "Value"

    class Config:
        frozen = True


class EraFragment(BaseModel):
    typename: Optional[Literal["Era"]] = Field(alias="__typename", exclude=True)
    name: str
    "The name of the era"
    id: ID
    start: Optional[datetime]
    "The start of the era"
    end: Optional[datetime]
    "The end of the era"
    timepoints: Optional[Tuple[Optional["TimepointFragment"], ...]]
    "Associated Timepoints"

    class Config:
        frozen = True


class DimensionMapFragmentChannel(BaseModel):
    """Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)"""

    typename: Optional[Literal["Channel"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class DimensionMapFragment(BaseModel):
    typename: Optional[Literal["DimensionMap"]] = Field(
        alias="__typename", exclude=True
    )
    channel: DimensionMapFragmentChannel
    id: ID
    dimension: str
    index: int
    "The index of the channel"

    class Config:
        frozen = True


class InstrumentFragment(BaseModel):
    typename: Optional[Literal["Instrument"]] = Field(alias="__typename", exclude=True)
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


class VideoFragment(BaseModel):
    typename: Optional[Literal["Video"]] = Field(alias="__typename", exclude=True)
    data: Optional[str]
    id: ID

    class Config:
        frozen = True


class TimepointFragment(BaseModel):
    typename: Optional[Literal["Timepoint"]] = Field(alias="__typename", exclude=True)
    name: Optional[str]
    "The name of the timepoint"
    id: ID
    delta_t: Optional[float] = Field(alias="deltaT")

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

    typename: Optional[Literal["User"]] = Field(alias="__typename", exclude=True)
    email: str

    class Config:
        frozen = True


class ExperimentFragment(BaseModel):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the experiment"
    creator: Optional[ExperimentFragmentCreator]
    "The user that created the experiment"

    class Config:
        frozen = True


class ListExperimentFragment(BaseModel):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the experiment"

    class Config:
        frozen = True


class RepresentationFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the sample"

    class Config:
        frozen = True


class RepresentationFragmentOmeroPhysicalsize(PhysicalSize, BaseModel):
    """Physical size of the image

    Each dimensions of the image has a physical size. This is the size of the
    pixel in the image. The physical size is given in micrometers on a PIXEL
    basis. This means that the physical size of the image is the size of the
    pixel in the image * the number of pixels in the image. For example, if
    the image is 1000x1000 pixels and the physical size of the image is 3 (x params) x 3 (y params),
    micrometer, the physical size of the image is 3000x3000 micrometer. If the image

    The t dimension is given in ms, since the time is given in ms.
    The C dimension is given in nm, since the wavelength is given in nm."""

    typename: Optional[Literal["PhysicalSize"]] = Field(
        alias="__typename", exclude=True
    )
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


class RepresentationFragmentOmeroPositionsStage(Stage, BaseModel):
    """An Stage is a set of positions that share a common space on a microscope and can
    be use to translate.


    """

    typename: Optional[Literal["Stage"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class RepresentationFragmentOmeroPositions(Position, BaseModel):
    """The relative position of a sample on a microscope stage"""

    typename: Optional[Literal["Position"]] = Field(alias="__typename", exclude=True)
    id: ID
    x: float
    "pixelSize for x in microns"
    y: float
    "pixelSize for y in microns"
    z: float
    "pixelSize for z in microns"
    stage: RepresentationFragmentOmeroPositionsStage

    class Config:
        frozen = True


class RepresentationFragmentOmeroDimensionmaps(BaseModel):
    """DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)"""

    typename: Optional[Literal["DimensionMap"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    dimension: str
    index: int
    "The index of the channel"

    class Config:
        frozen = True


class RepresentationFragmentOmeroChannels(BaseModel):
    """A channel in an image

    Channels can be highly variable in their properties. This class is a
    representation of the most common properties of a channel."""

    typename: Optional[Literal["OmeroChannel"]] = Field(
        alias="__typename", exclude=True
    )
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

    typename: Optional[Literal["Omero"]] = Field(alias="__typename", exclude=True)
    id: ID
    scale: Optional[Tuple[Optional[float], ...]]
    physical_size: Optional[RepresentationFragmentOmeroPhysicalsize] = Field(
        alias="physicalSize"
    )
    positions: Tuple[RepresentationFragmentOmeroPositions, ...]
    dimension_maps: Optional[
        Tuple[Optional[RepresentationFragmentOmeroDimensionmaps], ...]
    ] = Field(alias="dimensionMaps")
    "Associated maps of dimensions"
    affine_transformation: Optional[AffineMatrix] = Field(alias="affineTransformation")
    channels: Optional[Tuple[Optional[RepresentationFragmentOmeroChannels], ...]]

    class Config:
        frozen = True


class RepresentationFragmentOrigins(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"

    class Config:
        frozen = True


class RepresentationFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    sample: Optional[RepresentationFragmentSample]
    "The Sample this representation belosngs to"
    shape: Optional[Tuple[int, ...]]
    "The arrays shape format [c,t,z,y,x]"
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"
    created_while: Optional[str] = Field(alias="createdWhile")
    name: Optional[str]
    "Cleartext name"
    omero: Optional[RepresentationFragmentOmero]
    origins: Tuple[RepresentationFragmentOrigins, ...]

    class Config:
        frozen = True


class ListRepresentationFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    shape: Optional[Tuple[int, ...]]
    "The arrays shape format [c,t,z,y,x]"
    name: Optional[str]
    "Cleartext name"
    store: Optional[Store]

    class Config:
        frozen = True


class ModelFragmentContexts(BaseModel):
    """Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)"""

    typename: Optional[Literal["Context"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the context"

    class Config:
        frozen = True


class ModelFragment(BaseModel):
    typename: Optional[Literal["Model"]] = Field(alias="__typename", exclude=True)
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

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
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

    typename: Optional[Literal["User"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class MetricFragment(BaseModel):
    typename: Optional[Literal["Metric"]] = Field(alias="__typename", exclude=True)
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


class DatasetFragmentParent(BaseModel):
    """
    A dataset is a collection of data files and metadata files.
    It mimics the concept of a folder in a file system and is the top level
    object in the data model.

    """

    typename: Optional[Literal["Dataset"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class DatasetFragmentRepresentations(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    name: Optional[str]
    "Cleartext name"

    class Config:
        frozen = True


class DatasetFragmentOmerofiles(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the file"

    class Config:
        frozen = True


class DatasetFragment(BaseModel):
    typename: Optional[Literal["Dataset"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the experiment"
    parent: Optional[DatasetFragmentParent]
    representations: Optional[Tuple[Optional[DatasetFragmentRepresentations], ...]]
    "Associated images through Omero"
    omerofiles: Tuple[DatasetFragmentOmerofiles, ...]

    class Config:
        frozen = True


class ListDatasetFragment(BaseModel):
    typename: Optional[Literal["Dataset"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the experiment"

    class Config:
        frozen = True


class OmeroFileFragmentDatasets(BaseModel):
    """
    A dataset is a collection of data files and metadata files.
    It mimics the concept of a folder in a file system and is the top level
    object in the data model.

    """

    typename: Optional[Literal["Dataset"]] = Field(alias="__typename", exclude=True)
    id: ID

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

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    id: ID

    class Config:
        frozen = True


class OmeroFileFragment(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename", exclude=True)
    datasets: Tuple[OmeroFileFragmentDatasets, ...]
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

    typename: Optional[Literal["Omero"]] = Field(alias="__typename", exclude=True)
    representation: ListRepresentationFragment

    class Config:
        frozen = True


class PositionFragment(Position, BaseModel):
    typename: Optional[Literal["Position"]] = Field(alias="__typename", exclude=True)
    id: ID
    stage: ListStageFragment
    x: float
    "pixelSize for x in microns"
    y: float
    "pixelSize for y in microns"
    z: float
    "pixelSize for z in microns"
    omeros: Optional[Tuple[Optional[PositionFragmentOmeros], ...]]
    "Associated images through Omero"

    class Config:
        frozen = True


class ObjectiveFragment(Objective, BaseModel):
    typename: Optional[Literal["Objective"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    magnification: Optional[float]

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

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    name: str
    "The name of the experiment"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesUpdate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
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

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    name: str
    "The name of the experiment"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamplesCreate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
    name: str
    "The name of the sample"
    experiments: Tuple[Watch_samplesSubscriptionMysamplesCreateExperiments, ...]
    "The experiments this sample belongs to"

    class Config:
        frozen = True


class Watch_samplesSubscriptionMysamples(BaseModel):
    typename: Optional[Literal["SamplesEvent"]] = Field(
        alias="__typename", exclude=True
    )
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
    typename: Optional[Literal["RoiEvent"]] = Field(alias="__typename", exclude=True)
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

    typename: Optional[Literal["Label"]] = Field(alias="__typename", exclude=True)
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
        creator: Optional[ID]
        name: Optional[str]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "mutation create_label($instance: Int!, $representation: ID!, $creator: ID, $name: String, $created_while: AssignationID) {\n  createLabel(\n    instance: $instance\n    representation: $representation\n    creator: $creator\n    name: $name\n    createdWhile: $created_while\n  ) {\n    id\n    instance\n  }\n}"


class Create_contextMutation(BaseModel):
    create_context: Optional[ContextFragment] = Field(alias="createContext")
    "Create an Experiment\n    \n    This mutation creates an Experiment and returns the created Experiment.\n    "

    class Arguments(BaseModel):
        name: str
        experiment: Optional[ID]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Context on Context {\n  id\n  name\n  links {\n    id\n    leftId\n    rightId\n    leftType\n    rightType\n  }\n}\n\nmutation create_context($name: String!, $experiment: ID, $created_while: AssignationID) {\n  createContext(\n    name: $name\n    experiment: $experiment\n    createdWhile: $created_while\n  ) {\n    ...Context\n  }\n}"


class Create_thumbnailMutation(BaseModel):
    upload_thumbnail: Optional[ThumbnailFragment] = Field(alias="uploadThumbnail")

    class Arguments(BaseModel):
        rep: ID
        file: File
        major_color: Optional[str]
        blurhash: Optional[str]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nmutation create_thumbnail($rep: ID!, $file: ImageFile!, $major_color: String, $blurhash: String, $created_while: AssignationID) {\n  uploadThumbnail(\n    rep: $rep\n    file: $file\n    majorColor: $major_color\n    blurhash: $blurhash\n    createdWhile: $created_while\n  ) {\n    ...Thumbnail\n  }\n}"


class From_dfMutation(BaseModel):
    from_df: Optional[TableFragment] = Field(alias="fromDf")
    "Creates a Representation"

    class Arguments(BaseModel):
        df: ParquetInput
        name: str
        rep_origins: Optional[List[Optional[ID]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  repOrigins {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nmutation from_df($df: ParquetInput!, $name: String!, $rep_origins: [ID], $created_while: AssignationID) {\n  fromDf(\n    df: $df\n    name: $name\n    repOrigins: $rep_origins\n    createdWhile: $created_while\n  ) {\n    ...Table\n  }\n}"


class LinkMutation(BaseModel):
    link: Optional[ListLinkFragment]
    "Create an Comment \n    \n    This mutation creates a comment. It takes a commentable_id and a commentable_type.\n    If this is the first comment on the commentable, it will create a new comment thread.\n    If there is already a comment thread, it will add the comment to the thread (by setting\n    it's parent to the last parent comment in the thread).\n\n    CreateComment takes a list of Descendents, which are the comment tree. The Descendents\n    are a recursive structure, where each Descendent can have a list of Descendents as children.\n    The Descendents are either a Leaf, which is a text node, or a MentionDescendent, which is a\n    reference to another user on the platform.\n\n    Please convert your comment tree to a list of Descendents before sending it to the server.\n    TODO: Add a converter from a comment tree to a list of Descendents.\n\n    \n    (only signed in users)"

    class Arguments(BaseModel):
        relation: ID
        left_type: LinkableModels
        left_id: ID
        right_type: LinkableModels
        right_id: ID
        context: Optional[ID]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment ListLink on DataLink {\n  relation {\n    id\n    name\n  }\n  id\n  leftId\n  rightId\n  leftType\n  rightType\n}\n\nmutation link($relation: ID!, $left_type: LinkableModels!, $left_id: ID!, $right_type: LinkableModels!, $right_id: ID!, $context: ID, $created_while: AssignationID) {\n  link(\n    relation: $relation\n    leftType: $left_type\n    leftId: $left_id\n    rightType: $right_type\n    rightId: $right_id\n    context: $context\n    createdWhile: $created_while\n  ) {\n    ...ListLink\n  }\n}"


class Create_stageMutation(BaseModel):
    create_stage: Optional[StageFragment] = Field(alias="createStage")
    "Creates a Stage\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        name: str
        creator: Optional[ID]
        instrument: Optional[ID]
        tags: Optional[List[Optional[str]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Stage on Stage {\n  id\n  kind\n  name\n}\n\nmutation create_stage($name: String!, $creator: ID, $instrument: ID, $tags: [String], $created_while: AssignationID) {\n  createStage(\n    name: $name\n    creator: $creator\n    instrument: $instrument\n    tags: $tags\n    createdWhile: $created_while\n  ) {\n    ...Stage\n  }\n}"


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

    typename: Optional[Literal["User"]] = Field(alias="__typename", exclude=True)
    email: str

    class Config:
        frozen = True


class Create_sampleMutationCreatesample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
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
        name: Optional[str]
        creator: Optional[str]
        meta: Optional[Dict]
        experiments: Optional[List[Optional[ID]]]
        tags: Optional[List[Optional[str]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "mutation create_sample($name: String, $creator: String, $meta: GenericScalar, $experiments: [ID], $tags: [String], $created_while: AssignationID) {\n  createSample(\n    name: $name\n    creator: $creator\n    meta: $meta\n    experiments: $experiments\n    tags: $tags\n    createdWhile: $created_while\n  ) {\n    id\n    name\n    creator {\n      email\n    }\n  }\n}"


class CreateChannelMutation(BaseModel):
    create_channel: Optional[ChannelFragment] = Field(alias="createChannel")
    "Creates a Feature\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        name: str
        emission_wavelength: Optional[float]
        excitation_wavelength: Optional[float]
        acquisition_mode: Optional[str]
        color: Optional[str]

    class Meta:
        document = "fragment Channel on Channel {\n  name\n  id\n  dimensionMaps {\n    id\n    omero {\n      id\n    }\n  }\n}\n\nmutation CreateChannel($name: String!, $emissionWavelength: Float, $excitationWavelength: Float, $acquisitionMode: String, $color: String) {\n  createChannel(\n    name: $name\n    emissionWavelength: $emissionWavelength\n    excitationWavelength: $excitationWavelength\n    acquisitionMode: $acquisitionMode\n    color: $color\n  ) {\n    ...Channel\n  }\n}"


class Create_roiMutation(BaseModel):
    create_roi: Optional[ROIFragment] = Field(alias="createROI")
    "Creates a Sample"

    class Arguments(BaseModel):
        representation: ID
        vectors: List[Optional[InputVector]]
        creator: Optional[ID]
        type: RoiTypeInput
        label: Optional[str]
        tags: Optional[List[Optional[str]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n    shape\n    store\n    variety\n  }\n  derivedRepresentations {\n    id\n    store\n    shape\n    variety\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nmutation create_roi($representation: ID!, $vectors: [InputVector]!, $creator: ID, $type: RoiTypeInput!, $label: String, $tags: [String], $created_while: AssignationID) {\n  createROI(\n    representation: $representation\n    vectors: $vectors\n    type: $type\n    creator: $creator\n    label: $label\n    tags: $tags\n    createdWhile: $created_while\n  ) {\n    ...ROI\n  }\n}"


class Create_roisMutationCreaterois(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID

    class Config:
        frozen = True


class Create_roisMutation(BaseModel):
    create_rois: Optional[Create_roisMutationCreaterois] = Field(alias="createROIS")
    "Creates a Sample"

    class Arguments(BaseModel):
        representation: ID
        vectors_list: List[Optional[List[Optional[InputVector]]]]
        creator: Optional[ID]
        type: RoiTypeInput
        labels: Optional[List[Optional[str]]]
        tags: Optional[List[Optional[str]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "mutation create_rois($representation: ID!, $vectors_list: [[InputVector]]!, $creator: ID, $type: RoiTypeInput!, $labels: [String], $tags: [String], $created_while: AssignationID) {\n  createROIS(\n    representation: $representation\n    vectorsList: $vectors_list\n    type: $type\n    creator: $creator\n    labels: $labels\n    tags: $tags\n    createdWhile: $created_while\n  ) {\n    id\n  }\n}"


class Create_featureMutationCreatefeatureLabelRepresentation(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
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

    typename: Optional[Literal["Label"]] = Field(alias="__typename", exclude=True)
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

    typename: Optional[Literal["Feature"]] = Field(alias="__typename", exclude=True)
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
        key: Optional[str]
        value: FeatureValue
        creator: Optional[ID]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "mutation create_feature($label: ID!, $key: String, $value: FeatureValue!, $creator: ID, $created_while: AssignationID) {\n  createfeature(\n    label: $label\n    key: $key\n    value: $value\n    creator: $creator\n    createdWhile: $created_while\n  ) {\n    id\n    key\n    value\n    label {\n      id\n      representation {\n        id\n      }\n    }\n  }\n}"


class CreateEraMutation(BaseModel):
    create_era: Optional[EraFragment] = Field(alias="createEra")
    "Creates a Stage\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        name: Optional[str]
        start: Optional[datetime]
        end: Optional[datetime]

    class Meta:
        document = "fragment Timepoint on Timepoint {\n  name\n  id\n  deltaT\n}\n\nfragment Era on Era {\n  name\n  id\n  start\n  end\n  timepoints {\n    ...Timepoint\n  }\n}\n\nmutation CreateEra($name: String, $start: DateTime, $end: DateTime) {\n  createEra(name: $name, start: $start, end: $end) {\n    ...Era\n  }\n}"


class CreateDimensionMapMutation(BaseModel):
    create_dimension_map: Optional[DimensionMapFragment] = Field(
        alias="createDimensionMap"
    )
    "Creates a Feature\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        omero: ID
        dim: Dimension
        index: int
        channel: Optional[ID]

    class Meta:
        document = "fragment DimensionMap on DimensionMap {\n  channel {\n    id\n  }\n  id\n  dimension\n  index\n}\n\nmutation CreateDimensionMap($omero: ID!, $dim: Dimension!, $index: Int!, $channel: ID) {\n  createDimensionMap(omero: $omero, dim: $dim, index: $index, channel: $channel) {\n    ...DimensionMap\n  }\n}"


class Create_instrumentMutation(BaseModel):
    create_instrument: Optional[InstrumentFragment] = Field(alias="createInstrument")
    "Creates an Instrument\n    \n    This mutation creates an Instrument and returns the created Instrument.\n    The serial number is required and the manufacturer is inferred from the serial number.\n    "

    class Arguments(BaseModel):
        detectors: Optional[List[Optional[Dict]]]
        dichroics: Optional[List[Optional[Dict]]]
        filters: Optional[List[Optional[Dict]]]
        name: str
        objectives: Optional[List[Optional[ID]]]
        lot_number: Optional[str]
        serial_number: Optional[str]
        model: Optional[str]
        manufacturer: Optional[str]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Instrument on Instrument {\n  id\n  dichroics\n  detectors\n  filters\n  name\n  lotNumber\n  serialNumber\n  manufacturer\n  model\n}\n\nmutation create_instrument($detectors: [GenericScalar], $dichroics: [GenericScalar], $filters: [GenericScalar], $name: String!, $objectives: [ID], $lotNumber: String, $serialNumber: String, $model: String, $manufacturer: String, $created_while: AssignationID) {\n  createInstrument(\n    detectors: $detectors\n    dichroics: $dichroics\n    filters: $filters\n    name: $name\n    lotNumber: $lotNumber\n    objectives: $objectives\n    serialNumber: $serialNumber\n    model: $model\n    manufacturer: $manufacturer\n    createdWhile: $created_while\n  ) {\n    ...Instrument\n  }\n}"


class PresignMutationPresignFields(BaseModel):
    typename: Optional[Literal["PresignedFields"]] = Field(
        alias="__typename", exclude=True
    )
    key: str
    policy: str
    x_amz_algorithm: str = Field(alias="xAmzAlgorithm")
    x_amz_credential: str = Field(alias="xAmzCredential")
    x_amz_date: str = Field(alias="xAmzDate")
    x_amz_signature: str = Field(alias="xAmzSignature")

    class Config:
        frozen = True


class PresignMutationPresign(BaseModel):
    typename: Optional[Literal["Presigned"]] = Field(alias="__typename", exclude=True)
    bucket: str
    fields: PresignMutationPresignFields

    class Config:
        frozen = True


class PresignMutation(BaseModel):
    presign: Optional[PresignMutationPresign]
    "Presign a file for upload"

    class Arguments(BaseModel):
        file_name: str

    class Meta:
        document = "mutation presign($file_name: String!) {\n  presign(file: $file_name) {\n    bucket\n    fields {\n      key\n      policy\n      xAmzAlgorithm\n      xAmzCredential\n      xAmzDate\n      xAmzSignature\n    }\n  }\n}"


class Upload_videoMutation(BaseModel):
    upload_video: Optional[VideoFragment] = Field(alias="uploadVideo")

    class Arguments(BaseModel):
        file: BigFile
        representations: List[Optional[ID]]
        front_image: Optional[BigFile]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Video on Video {\n  data\n  id\n}\n\nmutation upload_video($file: BigFile!, $representations: [ID]!, $frontImage: BigFile, $created_while: AssignationID) {\n  uploadVideo(\n    file: $file\n    frontImage: $frontImage\n    representations: $representations\n    createdWhile: $created_while\n  ) {\n    ...Video\n  }\n}"


class CreateTimepointMutation(BaseModel):
    create_timepoint: Optional[TimepointFragment] = Field(alias="createTimepoint")
    "Creates a Timepoint\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        era: ID
        delta_t: float
        name: Optional[str]
        tolerance: Optional[float]

    class Meta:
        document = "fragment Timepoint on Timepoint {\n  name\n  id\n  deltaT\n}\n\nmutation CreateTimepoint($era: ID!, $delta_t: Float!, $name: String, $tolerance: Float) {\n  createTimepoint(era: $era, deltaT: $delta_t, name: $name, tolerance: $tolerance) {\n    ...Timepoint\n  }\n}"


class Create_experimentMutation(BaseModel):
    create_experiment: Optional[ExperimentFragment] = Field(alias="createExperiment")
    "Create an Experiment\n    \n    This mutation creates an Experiment and returns the created Experiment.\n    "

    class Arguments(BaseModel):
        name: str
        creator: Optional[str]
        description: Optional[str]
        tags: Optional[List[Optional[str]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Experiment on Experiment {\n  id\n  name\n  creator {\n    email\n  }\n}\n\nmutation create_experiment($name: String!, $creator: String, $description: String, $tags: [String], $created_while: AssignationID) {\n  createExperiment(\n    name: $name\n    creator: $creator\n    description: $description\n    tags: $tags\n    createdWhile: $created_while\n  ) {\n    ...Experiment\n  }\n}"


class From_xarrayMutation(BaseModel):
    """Creates a Representation from an xarray dataset."""

    from_x_array: Optional[RepresentationFragment] = Field(alias="fromXArray")
    "Creates a Representation"

    class Arguments(BaseModel):
        xarray: XArrayInput
        name: Optional[str]
        variety: Optional[RepresentationVarietyInput]
        origins: Optional[List[Optional[ID]]]
        file_origins: Optional[List[Optional[ID]]]
        roi_origins: Optional[List[Optional[ID]]]
        table_origins: Optional[List[Optional[ID]]]
        tags: Optional[List[Optional[str]]]
        experiments: Optional[List[Optional[ID]]]
        datasets: Optional[List[Optional[ID]]]
        sample: Optional[ID]
        omero: Optional[OmeroRepresentationInput]
        views: Optional[List[Optional[RepresentationViewInput]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  createdWhile\n  name\n  omero {\n    id\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    positions {\n      id\n      x\n      y\n      z\n      stage {\n        id\n      }\n    }\n    dimensionMaps {\n      id\n      dimension\n      index\n    }\n    affineTransformation\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nmutation from_xarray($xarray: XArrayInput!, $name: String, $variety: RepresentationVarietyInput, $origins: [ID], $file_origins: [ID], $roi_origins: [ID], $table_origins: [ID], $tags: [String], $experiments: [ID], $datasets: [ID], $sample: ID, $omero: OmeroRepresentationInput, $views: [RepresentationViewInput], $created_while: AssignationID) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n    fileOrigins: $file_origins\n    roiOrigins: $roi_origins\n    tableOrigins: $table_origins\n    experiments: $experiments\n    datasets: $datasets\n    variety: $variety\n    views: $views\n    createdWhile: $created_while\n  ) {\n    ...Representation\n  }\n}"


class Update_representationMutation(BaseModel):
    update_representation: Optional[RepresentationFragment] = Field(
        alias="updateRepresentation"
    )
    "Updates an Representation (also retriggers meta-data retrieval from data stored in)"

    class Arguments(BaseModel):
        id: ID
        tags: Optional[List[Optional[str]]]
        sample: Optional[ID]
        variety: Optional[RepresentationVarietyInput]

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  createdWhile\n  name\n  omero {\n    id\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    positions {\n      id\n      x\n      y\n      z\n      stage {\n        id\n      }\n    }\n    dimensionMaps {\n      id\n      dimension\n      index\n    }\n    affineTransformation\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nmutation update_representation($id: ID!, $tags: [String], $sample: ID, $variety: RepresentationVarietyInput) {\n  updateRepresentation(rep: $id, tags: $tags, sample: $sample, variety: $variety) {\n    ...Representation\n  }\n}"


class Create_modelMutation(BaseModel):
    create_model: Optional[ModelFragment] = Field(alias="createModel")
    "Creates an Instrument\n    \n    This mutation creates an Instrument and returns the created Instrument.\n    The serial number is required and the manufacturer is inferred from the serial number.\n    "

    class Arguments(BaseModel):
        data: ModelFile
        kind: ModelKind
        name: str
        contexts: Optional[List[Optional[ID]]]
        experiments: Optional[List[Optional[ID]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Model on Model {\n  id\n  data\n  kind\n  name\n  contexts {\n    id\n    name\n  }\n}\n\nmutation create_model($data: ModelFile!, $kind: ModelKind!, $name: String!, $contexts: [ID], $experiments: [ID], $created_while: AssignationID) {\n  createModel(\n    data: $data\n    kind: $kind\n    name: $name\n    contexts: $contexts\n    experiments: $experiments\n    createdWhile: $created_while\n  ) {\n    ...Model\n  }\n}"


class Create_metricMutation(BaseModel):
    create_metric: Optional[MetricFragment] = Field(alias="createMetric")
    "Create a metric\n\n    This mutation creates a metric and returns the created metric.\n    \n    "

    class Arguments(BaseModel):
        representation: Optional[ID]
        sample: Optional[ID]
        experiment: Optional[ID]
        key: str
        value: MetricValue
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  representation {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nmutation create_metric($representation: ID, $sample: ID, $experiment: ID, $key: String!, $value: MetricValue!, $created_while: AssignationID) {\n  createMetric(\n    representation: $representation\n    sample: $sample\n    experiment: $experiment\n    key: $key\n    value: $value\n    createdWhile: $created_while\n  ) {\n    ...Metric\n  }\n}"


class Create_datasetMutation(BaseModel):
    create_dataset: Optional[DatasetFragment] = Field(alias="createDataset")
    "Create an Experiment\n    \n    This mutation creates an Experiment and returns the created Experiment.\n    "

    class Arguments(BaseModel):
        name: str
        parent: Optional[ID]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Dataset on Dataset {\n  id\n  name\n  parent {\n    id\n  }\n  representations {\n    id\n    name\n  }\n  omerofiles {\n    id\n    name\n  }\n}\n\nmutation create_dataset($name: String!, $parent: ID, $created_while: AssignationID) {\n  createDataset(name: $name, parent: $parent, createdWhile: $created_while) {\n    ...Dataset\n  }\n}"


class Create_positionMutation(BaseModel):
    create_position: Optional[PositionFragment] = Field(alias="createPosition")
    "Creates a Feature\n    \n    This mutation creates a Feature and returns the created Feature.\n    We require a reference to the label that the feature belongs to.\n    As well as the key and value of the feature.\n    \n    There can be multiple features with the same label, but only one feature per key\n    per label"

    class Arguments(BaseModel):
        stage: ID
        x: float
        y: float
        z: float
        tolerance: Optional[float]
        name: Optional[str]
        tags: Optional[List[Optional[str]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = 'fragment ListRepresentation on Representation {\n  id\n  shape\n  name\n  store\n}\n\nfragment ListStage on Stage {\n  id\n  name\n  kind\n}\n\nfragment Position on Position {\n  id\n  stage {\n    ...ListStage\n  }\n  x\n  y\n  z\n  omeros(order: "-acquired") {\n    representation {\n      ...ListRepresentation\n    }\n  }\n}\n\nmutation create_position($stage: ID!, $x: Float!, $y: Float!, $z: Float!, $tolerance: Float, $name: String, $tags: [String], $created_while: AssignationID) {\n  createPosition(\n    stage: $stage\n    x: $x\n    y: $y\n    z: $z\n    tags: $tags\n    name: $name\n    tolerance: $tolerance\n    createdWhile: $created_while\n  ) {\n    ...Position\n  }\n}'


class Create_objectiveMutation(BaseModel):
    create_objective: Optional[ObjectiveFragment] = Field(alias="createObjective")
    "Creates an Instrument\n    \n    This mutation creates an Instrument and returns the created Instrument.\n    The serial number is required and the manufacturer is inferred from the serial number.\n    "

    class Arguments(BaseModel):
        serial_number: str
        name: str
        magnification: float
        na: Optional[float]
        immersion: Optional[str]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "fragment Objective on Objective {\n  id\n  name\n  magnification\n}\n\nmutation create_objective($serial_number: String!, $name: String!, $magnification: Float!, $na: Float, $immersion: String, $created_while: AssignationID) {\n  createObjective(\n    name: $name\n    serialNumber: $serial_number\n    magnification: $magnification\n    na: $na\n    immersion: $immersion\n    createdWhile: $created_while\n  ) {\n    ...Objective\n  }\n}"


class Upload_bioimageMutationUploadomerofile(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename", exclude=True)
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
        name: Optional[str]

    class Meta:
        document = "mutation upload_bioimage($file: ImageFile!, $name: String) {\n  uploadOmeroFile(file: $file, name: $name) {\n    id\n    file\n    type\n    name\n  }\n}"


class Upload_bigfileMutationUploadbigfile(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename", exclude=True)
    id: ID
    file: Optional[File]
    "The file"
    type: OmeroFileType
    "The type of the file"
    name: str
    "The name of the file"

    class Config:
        frozen = True


class Upload_bigfileMutation(BaseModel):
    upload_big_file: Optional[Upload_bigfileMutationUploadbigfile] = Field(
        alias="uploadBigFile"
    )
    "Upload a file to Mikro\n\n    This mutation uploads a file to Omero and returns the created OmeroFile.\n    "

    class Arguments(BaseModel):
        file: BigFile
        datasets: Optional[List[Optional[ID]]]
        created_while: Optional[AssignationID]

        @validator("created_while", pre=True, always=True)
        def created_while_validator(cls, value):
            return get_current_id(cls, value)

    class Meta:
        document = "mutation upload_bigfile($file: BigFile!, $datasets: [ID], $created_while: AssignationID) {\n  uploadBigFile(file: $file, datasets: $datasets, createdWhile: $created_while) {\n    id\n    file\n    type\n    name\n  }\n}"


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

    typename: Optional[Literal["Feature"]] = Field(alias="__typename", exclude=True)
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

    typename: Optional[Literal["Label"]] = Field(alias="__typename", exclude=True)
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

    typename: Optional[Literal["Label"]] = Field(alias="__typename", exclude=True)
    label: Optional[str]
    "The name of the instance"
    value: ID

    class Config:
        frozen = True


class Search_labelsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_labelsQueryOptions], ...]]
    "All Labels\n    \n    This query returns all Labels that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Labels that the user has access to. If the user is an amdin\n    or superuser, all Labels will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_labels($search: String, $values: [ID]) {\n  options: labels(name: $search, limit: 20, ids: $values) {\n    label: name\n    value: id\n  }\n}"


class Get_contextQuery(BaseModel):
    context: Optional[ContextFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Context on Context {\n  id\n  name\n  links {\n    id\n    leftId\n    rightId\n    leftType\n    rightType\n  }\n}\n\nquery get_context($id: ID!) {\n  context(id: $id) {\n    ...Context\n  }\n}"


class Get_mycontextsQuery(BaseModel):
    mycontexts: Optional[Tuple[Optional[ListContextFragment], ...]]
    "My Experiments runs a fast query on the database to return all\n    Experiments that the user has created. This query is faster than\n    the `experiments` query, but it does not return all Experiments that\n    the user has access to."

    class Arguments(BaseModel):
        limit: Optional[int]
        offset: Optional[int]

    class Meta:
        document = "fragment ListContext on Context {\n  id\n  name\n}\n\nquery get_mycontexts($limit: Int, $offset: Int) {\n  mycontexts(limit: $limit, offset: $offset) {\n    ...ListContext\n  }\n}"


class Expand_contextQuery(BaseModel):
    context: Optional[ContextFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Context on Context {\n  id\n  name\n  links {\n    id\n    leftId\n    rightId\n    leftType\n    rightType\n  }\n}\n\nquery expand_context($id: ID!) {\n  context(id: $id) {\n    ...Context\n  }\n}"


class Search_contextsQueryOptions(BaseModel):
    """Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)"""

    typename: Optional[Literal["Context"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the context"

    class Config:
        frozen = True


class Search_contextsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_contextsQueryOptions], ...]]
    "My Experiments runs a fast query on the database to return all\n    Experiments that the user has created. This query is faster than\n    the `experiments` query, but it does not return all Experiments that\n    the user has access to."

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_contexts($search: String, $values: [ID]) {\n  options: mycontexts(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


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

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: Optional[str]

    class Config:
        frozen = True


class Search_thumbnailsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_thumbnailsQueryOptions], ...]]
    "All Thumbnails\n    \n    This query returns all Thumbnails that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Thumbnails that the user has access to. If the user is an amdin\n    or superuser, all Thumbnails will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_thumbnails($search: String, $values: [ID]) {\n  options: thumbnails(name: $search, limit: 20, ids: $values) {\n    value: id\n    label: image\n  }\n}"


class Image_for_thumbnailQueryImage(BaseModel):
    """A Thumbnail is a render of a representation that is used to display the representation in the UI.

    Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.
    """

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename", exclude=True)
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

    typename: Optional[Literal["Table"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str

    class Config:
        frozen = True


class Search_tablesQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_tablesQueryOptions], ...]]
    "My samples return all of the users samples attached to the current user"

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_tables($search: String, $values: [ID]) {\n  options: tables(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class LinksQueryLinksRelation(BaseModel):
    """Relation(id, created_by, created_through, created_while, name, description)"""

    typename: Optional[Literal["Relation"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the relation"

    class Config:
        frozen = True


class LinksQueryLinksRepresentationInlineFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    store: Optional[Store]

    class Config:
        frozen = True


class LinksQueryLinksRepresentationInlineFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    store: Optional[Store]

    class Config:
        frozen = True


class LinksQueryLinks(BaseModel):
    """DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)"""

    typename: Optional[Literal["DataLink"]] = Field(alias="__typename", exclude=True)
    relation: LinksQueryLinksRelation
    "The relation between the two objects"
    left: LinksQueryLinksRepresentationInlineFragment
    "X"
    right: LinksQueryLinksRepresentationInlineFragment
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
        context: Optional[ID]
        limit: Optional[int] = Field(default="10")

    class Meta:
        document = "query Links($x_type: LinkableModels!, $y_type: LinkableModels!, $relation: String!, $context: ID, $limit: Int = 10) {\n  links(\n    xType: $x_type\n    yType: $y_type\n    relation: $relation\n    context: $context\n    limit: $limit\n  ) {\n    relation {\n      id\n      name\n    }\n    left {\n      ... on Representation {\n        id\n        store\n      }\n    }\n    right {\n      ... on Representation {\n        id\n        store\n      }\n    }\n  }\n}"


class Get_image_image_linksQueryLinksRelation(BaseModel):
    """Relation(id, created_by, created_through, created_while, name, description)"""

    typename: Optional[Literal["Relation"]] = Field(alias="__typename", exclude=True)
    id: ID
    name: str
    "The name of the relation"

    class Config:
        frozen = True


class Get_image_image_linksQueryLinksRepresentationInlineFragment(
    Representation, BaseModel
):
    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"

    class Config:
        frozen = True


class Get_image_image_linksQueryLinksRepresentationInlineFragment(
    Representation, BaseModel
):
    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"

    class Config:
        frozen = True


class Get_image_image_linksQueryLinks(BaseModel):
    """DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)"""

    typename: Optional[Literal["DataLink"]] = Field(alias="__typename", exclude=True)
    relation: Get_image_image_linksQueryLinksRelation
    "The relation between the two objects"
    left: Get_image_image_linksQueryLinksRepresentationInlineFragment
    "X"
    right: Get_image_image_linksQueryLinksRepresentationInlineFragment
    "Y"

    class Config:
        frozen = True


class Get_image_image_linksQuery(BaseModel):
    links: Optional[Tuple[Optional[Get_image_image_linksQueryLinks], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        relation: str
        context: Optional[ID]
        limit: Optional[int] = Field(default="10")

    class Meta:
        document = "query get_image_image_links($relation: String!, $context: ID, $limit: Int = 10) {\n  links(\n    xType: GRUNNLAG_REPRESENTATION\n    yType: GRUNNLAG_REPRESENTATION\n    relation: $relation\n    context: $context\n    limit: $limit\n  ) {\n    relation {\n      id\n      name\n    }\n    left {\n      ... on Representation {\n        id\n        store\n        variety\n      }\n    }\n    right {\n      ... on Representation {\n        id\n        store\n        variety\n      }\n    }\n  }\n}"


class Get_linkQuery(BaseModel):
    link: Optional[LinkFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Link on DataLink {\n  relation {\n    id\n    name\n  }\n  id\n  leftId\n  rightId\n  leftType\n  rightType\n}\n\nquery get_link($id: ID!) {\n  link(id: $id) {\n    ...Link\n  }\n}"


class Expand_linkQuery(BaseModel):
    link: Optional[LinkFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Link on DataLink {\n  relation {\n    id\n    name\n  }\n  id\n  leftId\n  rightId\n  leftType\n  rightType\n}\n\nquery expand_link($id: ID!) {\n  link(id: $id) {\n    ...Link\n  }\n}"


class Search_linksQueryOptions(BaseModel):
    """DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)"""

    typename: Optional[Literal["DataLink"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: ID

    class Config:
        frozen = True


class Search_linksQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_linksQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_links($search: String, $values: [ID]) {\n  options: links(relation: $search, limit: 30, ids: $values) {\n    value: id\n    label: id\n  }\n}"


class Get_stageQuery(BaseModel):
    stage: Optional[StageFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Stage on Stage {\n  id\n  kind\n  name\n}\n\nquery get_stage($id: ID!) {\n  stage(id: $id) {\n    ...Stage\n  }\n}"


class Expand_stageQuery(BaseModel):
    stage: Optional[StageFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Stage on Stage {\n  id\n  kind\n  name\n}\n\nquery expand_stage($id: ID!) {\n  stage(id: $id) {\n    ...Stage\n  }\n}"


class Search_stagesQueryOptions(Stage, BaseModel):
    """An Stage is a set of positions that share a common space on a microscope and can
    be use to translate.


    """

    typename: Optional[Literal["Stage"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the stage"

    class Config:
        frozen = True


class Search_stagesQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_stagesQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_stages($search: String, $values: [ID]) {\n  options: stages(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class Get_display_stageQueryStagePositionsOmerosPhysicalsize(PhysicalSize, BaseModel):
    """Physical size of the image

    Each dimensions of the image has a physical size. This is the size of the
    pixel in the image. The physical size is given in micrometers on a PIXEL
    basis. This means that the physical size of the image is the size of the
    pixel in the image * the number of pixels in the image. For example, if
    the image is 1000x1000 pixels and the physical size of the image is 3 (x params) x 3 (y params),
    micrometer, the physical size of the image is 3000x3000 micrometer. If the image

    The t dimension is given in ms, since the time is given in ms.
    The C dimension is given in nm, since the wavelength is given in nm."""

    typename: Optional[Literal["PhysicalSize"]] = Field(
        alias="__typename", exclude=True
    )
    x: Optional[float]
    "Physical size of *one* Pixel in the x dimension (in µm)"
    y: Optional[float]
    "Physical size of *one* Pixel in the t dimension (in µm)"
    z: Optional[float]
    "Physical size of *one* Pixel in the z dimension (in µm)"
    t: Optional[float]
    "Physical size of *one* Pixel in the t dimension (in ms)"

    class Config:
        frozen = True


class Get_display_stageQueryStagePositionsOmerosRepresentation(
    Representation, BaseModel
):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    store: Optional[Store]
    id: ID

    class Config:
        frozen = True


class Get_display_stageQueryStagePositionsOmeros(Omero, BaseModel):
    """Omero is a through model that stores the real world context of an image

    This means that it stores the position (corresponding to the relative displacement to
    a stage (Both are models)), objective and other meta data of the image.

    """

    typename: Optional[Literal["Omero"]] = Field(alias="__typename", exclude=True)
    physical_size: Optional[
        Get_display_stageQueryStagePositionsOmerosPhysicalsize
    ] = Field(alias="physicalSize")
    representation: Get_display_stageQueryStagePositionsOmerosRepresentation

    class Config:
        frozen = True


class Get_display_stageQueryStagePositions(Position, BaseModel):
    """The relative position of a sample on a microscope stage"""

    typename: Optional[Literal["Position"]] = Field(alias="__typename", exclude=True)
    x: float
    "pixelSize for x in microns"
    y: float
    "pixelSize for y in microns"
    z: float
    "pixelSize for z in microns"
    omeros: Optional[Tuple[Optional[Get_display_stageQueryStagePositionsOmeros], ...]]
    "Associated images through Omero"

    class Config:
        frozen = True


class Get_display_stageQueryStage(Stage, BaseModel):
    """An Stage is a set of positions that share a common space on a microscope and can
    be use to translate.


    """

    typename: Optional[Literal["Stage"]] = Field(alias="__typename", exclude=True)
    id: ID
    positions: Tuple[Get_display_stageQueryStagePositions, ...]

    class Config:
        frozen = True


class Get_display_stageQuery(BaseModel):
    stage: Optional[Get_display_stageQueryStage]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "query get_display_stage($id: ID!) {\n  stage(id: $id) {\n    id\n    positions {\n      x\n      y\n      z\n      omeros {\n        physicalSize {\n          x\n          y\n          z\n          t\n        }\n        representation {\n          store\n          id\n        }\n      }\n    }\n  }\n}"


class Get_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a Sample by ID\n    \n    Returns a single Sample by ID. If the user does not have access\n    to the Sample, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  experiments {\n    id\n  }\n}\n\nquery get_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class Search_sampleQueryOptions(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the sample"

    class Config:
        frozen = True


class Search_sampleQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_sampleQueryOptions], ...]]
    "All Samples\n    \n    This query returns all Samples that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Samples that the user has access to. If the user is an amdin\n    or superuser, all Samples will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_sample($search: String, $values: [ID]) {\n  options: samples(name: $search, limit: 20, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class Expand_sampleQuery(BaseModel):
    sample: Optional[SampleFragment]
    "Get a Sample by ID\n    \n    Returns a single Sample by ID. If the user does not have access\n    to the Sample, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Sample on Sample {\n  name\n  id\n  representations {\n    id\n  }\n  experiments {\n    id\n  }\n}\n\nquery expand_sample($id: ID!) {\n  sample(id: $id) {\n    ...Sample\n  }\n}"


class GetChannelQuery(BaseModel):
    channel: Optional[ChannelFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Channel on Channel {\n  name\n  id\n  dimensionMaps {\n    id\n    omero {\n      id\n    }\n  }\n}\n\nquery GetChannel($id: ID!) {\n  channel(id: $id) {\n    ...Channel\n  }\n}"


class SearchChannelsQueryOptions(BaseModel):
    """Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)"""

    typename: Optional[Literal["Channel"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the channel"

    class Config:
        frozen = True


class SearchChannelsQuery(BaseModel):
    options: Optional[Tuple[Optional[SearchChannelsQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query SearchChannels($search: String, $values: [ID]) {\n  options: channels(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class Get_roisQuery(BaseModel):
    rois: Optional[Tuple[Optional[ListROIFragment], ...]]
    "All Rois\n    \n    This query returns all Rois that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Rois that the user has access to. If the user is an amdin\n    or superuser, all Rois will be returned."

    class Arguments(BaseModel):
        representation: ID
        type: Optional[List[Optional[RoiTypeInput]]]

    class Meta:
        document = "fragment ListROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nquery get_rois($representation: ID!, $type: [RoiTypeInput]) {\n  rois(representation: $representation, type: $type) {\n    ...ListROI\n  }\n}"


class Expand_roiQuery(BaseModel):
    roi: Optional[ROIFragment]
    'Get a single Roi by ID"\n    \n    Returns a single Roi by ID. If the user does not have access\n    to the Roi, an error will be raised.'

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n    shape\n    store\n    variety\n  }\n  derivedRepresentations {\n    id\n    store\n    shape\n    variety\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nquery expand_roi($id: ID!) {\n  roi(id: $id) {\n    ...ROI\n  }\n}"


class Get_roiQuery(BaseModel):
    roi: Optional[ROIFragment]
    'Get a single Roi by ID"\n    \n    Returns a single Roi by ID. If the user does not have access\n    to the Roi, an error will be raised.'

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n    shape\n    store\n    variety\n  }\n  derivedRepresentations {\n    id\n    store\n    shape\n    variety\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nquery get_roi($id: ID!) {\n  roi(id: $id) {\n    ...ROI\n  }\n}"


class Search_roisQueryOptions(ROI, BaseModel):
    """A ROI is a region of interest in a representation.

    This region is to be regarded as a view on the representation. Depending
    on the implementatoin (type) of the ROI, the view can be constructed
    differently. For example, a rectangular ROI can be constructed by cropping
    the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
    representation with the polygon.

    The ROI can also store a name and a description. This is used to display the ROI in the UI.

    """

    typename: Optional[Literal["ROI"]] = Field(alias="__typename", exclude=True)
    label: ID
    value: ID

    class Config:
        frozen = True


class Search_roisQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_roisQueryOptions], ...]]
    "All Rois\n    \n    This query returns all Rois that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Rois that the user has access to. If the user is an amdin\n    or superuser, all Rois will be returned."

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_rois($search: String, $values: [ID]) {\n  options: rois(repname: $search, ids: $values) {\n    label: id\n    value: id\n  }\n}"


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

    typename: Optional[Literal["Feature"]] = Field(alias="__typename", exclude=True)
    label: str
    "The key of the feature"
    value: ID

    class Config:
        frozen = True


class Search_featuresQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_featuresQueryOptions], ...]]
    "All features\n    \n    This query returns all features that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all features that the user has access to. If the user is an amdin\n    or superuser, all features will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_features($search: String, $values: [ID]) {\n  options: features(substring: $search, limit: 20, ids: $values) {\n    label: key\n    value: id\n  }\n}"


class GetEraQuery(BaseModel):
    era: Optional[EraFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Timepoint on Timepoint {\n  name\n  id\n  deltaT\n}\n\nfragment Era on Era {\n  name\n  id\n  start\n  end\n  timepoints {\n    ...Timepoint\n  }\n}\n\nquery GetEra($id: ID!) {\n  era(id: $id) {\n    ...Era\n  }\n}"


class SearchErasQueryOptions(BaseModel):
    """Era(id, created_by, created_through, created_while, name, start, end, created_at)"""

    typename: Optional[Literal["Era"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the era"

    class Config:
        frozen = True


class SearchErasQuery(BaseModel):
    options: Optional[Tuple[Optional[SearchErasQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query SearchEras($search: String, $values: [ID]) {\n  options: eras(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class GetDimensionMapQuery(BaseModel):
    dimensionmap: Optional[DimensionMapFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment DimensionMap on DimensionMap {\n  channel {\n    id\n  }\n  id\n  dimension\n  index\n}\n\nquery GetDimensionMap($id: ID!) {\n  dimensionmap(id: $id) {\n    ...DimensionMap\n  }\n}"


class SearchDimensionMapsQueryOptions(BaseModel):
    """DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)"""

    typename: Optional[Literal["DimensionMap"]] = Field(
        alias="__typename", exclude=True
    )
    value: ID
    label: str

    class Config:
        frozen = True


class SearchDimensionMapsQuery(BaseModel):
    options: Optional[Tuple[Optional[SearchDimensionMapsQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query SearchDimensionMaps($search: String, $values: [ID]) {\n  options: dimensionmaps(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: dimension\n  }\n}"


class RequestQueryRequest(BaseModel):
    typename: Optional[Literal["Credentials"]] = Field(alias="__typename", exclude=True)
    access_key: str = Field(alias="accessKey")
    status: str
    secret_key: str = Field(alias="secretKey")
    session_token: str = Field(alias="sessionToken")

    class Config:
        frozen = True


class RequestQuery(BaseModel):
    request: Optional[RequestQueryRequest]
    "Requets a new set of credentials from the S3 server\n    encompassing the users credentials and the access key and secret key"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "query Request {\n  request {\n    accessKey\n    status\n    secretKey\n    sessionToken\n  }\n}"


class Get_instrumentQuery(BaseModel):
    instrument: Optional[InstrumentFragment]
    "Get a single instrumes by ID\n    \n    Returns a single instrument by ID. If the user does not have access\n    to the instrument, an error will be raised."

    class Arguments(BaseModel):
        id: Optional[ID]
        name: Optional[str]

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
    """Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)"""

    typename: Optional[Literal["Instrument"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str

    class Config:
        frozen = True


class Search_instrumentsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_instrumentsQueryOptions], ...]]
    "All Instruments\n    \n    This query returns all Instruments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Instruments that the user has access to. If the user is an amdin\n    or superuser, all Instruments will be returned."

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_instruments($search: String, $values: [ID]) {\n  options: instruments(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class Get_videoQuery(BaseModel):
    video: Optional[VideoFragment]
    "Get a single Thumbnail by ID\n    \n    Get a single Thumbnail by ID. If the user does not have access\n    to the Thumbnail, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Video on Video {\n  data\n  id\n}\n\nquery get_video($id: ID!) {\n  video(id: $id) {\n    ...Video\n  }\n}"


class Search_videosQueryOptions(BaseModel):
    typename: Optional[Literal["Video"]] = Field(alias="__typename", exclude=True)
    label: ID
    value: ID

    class Config:
        frozen = True


class Search_videosQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_videosQueryOptions], ...]]
    "All Thumbnails\n    \n    This query returns all Thumbnails that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Thumbnails that the user has access to. If the user is an amdin\n    or superuser, all Thumbnails will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_videos($search: String, $values: [ID]) {\n  options: videos(name: $search, ids: $values) {\n    label: id\n    value: id\n  }\n}"


class GetTimepointQuery(BaseModel):
    timepoint: Optional[TimepointFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Timepoint on Timepoint {\n  name\n  id\n  deltaT\n}\n\nquery GetTimepoint($id: ID!) {\n  timepoint(id: $id) {\n    ...Timepoint\n  }\n}"


class SearchTimepointsQueryOptions(BaseModel):
    """The relative position of a sample on a microscope stage"""

    typename: Optional[Literal["Timepoint"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: Optional[str]
    "The name of the timepoint"

    class Config:
        frozen = True


class SearchTimepointsQuery(BaseModel):
    options: Optional[Tuple[Optional[SearchTimepointsQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query SearchTimepoints($search: String, $values: [ID]) {\n  options: timepoints(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


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


class Eget_experimentsQuery(BaseModel):
    experiments: Optional[Tuple[Optional[ListExperimentFragment], ...]]
    "All Experiments \n ![Image](/static/img/data.png) \n This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned. \n If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query. \n \n    \n    "

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment ListExperiment on Experiment {\n  id\n  name\n}\n\nquery eget_experiments {\n  experiments {\n    ...ListExperiment\n  }\n}"


class Search_experimentQueryOptions(BaseModel):
    """
    An experiment is a collection of samples and their representations.
    It mimics the concept of an experiment in the lab and is the top level
    object in the data model.

    You can use the experiment to group samples and representations likewise
    to how you would group files into folders in a file system.
    """

    typename: Optional[Literal["Experiment"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the experiment"

    class Config:
        frozen = True


class Search_experimentQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_experimentQueryOptions], ...]]
    "All Experiments \n ![Image](/static/img/data.png) \n This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned. \n If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query. \n \n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_experiment($search: String, $values: [ID]) {\n  options: experiments(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class Expand_representationQuery(BaseModel):
    """Creates a new representation"""

    representation: Optional[RepresentationFragment]
    "Get a single Representation by ID\n    \n    Returns a single Representation by ID. If the user does not have access\n    to the Representation, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  createdWhile\n  name\n  omero {\n    id\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    positions {\n      id\n      x\n      y\n      z\n      stage {\n        id\n      }\n    }\n    dimensionMaps {\n      id\n      dimension\n      index\n    }\n    affineTransformation\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Get_representationQuery(BaseModel):
    representation: Optional[RepresentationFragment]
    "Get a single Representation by ID\n    \n    Returns a single Representation by ID. If the user does not have access\n    to the Representation, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  createdWhile\n  name\n  omero {\n    id\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    positions {\n      id\n      x\n      y\n      z\n      stage {\n        id\n      }\n    }\n    dimensionMaps {\n      id\n      dimension\n      index\n    }\n    affineTransformation\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery get_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Search_representationQueryOptions(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    value: ID
    label: Optional[str]
    "Cleartext name"

    class Config:
        frozen = True


class Search_representationQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_representationQueryOptions], ...]]
    "All Representations\n    \n    This query returns all Representations that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Representations that the user has access to. If the user is an amdin\n    or superuser, all Representations will be returned."

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_representation($search: String, $values: [ID]) {\n  options: representations(name: $search, limit: 20, ids: $values) {\n    value: id\n    label: name\n  }\n}"


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
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  createdWhile\n  name\n  omero {\n    id\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    positions {\n      id\n      x\n      y\n      z\n      stage {\n        id\n      }\n    }\n    dimensionMaps {\n      id\n      dimension\n      index\n    }\n    affineTransformation\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"


class My_accessiblesQuery(BaseModel):
    accessiblerepresentations: Optional[Tuple[Optional[RepresentationFragment], ...]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  shape\n  id\n  store\n  variety\n  createdWhile\n  name\n  omero {\n    id\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n    positions {\n      id\n      x\n      y\n      z\n      stage {\n        id\n      }\n    }\n    dimensionMaps {\n      id\n      dimension\n      index\n    }\n    affineTransformation\n    channels {\n      name\n      color\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery my_accessibles {\n  accessiblerepresentations {\n    ...Representation\n  }\n}"


class Search_tagsQueryOptions(BaseModel):
    typename: Optional[Literal["Tag"]] = Field(alias="__typename", exclude=True)
    value: str
    label: str

    class Config:
        frozen = True


class Search_tagsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_tagsQueryOptions], ...]]
    "All Tags\n    \n    Returns all Tags that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Tags that the user has access to. If the user is an amdin\n    or superuser, all Tags will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_tags($search: String, $values: [ID]) {\n  options: tags(name: $search, ids: $values) {\n    value: slug\n    label: name\n  }\n}"


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

    typename: Optional[Literal["Model"]] = Field(alias="__typename", exclude=True)
    label: str
    "The name of the model"
    value: ID

    class Config:
        frozen = True


class Search_modelsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_modelsQueryOptions], ...]]
    "All Labels\n    \n    This query returns all Labels that are stored on the platform\n    depending on the user's permissions.s Generally, this query will return\n    all Labels that the user has access to. If the user is an amdin\n    or superuser, all Labels wsill be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_models($search: String, $values: [ID]) {\n  options: models(name: $search, limit: 20, ids: $values) {\n    label: name\n    value: id\n  }\n}"


class Expand_metricQuery(BaseModel):
    """Creates a new representation"""

    metric: Optional[MetricFragment]
    "Get a single Metric by ID\n    \n    Returns a single Metric by ID. If the user does not have access\n    to the Metric, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  representation {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nquery expand_metric($id: ID!) {\n  metric(id: $id) {\n    ...Metric\n  }\n}"


class Get_datasetQuery(BaseModel):
    dataset: Optional[DatasetFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Dataset on Dataset {\n  id\n  name\n  parent {\n    id\n  }\n  representations {\n    id\n    name\n  }\n  omerofiles {\n    id\n    name\n  }\n}\n\nquery get_dataset($id: ID!) {\n  dataset(id: $id) {\n    ...Dataset\n  }\n}"


class Expand_datasetQuery(BaseModel):
    dataset: Optional[DatasetFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Dataset on Dataset {\n  id\n  name\n  parent {\n    id\n  }\n  representations {\n    id\n    name\n  }\n  omerofiles {\n    id\n    name\n  }\n}\n\nquery expand_dataset($id: ID!) {\n  dataset(id: $id) {\n    ...Dataset\n  }\n}"


class Get_datasetsQuery(BaseModel):
    datasets: Optional[Tuple[Optional[ListDatasetFragment], ...]]
    "All Experiments \n ![Image](/static/img/data.png) \n This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned. \n If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query. \n \n    \n    "

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment ListDataset on Dataset {\n  id\n  name\n}\n\nquery get_datasets {\n  datasets {\n    ...ListDataset\n  }\n}"


class Search_datasetsQueryOptions(BaseModel):
    """
    A dataset is a collection of data files and metadata files.
    It mimics the concept of a folder in a file system and is the top level
    object in the data model.

    """

    typename: Optional[Literal["Dataset"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the experiment"

    class Config:
        frozen = True


class Search_datasetsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_datasetsQueryOptions], ...]]
    "All Experiments \n ![Image](/static/img/data.png) \n This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned. \n If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query. \n \n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_datasets($search: String, $values: [ID]) {\n  options: datasets(name: $search, limit: 30, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class ThiernoQueryRepresentationsSamplePinnedby(BaseModel):
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

    typename: Optional[Literal["User"]] = Field(alias="__typename", exclude=True)
    name: str
    "The name of the user"

    class Config:
        frozen = True


class ThiernoQueryRepresentationsSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename", exclude=True)
    id: ID
    pinned_by: Tuple[ThiernoQueryRepresentationsSamplePinnedby, ...] = Field(
        alias="pinnedBy"
    )
    "The users that have pinned the sample"

    class Config:
        frozen = True


class ThiernoQueryRepresentations(Representation, BaseModel):
    """A Representation is 5-dimensional representation of an image

    Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

    typename: Optional[Literal["Representation"]] = Field(
        alias="__typename", exclude=True
    )
    created_at: datetime = Field(alias="createdAt")
    store: Optional[Store]
    sample: Optional[ThiernoQueryRepresentationsSample]
    "The Sample this representation belosngs to"

    class Config:
        frozen = True


class ThiernoQuery(BaseModel):
    representations: Optional[Tuple[Optional[ThiernoQueryRepresentations], ...]]
    "All Representations\n    \n    This query returns all Representations that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Representations that the user has access to. If the user is an amdin\n    or superuser, all Representations will be returned."

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "query Thierno {\n  representations(limit: 10) {\n    createdAt\n    store\n    sample {\n      id\n      pinnedBy {\n        name\n      }\n    }\n  }\n}"


class Get_positionQuery(BaseModel):
    position: Optional[PositionFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = 'fragment ListRepresentation on Representation {\n  id\n  shape\n  name\n  store\n}\n\nfragment ListStage on Stage {\n  id\n  name\n  kind\n}\n\nfragment Position on Position {\n  id\n  stage {\n    ...ListStage\n  }\n  x\n  y\n  z\n  omeros(order: "-acquired") {\n    representation {\n      ...ListRepresentation\n    }\n  }\n}\n\nquery get_position($id: ID!) {\n  position(id: $id) {\n    ...Position\n  }\n}'


class Expand_positionQuery(BaseModel):
    position: Optional[PositionFragment]
    'Get a single experiment by ID"\n    \n    Returns a single experiment by ID. If the user does not have access\n    to the experiment, an error will be raised.\n    \n    '

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = 'fragment ListRepresentation on Representation {\n  id\n  shape\n  name\n  store\n}\n\nfragment ListStage on Stage {\n  id\n  name\n  kind\n}\n\nfragment Position on Position {\n  id\n  stage {\n    ...ListStage\n  }\n  x\n  y\n  z\n  omeros(order: "-acquired") {\n    representation {\n      ...ListRepresentation\n    }\n  }\n}\n\nquery expand_position($id: ID!) {\n  position(id: $id) {\n    ...Position\n  }\n}'


class Search_positionsQueryOptions(Position, BaseModel):
    """The relative position of a sample on a microscope stage"""

    typename: Optional[Literal["Position"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the possition"

    class Config:
        frozen = True


class Search_positionsQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_positionsQueryOptions], ...]]
    "All Experiments\n    \n    This query returns all Experiments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Experiments that the user has access to. If the user is an amdin\n    or superuser, all Experiments will be returned.\n\n    If you want to retrieve only the Experiments that you have created,\n    use the `myExperiments` query.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]
        stage: Optional[ID]

    class Meta:
        document = "query search_positions($search: String, $values: [ID], $stage: ID) {\n  options: positions(name: $search, limit: 30, stage: $stage, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class Get_objectiveQuery(BaseModel):
    objective: Optional[ObjectiveFragment]
    "Get a single instrumes by ID\n    \n    Returns a single instrument by ID. If the user does not have access\n    to the instrument, an error will be raised."

    class Arguments(BaseModel):
        id: Optional[ID]
        name: Optional[str]

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
    """Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)"""

    typename: Optional[Literal["Objective"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str

    class Config:
        frozen = True


class Search_objectivesQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_objectivesQueryOptions], ...]]
    "All Instruments\n    \n    This query returns all Instruments that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Instruments that the user has access to. If the user is an amdin\n    or superuser, all Instruments will be returned."

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_objectives($search: String, $values: [ID]) {\n  options: objectives(search: $search, ids: $values) {\n    value: id\n    label: name\n  }\n}"


class Get_omero_fileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single Omero File by ID\n    \n    Returns a single Omero File by ID. If the user does not have access\n    to the Omero File, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  datasets {\n    id\n  }\n  id\n  name\n  file\n  type\n  experiments {\n    id\n  }\n}\n\nquery get_omero_file($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Expand_omerofileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single Omero File by ID\n    \n    Returns a single Omero File by ID. If the user does not have access\n    to the Omero File, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  datasets {\n    id\n  }\n  id\n  name\n  file\n  type\n  experiments {\n    id\n  }\n}\n\nquery expand_omerofile($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Search_omerofileQueryOptions(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename", exclude=True)
    value: ID
    label: str
    "The name of the file"

    class Config:
        frozen = True


class Search_omerofileQuery(BaseModel):
    options: Optional[Tuple[Optional[Search_omerofileQueryOptions], ...]]
    "All OmeroFiles\n\n    This query returns all OmeroFiles that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all OmeroFiles that the user has access to. If the user is an amdin\n    or superuser, all OmeroFiles will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str]
        values: Optional[List[Optional[ID]]]

    class Meta:
        document = "query search_omerofile($search: String, $values: [ID]) {\n  options: omerofiles(name: $search, ids: $values) {\n    value: id\n    label: name\n  }\n}"


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
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
            },
            rath=rath,
        )
    ).create_label


def create_label(
    instance: int,
    representation: ID,
    creator: Optional[ID] = None,
    name: Optional[str] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
            "created_while": created_while,
        },
        rath=rath,
    ).create_label


async def acreate_context(
    name: str,
    experiment: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[ContextFragment]:
    """create_context


     createContext: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


    Arguments:
        name (str): name
        experiment (Optional[ID], optional): experiment.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return (
        await aexecute(
            Create_contextMutation,
            {"name": name, "experiment": experiment, "created_while": created_while},
            rath=rath,
        )
    ).create_context


def create_context(
    name: str,
    experiment: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[ContextFragment]:
    """create_context


     createContext: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


    Arguments:
        name (str): name
        experiment (Optional[ID], optional): experiment.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return execute(
        Create_contextMutation,
        {"name": name, "experiment": experiment, "created_while": created_while},
        rath=rath,
    ).create_context


async def acreate_thumbnail(
    rep: ID,
    file: File,
    major_color: Optional[str] = None,
    blurhash: Optional[str] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
            },
            rath=rath,
        )
    ).upload_thumbnail


def create_thumbnail(
    rep: ID,
    file: File,
    major_color: Optional[str] = None,
    blurhash: Optional[str] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return execute(
        Create_thumbnailMutation,
        {
            "rep": rep,
            "file": file,
            "major_color": major_color,
            "blurhash": blurhash,
            "created_while": created_while,
        },
        rath=rath,
    ).upload_thumbnail


async def afrom_df(
    df: ParquetInput,
    name: str,
    rep_origins: Optional[List[Optional[ID]]] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return (
        await aexecute(
            From_dfMutation,
            {
                "df": df,
                "name": name,
                "rep_origins": rep_origins,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).from_df


def from_df(
    df: ParquetInput,
    name: str,
    rep_origins: Optional[List[Optional[ID]]] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TableFragment]"""
    return execute(
        From_dfMutation,
        {
            "df": df,
            "name": name,
            "rep_origins": rep_origins,
            "created_while": created_while,
        },
        rath=rath,
    ).from_df


async def alink(
    relation: ID,
    left_type: LinkableModels,
    left_id: ID,
    right_type: LinkableModels,
    right_id: ID,
    context: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[ListLinkFragment]:
    """link


     link: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (ID): relation
        left_type (LinkableModels): left_type
        left_id (ID): left_id
        right_type (LinkableModels): right_type
        right_id (ID): right_id
        context (Optional[ID], optional): context.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ListLinkFragment]"""
    return (
        await aexecute(
            LinkMutation,
            {
                "relation": relation,
                "left_type": left_type,
                "left_id": left_id,
                "right_type": right_type,
                "right_id": right_id,
                "context": context,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).link


def link(
    relation: ID,
    left_type: LinkableModels,
    left_id: ID,
    right_type: LinkableModels,
    right_id: ID,
    context: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[ListLinkFragment]:
    """link


     link: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (ID): relation
        left_type (LinkableModels): left_type
        left_id (ID): left_id
        right_type (LinkableModels): right_type
        right_id (ID): right_id
        context (Optional[ID], optional): context.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ListLinkFragment]"""
    return execute(
        LinkMutation,
        {
            "relation": relation,
            "left_type": left_type,
            "left_id": left_id,
            "right_type": right_type,
            "right_id": right_id,
            "context": context,
            "created_while": created_while,
        },
        rath=rath,
    ).link


async def acreate_stage(
    name: str,
    creator: Optional[ID] = None,
    instrument: Optional[ID] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[StageFragment]:
    """create_stage


     createStage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        name (str): name
        creator (Optional[ID], optional): creator.
        instrument (Optional[ID], optional): instrument.
        tags (Optional[List[Optional[str]]], optional): tags.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return (
        await aexecute(
            Create_stageMutation,
            {
                "name": name,
                "creator": creator,
                "instrument": instrument,
                "tags": tags,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).create_stage


def create_stage(
    name: str,
    creator: Optional[ID] = None,
    instrument: Optional[ID] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[StageFragment]:
    """create_stage


     createStage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        name (str): name
        creator (Optional[ID], optional): creator.
        instrument (Optional[ID], optional): instrument.
        tags (Optional[List[Optional[str]]], optional): tags.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[StageFragment]"""
    return execute(
        Create_stageMutation,
        {
            "name": name,
            "creator": creator,
            "instrument": instrument,
            "tags": tags,
            "created_while": created_while,
        },
        rath=rath,
    ).create_stage


async def acreate_sample(
    name: Optional[str] = None,
    creator: Optional[str] = None,
    meta: Optional[Dict] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
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
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
            "created_while": created_while,
        },
        rath=rath,
    ).create_sample


async def acreate_channel(
    name: str,
    emission_wavelength: Optional[float] = None,
    excitation_wavelength: Optional[float] = None,
    acquisition_mode: Optional[str] = None,
    color: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[ChannelFragment]:
    """CreateChannel


     createChannel: Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)


    Arguments:
        name (str): name
        emission_wavelength (Optional[float], optional): emissionWavelength.
        excitation_wavelength (Optional[float], optional): excitationWavelength.
        acquisition_mode (Optional[str], optional): acquisitionMode.
        color (Optional[str], optional): color.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ChannelFragment]"""
    return (
        await aexecute(
            CreateChannelMutation,
            {
                "name": name,
                "emissionWavelength": emission_wavelength,
                "excitationWavelength": excitation_wavelength,
                "acquisitionMode": acquisition_mode,
                "color": color,
            },
            rath=rath,
        )
    ).create_channel


def create_channel(
    name: str,
    emission_wavelength: Optional[float] = None,
    excitation_wavelength: Optional[float] = None,
    acquisition_mode: Optional[str] = None,
    color: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[ChannelFragment]:
    """CreateChannel


     createChannel: Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)


    Arguments:
        name (str): name
        emission_wavelength (Optional[float], optional): emissionWavelength.
        excitation_wavelength (Optional[float], optional): excitationWavelength.
        acquisition_mode (Optional[str], optional): acquisitionMode.
        color (Optional[str], optional): color.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ChannelFragment]"""
    return execute(
        CreateChannelMutation,
        {
            "name": name,
            "emissionWavelength": emission_wavelength,
            "excitationWavelength": excitation_wavelength,
            "acquisitionMode": acquisition_mode,
            "color": color,
        },
        rath=rath,
    ).create_channel


async def acreate_roi(
    representation: ID,
    vectors: List[Optional[InputVector]],
    type: RoiTypeInput,
    creator: Optional[ID] = None,
    label: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
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
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
            "created_while": created_while,
        },
        rath=rath,
    ).create_roi


async def acreate_rois(
    representation: ID,
    vectors_list: List[Optional[List[Optional[InputVector]]]],
    type: RoiTypeInput,
    creator: Optional[ID] = None,
    labels: Optional[List[Optional[str]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[Create_roisMutationCreaterois]:
    """create_rois


     createROIS: A Representation is 5-dimensional representation of an image

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
        representation (ID): representation
        vectors_list (List[Optional[List[Optional[InputVector]]]]): vectors_list
        type (RoiTypeInput): type
        creator (Optional[ID], optional): creator.
        labels (Optional[List[Optional[str]]], optional): labels.
        tags (Optional[List[Optional[str]]], optional): tags.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_roisMutationCreaterois]"""
    return (
        await aexecute(
            Create_roisMutation,
            {
                "representation": representation,
                "vectors_list": vectors_list,
                "creator": creator,
                "type": type,
                "labels": labels,
                "tags": tags,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).create_rois


def create_rois(
    representation: ID,
    vectors_list: List[Optional[List[Optional[InputVector]]]],
    type: RoiTypeInput,
    creator: Optional[ID] = None,
    labels: Optional[List[Optional[str]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[Create_roisMutationCreaterois]:
    """create_rois


     createROIS: A Representation is 5-dimensional representation of an image

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
        representation (ID): representation
        vectors_list (List[Optional[List[Optional[InputVector]]]]): vectors_list
        type (RoiTypeInput): type
        creator (Optional[ID], optional): creator.
        labels (Optional[List[Optional[str]]], optional): labels.
        tags (Optional[List[Optional[str]]], optional): tags.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_roisMutationCreaterois]"""
    return execute(
        Create_roisMutation,
        {
            "representation": representation,
            "vectors_list": vectors_list,
            "creator": creator,
            "type": type,
            "labels": labels,
            "tags": tags,
            "created_while": created_while,
        },
        rath=rath,
    ).create_rois


async def acreate_feature(
    label: ID,
    value: FeatureValue,
    key: Optional[str] = None,
    creator: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_featureMutationCreatefeature]"""
    return (
        await aexecute(
            Create_featureMutation,
            {
                "label": label,
                "key": key,
                "value": value,
                "creator": creator,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).createfeature


def create_feature(
    label: ID,
    value: FeatureValue,
    key: Optional[str] = None,
    creator: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Create_featureMutationCreatefeature]"""
    return execute(
        Create_featureMutation,
        {
            "label": label,
            "key": key,
            "value": value,
            "creator": creator,
            "created_while": created_while,
        },
        rath=rath,
    ).createfeature


async def acreate_era(
    name: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    rath: MikroRath = None,
) -> Optional[EraFragment]:
    """CreateEra


     createEra: Era(id, created_by, created_through, created_while, name, start, end, created_at)


    Arguments:
        name (Optional[str], optional): name.
        start (Optional[datetime], optional): start.
        end (Optional[datetime], optional): end.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[EraFragment]"""
    return (
        await aexecute(
            CreateEraMutation, {"name": name, "start": start, "end": end}, rath=rath
        )
    ).create_era


def create_era(
    name: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    rath: MikroRath = None,
) -> Optional[EraFragment]:
    """CreateEra


     createEra: Era(id, created_by, created_through, created_while, name, start, end, created_at)


    Arguments:
        name (Optional[str], optional): name.
        start (Optional[datetime], optional): start.
        end (Optional[datetime], optional): end.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[EraFragment]"""
    return execute(
        CreateEraMutation, {"name": name, "start": start, "end": end}, rath=rath
    ).create_era


async def acreate_dimension_map(
    omero: ID,
    dim: Dimension,
    index: int,
    channel: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[DimensionMapFragment]:
    """CreateDimensionMap


     createDimensionMap: DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)


    Arguments:
        omero (ID): omero
        dim (Dimension): dim
        index (int): index
        channel (Optional[ID], optional): channel.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DimensionMapFragment]"""
    return (
        await aexecute(
            CreateDimensionMapMutation,
            {"omero": omero, "dim": dim, "index": index, "channel": channel},
            rath=rath,
        )
    ).create_dimension_map


def create_dimension_map(
    omero: ID,
    dim: Dimension,
    index: int,
    channel: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[DimensionMapFragment]:
    """CreateDimensionMap


     createDimensionMap: DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)


    Arguments:
        omero (ID): omero
        dim (Dimension): dim
        index (int): index
        channel (Optional[ID], optional): channel.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DimensionMapFragment]"""
    return execute(
        CreateDimensionMapMutation,
        {"omero": omero, "dim": dim, "index": index, "channel": channel},
        rath=rath,
    ).create_dimension_map


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
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[InstrumentFragment]:
    """create_instrument


     createInstrument: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
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
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[InstrumentFragment]:
    """create_instrument


     createInstrument: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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
        created_while (Optional[AssignationID], optional): created_while.
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
            "created_while": created_while,
        },
        rath=rath,
    ).create_instrument


async def apresign(
    file_name: str, rath: MikroRath = None
) -> Optional[PresignMutationPresign]:
    """presign



    Arguments:
        file_name (str): file_name
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PresignMutationPresign]"""
    return (
        await aexecute(PresignMutation, {"file_name": file_name}, rath=rath)
    ).presign


def presign(file_name: str, rath: MikroRath = None) -> Optional[PresignMutationPresign]:
    """presign



    Arguments:
        file_name (str): file_name
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PresignMutationPresign]"""
    return execute(PresignMutation, {"file_name": file_name}, rath=rath).presign


async def aupload_video(
    file: BigFile,
    representations: List[Optional[ID]],
    front_image: Optional[BigFile] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[VideoFragment]:
    """upload_video



    Arguments:
        file (BigFile): file
        representations (List[Optional[ID]]): representations
        front_image (Optional[BigFile], optional): frontImage.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[VideoFragment]"""
    return (
        await aexecute(
            Upload_videoMutation,
            {
                "file": file,
                "representations": representations,
                "frontImage": front_image,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).upload_video


def upload_video(
    file: BigFile,
    representations: List[Optional[ID]],
    front_image: Optional[BigFile] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[VideoFragment]:
    """upload_video



    Arguments:
        file (BigFile): file
        representations (List[Optional[ID]]): representations
        front_image (Optional[BigFile], optional): frontImage.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[VideoFragment]"""
    return execute(
        Upload_videoMutation,
        {
            "file": file,
            "representations": representations,
            "frontImage": front_image,
            "created_while": created_while,
        },
        rath=rath,
    ).upload_video


async def acreate_timepoint(
    era: ID,
    delta_t: float,
    name: Optional[str] = None,
    tolerance: Optional[float] = None,
    rath: MikroRath = None,
) -> Optional[TimepointFragment]:
    """CreateTimepoint


     createTimepoint: The relative position of a sample on a microscope stage


    Arguments:
        era (ID): era
        delta_t (float): delta_t
        name (Optional[str], optional): name.
        tolerance (Optional[float], optional): tolerance.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TimepointFragment]"""
    return (
        await aexecute(
            CreateTimepointMutation,
            {"era": era, "delta_t": delta_t, "name": name, "tolerance": tolerance},
            rath=rath,
        )
    ).create_timepoint


def create_timepoint(
    era: ID,
    delta_t: float,
    name: Optional[str] = None,
    tolerance: Optional[float] = None,
    rath: MikroRath = None,
) -> Optional[TimepointFragment]:
    """CreateTimepoint


     createTimepoint: The relative position of a sample on a microscope stage


    Arguments:
        era (ID): era
        delta_t (float): delta_t
        name (Optional[str], optional): name.
        tolerance (Optional[float], optional): tolerance.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TimepointFragment]"""
    return execute(
        CreateTimepointMutation,
        {"era": era, "delta_t": delta_t, "name": name, "tolerance": tolerance},
        rath=rath,
    ).create_timepoint


async def acreate_experiment(
    name: str,
    creator: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
            },
            rath=rath,
        )
    ).create_experiment


def create_experiment(
    name: str,
    creator: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ExperimentFragment]"""
    return execute(
        Create_experimentMutation,
        {
            "name": name,
            "creator": creator,
            "description": description,
            "tags": tags,
            "created_while": created_while,
        },
        rath=rath,
    ).create_experiment


async def afrom_xarray(
    xarray: XArrayInput,
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[ID]]] = None,
    file_origins: Optional[List[Optional[ID]]] = None,
    roi_origins: Optional[List[Optional[ID]]] = None,
    table_origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    datasets: Optional[List[Optional[ID]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    views: Optional[List[Optional[RepresentationViewInput]]] = None,
    created_while: Optional[AssignationID] = None,
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
        table_origins (Optional[List[Optional[ID]]], optional): table_origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
        datasets (Optional[List[Optional[ID]]], optional): datasets.
        sample (Optional[ID], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        views (Optional[List[Optional[RepresentationViewInput]]], optional): views.
        created_while (Optional[AssignationID], optional): created_while.
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
                "table_origins": table_origins,
                "tags": tags,
                "experiments": experiments,
                "datasets": datasets,
                "sample": sample,
                "omero": omero,
                "views": views,
                "created_while": created_while,
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
    table_origins: Optional[List[Optional[ID]]] = None,
    tags: Optional[List[Optional[str]]] = None,
    experiments: Optional[List[Optional[ID]]] = None,
    datasets: Optional[List[Optional[ID]]] = None,
    sample: Optional[ID] = None,
    omero: Optional[OmeroRepresentationInput] = None,
    views: Optional[List[Optional[RepresentationViewInput]]] = None,
    created_while: Optional[AssignationID] = None,
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
        table_origins (Optional[List[Optional[ID]]], optional): table_origins.
        tags (Optional[List[Optional[str]]], optional): tags.
        experiments (Optional[List[Optional[ID]]], optional): experiments.
        datasets (Optional[List[Optional[ID]]], optional): datasets.
        sample (Optional[ID], optional): sample.
        omero (Optional[OmeroRepresentationInput], optional): omero.
        views (Optional[List[Optional[RepresentationViewInput]]], optional): views.
        created_while (Optional[AssignationID], optional): created_while.
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
            "table_origins": table_origins,
            "tags": tags,
            "experiments": experiments,
            "datasets": datasets,
            "sample": sample,
            "omero": omero,
            "views": views,
            "created_while": created_while,
        },
        rath=rath,
    ).from_x_array


async def aupdate_representation(
    id: ID,
    tags: Optional[List[Optional[str]]] = None,
    sample: Optional[ID] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    rath: MikroRath = None,
) -> Optional[RepresentationFragment]:
    """update_representation


     updateRepresentation: A Representation is 5-dimensional representation of an image

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
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
    created_while: Optional[AssignationID] = None,
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
        created_while (Optional[AssignationID], optional): created_while.
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
            "created_while": created_while,
        },
        rath=rath,
    ).create_model


async def acreate_metric(
    key: str,
    value: MetricValue,
    representation: Optional[ID] = None,
    sample: Optional[ID] = None,
    experiment: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[MetricFragment]:
    """create_metric



    Arguments:
        key (str): key
        value (MetricValue): value
        representation (Optional[ID], optional): representation.
        sample (Optional[ID], optional): sample.
        experiment (Optional[ID], optional): experiment.
        created_while (Optional[AssignationID], optional): created_while.
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
                "created_while": created_while,
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
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[MetricFragment]:
    """create_metric



    Arguments:
        key (str): key
        value (MetricValue): value
        representation (Optional[ID], optional): representation.
        sample (Optional[ID], optional): sample.
        experiment (Optional[ID], optional): experiment.
        created_while (Optional[AssignationID], optional): created_while.
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
            "created_while": created_while,
        },
        rath=rath,
    ).create_metric


async def acreate_dataset(
    name: str,
    parent: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[DatasetFragment]:
    """create_dataset


     createDataset:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        name (str): name
        parent (Optional[ID], optional): parent.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DatasetFragment]"""
    return (
        await aexecute(
            Create_datasetMutation,
            {"name": name, "parent": parent, "created_while": created_while},
            rath=rath,
        )
    ).create_dataset


def create_dataset(
    name: str,
    parent: Optional[ID] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[DatasetFragment]:
    """create_dataset


     createDataset:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        name (str): name
        parent (Optional[ID], optional): parent.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DatasetFragment]"""
    return execute(
        Create_datasetMutation,
        {"name": name, "parent": parent, "created_while": created_while},
        rath=rath,
    ).create_dataset


async def acreate_position(
    stage: ID,
    x: float,
    y: float,
    z: float,
    tolerance: Optional[float] = None,
    name: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[PositionFragment]:
    """create_position


     createPosition: The relative position of a sample on a microscope stage


    Arguments:
        stage (ID): stage
        x (float): x
        y (float): y
        z (float): z
        tolerance (Optional[float], optional): tolerance.
        name (Optional[str], optional): name.
        tags (Optional[List[Optional[str]]], optional): tags.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return (
        await aexecute(
            Create_positionMutation,
            {
                "stage": stage,
                "x": x,
                "y": y,
                "z": z,
                "tolerance": tolerance,
                "name": name,
                "tags": tags,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).create_position


def create_position(
    stage: ID,
    x: float,
    y: float,
    z: float,
    tolerance: Optional[float] = None,
    name: Optional[str] = None,
    tags: Optional[List[Optional[str]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[PositionFragment]:
    """create_position


     createPosition: The relative position of a sample on a microscope stage


    Arguments:
        stage (ID): stage
        x (float): x
        y (float): y
        z (float): z
        tolerance (Optional[float], optional): tolerance.
        name (Optional[str], optional): name.
        tags (Optional[List[Optional[str]]], optional): tags.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[PositionFragment]"""
    return execute(
        Create_positionMutation,
        {
            "stage": stage,
            "x": x,
            "y": y,
            "z": z,
            "tolerance": tolerance,
            "name": name,
            "tags": tags,
            "created_while": created_while,
        },
        rath=rath,
    ).create_position


async def acreate_objective(
    serial_number: str,
    name: str,
    magnification: float,
    na: Optional[float] = None,
    immersion: Optional[str] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[ObjectiveFragment]:
    """create_objective


     createObjective: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


    Arguments:
        serial_number (str): serial_number
        name (str): name
        magnification (float): magnification
        na (Optional[float], optional): na.
        immersion (Optional[str], optional): immersion.
        created_while (Optional[AssignationID], optional): created_while.
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
                "na": na,
                "immersion": immersion,
                "created_while": created_while,
            },
            rath=rath,
        )
    ).create_objective


def create_objective(
    serial_number: str,
    name: str,
    magnification: float,
    na: Optional[float] = None,
    immersion: Optional[str] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[ObjectiveFragment]:
    """create_objective


     createObjective: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


    Arguments:
        serial_number (str): serial_number
        name (str): name
        magnification (float): magnification
        na (Optional[float], optional): na.
        immersion (Optional[str], optional): immersion.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return execute(
        Create_objectiveMutation,
        {
            "serial_number": serial_number,
            "name": name,
            "magnification": magnification,
            "na": na,
            "immersion": immersion,
            "created_while": created_while,
        },
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


async def aupload_bigfile(
    file: BigFile,
    datasets: Optional[List[Optional[ID]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[Upload_bigfileMutationUploadbigfile]:
    """upload_bigfile



    Arguments:
        file (BigFile): file
        datasets (Optional[List[Optional[ID]]], optional): datasets.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Upload_bigfileMutationUploadbigfile]"""
    return (
        await aexecute(
            Upload_bigfileMutation,
            {"file": file, "datasets": datasets, "created_while": created_while},
            rath=rath,
        )
    ).upload_big_file


def upload_bigfile(
    file: BigFile,
    datasets: Optional[List[Optional[ID]]] = None,
    created_while: Optional[AssignationID] = None,
    rath: MikroRath = None,
) -> Optional[Upload_bigfileMutationUploadbigfile]:
    """upload_bigfile



    Arguments:
        file (BigFile): file
        datasets (Optional[List[Optional[ID]]], optional): datasets.
        created_while (Optional[AssignationID], optional): created_while.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Upload_bigfileMutationUploadbigfile]"""
    return execute(
        Upload_bigfileMutation,
        {"file": file, "datasets": datasets, "created_while": created_while},
        rath=rath,
    ).upload_big_file


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_labelsQueryLabels]]]"""
    return (
        await aexecute(
            Search_labelsQuery, {"search": search, "values": values}, rath=rath
        )
    ).labels


def search_labels(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_labelsQueryLabels]]]"""
    return execute(
        Search_labelsQuery, {"search": search, "values": values}, rath=rath
    ).labels


async def aget_context(id: ID, rath: MikroRath = None) -> Optional[ContextFragment]:
    """get_context


     context: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return (await aexecute(Get_contextQuery, {"id": id}, rath=rath)).context


def get_context(id: ID, rath: MikroRath = None) -> Optional[ContextFragment]:
    """get_context


     context: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


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


     mycontexts: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


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


     mycontexts: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


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


     context: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return (await aexecute(Expand_contextQuery, {"id": id}, rath=rath)).context


def expand_context(id: ID, rath: MikroRath = None) -> Optional[ContextFragment]:
    """expand_context


     context: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ContextFragment]"""
    return execute(Expand_contextQuery, {"id": id}, rath=rath).context


async def asearch_contexts(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_contextsQueryOptions]]]:
    """search_contexts


     options: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_contextsQueryMycontexts]]]"""
    return (
        await aexecute(
            Search_contextsQuery, {"search": search, "values": values}, rath=rath
        )
    ).mycontexts


def search_contexts(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_contextsQueryOptions]]]:
    """search_contexts


     options: Context(id, created_by, created_through, created_while, name, created_at, experiment, creator)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_contextsQueryMycontexts]]]"""
    return execute(
        Search_contextsQuery, {"search": search, "values": values}, rath=rath
    ).mycontexts


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_thumbnailsQueryOptions]]]:
    """search_thumbnails


     options: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]"""
    return (
        await aexecute(
            Search_thumbnailsQuery, {"search": search, "values": values}, rath=rath
        )
    ).thumbnails


def search_thumbnails(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_thumbnailsQueryOptions]]]:
    """search_thumbnails


     options: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]"""
    return execute(
        Search_thumbnailsQuery, {"search": search, "values": values}, rath=rath
    ).thumbnails


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
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
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tablesQueryTables]]]"""
    return (
        await aexecute(
            Search_tablesQuery, {"search": search, "values": values}, rath=rath
        )
    ).tables


def search_tables(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
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
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tablesQueryTables]]]"""
    return execute(
        Search_tablesQuery, {"search": search, "values": values}, rath=rath
    ).tables


async def alinks(
    x_type: LinkableModels,
    y_type: LinkableModels,
    relation: str,
    context: Optional[ID] = None,
    limit: Optional[int] = 10,
    rath: MikroRath = None,
) -> Optional[List[Optional[LinksQueryLinks]]]:
    """Links


     links: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


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


     links: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


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


async def aget_image_image_links(
    relation: str,
    context: Optional[ID] = None,
    limit: Optional[int] = 10,
    rath: MikroRath = None,
) -> Optional[List[Optional[Get_image_image_linksQueryLinks]]]:
    """get_image_image_links


     links: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (str): relation
        context (Optional[ID], optional): context.
        limit (Optional[int], optional): limit. Defaults to 10
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Get_image_image_linksQueryLinks]]]"""
    return (
        await aexecute(
            Get_image_image_linksQuery,
            {"relation": relation, "context": context, "limit": limit},
            rath=rath,
        )
    ).links


def get_image_image_links(
    relation: str,
    context: Optional[ID] = None,
    limit: Optional[int] = 10,
    rath: MikroRath = None,
) -> Optional[List[Optional[Get_image_image_linksQueryLinks]]]:
    """get_image_image_links


     links: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        relation (str): relation
        context (Optional[ID], optional): context.
        limit (Optional[int], optional): limit. Defaults to 10
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Get_image_image_linksQueryLinks]]]"""
    return execute(
        Get_image_image_linksQuery,
        {"relation": relation, "context": context, "limit": limit},
        rath=rath,
    ).links


async def aget_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """get_link


     link: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return (await aexecute(Get_linkQuery, {"id": id}, rath=rath)).link


def get_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """get_link


     link: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return execute(Get_linkQuery, {"id": id}, rath=rath).link


async def aexpand_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """expand_link


     link: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return (await aexecute(Expand_linkQuery, {"id": id}, rath=rath)).link


def expand_link(id: ID, rath: MikroRath = None) -> Optional[LinkFragment]:
    """expand_link


     link: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[LinkFragment]"""
    return execute(Expand_linkQuery, {"id": id}, rath=rath).link


async def asearch_links(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_linksQueryOptions]]]:
    """search_links


     options: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_linksQueryLinks]]]"""
    return (
        await aexecute(
            Search_linksQuery, {"search": search, "values": values}, rath=rath
        )
    ).links


def search_links(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_linksQueryOptions]]]:
    """search_links


     options: DataLink(id, created_by, created_through, created_while, x_content_type, x_id, y_content_type, y_id, relation, left_type, right_type, context, created_at, creator)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_linksQueryLinks]]]"""
    return execute(
        Search_linksQuery, {"search": search, "values": values}, rath=rath
    ).links


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_stagesQueryOptions]]]:
    """search_stages


     options: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_stagesQueryStages]]]"""
    return (
        await aexecute(
            Search_stagesQuery, {"search": search, "values": values}, rath=rath
        )
    ).stages


def search_stages(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_stagesQueryOptions]]]:
    """search_stages


     options: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_stagesQueryStages]]]"""
    return execute(
        Search_stagesQuery, {"search": search, "values": values}, rath=rath
    ).stages


async def aget_display_stage(
    id: ID, rath: MikroRath = None
) -> Optional[Get_display_stageQueryStage]:
    """get_display_stage


     stage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Get_display_stageQueryStage]"""
    return (await aexecute(Get_display_stageQuery, {"id": id}, rath=rath)).stage


def get_display_stage(
    id: ID, rath: MikroRath = None
) -> Optional[Get_display_stageQueryStage]:
    """get_display_stage


     stage: An Stage is a set of positions that share a common space on a microscope and can
        be use to translate.





    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[Get_display_stageQueryStage]"""
    return execute(Get_display_stageQuery, {"id": id}, rath=rath).stage


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_sampleQueryOptions]]]:
    """search_sample


     options: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_sampleQuerySamples]]]"""
    return (
        await aexecute(
            Search_sampleQuery, {"search": search, "values": values}, rath=rath
        )
    ).samples


def search_sample(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_sampleQueryOptions]]]:
    """search_sample


     options: Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_sampleQuerySamples]]]"""
    return execute(
        Search_sampleQuery, {"search": search, "values": values}, rath=rath
    ).samples


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


async def aget_channel(id: ID, rath: MikroRath = None) -> Optional[ChannelFragment]:
    """GetChannel


     channel: Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ChannelFragment]"""
    return (await aexecute(GetChannelQuery, {"id": id}, rath=rath)).channel


def get_channel(id: ID, rath: MikroRath = None) -> Optional[ChannelFragment]:
    """GetChannel


     channel: Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ChannelFragment]"""
    return execute(GetChannelQuery, {"id": id}, rath=rath).channel


async def asearch_channels(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchChannelsQueryOptions]]]:
    """SearchChannels


     options: Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchChannelsQueryChannels]]]"""
    return (
        await aexecute(
            SearchChannelsQuery, {"search": search, "values": values}, rath=rath
        )
    ).channels


def search_channels(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchChannelsQueryOptions]]]:
    """SearchChannels


     options: Channel(id, created_by, created_through, created_while, name, emission_wavelength, excitation_wavelength, acquisition_mode, color)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchChannelsQueryChannels]]]"""
    return execute(
        SearchChannelsQuery, {"search": search, "values": values}, rath=rath
    ).channels


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_roisQueryRois]]]"""
    return (
        await aexecute(
            Search_roisQuery, {"search": search, "values": values}, rath=rath
        )
    ).rois


def search_rois(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_roisQueryRois]]]"""
    return execute(
        Search_roisQuery, {"search": search, "values": values}, rath=rath
    ).rois


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_featuresQueryFeatures]]]"""
    return (
        await aexecute(
            Search_featuresQuery, {"search": search, "values": values}, rath=rath
        )
    ).features


def search_features(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_featuresQueryFeatures]]]"""
    return execute(
        Search_featuresQuery, {"search": search, "values": values}, rath=rath
    ).features


async def aget_era(id: ID, rath: MikroRath = None) -> Optional[EraFragment]:
    """GetEra


     era: Era(id, created_by, created_through, created_while, name, start, end, created_at)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[EraFragment]"""
    return (await aexecute(GetEraQuery, {"id": id}, rath=rath)).era


def get_era(id: ID, rath: MikroRath = None) -> Optional[EraFragment]:
    """GetEra


     era: Era(id, created_by, created_through, created_while, name, start, end, created_at)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[EraFragment]"""
    return execute(GetEraQuery, {"id": id}, rath=rath).era


async def asearch_eras(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchErasQueryOptions]]]:
    """SearchEras


     options: Era(id, created_by, created_through, created_while, name, start, end, created_at)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchErasQueryEras]]]"""
    return (
        await aexecute(SearchErasQuery, {"search": search, "values": values}, rath=rath)
    ).eras


def search_eras(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchErasQueryOptions]]]:
    """SearchEras


     options: Era(id, created_by, created_through, created_while, name, start, end, created_at)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchErasQueryEras]]]"""
    return execute(
        SearchErasQuery, {"search": search, "values": values}, rath=rath
    ).eras


async def aget_dimension_map(
    id: ID, rath: MikroRath = None
) -> Optional[DimensionMapFragment]:
    """GetDimensionMap


     dimensionmap: DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DimensionMapFragment]"""
    return (await aexecute(GetDimensionMapQuery, {"id": id}, rath=rath)).dimensionmap


def get_dimension_map(id: ID, rath: MikroRath = None) -> Optional[DimensionMapFragment]:
    """GetDimensionMap


     dimensionmap: DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DimensionMapFragment]"""
    return execute(GetDimensionMapQuery, {"id": id}, rath=rath).dimensionmap


async def asearch_dimension_maps(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchDimensionMapsQueryOptions]]]:
    """SearchDimensionMaps


     options: DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchDimensionMapsQueryDimensionmaps]]]"""
    return (
        await aexecute(
            SearchDimensionMapsQuery, {"search": search, "values": values}, rath=rath
        )
    ).dimensionmaps


def search_dimension_maps(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchDimensionMapsQueryOptions]]]:
    """SearchDimensionMaps


     options: DimensionMap(id, created_by, created_through, created_while, omero, channel, dimension, index)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchDimensionMapsQueryDimensionmaps]]]"""
    return execute(
        SearchDimensionMapsQuery, {"search": search, "values": values}, rath=rath
    ).dimensionmaps


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


     instrument: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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


     instrument: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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


     instrument: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return (await aexecute(Expand_instrumentQuery, {"id": id}, rath=rath)).instrument


def expand_instrument(id: ID, rath: MikroRath = None) -> Optional[InstrumentFragment]:
    """expand_instrument


     instrument: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return execute(Expand_instrumentQuery, {"id": id}, rath=rath).instrument


async def asearch_instruments(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_instrumentsQueryOptions]]]:
    """search_instruments


     options: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_instrumentsQueryInstruments]]]"""
    return (
        await aexecute(
            Search_instrumentsQuery, {"search": search, "values": values}, rath=rath
        )
    ).instruments


def search_instruments(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_instrumentsQueryOptions]]]:
    """search_instruments


     options: Instrument(id, created_by, created_through, created_while, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_instrumentsQueryInstruments]]]"""
    return execute(
        Search_instrumentsQuery, {"search": search, "values": values}, rath=rath
    ).instruments


async def aget_video(id: ID, rath: MikroRath = None) -> Optional[VideoFragment]:
    """get_video



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[VideoFragment]"""
    return (await aexecute(Get_videoQuery, {"id": id}, rath=rath)).video


def get_video(id: ID, rath: MikroRath = None) -> Optional[VideoFragment]:
    """get_video



    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[VideoFragment]"""
    return execute(Get_videoQuery, {"id": id}, rath=rath).video


async def asearch_videos(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_videosQueryOptions]]]:
    """search_videos



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_videosQueryVideos]]]"""
    return (
        await aexecute(
            Search_videosQuery, {"search": search, "values": values}, rath=rath
        )
    ).videos


def search_videos(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_videosQueryOptions]]]:
    """search_videos



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_videosQueryVideos]]]"""
    return execute(
        Search_videosQuery, {"search": search, "values": values}, rath=rath
    ).videos


async def aget_timepoint(id: ID, rath: MikroRath = None) -> Optional[TimepointFragment]:
    """GetTimepoint


     timepoint: The relative position of a sample on a microscope stage


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TimepointFragment]"""
    return (await aexecute(GetTimepointQuery, {"id": id}, rath=rath)).timepoint


def get_timepoint(id: ID, rath: MikroRath = None) -> Optional[TimepointFragment]:
    """GetTimepoint


     timepoint: The relative position of a sample on a microscope stage


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[TimepointFragment]"""
    return execute(GetTimepointQuery, {"id": id}, rath=rath).timepoint


async def asearch_timepoints(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchTimepointsQueryOptions]]]:
    """SearchTimepoints


     options: The relative position of a sample on a microscope stage


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchTimepointsQueryTimepoints]]]"""
    return (
        await aexecute(
            SearchTimepointsQuery, {"search": search, "values": values}, rath=rath
        )
    ).timepoints


def search_timepoints(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[SearchTimepointsQueryOptions]]]:
    """SearchTimepoints


     options: The relative position of a sample on a microscope stage


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[SearchTimepointsQueryTimepoints]]]"""
    return execute(
        SearchTimepointsQuery, {"search": search, "values": values}, rath=rath
    ).timepoints


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


async def aeget_experiments(
    rath: MikroRath = None,
) -> Optional[List[Optional[ListExperimentFragment]]]:
    """eget_experiments


     experiments:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListExperimentFragment]]]"""
    return (await aexecute(Eget_experimentsQuery, {}, rath=rath)).experiments


def eget_experiments(
    rath: MikroRath = None,
) -> Optional[List[Optional[ListExperimentFragment]]]:
    """eget_experiments


     experiments:
        An experiment is a collection of samples and their representations.
        It mimics the concept of an experiment in the lab and is the top level
        object in the data model.

        You can use the experiment to group samples and representations likewise
        to how you would group files into folders in a file system.



    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListExperimentFragment]]]"""
    return execute(Eget_experimentsQuery, {}, rath=rath).experiments


async def asearch_experiment(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_experimentQueryExperiments]]]"""
    return (
        await aexecute(
            Search_experimentQuery, {"search": search, "values": values}, rath=rath
        )
    ).experiments


def search_experiment(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_experimentQueryExperiments]]]"""
    return execute(
        Search_experimentQuery, {"search": search, "values": values}, rath=rath
    ).experiments


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

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_representationQueryOptions]]]:
    """search_representation


     options: A Representation is 5-dimensional representation of an image

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_representationQueryRepresentations]]]"""
    return (
        await aexecute(
            Search_representationQuery, {"search": search, "values": values}, rath=rath
        )
    ).representations


def search_representation(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_representationQueryOptions]]]:
    """search_representation


     options: A Representation is 5-dimensional representation of an image

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_representationQueryRepresentations]]]"""
    return execute(
        Search_representationQuery, {"search": search, "values": values}, rath=rath
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

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_tagsQueryOptions]]]:
    """search_tags



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tagsQueryTags]]]"""
    return (
        await aexecute(
            Search_tagsQuery, {"search": search, "values": values}, rath=rath
        )
    ).tags


def search_tags(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_tagsQueryOptions]]]:
    """search_tags



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_tagsQueryTags]]]"""
    return execute(
        Search_tagsQuery, {"search": search, "values": values}, rath=rath
    ).tags


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_modelsQueryOptions]]]:
    """search_models


     options: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_modelsQueryModels]]]"""
    return (
        await aexecute(
            Search_modelsQuery, {"search": search, "values": values}, rath=rath
        )
    ).models


def search_models(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_modelsQueryOptions]]]:
    """search_models


     options: A

        Mikro uses the omero-meta data to create representations of the file. See Representation for more information.


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_modelsQueryModels]]]"""
    return execute(
        Search_modelsQuery, {"search": search, "values": values}, rath=rath
    ).models


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


async def aget_dataset(id: ID, rath: MikroRath = None) -> Optional[DatasetFragment]:
    """get_dataset


     dataset:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DatasetFragment]"""
    return (await aexecute(Get_datasetQuery, {"id": id}, rath=rath)).dataset


def get_dataset(id: ID, rath: MikroRath = None) -> Optional[DatasetFragment]:
    """get_dataset


     dataset:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DatasetFragment]"""
    return execute(Get_datasetQuery, {"id": id}, rath=rath).dataset


async def aexpand_dataset(id: ID, rath: MikroRath = None) -> Optional[DatasetFragment]:
    """expand_dataset


     dataset:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DatasetFragment]"""
    return (await aexecute(Expand_datasetQuery, {"id": id}, rath=rath)).dataset


def expand_dataset(id: ID, rath: MikroRath = None) -> Optional[DatasetFragment]:
    """expand_dataset


     dataset:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[DatasetFragment]"""
    return execute(Expand_datasetQuery, {"id": id}, rath=rath).dataset


async def aget_datasets(
    rath: MikroRath = None,
) -> Optional[List[Optional[ListDatasetFragment]]]:
    """get_datasets


     datasets:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListDatasetFragment]]]"""
    return (await aexecute(Get_datasetsQuery, {}, rath=rath)).datasets


def get_datasets(
    rath: MikroRath = None,
) -> Optional[List[Optional[ListDatasetFragment]]]:
    """get_datasets


     datasets:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[ListDatasetFragment]]]"""
    return execute(Get_datasetsQuery, {}, rath=rath).datasets


async def asearch_datasets(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_datasetsQueryOptions]]]:
    """search_datasets


     options:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_datasetsQueryDatasets]]]"""
    return (
        await aexecute(
            Search_datasetsQuery, {"search": search, "values": values}, rath=rath
        )
    ).datasets


def search_datasets(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_datasetsQueryOptions]]]:
    """search_datasets


     options:
        A dataset is a collection of data files and metadata files.
        It mimics the concept of a folder in a file system and is the top level
        object in the data model.




    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_datasetsQueryDatasets]]]"""
    return execute(
        Search_datasetsQuery, {"search": search, "values": values}, rath=rath
    ).datasets


async def athierno(
    rath: MikroRath = None,
) -> Optional[List[Optional[ThiernoQueryRepresentations]]]:
    """Thierno


     representations: A Representation is 5-dimensional representation of an image

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
        Optional[List[Optional[ThiernoQueryRepresentations]]]"""
    return (await aexecute(ThiernoQuery, {}, rath=rath)).representations


def thierno(
    rath: MikroRath = None,
) -> Optional[List[Optional[ThiernoQueryRepresentations]]]:
    """Thierno


     representations: A Representation is 5-dimensional representation of an image

        Mikro stores each image as sa 5-dimensional representation. The dimensions are:
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
        Optional[List[Optional[ThiernoQueryRepresentations]]]"""
    return execute(ThiernoQuery, {}, rath=rath).representations


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    stage: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_positionsQueryOptions]]]:
    """search_positions


     options: The relative position of a sample on a microscope stage


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        stage (Optional[ID], optional): stage.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_positionsQueryPositions]]]"""
    return (
        await aexecute(
            Search_positionsQuery,
            {"search": search, "values": values, "stage": stage},
            rath=rath,
        )
    ).positions


def search_positions(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    stage: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_positionsQueryOptions]]]:
    """search_positions


     options: The relative position of a sample on a microscope stage


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        stage (Optional[ID], optional): stage.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_positionsQueryPositions]]]"""
    return execute(
        Search_positionsQuery,
        {"search": search, "values": values, "stage": stage},
        rath=rath,
    ).positions


async def aget_objective(
    id: Optional[ID] = None, name: Optional[str] = None, rath: MikroRath = None
) -> Optional[ObjectiveFragment]:
    """get_objective


     objective: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


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


     objective: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


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


     objective: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return (await aexecute(Expand_objectiveQuery, {"id": id}, rath=rath)).objective


def expand_objective(id: ID, rath: MikroRath = None) -> Optional[ObjectiveFragment]:
    """expand_objective


     objective: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ObjectiveFragment]"""
    return execute(Expand_objectiveQuery, {"id": id}, rath=rath).objective


async def asearch_objectives(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_objectivesQueryOptions]]]:
    """search_objectives


     options: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_objectivesQueryObjectives]]]"""
    return (
        await aexecute(
            Search_objectivesQuery, {"search": search, "values": values}, rath=rath
        )
    ).objectives


def search_objectives(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_objectivesQueryOptions]]]:
    """search_objectives


     options: Objective(id, created_by, created_through, created_while, serial_number, name, magnification, na, immersion)


    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_objectivesQueryObjectives]]]"""
    return execute(
        Search_objectivesQuery, {"search": search, "values": values}, rath=rath
    ).objectives


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
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_omerofileQueryOptions]]]:
    """search_omerofile



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_omerofileQueryOmerofiles]]]"""
    return (
        await aexecute(
            Search_omerofileQuery, {"search": search, "values": values}, rath=rath
        )
    ).omerofiles


def search_omerofile(
    search: Optional[str] = None,
    values: Optional[List[Optional[ID]]] = None,
    rath: MikroRath = None,
) -> Optional[List[Optional[Search_omerofileQueryOptions]]]:
    """search_omerofile



    Arguments:
        search (Optional[str], optional): search.
        values (Optional[List[Optional[ID]]], optional): values.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_omerofileQueryOmerofiles]]]"""
    return execute(
        Search_omerofileQuery, {"search": search, "values": values}, rath=rath
    ).omerofiles


DescendendInput.update_forward_refs()
EraFragment.update_forward_refs()
OmeroRepresentationInput.update_forward_refs()
