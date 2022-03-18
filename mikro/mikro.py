import os
from mikro.errors import NoMikroFound
from rath import rath
import xarray as xr
import pandas as pd
import contextvars
import logging

current_mikro_rath = contextvars.ContextVar("current_mikro_rath")


class MikroRath(rath.Rath):
    async def __aenter__(self):
        await super().__aenter__()
        current_mikro_rath.set(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        current_mikro_rath.set(None)
