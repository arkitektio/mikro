import os
from mikro.errors import NoMikroFound
from rath import rath
import xarray as xr
import pandas as pd
import contextvars
import logging
current_mikro = contextvars.ContextVar("current_mikro", default=None)
GLOBAL_MIKRO = None


logger = logging.getLogger(__name__)


def set_current_mikro(herre, set_global=True):
    global GLOBAL_MIKRO
    current_mikro.set(herre)
    if set_global:
        GLOBAL_MIKRO = herre

def set_global_mikro(herre):
    global GLOBAL_MIKRO
    GLOBAL_MIKRO = herre

def get_current_mikro(allow_global=True):
    global GLOBAL_MIKRO
    herre = current_mikro.get()

    if not herre:
        if not allow_global:
            raise NoMikroFound(
                "No current mikro found and global mikro are not allowed"
            )
        if not GLOBAL_MIKRO:
            if os.getenv("MIKRO_ALLOW_FAKTS_GLOBAL", "True") == "True":
                try:
                    
                    from mikro.fakts.mikro import FaktsMikro
                    GLOBAL_MIKRO = FaktsMikro()
                    return GLOBAL_MIKRO
                except ImportError as e:
                    raise NoMikroFound("Error creating Fakts Mikro") from e
            else:
                raise NoMikroFound("No current mikro found and and no global mikro found")

    return herre


class Mikro(rath.Rath):
    pass





