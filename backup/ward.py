import os
from pydantic.main import BaseModel
from s3fs.core import S3FileSystem
from fakts import Fakts, get_current_fakts, Config
from herre.herre import Herre
from herre.wards.query import TypedQuery
from herre.access.object import GraphQLObject
from herre import get_current_herre
from herre.wards.graphql import ParsedQuery, GraphQLWard
import aiohttp
import xarray as xr

from mikro.funcs import shrink_xarray


class S3Config(BaseModel):
    host: str
    port: int
    secure: bool


class MikroConfig(Config):
    host: str
    port: int
    secure: bool
    s3: S3Config

    class Config:
        group = "mikro"
        env_prefix = "mikro_"

    @property
    def endpoint(self):
        return f"http://{self.host}:{self.port}/graphql"


class AccessParams(GraphQLObject):
    access_key: str
    secret_key: str


class Transcript(GraphQLObject):
    protocol: str
    path: str
    params: AccessParams


class MikroWard(GraphQLWard):
    configClass = MikroConfig
    config: MikroConfig

    shrinker_funcs = {xr.DataArray: shrink_xarray}

    class Meta:
        key = "mikro"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, *kwargs)
        self._s3fs = None

    async def negotiate(self):
        transcript_query = await self.arun(
            """mutation Negotiate {
            negotiate 
        }"""
        )
        return Transcript(**transcript_query["negotiate"])

    @property
    def s3fs(self):
        if not self._s3fs:
            transcript = self.transcript
            protocol = "https" if self.config.s3.secure else "http"
            endpoint_url = f"{protocol}://{self.config.s3.host}:{self.config.s3.port}"

            os.environ["AWS_ACCESS_KEY_ID"] = transcript.params.access_key
            os.environ["AWS_SECRET_ACCESS_KEY"] = transcript.params.secret_key

            self._s3fs = S3FileSystem(client_kwargs={"endpoint_url": endpoint_url})
        return self._s3fs


class playground:
    def __init__(self, width=900, height=700) -> None:
        herre = get_current_herre()
        self.width = width
        self.height = height

    def _repr_html_(self):
        return f"<iframe src='http://{self.config.host}:{self.config.port}/graphql' width={self.width} height={self.height}></iframe>"


class gql(TypedQuery):
    ward_key = "mikro"
