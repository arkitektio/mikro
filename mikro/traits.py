"""
Traits for Mikro.

Traits are mixins that are added to every graphql type that exists on the mikro schema.
We use them to add functionality to the graphql types that extend from the base type.

Every GraphQL Model on Mikro gets a identifier and shrinking methods to ensure the compatibliity
with arkitekt. This is done by adding the identifier and the shrinking methods to the graphql type.
If you want to add your own traits to the graphql type, you can do so by adding them in the graphql
.config.yaml file.

"""

import xarray as xr
import pandas as pd


class Representation:
    """Representation Trait

    Implements both identifier and shrinking methods.
    Also Implements the data attribute

    Attributes:
        data (xarray.Dataset): The data of the representation.

    """

    def get_identifier():
        return "representation"

    async def shrink(self):
        return self.id

    @property
    def data(self) -> xr.DataArray:
        """The Data of the Representation as an xr.DataArray

        Returns:
            xr.DataArray: The associated object.

        Raises:
            AssertionError: If the representation has no store attribute quries
        """
        assert (
            self.store is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

        return self.store.open()


class Experiment:
    def get_identifier():
        return "experiment"

    async def shrink(self):
        return self.id


class Sample:
    def get_identifier():
        return "sample"

    async def shrink(self):
        return self.id


class Table:
    """Table Trait

    Implements both identifier and shrinking methods.
    Also Implements the data attribute

    Attributes:
        data (pd.DataFrame): The data of the table.

    """

    @property
    def data(self) -> pd.DataFrame:
        assert (
            self.parquet is not None
        ), "Please query 'parquet' in your request on 'Table'. Data is not accessible otherwise"
        return self.parquet.df

    def get_identifier():
        return "table"


class Thumbnail:
    def get_identifier():
        return "thumbnail"


class OmeroFile:
    def get_identifier():
        return "omerofile"
