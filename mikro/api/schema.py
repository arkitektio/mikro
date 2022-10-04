from mikro.traits import ROI, Table, Representation, Vectorizable
from typing import Dict, Literal, List, Iterator, Optional, AsyncIterator
from mikro.scalars import (
    DataFrame,
    Store,
    MetricValue,
    ArrayInput,
    FeatureValue,
    Parquet,
    File,
)
from mikro.funcs import aexecute, asubscribe, execute, subscribe
from mikro.rath import MikroRath
from rath.scalars import ID
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class CommentableModels(str, Enum):
    GRUNNLAG_USERMETA = "GRUNNLAG_USERMETA"
    GRUNNLAG_ANTIBODY = "GRUNNLAG_ANTIBODY"
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_INSTRUMENT = "GRUNNLAG_INSTRUMENT"
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
    GRUNNLAG_EXPERIMENT = "GRUNNLAG_EXPERIMENT"
    GRUNNLAG_EXPERIMENTALGROUP = "GRUNNLAG_EXPERIMENTALGROUP"
    GRUNNLAG_ANIMAL = "GRUNNLAG_ANIMAL"
    GRUNNLAG_OMEROFILE = "GRUNNLAG_OMEROFILE"
    GRUNNLAG_SAMPLE = "GRUNNLAG_SAMPLE"
    GRUNNLAG_REPRESENTATION = "GRUNNLAG_REPRESENTATION"
    GRUNNLAG_INSTRUMENT = "GRUNNLAG_INSTRUMENT"
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


class PandasDType(str, Enum):
    OBJECT = "OBJECT"
    INT64 = "INT64"
    FLOAT64 = "FLOAT64"
    BOOL = "BOOL"
    CATEGORY = "CATEGORY"
    DATETIME65 = "DATETIME65"
    TIMEDELTA = "TIMEDELTA"
    UNICODE = "UNICODE"


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
    """The Omero Meta Data of an Image

    Follows closely the omexml model. With a few alterations:
    - The data model of the datasets and experimenters is
    part of the mikro datamodel and are not accessed here.
    - Some parameters are ommited as they are not really used"""

    planes: Optional[List[Optional["PlaneInput"]]]
    channels: Optional[List[Optional["ChannelInput"]]]
    physical_size: Optional["PhysicalSizeInput"] = Field(alias="physicalSize")
    scale: Optional[List[Optional[float]]]
    acquisition_date: Optional[datetime] = Field(alias="acquisitionDate")
    objective_settings: Optional["ObjectiveSettingsInput"] = Field(
        alias="objectiveSettings"
    )
    imaging_environment: Optional["ImagingEnvironmentInput"] = Field(
        alias="imagingEnvironment"
    )
    instrument: Optional[ID]


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


class ImagingEnvironmentInput(BaseModel):
    """The imaging environment during the acquisition

    Follows the OME model for imaging environment"""

    air_pessure: Optional[float] = Field(alias="airPessure")
    "The air pressure during the acquisition"
    co2_percent: Optional[float] = Field(alias="co2Percent")
    "The CO2 percentage in the environment"
    humidity: Optional[float]
    "The humidity of the imaging environment"
    temperature: Optional[float]
    "The temperature of the imaging environment"
    map: Optional[Dict]
    "A map of the imaging environment. Key value based"


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


class LabelFragment(BaseModel):
    typename: Optional[Literal["Label"]] = Field(alias="__typename")
    instance: int
    "The instance value of the representation (pixel value). Must be a value of the image array"
    id: ID
    representation: Optional[LabelFragmentRepresentation]
    "The Representation this Label instance belongs to"


class ThumbnailFragment(BaseModel):
    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    id: ID
    image: Optional[str]


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


class TableFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID


class TableFragmentRepresentation(Representation, BaseModel):
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


class TableFragment(Table, BaseModel):
    typename: Optional[Literal["Table"]] = Field(alias="__typename")
    id: ID
    name: str
    tags: Optional[List[Optional[str]]]
    "A comma-separated list of tags."
    store: Optional[Parquet]
    "The parquet store for the table"
    creator: Optional[TableFragmentCreator]
    "The creator of the Table"
    sample: Optional[TableFragmentSample]
    "Sample this table belongs to"
    representation: Optional[TableFragmentRepresentation]
    "The Representation this Table belongs to"
    experiment: Optional[TableFragmentExperiment]
    "The Experiment this Table belongs to."


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


class SampleFragment(BaseModel):
    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    "The name of the sample"
    id: ID
    representations: Optional[List[Optional[SampleFragmentRepresentations]]]
    "Associated representations of this Sample"
    experiments: List[SampleFragmentExperiments]
    "The experiments this sample belongs to"


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


class ROIFragment(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    id: ID
    label: Optional[str]
    "The label of the ROI (for UI)"
    vectors: Optional[List[Optional[ROIFragmentVectors]]]
    "The vectors of the ROI"
    type: ROIType
    "The Roi can have varying types, consult your API"
    representation: Optional[ROIFragmentRepresentation]
    "The Representation this ROI was original used to create (drawn on)"
    derived_representations: List[ROIFragmentDerivedrepresentations] = Field(
        alias="derivedRepresentations"
    )
    creator: ROIFragmentCreator
    "The user that created the ROI"


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


class ListROIFragment(ROI, BaseModel):
    typename: Optional[Literal["ROI"]] = Field(alias="__typename")
    id: ID
    label: Optional[str]
    "The label of the ROI (for UI)"
    vectors: Optional[List[Optional[ListROIFragmentVectors]]]
    "The vectors of the ROI"
    type: ROIType
    "The Roi can have varying types, consult your API"
    representation: Optional[ListROIFragmentRepresentation]
    "The Representation this ROI was original used to create (drawn on)"
    creator: ListROIFragmentCreator
    "The user that created the ROI"


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


class FeatureFragment(BaseModel):
    typename: Optional[Literal["Feature"]] = Field(alias="__typename")
    label: Optional[FeatureFragmentLabel]
    "The Label this Feature belongs to"
    id: ID
    key: str
    "The key of the feature"
    value: Optional[FeatureValue]
    "Value"


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


class ExperimentFragment(BaseModel):
    typename: Optional[Literal["Experiment"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the experiment"
    creator: Optional[ExperimentFragmentCreator]
    "The user that created the experiment"


class RepresentationFragmentSample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the sample"


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


class RepresentationFragmentOmero(BaseModel):
    """Omero is a model that stores the omero meta data

    This model is used to store the omero meta data. It is used to store the meta data of the omero file.
    Its implementation is based on the omero meta data model. Refer to the omero documentation for more information.



    """

    typename: Optional[Literal["Omero"]] = Field(alias="__typename")
    scale: Optional[List[Optional[float]]]
    physical_size: Optional[RepresentationFragmentOmeroPhysicalsize] = Field(
        alias="physicalSize"
    )


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


class RepresentationFragment(Representation, BaseModel):
    typename: Optional[Literal["Representation"]] = Field(alias="__typename")
    sample: Optional[RepresentationFragmentSample]
    "The Sample this representation belosngs to"
    id: ID
    store: Optional[Store]
    variety: RepresentationVariety
    "The Representation can have vasrying types, consult your API"
    name: Optional[str]
    "Cleartext name"
    omero: Optional[RepresentationFragmentOmero]
    origins: List[RepresentationFragmentOrigins]


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


class OmeroFileFragment(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the file"
    file: Optional[File]
    "The file"
    type: OmeroFileType
    "The type of the file"


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


class Watch_samplesSubscriptionMysamplesUpdate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the sample"
    experiments: List[Watch_samplesSubscriptionMysamplesUpdateExperiments]
    "The experiments this sample belongs to"


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


class Watch_samplesSubscriptionMysamplesCreate(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    name: str
    "The name of the sample"
    experiments: List[Watch_samplesSubscriptionMysamplesCreateExperiments]
    "The experiments this sample belongs to"


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


class Watch_roisSubscriptionRois(BaseModel):
    typename: Optional[Literal["RoiEvent"]] = Field(alias="__typename")
    update: Optional[ListROIFragment]
    delete: Optional[ID]
    create: Optional[ListROIFragment]


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


class Create_thumbnailMutation(BaseModel):
    upload_thumbnail: Optional[ThumbnailFragment] = Field(alias="uploadThumbnail")

    class Arguments(BaseModel):
        rep: ID
        file: File
        major_color: Optional[str] = None

    class Meta:
        document = "fragment Thumbnail on Thumbnail {\n  id\n  image\n}\n\nmutation create_thumbnail($rep: ID!, $file: ImageFile!, $major_color: String) {\n  uploadThumbnail(rep: $rep, file: $file, majorColor: $major_color) {\n    ...Thumbnail\n  }\n}"


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
        df: DataFrame
        name: str

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nmutation from_df($df: DataFrame!, $name: String!) {\n  fromDf(df: $df, name: $name) {\n    ...Table\n  }\n}"


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


class Create_sampleMutationCreatesample(BaseModel):
    """Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure), was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample"""

    typename: Optional[Literal["Sample"]] = Field(alias="__typename")
    id: ID
    name: str
    "The name of the sample"
    creator: Optional[Create_sampleMutationCreatesampleCreator]
    "The user that created the sample"


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


class Get_roiQuery(BaseModel):
    roi: Optional[ROIFragment]
    'Get a single Roi by ID"\n    \n    Returns a single Roi by ID. If the user does not have access\n    to the Roi, an error will be raised.'

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment ROI on ROI {\n  id\n  label\n  vectors {\n    x\n    y\n    t\n    c\n    z\n  }\n  type\n  representation {\n    id\n  }\n  derivedRepresentations {\n    id\n  }\n  creator {\n    email\n    id\n    color\n  }\n}\n\nquery get_roi($id: ID!) {\n  roi(id: $id) {\n    ...ROI\n  }\n}"


class Search_roisQueryRois(ROI, BaseModel):
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


class Search_roisQuery(BaseModel):
    rois: Optional[List[Optional[Search_roisQueryRois]]]
    "All Rois\n    \n    This query returns all Rois that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Rois that the user has access to. If the user is an amdin\n    or superuser, all Rois will be returned."

    class Arguments(BaseModel):
        search: str

    class Meta:
        document = "query search_rois($search: String!) {\n  rois(repname: $search) {\n    label: id\n    value: id\n  }\n}"


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
        lot_number: Optional[str] = None
        serial_number: Optional[str] = None
        model: Optional[str] = None
        manufacturer: Optional[str] = None

    class Meta:
        document = "fragment Instrument on Instrument {\n  id\n  dichroics\n  detectors\n  filters\n  name\n  lotNumber\n  serialNumber\n  manufacturer\n  model\n}\n\nmutation create_instrument($detectors: [GenericScalar], $dichroics: [GenericScalar], $filters: [GenericScalar], $name: String!, $lotNumber: String, $serialNumber: String, $model: String, $manufacturer: String) {\n  createInstrument(\n    detectors: $detectors\n    dichroics: $dichroics\n    filters: $filters\n    name: $name\n    lotNumber: $lotNumber\n    serialNumber: $serialNumber\n    model: $model\n    manufacturer: $manufacturer\n  ) {\n    ...Instrument\n  }\n}"


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
        xarray: ArrayInput
        name: Optional[str] = None
        variety: Optional[RepresentationVarietyInput] = None
        origins: Optional[List[Optional[ID]]] = None
        file_origins: Optional[List[Optional[ID]]] = None
        roi_origins: Optional[List[Optional[ID]]] = None
        tags: Optional[List[Optional[str]]] = None
        sample: Optional[ID] = None
        omero: Optional[OmeroRepresentationInput] = None

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nmutation from_xarray($xarray: XArray!, $name: String, $variety: RepresentationVarietyInput, $origins: [ID], $file_origins: [ID], $roi_origins: [ID], $tags: [String], $sample: ID, $omero: OmeroRepresentationInput) {\n  fromXArray(\n    xarray: $xarray\n    name: $name\n    origins: $origins\n    tags: $tags\n    sample: $sample\n    omero: $omero\n    fileOrigins: $file_origins\n    roiOrigins: $roi_origins\n    variety: $variety\n  ) {\n    ...Representation\n  }\n}"


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
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nmutation update_representation($id: ID!, $tags: [String], $sample: ID, $variety: RepresentationVarietyInput) {\n  updateRepresentation(rep: $id, tags: $tags, sample: $sample, variety: $variety) {\n    ...Representation\n  }\n}"


class Create_metricMutation(BaseModel):
    create_metric: Optional[MetricFragment] = Field(alias="createMetric")
    "Create a metric\n\n    This mutation creates a metric and returns the created metric.\n    "

    class Arguments(BaseModel):
        representation: Optional[ID] = None
        sample: Optional[ID] = None
        experiment: Optional[ID] = None
        key: str
        value: MetricValue

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  representation {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nmutation create_metric($representation: ID, $sample: ID, $experiment: ID, $key: String!, $value: MetricValue!) {\n  createMetric(\n    representation: $representation\n    sample: $sample\n    experiment: $experiment\n    key: $key\n    value: $value\n  ) {\n    ...Metric\n  }\n}"


class Upload_bioimageMutationUploadomerofile(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    id: ID
    file: Optional[File]
    "The file"
    type: OmeroFileType
    "The type of the file"
    name: str
    "The name of the file"


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
    features: Optional[List[Optional[Get_labelQueryLabelforFeatures]]]
    "Features attached to this Label"


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


class Search_thumbnailsQueryThumbnails(BaseModel):
    """A Thumbnail is a render of a representation that is used to display the representation in the UI.

    Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.
    """

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    value: ID
    label: Optional[str]


class Search_thumbnailsQuery(BaseModel):
    thumbnails: Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]
    "All Thumbnails\n    \n    This query returns all Thumbnails that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Thumbnails that the user has access to. If the user is an amdin\n    or superuser, all Thumbnails will be returned.\n    \n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_thumbnails($search: String) {\n  thumbnails(name: $search, limit: 20) {\n    value: id\n    label: image\n  }\n}"


class Image_for_thumbnailQueryImage(BaseModel):
    """A Thumbnail is a render of a representation that is used to display the representation in the UI.

    Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.
    """

    typename: Optional[Literal["Thumbnail"]] = Field(alias="__typename")
    path: Optional[str]
    label: Optional[str]


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
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery get_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


class Expand_tableQuery(BaseModel):
    table: Optional[TableFragment]
    "Get a single representation by ID"

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Table on Table {\n  id\n  name\n  tags\n  store\n  creator {\n    email\n  }\n  sample {\n    id\n  }\n  representation {\n    id\n  }\n  experiment {\n    id\n  }\n}\n\nquery expand_table($id: ID!) {\n  table(id: $id) {\n    ...Table\n  }\n}"


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


class Search_tablesQuery(BaseModel):
    options: Optional[List[Optional[Search_tablesQueryOptions]]]
    "My samples return all of the users samples attached to the current user"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "query search_tables {\n  options: tables {\n    value: id\n    label: name\n  }\n}"


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


class Search_sampleQuery(BaseModel):
    options: Optional[List[Optional[Search_sampleQueryOptions]]]
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
    rois: Optional[List[Optional[ListROIFragment]]]
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


class Expand_featureQuery(BaseModel):
    feature: Optional[FeatureFragment]
    "Get a single feature by ID\n    \n    Returns a single feature by ID. If the user does not have access\n    to the feature, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Feature on Feature {\n  label {\n    instance\n    representation {\n      id\n    }\n  }\n  id\n  key\n  value\n}\n\nquery expand_feature($id: ID!) {\n  feature(id: $id) {\n    ...Feature\n  }\n}"


class RequestQueryRequest(BaseModel):
    typename: Optional[Literal["Credentials"]] = Field(alias="__typename")
    access_key: Optional[str] = Field(alias="accessKey")
    status: Optional[str]
    secret_key: Optional[str] = Field(alias="secretKey")


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
    """Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)"""

    typename: Optional[Literal["Instrument"]] = Field(alias="__typename")
    value: ID
    label: str


class Search_instrumentsQuery(BaseModel):
    options: Optional[List[Optional[Search_instrumentsQueryOptions]]]
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


class Search_experimentQuery(BaseModel):
    options: Optional[List[Optional[Search_experimentQueryOptions]]]
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
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery expand_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


class Get_representationQuery(BaseModel):
    representation: Optional[RepresentationFragment]
    "Get a single Representation by ID\n    \n    Returns a single Representation by ID. If the user does not have access\n    to the Representation, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery get_representation($id: ID!) {\n  representation(id: $id) {\n    ...Representation\n  }\n}"


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


class Search_representationQuery(BaseModel):
    options: Optional[List[Optional[Search_representationQueryOptions]]]
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
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery get_random_rep {\n  randomRepresentation {\n    ...Representation\n  }\n}"


class My_accessiblesQuery(BaseModel):
    accessiblerepresentations: Optional[List[Optional[RepresentationFragment]]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Representation on Representation {\n  sample {\n    id\n    name\n  }\n  id\n  store\n  variety\n  name\n  omero {\n    scale\n    physicalSize {\n      x\n      y\n      z\n      t\n      c\n    }\n  }\n  origins {\n    id\n    store\n    variety\n  }\n}\n\nquery my_accessibles {\n  accessiblerepresentations {\n    ...Representation\n  }\n}"


class Search_tagsQueryOptions(BaseModel):
    typename: Optional[Literal["Tag"]] = Field(alias="__typename")
    value: str
    label: str


class Search_tagsQuery(BaseModel):
    options: Optional[List[Optional[Search_tagsQueryOptions]]]
    "All Tags\n    \n    Returns all Tags that are stored on the platform\n    depending on the user's permissions. Generally, this query will return\n    all Tags that the user has access to. If the user is an amdin\n    or superuser, all Tags will be returned.\n    "

    class Arguments(BaseModel):
        search: Optional[str] = None

    class Meta:
        document = "query search_tags($search: String) {\n  options: tags(name: $search) {\n    value: slug\n    label: name\n  }\n}"


class Expand_metricQuery(BaseModel):
    """Creates a new representation"""

    metric: Optional[MetricFragment]
    "Get a single Metric by ID\n    \n    Returns a single Metric by ID. If the user does not have access\n    to the Metric, an error will be raised.\n    "

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment Metric on Metric {\n  id\n  representation {\n    id\n  }\n  key\n  value\n  creator {\n    id\n  }\n  createdAt\n}\n\nquery expand_metric($id: ID!) {\n  metric(id: $id) {\n    ...Metric\n  }\n}"


class Get_omero_fileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single Omero File by ID\n    \n    Returns a single Omero File by ID. If the user does not have access\n    to the Omero File, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n  type\n}\n\nquery get_omero_file($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Expand_omerofileQuery(BaseModel):
    omerofile: Optional[OmeroFileFragment]
    "Get a single Omero File by ID\n    \n    Returns a single Omero File by ID. If the user does not have access\n    to the Omero File, an error will be raised."

    class Arguments(BaseModel):
        id: ID

    class Meta:
        document = "fragment OmeroFile on OmeroFile {\n  id\n  name\n  file\n  type\n}\n\nquery expand_omerofile($id: ID!) {\n  omerofile(id: $id) {\n    ...OmeroFile\n  }\n}"


class Search_omerofileQueryOptions(BaseModel):
    typename: Optional[Literal["OmeroFile"]] = Field(alias="__typename")
    value: ID
    label: str
    "The name of the file"


class Search_omerofileQuery(BaseModel):
    options: Optional[List[Optional[Search_omerofileQueryOptions]]]
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


async def acreate_thumbnail(
    rep: ID, file: File, major_color: Optional[str] = None, rath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """create_thumbnail


     uploadThumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        rep (ID): rep
        file (File): file
        major_color (Optional[str], optional): major_color.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return (
        await aexecute(
            Create_thumbnailMutation,
            {"rep": rep, "file": file, "major_color": major_color},
            rath=rath,
        )
    ).upload_thumbnail


def create_thumbnail(
    rep: ID, file: File, major_color: Optional[str] = None, rath: MikroRath = None
) -> Optional[ThumbnailFragment]:
    """create_thumbnail


     uploadThumbnail: A Thumbnail is a render of a representation that is used to display the representation in the UI.

        Thumbnails can also store the major color of the representation. This is used to color the representation in the UI.



    Arguments:
        rep (ID): rep
        file (File): file
        major_color (Optional[str], optional): major_color.
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[ThumbnailFragment]"""
    return execute(
        Create_thumbnailMutation,
        {"rep": rep, "file": file, "major_color": major_color},
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
    df: DataFrame, name: str, rath: MikroRath = None
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


     fromDf:  A Table is a collection of tabular data.

        It provides a way to store data in a tabular format and associate it with a Representation,
        Sample or Experiment. It is a way to store data that might be to large to store in a
        Feature or Metric on this Experiments. Or it might be data that is not easily represented
        as a Feature or Metric.

        Tables can be easily created from a pandas DataFrame and can be converted to a pandas DataFrame.
        Its columns are defined by the columns of the DataFrame.





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
    search: str, rath: MikroRath = None
) -> Optional[List[Optional[Search_roisQueryRois]]]:
    """search_rois


     rois: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




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


     rois: A ROI is a region of interest in a representation.

        This region is to be regarded as a view on the representation. Depending
        on the implementatoin (type) of the ROI, the view can be constructed
        differently. For example, a rectangular ROI can be constructed by cropping
        the representation according to its 2 vectors. while a polygonal ROI can be constructed by masking the
        representation with the polygon.

        The ROI can also store a name and a description. This is used to display the ROI in the UI.




    Arguments:
        search (str): search
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[List[Optional[Search_roisQueryRois]]]"""
    return execute(Search_roisQuery, {"search": search}, rath=rath).rois


async def acreate_feature(
    label: ID,
    value: FeatureValue,
    key: Optional[str] = None,
    creator: Optional[ID] = None,
    rath: MikroRath = None,
) -> Optional[Create_featureMutationCreatefeature]:
    """create_feature


     createfeature:  A Feature is a numerical key value pair that is attached to a Label.

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


     createfeature:  A Feature is a numerical key value pair that is attached to a Label.

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
    lot_number: Optional[str] = None,
    serial_number: Optional[str] = None,
    model: Optional[str] = None,
    manufacturer: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[InstrumentFragment]:
    """create_instrument


     createInstrument: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        name (str): name
        detectors (Optional[List[Optional[Dict]]], optional): detectors.
        dichroics (Optional[List[Optional[Dict]]], optional): dichroics.
        filters (Optional[List[Optional[Dict]]], optional): filters.
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
    lot_number: Optional[str] = None,
    serial_number: Optional[str] = None,
    model: Optional[str] = None,
    manufacturer: Optional[str] = None,
    rath: MikroRath = None,
) -> Optional[InstrumentFragment]:
    """create_instrument


     createInstrument: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        name (str): name
        detectors (Optional[List[Optional[Dict]]], optional): detectors.
        dichroics (Optional[List[Optional[Dict]]], optional): dichroics.
        filters (Optional[List[Optional[Dict]]], optional): filters.
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
    xarray: ArrayInput,
    name: Optional[str] = None,
    variety: Optional[RepresentationVarietyInput] = None,
    origins: Optional[List[Optional[ID]]] = None,
    file_origins: Optional[List[Optional[ID]]] = None,
    roi_origins: Optional[List[Optional[ID]]] = None,
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
        file_origins (Optional[List[Optional[ID]]], optional): file_origins.
        roi_origins (Optional[List[Optional[ID]]], optional): roi_origins.
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
                "file_origins": file_origins,
                "roi_origins": roi_origins,
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
    file_origins: Optional[List[Optional[ID]]] = None,
    roi_origins: Optional[List[Optional[ID]]] = None,
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
        file_origins (Optional[List[Optional[ID]]], optional): file_origins.
        roi_origins (Optional[List[Optional[ID]]], optional): roi_origins.
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
            "file_origins": file_origins,
            "roi_origins": roi_origins,
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
) -> Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]:
    """search_thumbnails


     thumbnails: A Thumbnail is a render of a representation that is used to display the representation in the UI.

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
) -> Optional[List[Optional[Search_thumbnailsQueryThumbnails]]]:
    """search_thumbnails


     thumbnails: A Thumbnail is a render of a representation that is used to display the representation in the UI.

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


async def aexpand_feature(id: ID, rath: MikroRath = None) -> Optional[FeatureFragment]:
    """expand_feature


     feature:  A Feature is a numerical key value pair that is attached to a Label.

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


     feature:  A Feature is a numerical key value pair that is attached to a Label.

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


     instrument: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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


     instrument: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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


     instrument: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


    Arguments:
        id (ID): id
        rath (mikro.rath.MikroRath, optional): The mikro rath client

    Returns:
        Optional[InstrumentFragment]"""
    return (await aexecute(Expand_instrumentQuery, {"id": id}, rath=rath)).instrument


def expand_instrument(id: ID, rath: MikroRath = None) -> Optional[InstrumentFragment]:
    """expand_instrument


     instrument: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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


     options: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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


     options: Instrument(id, name, detectors, dichroics, filters, lot_number, manufacturer, model, serial_number)


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
