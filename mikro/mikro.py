from rath import rath
import contextvars

current_mikro_rath = contextvars.ContextVar("current_mikro_rath")


class MikroRath(rath.Rath):
    async def __aenter__(self):
        await super().__aenter__()
        current_mikro_rath.set(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        current_mikro_rath.set(None)
