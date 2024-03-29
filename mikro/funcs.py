""" This module provides helpers for the mikro rath api
they are wrapped functions for the turms generated api"""
from mikro.rath import MikroRath, current_mikro_rath
from koil.helpers import unkoil
from typing import Optional
from rath.rath import Rath, current_rath
from typing import Any, Dict
from pydantic import BaseModel





async def aexecute(
    operation: Any, variables: Dict[str, Any],
    rath: Optional[MikroRath] = None
):
    rath = rath or current_mikro_rath.get()
    x = await rath.aquery(operation.Meta.document, operation.Arguments(**variables))
    return operation(**x.data)


def execute(
    operation: Any, variables: Dict[str, Any],
    rath: Optional[MikroRath] = None,
):
    return unkoil(aexecute, operation, variables, rath)


def subscribe(operation: Any, variables: Dict[str, Any], rath: Optional[MikroRath] = None):
    rath = rath or current_mikro_rath.get()
    for ev in rath.subscribe(operation.Meta.document, operation.Arguments(**variables)):
        yield operation(**ev.data)


async def asubscribe(operation: Any, variables: Dict[str, Any], rath: Optional[MikroRath] = None):
    rath = rath or current_mikro_rath.get()
    async for event in rath.asubscribe(
        operation.Meta.document, operation.Arguments(**variables)
    ):
        yield operation(**event.data)
