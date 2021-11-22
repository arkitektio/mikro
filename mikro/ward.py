from pydantic.main import BaseModel
from fakts import Fakts, get_current_fakts, Config
from herre.herre import Herre
from herre.wards.query import TypedQuery
from herre.access.object import GraphQLObject
from herre import get_current_herre
from herre.wards.graphql import ParsedQuery, GraphQLWard
import aiohttp
import xarray as xr


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

    class Meta:
        key = "mikro"

    async def negotiate(self):
        transcript_query = await self.arun(
            ParsedQuery(
                """mutation Negotiate {
            negotiate 
        }"""
            )
        )
        return Transcript(**transcript_query["negotiate"])


class playground:
    def __init__(self, width=900, height=700) -> None:
        herre = get_current_herre()
        self.width = width
        self.height = height

    def _repr_html_(self):
        return f"<iframe src='http://{self.config.host}:{self.config.port}/graphql' width={self.width} height={self.height}></iframe>"


class gql(TypedQuery):
    ward_key = "mikro"
