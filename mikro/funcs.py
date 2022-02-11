from mikro.mikro import Mikro, get_current_mikro


def execute(operation, variables, mikro: Mikro = None):
    mikro = mikro or get_current_mikro()
    return operation(**mikro.execute(operation.Meta.document, variables).data)


async def aexecute(operation, variables, mikro: Mikro = None):
    mikro = mikro or get_current_mikro()
    x = await mikro.aexecute(operation.Meta.document, variables)
    return operation(**x.data)


def subscribe(operation, variables, mikro: Mikro = None):
    mikro = mikro or get_current_mikro()

    for event in mikro.subscribe(operation.Meta.document, variables):
        yield operation(**event.data)


async def asubscribe(operation, variables, mikro: Mikro = None):
    mikro = mikro or get_current_mikro()
    async for event in mikro.asubscribe(operation.Meta.document, variables):
        yield operation(**event.data)
