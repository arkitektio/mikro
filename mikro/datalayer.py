
import contextvars
import logging
import os
from koil.loop import koil
from mikro.errors import NoDataLayerFound 
import s3fs


current_datalayer = contextvars.ContextVar("current_datalayer", default=None)
GLOBAL_DATALAYER = None


def set_current_datalayer(filesystem, set_global=True):
    global GLOBAL_DATALAYER
    current_datalayer.set(filesystem)
    if set_global:
        GLOBAL_DATALAYER = filesystem

def set_global_datalayer(filesystem):
    global GLOBAL_DATALAYER
    GLOBAL_DATALAYER = filesystem

def get_current_datalayer(allow_global=True):
    global GLOBAL_DATALAYER
    datalayer = current_datalayer.get()

    if not datalayer:
        if not allow_global:
            raise NoDataLayerFound(
                "No current mikro found and global mikro are not allowed"
            )
        if not GLOBAL_DATALAYER:
            if os.getenv("MIKRO_ALLOW_DATALAYER_GLOBAL", "True") == "True":
                try:
                    from mikro.fakts.datalayer import FaktsDataLayer
                    GLOBAL_DATALAYER = FaktsDataLayer()
                    return GLOBAL_DATALAYER
                except ImportError as e:
                    raise NoDataLayerFound("Error creating Fakts Mikro") from e
            else:
                raise NoDataLayerFound("No current mikro found and and no global mikro found")

    return datalayer


class DataLayer:
    
    def __init__(self, access_key="", secret_key="", endpoint_url="") -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self.connected = False
        super().__init__()

    async def aconnect(self):
        if self.access_key:
            os.environ["AWS_ACCESS_KEY_ID"] = self.access_key
        if self.secret_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = self.secret_key

        self._s3fs = s3fs.S3FileSystem(secret=self.secret_key, access=self.access_key, client_kwargs={"endpoint_url": self.endpoint_url})
        self.connected = True

    def connect(self):
        return koil(self.aconnect)

    @property
    def fs(self):
        assert self.s3fs is not None, "Filesystem is not connected yet, please make sure to connect first"