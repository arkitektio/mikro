import os
from typing import List
import jwt
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


DIR_NAME = os.path.dirname(os.path.realpath(__file__))


def build_relative(path):
    return os.path.join(DIR_NAME, path)



def request_token(sub: int = 1, roles: List[str] = None, scopes: List[str] = None) -> str:
    """ Request a JWT Token that is signed with the private key"""
    roles = roles or ["admin"]
    scopes = scopes or ["read", "write"]

    due_date = datetime.datetime.now() 
    header = {"alg": "RS256"}
    expiry = int(due_date.timestamp())
    payload = {
        "iss": "lok", 
        "exp": expiry, 
        "aud": "mikro",
        "sub": 1, 
        "client_id": "abc",
        "version": "1.0",
        "roles": ["admin", "user"],
        "scopes": ["read", "write"],
    }

    private_key = serialization.load_pem_private_key(
        secret, password=None, backend=default_backend()
    )

    token=jwt.encode(payload, private_key, algorithm='RS256')
    print(token)