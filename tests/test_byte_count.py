"""ByteCount: the server's 64-bit byte count, which GraphQL's Int cannot carry."""

import pytest
from pydantic import BaseModel, ValidationError

from mikro.api.schema import MediaUploadGrant
from mikro.scalars import ByteCount


class _Holder(BaseModel):
    size: ByteCount


def test_a_count_past_int32_round_trips_as_a_plain_number() -> None:
    holder = _Holder(size=3_000_000_000)

    assert isinstance(holder.size, ByteCount)
    assert holder.size == 3_000_000_000
    assert holder.model_dump_json() == '{"size":3000000000}'


def test_a_numeric_string_is_accepted() -> None:
    assert _Holder(size="42").size == 42


@pytest.mark.parametrize("bad", [-1, True, 1.5, None, "many"])
def test_what_the_server_refuses_is_refused(bad: object) -> None:
    with pytest.raises(ValidationError):
        _Holder(size=bad)


def test_grants_carry_their_budget_as_a_byte_count() -> None:
    grant = MediaUploadGrant.model_validate(
        {
            "accessKey": "a",
            "secretKey": "s",
            "sessionToken": "t",
            "path": "s3://b/k",
            "key": "k",
            "bucket": "b",
            "expiresIn": 60,
            "maxBytes": 5_000_000_000,
            "store": "store",
        }
    )

    assert isinstance(grant.max_bytes, ByteCount)
    assert grant.max_bytes == 5_000_000_000
