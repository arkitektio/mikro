"""
Traits for Mikro.

Traits are mixins that are added to every graphql type that exists on the mikro schema.
We use them to add functionality to the graphql types that extend from the base type.

Every GraphQL Model on Mikro gets a identifier and shrinking methods to ensure the compatibliity
with arkitekt. This is done by adding the identifier and the shrinking methods to the graphql type.
If you want to add your own traits to the graphql type, you can do so by adding them in the graphql
.config.yaml file.

"""

from asyncio import get_running_loop
from typing import Awaitable, List, TypeVar, Tuple, Protocol, Optional
import numpy as np
from pydantic import BaseModel
import xarray as xr
import pandas as pd
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from mikro.api.schema import InputVector
    from mikro.api.schema import PhysicalSizeInput


class Representation(BaseModel):
    """Representation Trait

    Implements both identifier and shrinking methods.
    Also Implements the data attribute

    Attributes:
        data (xarray.Dataset): The data of the representation.

    """

    @classmethod
    def get_identifier(cls) -> str:
        return "@mikro/representation"

    @property
    def data(self) -> xr.DataArray:
        """The Data of the Representation as an xr.DataArray

        Will be of shape [c,t,z,y,x]


        Attention: Not accessible from asyncio

        Returns:
            xr.DataArray: The associated object.

        Raises:
            AssertionError: If the representation has no store attribute quries
        """
        pstore = getattr(self, "store", None)
        assert (
            pstore is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

        return pstore.open(cached=False)

    @property
    def cached_data(self) -> xr.DataArray:
        """The Data of the Representation as an xr.DataArray

        Will be of shape [c,t,z,y,x]


        Attention: Not accessible from asyncio

        Returns:
            xr.DataArray: The associated object.

        Raises:
            AssertionError: If the representation has no store attribute quries
        """
        pstore = getattr(self, "store", None)
        assert (
            pstore is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

        return pstore.open(cached=False)

    async def adata(self) -> Awaitable[xr.DataArray]:
        """The Data of the Representation as an xr.DataArray. Accessible from asyncio.

        Returns:
            xr.DataArray: The associated object.

        Raises:
            AssertionError: If the representation has no store attribute quries
        """
        pstore = getattr(self, "store", None)
        assert (
            pstore is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

        return await pstore.aopen()

    def _repr_html_(self):
        return (
            f'<h3>{getattr(self, "name", "No name queried")}</h3>'
            + (
                self.omero._repr_html_()
                if hasattr(self, "omero") and self.omero != None
                else "No metadata<br/>"
            )
            + (self.data._repr_html_() if hasattr(self, "store") else "No data queried")
        )


class Omero(BaseModel):
    def _repr_html_(self):
        return f"""<div>
        OMERO
        <table>
            {f'<tr><td>Position</td><td>{self.position._repr_html_inline_()}</tr>' if getattr(self, "position", None) else  ''}
            {f'<tr><td>PhysicalSize</td><td>{self.physical_size}</tr>' if getattr(self, "physical_size", None) else ''}
            {f'<tr><td>Objective</td><td>{self.objective.id}</tr>' if getattr(self, "objective", None) else ''}
        </table>
         </div>"""


class Position:
    pass

    def _repr_html_inline_(self):
        return f"""X={getattr(self, "x", "No x queried")} Y={getattr(self, "y", "No y queried")} Z={getattr(self, "z", "No z queried")}"""

    def _repr_html_(self):
        return f"""<div>
        <h4>Position</h4>
        <table>
            {f'<tr><td>Stage</td><td>{self.stage.id}</tr>' if getattr(self, "stage", None) else  ''}
        </table>
            </div>"""


class Stage:
    pass


class Objective:
    """Additional Methods for ROI"""

    def calculate_physical(
        self, stage: Stage, t: int = 1, c: int = 1
    ) -> "PhysicalSizeInput":
        """Calculate the new physical values of the ROI

        Args:
            new_physical (dict): The new physical values of the ROI
        """
        from mikro.api.schema import PhysicalSizeInput

        if not hasattr(self, "magnification"):
            raise AttributeError(
                "Objective has no magnification attribute. Please query 'magnification' in your request on 'Objective'."
            )

        if not hasattr(stage, "stage_size"):
            raise AttributeError(
                "Stage has no stage_size attribute. Please query 'stageSize' in your request on 'Stage'"
            )

        return PhysicalSizeInput(
            x=stage.stage_size.x / self.magnification,
            y=stage.stage_size.y / self.magnification,
            z=stage.stage_size.z / self.magnification,
            c=c,
            t=t,
        )


class PhysicalSizeProtocol(Protocol):
    """A Protocol for Vectorizable data

    Attributes:
        x (float): The x value
        y (float): The y value
        z (float): The z value
        t (float): The t value
        c (float): The c value
    """

    x: float
    y: float
    z: float
    t: float
    c: float

    def __call__(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        z: Optional[int] = None,
        t: Optional[int] = None,
        c: Optional[int] = None,
    ):
        ...


class PhysicalSize:
    """Additional Methods for PhysicalSize"""

    def is_similar(
        self: PhysicalSizeProtocol,
        other: PhysicalSizeProtocol,
        tolerance=0.02,
        raise_exception=False,
    ) -> bool:
        if hasattr(self, "x") and self.x is not None and other.x is not None:
            if abs(other.x - self.x) > tolerance:
                if raise_exception:
                    raise ValueError(
                        f"X values are not similar: {self.x} vs {other.x} is above tolerance {tolerance}"
                    )
                return False
        if hasattr(self, "y") and self.y is not None and other.y is not None:
            if abs(other.y - self.y) > tolerance:
                if raise_exception:
                    raise ValueError(
                        f"Y values are not similar: {self.y} vs {other.y} is above tolerance {tolerance}"
                    )
                return False
        if hasattr(self, "z") and self.z is not None and other.z is not None:
            if abs(other.z - self.z) > tolerance:
                if raise_exception:
                    raise ValueError(
                        f"Z values are not similar: {self.z} vs {other.z} is above tolerance {tolerance}"
                    )
                return False
        if hasattr(self, "t") and self.t is not None and other.t is not None:
            if abs(other.t - self.t) > tolerance:
                if raise_exception:
                    raise ValueError(
                        f"T values are not similar: {self.t} vs {other.t} is above tolerance {tolerance}"
                    )
                return False
        if hasattr(self, "c") and self.c is not None and other.c is not None:
            if abs(other.c - self.c) > tolerance:
                if raise_exception:
                    raise ValueError(
                        f"C values are not similar: {self.c} vs {other.c} is above tolerance {tolerance}"
                    )
                return False

        return True

    def to_scale(self):
        return [
            getattr(self, "t", 1) or 1,
            getattr(self, "c", 1) or 1,
            getattr(self, "z", 1) or 1,
            getattr(self, "y", 1) or 1,
            getattr(self, "x", 1) or 1,
        ]


class ROI(BaseModel):
    """Additional Methods for ROI"""

    @property
    def vector_data(self) -> np.ndarray:
        """A numpy array of the vectors of the ROI

        Returns:
            np.ndarray: _description_
        """
        return self.get_vector_data(dims="yx")

    def get_vector_data(self, dims="yx") -> np.ndarray:
        vector_list = getattr(self, "vectors", None)
        assert (
            vector_list
        ), "Please query 'vectors' in your request on 'ROI'. Data is not accessible otherwise"
        vector_list: list
        accesors = list(dims)
        return np.array([[getattr(v, ac) for ac in accesors] for v in vector_list])

    def get_vector_pandas(self, dims="yx") -> pd.DataFrame:
        vector_list = getattr(self, "vectors", None)
        assert (
            vector_list
        ), "Please query 'vectors' in your request on 'ROI'. Data is not accessible otherwise"
        vector_list: list
        accesors = list(dims)

        return pd.DataFrame.from_records(
            [[getattr(v, ac) for ac in accesors] for v in vector_list], columns=accesors
        )

    def center(self) -> "InputVector":
        """The center of the ROI

        Caluclates the geometrical center of the ROI according to its type
        and the vectors of the ROI.

        Returns:
            InputVector: The center of the ROI
        """
        from mikro.api.schema import RoiTypeInput, InputVector

        assert hasattr(
            self, "type"
        ), "Please query 'type' in your request on 'ROI'. Center is not accessible otherwise"
        if self.type == RoiTypeInput.RECTANGLE:
            return InputVector.from_array(
                self.get_vector_data(dims="ctzyx").mean(axis=0)
            )

        raise NotImplementedError(
            f"Center calculation not implemented for this ROI type {self.type}"
        )

    def center_as_array(self) -> np.ndarray:
        """The center of the ROI

        Caluclates the geometrical center of the ROI according to its type
        and the vectors of the ROI.

        Returns:
            InputVector: The center of the ROI
        """
        from mikro.api.schema import RoiTypeInput, InputVector

        assert hasattr(
            self, "type"
        ), "Please query 'type' in your request on 'ROI'. Center is not accessible otherwise"
        if self.type == RoiTypeInput.RECTANGLE:
            return self.get_vector_data(dims="ctzyx").mean(axis=0)
        if self.type == RoiTypeInput.POINT:
            return self.get_vector_data(dims="ctzyx")[0]

        raise NotImplementedError(
            f"Center calculation not implemented for this ROI type {self.type}"
        )


class Table(BaseModel):
    """Table Trait

    Implements both identifier and shrinking methods.
    Also Implements the data attribute

    Attributes:
        data (pd.DataFrame): The data of the table.

    """

    @property
    def data(self) -> pd.DataFrame:
        """The data of this table as a pandas dataframe

        Returns:
            pd.DataFrame: The Dataframe
        """
        pstore = getattr(self, "store", None)
        assert (
            pstore is not None
        ), "Please query 'parquet' in your request on 'Table'. Data is not accessible otherwise"
        return pstore.open()


V = TypeVar("V")


class Vector(Protocol):
    """A Protocol for Vectorizable data

    Attributes:
        x (float): The x value
        y (float): The y value
        z (float): The z value
        t (float): The t value
        c (float): The c value
    """

    x: float
    y: float
    z: float
    t: float
    c: float

    def __call__(
        self: V,
        x: Optional[int] = None,
        y: Optional[int] = None,
        z: Optional[int] = None,
        t: Optional[int] = None,
        c: Optional[int] = None,
    ) -> V:
        ...


T = TypeVar("T", bound=Vector)


class Vectorizable:
    """Mixin for Vectorizable data
    adds functionality to convert a numpy array to a list of vectors
    """

    @classmethod
    def list_from_numpyarray(
        cls: T,
        x: np.ndarray,
        t: Optional[int] = None,
        c: Optional[int] = None,
        z: Optional[int] = None,
    ) -> List[Vector]:
        """Creates a list of InputVector from a numpya array

        Args:
            vector_list (List[List[float]]): A list of lists of floats

        Returns:
            List[Vectorizable]: A list of InputVector
        """
        assert x.ndim == 2, "Needs to be a List array of vectors"
        if x.shape[1] == 4:
            return [cls(x=i[1], y=i[0], z=i[2], t=i[3], c=c) for i in x.tolist()]
        if x.shape[1] == 3:
            return [cls(x=i[1], y=i[0], z=i[2], t=t, c=c) for i in x.tolist()]
        elif x.shape[1] == 2:
            return [cls(x=i[1], y=i[0], t=t, c=c, z=z) for i in x.tolist()]
        else:
            raise NotImplementedError(
                f"Incompatible shape {x.shape} of {x}. List dimension needs to either be of size 2 or 3"
            )

    @classmethod
    def from_array(
        cls: T,
        x: np.ndarray,
    ) -> Vector:
        return cls(x=x[4], y=x[3], z=x[2], t=x[1], c=x[0])
