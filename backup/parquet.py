from mikro.ward import MikroWard
from herre.wards.registry import get_ward_registry
import os
import s3fs
import xarray as xr
import pyarrow.parquet as pq
from pyarrow import Table as ArrowTable
import pandas as pd


class Parquet:
    def _getFileSystem(self):
        ward: MikroWard = get_ward_registry().get_ward_instance("mikro")
        transcript = ward.transcript
        protocol = "https" if ward.config.s3.secure else "http"
        endpoint_url = f"{protocol}://{ward.config.s3.host}:{ward.config.s3.port}"

        os.environ["AWS_ACCESS_KEY_ID"] = transcript.params.access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = transcript.params.secret_key

        s3_path = f"parquet/{self.store}"
        s3 = s3fs.S3FileSystem(client_kwargs={"endpoint_url": endpoint_url})
        return s3

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
