from herre.wards.registry import get_ward_registry
import xarray as xr

from mikro.scalars import Store


class RepresentationException(Exception):
    pass


class Array:
    store: Store

    def _getZarrStore(self):
        ward = get_ward_registry().get_ward_instance("mikro")
        s3_path = f"{self.store}"
        return ward.s3fs.get_mapper(s3_path)

    @property
    def data(self) -> xr.DataArray:
        assert (
            self.store is not None
        ), "Please query 'store' in your request on 'Representation'. Data is not accessible otherwise"
        return self.store.store

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
