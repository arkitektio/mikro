"""
Traits for Mikro.

Traits are mixins that are added to every graphql type that exists on the mikro schema.
We use them to add functionality to the graphql types that extend from the base type.

Every GraphQL Model on Mikro gets a identifier and shrinking methods to ensure the compatibliity
with arkitekt. This is done by adding the identifier and the shrinking methods to the graphql type.
If you want to add your own traits to the graphql type, you can do so by adding them in the graphql
.config.yaml file.

"""

from typing import List
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

    @classmethod
    def get_identifier(cls):
        return "representation"

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


class Experiment(BaseModel, ShrinkByID):
    id: str

    @classmethod
    def get_identifier(cls):
        return "experiment"


class ROI(BaseModel, ShrinkByID):
    """Additional Methods for ROI"""

    id: str

    @classmethod
    def get_identifier(cls):
        """THis classes identifier on the platform"""
        return "roi"

    async def ashrink(self):
        """Shrinks this to a unique identifier on
        the mikro server

        Returns:
            str: The unique identifier
        """
        return self.id

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


class Sample(BaseModel, ShrinkByID):
    id: str

    @classmethod
    def get_identifier(cls):
        return "sample"


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

    @classmethod
    def get_identifier(cls):
        return "table"


class Thumbnail(BaseModel, ShrinkByID):
    id: str

    @classmethod
    def get_identifier(cls):
        return "thumbnail"


class OmeroFile(BaseModel, ShrinkByID):
    id: str

    @classmethod
    def get_identifier(cls):
        return "omerofile"
