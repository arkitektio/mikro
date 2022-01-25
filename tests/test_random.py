from mikro.api.schema import aget_random_rep
import pytest


async def test_normal_query():

    rep = await aget_random_rep()
    assert rep.id is not None, "Did not return random representation"


async def test_normal_query():

    rep = await aget_random_rep()
    assert rep.id is not None, "Did not return random representation"
