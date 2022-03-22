from mikro.rath import MikroRath, current_mikro_rath


def execute(
    operation,
    variables,
    mikrorath: MikroRath = None,
):
    mikro = mikrorath or current_mikro_rath.get()
    return operation(**mikro.execute(operation.Meta.document, variables).data)


async def aexecute(
    operation,
    variables,
    mikrorath: MikroRath = None,
):
    mikro = mikrorath or current_mikro_rath.get()
    x = await mikro.aexecute(operation.Meta.document, variables)
    return operation(**x.data)


def subscribe(operation, variables, mikrorath: MikroRath = None):
    mikro = mikrorath or current_mikro_rath.get()
    for ev in mikro.subscribe(operation.Meta.document, variables):
        yield operation(**ev.data)


async def asubscribe(operation, variables, mikrorath: MikroRath = None):
    mikro = mikrorath or current_mikro_rath.get()
    async for event in mikro.asubscribe(
        operation.Meta.document,
        variables,
    ):
        yield operation(**event.data)
