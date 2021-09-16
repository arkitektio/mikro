from herre.auth import HerreClient
from mikro import gql, Representation, Sample
import pytest

async def test_normal_query():


    herre =  HerreClient(config_path="tests/configs/bergen.yaml")

    query = await gql("""
                    query {
            representations{
                name
                thumbnail
                store
                tags
                sample {
                name
                }
                
            }
            }
    """)()

    assert len(query.representations) > 0, "Wanted Representatoin List"

