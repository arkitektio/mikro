from mikro.datalayer import DataLayer
import xarray as xr
import zarr


class LocalDataLayer(DataLayer):
    directory: str = "data"

    def _storedataset(self, dataset: xr.Dataset, path):
        store = self.open_store(path)
        dataset.to_zarr(store=store, consolidated=True, compute=True)
        return path

    def _storetable(self, table, path):
        import pyarrow.parquet as pq

        s3_path = f"s3://parquet/{path}"
        pq.write_table(table, s3_path, filesystem=self.fs)
        return path

    def open_store(self, path):
        return zarr.DirectoryStore(f"{self.directory}/{path}")

    @property
    def fs(self):
        assert (
            self._s3fs is not None
        ), "Filesystem is not connected yet, please make sure to connect first"
        return self._s3fs

    async def aget_credentials(self, id=None):
        from mikro.api.schema import arequest

        c = await arequest()
        self.access_key = c.access_key
        self.secret_key = c.secret_key
        self.session_token = c.session_token

    async def aconnect(self):
        """Connect to the S3 instance"""
        self._connected = True

        self._s3fs = zarr.DirectoryStore("data")

        return self
