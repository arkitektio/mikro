from mikro.rath import MikroRath, current_mikro_rath


def execute(
    operation,
    variables,
    rath: MikroRath = None,
):
    rath = rath or current_mikro_rath.get()
    return operation(**rath.execute(operation.Meta.document, variables).data)


async def aexecute(
    operation,
    variables,
    rath: MikroRath = None,
):
    rath = rath or current_mikro_rath.get()
    x = await rath.aexecute(operation.Meta.document, variables)
    return operation(**x.data)


def subscribe(operation, variables, rath: MikroRath = None):
    rath = rath or current_mikro_rath.get()
    for ev in rath.subscribe(operation.Meta.document, variables):
        yield operation(**ev.data)


async def asubscribe(operation, variables, rath: MikroRath = None):
    rath = rath or current_mikro_rath.get()
    async for event in rath.asubscribe(
        operation.Meta.document,
        variables,
    ):
        yield operation(**event.data)
