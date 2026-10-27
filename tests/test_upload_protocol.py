"""The upload protocol every kind shares: grant, write with self-renewing credentials, finish.

No network. The rath is a stub that answers request/finish/refresh mutations and records what
it was asked, and the writes are replaced, because what is under test is the protocol around
them: that a failed write is reported rather than left to rot, that every kind is finished,
that a file declares the size the server holds it to, and that credentials renew themselves
against the same store instead of dying with a 403 halfway through a long write.
"""

import datetime
import io
import re
from types import SimpleNamespace
from typing import Any

import pytest

from mikro.datalayer import DataLayer
from mikro.io import obstore as mikro_obstore
from mikro.middleware.upload import UploadMiddleware
from mikro.scalars import FileLike, ImageFileLike


def _grant(key: str = "svc/org/abc", expires_in: int = 3600, access: str = "AK") -> dict[str, Any]:
    return {
        "accessKey": access,
        "secretKey": "SK",
        "sessionToken": "TOKEN",
        "path": f"s3://bucket/{key}",
        "key": key,
        "bucket": "bucket",
        "expiresIn": expires_in,
        "maxBytes": 11,
        "store": "42",
    }


class StubRath:
    """Answers request*Upload with a grant, finish*Upload with a store, and records the calls."""

    def __init__(self) -> None:
        """Start with nothing asked."""
        self.asked: list[tuple[str, dict[str, Any]]] = []

    def query(self, document: str, variables: dict[str, Any], **_: Any) -> SimpleNamespace:  # noqa: ANN401
        """Answer by which mutation was asked for, the way the server would."""
        field = re.search(r"\{\s*(\w+)\(", document).group(1)  # type: ignore[union-attr]
        self.asked.append((field, variables))
        if field.startswith(("request", "refresh")):
            return SimpleNamespace(data={field: _grant()})
        if field.startswith("finish"):
            return SimpleNamespace(data={field: {"id": "42", "key": "svc/org/abc", "bucket": "bucket", "path": "s3://bucket/svc/org/abc"}})
        raise AssertionError(f"unexpected mutation {field}")


@pytest.fixture
def middleware() -> UploadMiddleware:
    layer = UploadMiddleware(datalayer=DataLayer(endpoint_url="http://s3.test"))
    layer._cached_datalayer_url = "http://s3.test"  # else it resolves through koil
    return layer


def test_a_file_declares_its_size_and_is_finished(middleware: UploadMiddleware, monkeypatch: pytest.MonkeyPatch) -> None:
    """A big file used to be uploaded and never finished: a store the server could not tell from an abandoned one."""
    monkeypatch.setattr("mikro.middleware.upload.upload_bigfile", lambda file, grant, datalayer: grant.store)
    rath = StubRath()

    processed = middleware.process_variables({"file": FileLike(io.BytesIO(b"hello world"), name="a.txt")}, None, rath)  # type: ignore[arg-type]

    assert processed == {"file": "42"}
    assert [field for field, _ in rath.asked] == ["requestBigfileUpload", "finishBigfileUpload"]
    assert rath.asked[0][1]["input"] == {"originalFileName": "a.txt", "fileSize": 11}
    assert rath.asked[1][1]["input"] == {"storeId": "42", "valid": True}


def test_a_failed_write_is_reported_and_its_error_kept(middleware: UploadMiddleware, monkeypatch: pytest.MonkeyPatch) -> None:
    """`valid=false` ends the upload on the server at once; the caller still sees what went wrong."""

    def broken(file: Any, grant: Any, datalayer: Any) -> str:  # noqa: ANN401
        raise ConnectionResetError("the link went away")

    monkeypatch.setattr("mikro.middleware.upload.store_media_file", broken)
    rath = StubRath()

    with pytest.raises(ConnectionResetError, match="went away"):
        middleware.process_variables({"image": ImageFileLike(io.BytesIO(b"png"), name="a.png")}, None, rath)  # type: ignore[arg-type]

    assert [field for field, _ in rath.asked] == ["requestMediaUpload", "finishMediaUpload"]
    assert rath.asked[1][1]["input"] == {"storeId": "42", "valid": False}


def test_a_write_builds_stores_that_renew_their_credentials(middleware: UploadMiddleware, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inside an upload `create_s3_store` hands obstore a provider, not the grant's static keys."""
    built: list[Any] = []

    def write(file: Any, grant: Any, datalayer: Any) -> str:  # noqa: ANN401
        built.append(mikro_obstore.create_s3_store("http://s3.test", grant))
        return grant.store

    monkeypatch.setattr("mikro.middleware.upload.upload_bigfile", write)
    middleware.process_variables({"file": FileLike(io.BytesIO(b"x"), name="a")}, None, StubRath())  # type: ignore[arg-type]

    assert isinstance(built[0].credential_provider, mikro_obstore.RefreshingUploadCredentials)
    assert mikro_obstore.upload_refresher.get() is None, "and only for the duration of the write"


def test_credentials_are_renewed_against_the_same_store_before_they_expire() -> None:
    refreshed: list[str] = []

    def refresh() -> Any:  # noqa: ANN401
        refreshed.append("asked")
        return SimpleNamespace(access_key="AK2", secret_key="SK2", session_token="T2", expires_in=3600)

    short = SimpleNamespace(access_key="AK1", secret_key="SK1", session_token="T1", expires_in=3600)
    provider = mikro_obstore.RefreshingUploadCredentials(short, refresh)

    assert provider()["access_key_id"] == "AK1", "a fresh grant is used as it is"
    assert refreshed == []

    provider._expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=30)
    renewed = provider()

    assert renewed["access_key_id"] == "AK2" and renewed["token"] == "T2"
    assert refreshed == ["asked"]
    assert renewed["expires_at"] is not None and renewed["expires_at"] > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
