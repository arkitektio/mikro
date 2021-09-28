
from herre.wards.query import TypedQuery
from herre.access.object import GraphQLObject
from herre.config.herre import BaseConfig
from herre.auth import HerreClient, get_current_herre
from herre.wards.graphql import ParsedQuery, GraphQLWard
import aiohttp
import xarray as xr


class MikroConfig(BaseConfig):
    host: str
    port: int
    secure: bool

    class Config:
        yaml_group = "mikro"
        env_prefix = "mikro_"


class AccessParams(GraphQLObject):
    access_key: str
    secret_key: str

class Transcript(GraphQLObject):
    protocol: str
    path: str
    params: AccessParams


class MikroWard(GraphQLWard):

    class Meta:
        key = "mikro"

    def __init__(self, herre: HerreClient) -> None:
        self.config = MikroConfig.from_file(herre.config_path)
        self.transcript: Transcript = None
        super().__init__(herre, f"http://{self.config.host}:{self.config.port}/graphql")


    async def negotiate(self):
        transcript_query = await self.run(ParsedQuery("""mutation Negotiate {
            negotiate 
        }"""))
        return Transcript(**transcript_query["negotiate"])



class playground():

    def __init__(self, width=900, height=700) -> None:
        herre = get_current_herre()
        self.config = MikroConfig.from_file(herre.config_path)
        self.width = width
        self.height = height

    def _repr_html_(self):
        return f"<iframe src='http://{self.config.host}:{self.config.port}/graphql' width={self.width} height={self.height}></iframe>"



class gql(TypedQuery):
    ward_key = "mikro"
    


