"""A smoke test that the client, the datalayer and the array upload all work."""

import numpy as np
import pytest
import xarray as xr

from mikro_next.api.schema import create_array_dataset

from .conftest import DeployedMikro


@pytest.mark.integration
def test_create_array(deployed_app: DeployedMikro) -> None:
    """Upload an array and read the same shape back out of its Zarr store.

    Round-tripping the pixels is what makes this a real check of the wiring:
    the mutation, the upload middleware and the object store all have to be
    working for ``level_data`` to return anything at all.
    """
    dataset = create_array_dataset(
        data=xr.DataArray(np.zeros((10, 256, 256)), dims=["z", "y", "x"]),
        scales=[],
        name="initialization_volume",
        axes=["z", "y", "x"],
    )

    assert dataset.id, "Dataset should have an ID"
    assert dataset.level_data().shape == (10, 256, 256), (
        "The stored array should have the shape it was uploaded with"
    )
