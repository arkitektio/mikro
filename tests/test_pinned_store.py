"""A pinned datalayer's stores trust its hub's certificate themselves, not via SSL_CERT_FILE.

obstore >= 0.11 verifies with the platform's verifier, which on macOS and Windows asks the OS
trust store and never reads SSL_CERT_FILE: the hub's certificate has to reach each store.
"""

import datetime
import ipaddress
import os
import socket
import ssl
import threading
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import obstore
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from fakts import Alias

from mikro.datalayer import DataLayer
from mikro.io.obstore import acreate_s3_store

GRANT = SimpleNamespace(
    access_key="access",
    secret_key="secret",
    session_token="",
    bucket="bucket",
    key="some/object",
)


def _hub_certificate() -> tuple[str, bytes]:
    """A certificate shaped like konstruktor's: self-signed, end-entity, ECDSA P-256."""
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Arkitekt hub")])
    now = datetime.datetime.now(datetime.UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=30))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                ]
            ),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(key, hashes.SHA256())
    )
    pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return pem, key_pem


@pytest.fixture()
def hub(tmp_path: Path) -> Iterator[tuple[int, str]]:
    """An HTTPS endpoint serving the hub certificate and answering every request 404."""
    pem, key_pem = _hub_certificate()
    (tmp_path / "hub.crt").write_text(pem)
    (tmp_path / "hub.key").write_bytes(key_pem)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(tmp_path / "hub.crt", tmp_path / "hub.key")

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)

    def serve() -> None:
        while True:
            try:
                raw, _ = listener.accept()
            except OSError:
                return
            try:
                with context.wrap_socket(raw, server_side=True) as conn:
                    data = b""
                    while b"\r\n\r\n" not in data:
                        chunk = conn.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    conn.sendall(
                        b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                    )
            except (ssl.SSLError, OSError):
                continue  # a client that refused the certificate

    threading.Thread(target=serve, daemon=True).start()
    yield listener.getsockname()[1], pem
    listener.close()


@pytest.mark.asyncio
async def test_a_pinned_datalayer_reaches_its_hub_without_ssl_cert_file(
    hub: tuple[int, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The store verifies the hub by the alias's certificate, and the env is left alone."""
    port, pem = hub
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    alias = Alias(id="s3", host="localhost", port=port, ssl=True, certificates=[pem])

    datalayer = DataLayer.from_alias(alias)
    store = await acreate_s3_store(GRANT, datalayer)

    # A 404 is the endpoint's answer, so TLS to it was verified and the request went through.
    with pytest.raises(FileNotFoundError):
        await obstore.get_async(store, GRANT.key)
    assert "SSL_CERT_FILE" not in os.environ
