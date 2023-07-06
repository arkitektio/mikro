import jwt
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


serviceID = "abc"
secret = b"""
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDGFj0zB7j6KrTR
FEP+a2Z7toLEwJ0ROF3qSkq6vo2aK5TGRv+D3V/6VhvM2NgtUIO1iqwvf4XETamh
Ht2xlVzJyoyMAnAGkwkMyQJpI6wG5g7NtrRc1kkeefWbLBVW+aEI++3ec3eD9PUh
njXbQXJwju8l2ldKg2skw2fZWrjfWo0S0CuvB05nXJ8BmmAo65BBv29gGVywzZEA
pv/Zu16l6ftCZSEKi/zMbK6YxCekl/h3sfK7uGj6uaab7XSqqANHDZDTSotD5ws8
UdMb3IP4/qoJiJm0Lsw5XpmFTt9M+ekiv/9HsWjXtzOd0BpqxynlvF1fWDr0HVnr
UCh1XMznAgMBAAECggEAPz/OnsKyf76vKats4onsmUf3jVdrT5pN8odyQRqjID0W
LhFxeOtwwABKtCfxLtbsl0UGIcx4K+wYY8f1RcTJce1o3zPQDWlZlGmCiYvIXBON
WoYiJRqPEloi4D89OR5QGwxGMadw3AOVWfyoea/2GJarKc0D3lkEFyMFv9NGAJrb
bb6/e2zf4WQ+6slUW4N1djZW2q5JtZR4a4v6nW9K4laC0UgOAzlKcfgfNuym3dcL
c+VuUUWxIsF5QNKtcgOzjxekmT5axZugFFjedLo65qGzKw08Fwk5b3x2BR1DzCVr
/fl+O4DSjwsu4u72fFGex4XqnIF9ovpOmLvnP09skQKBgQDhwJW/xTa1cgayFTK2
dhGwbjTHOchfl7ZRfBBa9SXEYiV/69Qn+kLLwKYQ/Zk1LBBy4wcDcO32mLi3ZYxa
IWjPp+9tGIY3uo4gZNYPQt1Vbpndkrh+uo5arTEG2YW5AW7/q/ujw50L3SfE3AMs
CN8FM4B9SdQP7xLElm0G856A8wKBgQDgoLd7kfksLI53IDkvjFeM3Lgg1XA6fN2g
wBAx7ckBFI2jAIEs/eUmPZWFIEuWwwhyrjmf6XwZEnpXJTRGyeyOiCcfb9x5qCWK
RSh+UR9JirRYCkWIqHo+mSWaSRgLiQOCSxMwLCGycbfzfXDq0avqjFmmdW0kh7if
npnHTlRhPQKBgHAvfDtojd9tYtZsol76HaBHpAK9PE4E3p1vwdDxsmr9OxVu5GdZ
fogynFQlMlWyKBpvp7SWEitRibnZxP2lTKilE95rKYfYNXjzo0zCNauW4u+xUe3o
V4XIO2zj/AgMJlT36n1fYFPc+z5g91KStgGnrlqUrcWdUP5Qoq2ps0LxAoGAfmVQ
+YJpEBc+Tv/dzciNlyC3pxoS3YZXe1W3hzDC8w2qqTbmePeg0oTCtrc2cW3rOgSZ
Pkc2YjFIj/LKWK7UolswkHr0N6yK+yPxJirljQ80bXnSKJSMvN6WDxvkINGHHPC7
qlaa23srxCIowKkcsI0rAQSAVpbcJ00qQMDtsA0CgYEAuCw+oo9G/OIiNtGcmee+
6OB/jQB42ZMJD6RTCzTRsjAwGvN+nlkCEIyT+1A4Th4cdmrvxm6eeLABZ85VfHrZ
T8Xz5BnVAhN5QjOvielXW79b87jLun3i7CaMnsA1SGgnDdkBPpJvOe1tyCmZiN3A
X95jwe+hRAc3nA1/yc55ais=
-----END PRIVATE KEY-----
"""
due_date = datetime.datetime.now() 
header = {"alg": "RS256"}
expiry = int(due_date.timestamp())
payload = {
    "iss": serviceID, 
    "exp": expiry, 
    "aud": "herre",
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