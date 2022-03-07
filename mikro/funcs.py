from mikro.mikro import MikroRath, current_mikro_rath


def execute(operation, variables, mikrorath: MikroRath = None, as_task=False):
    mikro = mikrorath or current_mikro_rath.get()
    return operation(
        **mikro.execute(operation.Meta.document, variables, as_task=as_task).data
    )


async def aexecute(operation, variables, mikrorath: MikroRath = None, as_task=False):
    mikro = mikrorath or current_mikro_rath.get()
    x = await mikro.aexecute(operation.Meta.document, variables, as_task=as_task)
    return operation(**x.data)


def subscribe(operation, variables, mikrorath: MikroRath = None, as_task=False):
    mikro = mikrorath or current_mikro_rath.get()
    return mikro.subscribe(operation.Meta.document, variables, as_task=as_task)


async def asubscribe(operation, variables, mikrorath: MikroRath = None, as_task=False):
    mikro = mikrorath or current_mikro_rath.get()
    async for event in mikro.asubscribe(
        operation.Meta.document, variables, as_task=as_task
    ):
        yield operation(**event.data)
