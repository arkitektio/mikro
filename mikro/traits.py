from typing import Optional
import xarray as xr
import pandas as pd


class Representation:
    def get_identifier():
        return "representation"

    async def shrink(self):
        return self.id

    @property
    def data(self) -> xr.DataArray:
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
