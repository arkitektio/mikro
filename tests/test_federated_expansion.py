"""Federated expansion is a setting of the client, not of the process.

It defaults from ``MIKRO_FEDERATED_EXPANSION`` when the client is built, so two
clients in one process can differ, and the environment is read then rather than
when the module was imported.
"""

import pytest

from mikro.mikro import FEDERATED_EXPANSION_ENV, Mikro


def _client(**overrides: object) -> Mikro:
    return Mikro.model_construct(**overrides)


def test_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(FEDERATED_EXPANSION_ENV, raising=False)
    assert Mikro.model_fields["federated_expansion"].get_default(call_default_factory=True) is False


def test_the_environment_is_read_when_the_client_is_built(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FEDERATED_EXPANSION_ENV, "1")
    assert Mikro.model_fields["federated_expansion"].get_default(call_default_factory=True) is True
    monkeypatch.setenv(FEDERATED_EXPANSION_ENV, "0")
    assert Mikro.model_fields["federated_expansion"].get_default(call_default_factory=True) is False


def test_two_clients_in_one_process_can_differ() -> None:
    on, off = _client(federated_expansion=True), _client(federated_expansion=False)

    assert on.can_expand_many("@mikro/arraydataset") is True
    assert off.can_expand_many("@mikro/arraydataset") is False
    assert on.can_expand_many("@mikro/nothing-of-the-kind") is False, "needs a fragment too"
