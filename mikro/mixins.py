import xarray as xr
import pandas as pd
from mikro.scalars import Store
from mikro.scalars import Parquet


class RepresentationException(Exception):
    pass


class Array:
    store: Store

    @property
    def data(self) -> xr.DataArray:
        assert (
            self.store is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"

        return self.store.open()


class DataFrame:
    parquet: Parquet

    @property
    def data(self) -> pd.DataFrame:
        assert (
            self.parquet is not None
        ), "Please query 'parquet' in your request on 'Table'. Data is not accessible otherwise"
        return self.parquet.df
