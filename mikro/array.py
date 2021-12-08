from fakts import config
from mikro.ward import MikroWard
from herre.wards.registry import get_ward_registry
import os
import s3fs
import xarray as xr


class RepresentationException(Exception):
    pass


class Array:
    def _getZarrStore(self):
        ward: MikroWard = get_ward_registry().get_ward_instance("mikro")
        transcript = ward.transcript
        protocol = "https" if ward.config.s3.secure else "http"
        endpoint_url = f"{protocol}://{ward.config.s3.host}:{ward.config.s3.port}"

        os.environ["AWS_ACCESS_KEY_ID"] = transcript.params.access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = transcript.params.secret_key

        s3_path = f"zarr/{self.store}"
        store = s3fs.S3FileSystem(client_kwargs={"endpoint_url": endpoint_url})
        return store.get_mapper(s3_path)

    @property
    def data(self) -> xr.DataArray:
        assert (
            self.store is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"
        return xr.open_zarr(store=self._getZarrStore(), consolidated=True)["data"]

    def save_array(self, array: xr.DataArray, compute=True, chunks=None):
        apiversion = "0.1"
        fileversion = "0.1"

        if "x" not in array.dims:
            raise RepresentationException(
                "Representations must always have a 'x' Dimension"
            )

        if "y" not in array.dims:
            raise RepresentationException(
                "Representations must always have a 'y' Dimension"
            )

        if "t" not in array.dims:
            array = array.expand_dims("t")
        if "c" not in array.dims:
            array = array.expand_dims("c")
        if "z" not in array.dims:
            array = array.expand_dims("z")

        chunks = chunks or {
            "t": 1,
            "x": array.sizes["x"],
            "y": array.sizes["y"],
            "z": 1,
        }

        array = array.chunk(
            {key: chunksize for key, chunksize in chunks.items() if key in array.dims}
        )
        if apiversion == "0.1":
            dataset = array.to_dataset(name="data")
            dataset.attrs["apiversion"] = apiversion
            dataset.attrs["fileversion"] = fileversion
            if fileversion == "0.1":
                dataset.attrs["model"] = str(self.Meta.identifier)
                dataset.attrs["unique"] = str(self.unique)
            else:
                raise NotImplementedError(
                    "This FileVersion has not been Implemented yet"
                )
        else:
            raise NotImplementedError("This API Version has not been Implemented Yet")

        return dataset.to_zarr(
            store=self._getZarrStore(), consolidated=True, compute=compute
        )
