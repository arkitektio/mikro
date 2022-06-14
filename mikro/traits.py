"""
Traits for Mikro.

Traits are mixins that are added to every graphql type that exists on the mikro schema.
We use them to add functionality to the graphql types that extend from the base type.

Every GraphQL Model on Mikro gets a identifier and shrinking methods to ensure the compatibliity
with arkitekt. This is done by adding the identifier and the shrinking methods to the graphql type.
If you want to add your own traits to the graphql type, you can do so by adding them in the graphql
.config.yaml file.

"""

from typing import List, TypeVar
import numpy as np
from pydantic import BaseModel
import xarray as xr
import pandas as pd

from rath.links.shrink import ShrinkByID


class Representation(BaseModel, ShrinkByID):
    """Representation Trait

    Implements both identifier and shrinking methods.
    Also Implements the data attribute

    Attributes:
        data (xarray.Dataset): The data of the representation.

    """

    id: str

    @property
    def data(self) -> xr.DataArray:
        """The Data of the Representation as an xr.DataArray

        Returns:
            xr.DataArray: The associated object.

        Raises:
            AssertionError: If the representation has no store attribute quries
        """
        pstore = getattr(self, "store", None)
        assert (
            pstore is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

        return pstore.open()

    @property
    def adata(self) -> xr.DataArray:
        """The Data of the Representation as an xr.DataArray

        Returns:
            xr.DataArray: The associated object.

        Raises:
            AssertionError: If the representation has no store attribute quries
        """
        pstore = getattr(self, "store", None)
        assert (
            pstore is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

        return pstore.aopen()


class ROI(BaseModel, ShrinkByID):
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
        return np.array([[v.x, v.y, v.z] for v in vector_list])


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
        pstore = getattr(self, "parquet", None)
        assert (
            pstore is not None
        ), "Please query 'parquet' in your request on 'Table'. Data is not accessible otherwise"
        return pstore.df


T = TypeVar("T", bound="BaseModel")


class Vectorizable:
    @classmethod
    def list_from_numpyarray(cls: T, x: np.ndarray) -> List[T]:
        """Creates a list of InputVector from a numpya array

        Args:
            vector_list (List[List[float]]): A list of lists of floats

        Returns:
            List[Vectorizable]: A list of InputVector
        """
        assert x.ndim == 2, "Needs to be a List array of vectors"
        if x.shape[1] == 3:
            return [cls(x=i[0], y=i[1], z=i[2]) for i in x.tolist()]
        elif x.shape[1] == 2:
            return [cls(x=i[0], y=i[1]) for i in x.tolist()]
        else:
            raise NotImplementedError(
                f"Incompatible shape {x.shape} of {x}. List dimension needs to either be of size 2 or 3"
            )
