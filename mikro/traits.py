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
from typing import Awaitable, List, TypeVar, Tuple
import numpy as np
from pydantic import BaseModel
import xarray as xr
import pandas as pd

from rath.links.shrink import ShrinkByID


class Representation(BaseModel):
    """Representation Trait

    Implements both identifier and shrinking methods.
    Also Implements the data attribute

    Attributes:
        data (xarray.Dataset): The data of the representation.

    """

    id: str

    def get_identifier():
        return "@mikro/representation"

    @property
    def data(self) -> xr.DataArray:
        """The Data of the Representation as an xr.DataArray. Not accessible from asyncio

        Returns:
            xr.DataArray: The associated object.

        Raises:
            AssertionError: If the representation has no store attribute quries
        """
        try:
            get_running_loop()
        except RuntimeError:
            pstore = getattr(self, "store", None)
            assert (
                pstore is not None
            ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

            return pstore.open()

        raise RuntimeError(
            "This method is not available when running in an event loop . Please use adata to retreive a future to your data."
        )

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


class Stage:
    pass


class Objective:
    """Additional Methods for ROI"""

    def calculate_physical(self, stage: Stage, t: int = 1, c: int = 1):
        """Calculate the new physical values of the ROI

        Args:
            new_physical (dict): The new physical values of the ROI
        """
        from mikro.api.schema import PhysicalSizeInput

        if not hasattr(self, "magnification"):
            raise AttributeError(
                "Objective has no magnification attribute. Please query 'magnification' in your request on 'Objective'."
            )

        if not hasattr(stage, "physical_size"):
            raise AttributeError(
                "Stage has no physical_size attribute. Please query 'physicalSize' in your request on 'Stage'"
            )

        return PhysicalSizeInput(
            x=stage.physical_size[0] / self.magnification,
            y=stage.physical_size[1] / self.magnification,
            z=stage.physical_size[2] / self.magnification,
            c=c,
            t=t,
        )


class ROI(BaseModel):
    """Additional Methods for ROI"""

    @property
    def vector_data(self) -> np.ndarray:
        """A numpy array of the vectors of the ROI

        Returns:
            np.ndarray: _description_
        """
        vector_list = getattr(self, "vectors", None)
        assert (
            vector_list
        ), "Please query 'vectors' in your request on 'ROI'. Data is not accessible otherwise"
        vector_list: list
        return np.array([[v.x, v.y] for v in vector_list])


class Table(BaseModel, ShrinkByID):
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


T = TypeVar("T", bound="BaseModel")


class Vectorizable:
    """Mixin for Vectorizable data
    adds functionality to convert a numpy array to a list of vectors
    """

    @classmethod
    def list_from_numpyarray(cls: T, x: np.ndarray, t=None, c=None, z=None) -> List[T]:
        """Creates a list of InputVector from a numpya array

        Args:
            vector_list (List[List[float]]): A list of lists of floats

        Returns:
            List[Vectorizable]: A list of InputVector
        """
        assert x.ndim == 2, "Needs to be a List array of vectors"
        if x.shape[1] == 4:
            return [cls(x=i[0], y=i[1], z=i[2], t=i[3], c=c) for i in x.tolist()]
        if x.shape[1] == 3:
            return [cls(x=i[0], y=i[1], z=i[2], t=t, c=c) for i in x.tolist()]
        elif x.shape[1] == 2:
            return [cls(x=i[0], y=i[1], t=t, c=c, z=z) for i in x.tolist()]
        else:
            raise NotImplementedError(
                f"Incompatible shape {x.shape} of {x}. List dimension needs to either be of size 2 or 3"
            )
