import xarray
import pyarrow.parquet as pq
from pyarrow import Table as ArrowTable
import pandas as pd


class Parquet:
    @property
    def data(self) -> pd.DataFrame:
        assert (
            self.store is not None
        ), "Please query 'store' in your request on 'Table'. Data is not accessible otherwise"
        s3_path = f"parquet/{self.store}"
        return (
            pq.ParquetDataset(s3_path, filesystem=self._getFileSystem())
            .read_pandas()
            .to_pandas()
        )

    def save_df(self, df: pd.DataFrame):
        table: ArrowTable = ArrowTable.from_pandas(df)
        s3_path = f"parquet/{self.store}"
        pq.write_table(table, s3_path, filesystem=self._getFileSystem())
