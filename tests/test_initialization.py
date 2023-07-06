from mikro import Mikro
from mikro.datalayer import DataLayer
from mikro.testing.datalayer import LocalDataLayer
from mikro.rath import MikroRath, MikroLinkComposition, AuthTokenLink, SplitLink
from rath.links.testing.mock import AsyncMockLink
from mikro.api.schema import from_xarray, RepresentationVariety
import xarray as xr
import numpy as np


async def aget_token():
    return "XXXX"


async def mock_request(operation):
    return {
        "accessKey": "XXXX",
        "status": "PENDING",
        "secretKey": "XXXX",
        "sessionToken": "XXXX",
    }


async def mock_from_xarray(operation):
    return {
        "id": 1,
        "name": "test",
        "description": "test",
        "store": operation.variables["xarray"],
        "variety": operation.variables.get("variety", None)
        or RepresentationVariety.VOXEL,
        "origins": [],
    }


def test_mikro(tmp_path_factory):
    link = MikroLinkComposition(
        auth=AuthTokenLink(token_loader=aget_token, token_refresher=aget_token),
        split=SplitLink(
            left=AsyncMockLink(
                query_resolver={
                    "request": mock_request,
                },
                mutation_resolver={
                    "fromXArray": mock_from_xarray,
                },
            ),
            right=AsyncMockLink(),
            split=lambda x: True,
        ),
    )

    app = Mikro(
        datalayer=LocalDataLayer(
            endpoint_url="s3.amazonaws.com",
            directory=str(tmp_path_factory.mktemp("data")),
        ),
        rath=MikroRath(link=link),
    )

    with app:
        l = from_xarray(xr.DataArray(np.zeros((1000, 1000, 10)), dims=["x", "y", "z"]))
        assert l.data.shape == (
            1,
            1,
            10,
            1000,
            1000,
        ), "Shape should be (10, 1000, 1000)"
        pass
