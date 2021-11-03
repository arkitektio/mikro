from herre.access.object import GraphQLObject
from mikro.graphql.mutations.experiment import CREATE_EXPERIMENT
from mikro.graphql.mutations.representation import (
    CREATE_REPRESENTATION,
    UPDATE_REPRESENTATION,
)
from mikro.graphql.queries.sample import GET_SAMPLE
from mikro.graphql.mutations.sample import CREATE_SAMPLE
from mikro.array import Array
from mikro.manager import AsyncRepresentationManager, SyncRepresentationManager
from typing import Any, List, Optional
from herre.convenience import GraphQLModel
import xarray as xr
from typing import ForwardRef
from enum import Enum
from mikro.ward import MikroWard
from mikro.graphql.queries.experiment import GET_EXPERIMENT
from mikro.graphql.queries.representation import GET_REPRESENTATION
from mikro.widgets import MY_TOP_REPRESENTATIONS

Representation = ForwardRef("Representation")
Sample = ForwardRef("Sample")
Experiment = ForwardRef("Experiment")


class RepresentationVariety(str, Enum):
    VOXEL = "VOXEL"
    MASK = "MASK"
    UNKNOWN = "UNKNOWN"


class RepresentationMetric(GraphQLModel):
    key: Optional[str]
    value: Optional[Any]

    class Meta:
        identifier = "representationmetric"
        ward = "mikro"


class Sample(GraphQLModel):
    name: Optional[str]
    meta: Optional[dict]
    representations: Optional[List[Representation]]
    experiments: Optional[List[Experiment]]
    name: Optional[str]

    class Meta:
        identifier = "sample"
        ward = "mikro"
        create = CREATE_SAMPLE
        get = GET_SAMPLE


class Experiment(GraphQLModel):
    meta: Optional[dict]
    id: Optional[int]
    name: Optional[str]
    description: Optional[str]
    descriptionLong: Optional[str]
    samples: Optional[List[Sample]]

    class Meta:
        identifier = "experiment"
        ward = "mikro"
        get = GET_EXPERIMENT
        create = CREATE_EXPERIMENT


class Plane(GraphQLObject):
    zIndex: Optional[int] = 0
    yIndex: Optional[int] = 0
    xIndex: Optional[int] = 0
    cIndex: Optional[int] = 0
    tIndex: Optional[int] = 0
    exposureTime: Optional[float] = 0
    deltaT: Optional[float] = 0


class PhysicalSize(GraphQLObject):
    x: Optional[float] = 1
    y: Optional[float] = 1
    z: Optional[float] = 1
    t: Optional[float] = 1


class Channel(GraphQLObject):
    name: Optional[str] = "Test"
    emmissionWavelength: Optional[float] = 0
    excitationWavelength: Optional[float] = 0
    acquisitionMode: Optional[str] = "Standard"
    color: Optional[str] = "rgb(244,255,232)"


class OmeroRepresentation(GraphQLObject):
    physicalSize: Optional[PhysicalSize]
    channels: Optional[List[Channel]]
    planes: Optional[List[Plane]]


class Representation(GraphQLModel, Array):
    """Representation

    A Representation is a Five Dimensional Array that lets you access data

    Args:
        GraphQLStructure ([type]): [description]
    """

    omero: Optional[OmeroRepresentation]
    meta: Optional[dict]
    name: Optional[str]
    package: Optional[str]
    store: Optional[str]
    shape: Optional[List[int]]
    image: Optional[str]
    unique: Optional[str]
    variety: Optional[RepresentationVariety]
    sample: Optional[Sample]
    tags: Optional[List[str]]
    metrics: Optional[List[RepresentationMetric]]
    thumbnail: Optional[str]

    asyncs = AsyncRepresentationManager()
    objects = SyncRepresentationManager()

    class Meta:
        identifier = "representation"
        ward = "mikro"
        get = GET_REPRESENTATION
        create = CREATE_REPRESENTATION
        update = UPDATE_REPRESENTATION
        default_widget = MY_TOP_REPRESENTATIONS


class Render(GraphQLModel):
    representation: Optional[Representation]

    class Meta:
        identifier = "render"
        ward = "mikro"


class Table(GraphQLModel):
    id: Optional[int]
    name: Optional[str]
    columns: Optional[List[str]]
    query: Optional[List[List[Any]]]

    class Meta:
        identifier = "table"
        ward = "mikro"


Representation.update_forward_refs()
Sample.update_forward_refs()
Experiment.update_forward_refs()
