
from concurrent.futures.thread import ThreadPoolExecutor
from herre.access.model.graphql import GraphQLSyncModelManager
from herre.access.model import GraphQLAsyncModelManager
from herre.excecutors import default_executor
import asyncio
import xarray as xr


class AsyncRepresentationManager(GraphQLAsyncModelManager):

    async def from_xarray(self, array: xr.DataArray, compute=True, **kwargs):
        instance = await self.create(**kwargs)
        executor = default_executor.get()
        if executor:
            co_future = executor.submit(instance.save_array, array, compute=True)
            await asyncio.wrap_future(co_future) 
        else:   
            with ThreadPoolExecutor(max_workers=4) as executor:
                co_future = executor.submit(instance.save_array, array, compute=True)
                await asyncio.wrap_future(co_future)    
        instance = await self.update(id=instance.id, **kwargs)
        return instance

    async def update(self, **kwargs) -> "Representation":
        return await self.from_query(self.modelClass.Meta.update, **kwargs)



class SyncRepresentationManager(GraphQLSyncModelManager):

    def from_xarray(self, array: xr.DataArray, compute=True, **kwargs):
        instance = self.create(**kwargs)
        instance.save_array(array, compute=compute)
        instance = self.update(id=instance.id, **kwargs)
        return instance

    def update(self, **kwargs) -> "Representation":
        return self.from_query(self.modelClass.Meta.update, **kwargs)