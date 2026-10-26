"""Password hashing (scrypt, stdlib) and JWT access tokens."""
import base64
import hashlib
import hmac
import os
import secrets
import time
import uuid

import jwt

from app.core.config import settings

_N, _R, _P = 2**14, 8, 1
_EPHEMERAL_SECRET = secrets.token_urlsafe(48)  # dev only: tokens die on restart


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    b64 = lambda b: base64.b64encode(b).decode()
    return f"scrypt${_N}${_R}${_P}${b64(salt)}${b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, expected = stored.split("$")
        if scheme != "scrypt":
            return False
        dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt),
                            n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(dk, base64.b64decode(expected))
    except Exception:
        return False


DUMMY_HASH = hash_password("codeproof-dummy-password")  # equalizes timing for unknown emails


def _secret() -> str:
    if settings.jwt_secret:
        if settings.environment == "production" and len(settings.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters in production")
        return settings.jwt_secret
    if settings.environment == "production":
        raise RuntimeError("JWT_SECRET must be set in production")
    return _EPHEMERAL_SECRET


def create_access_token(user_id: int, role: str) -> str:
    now = int(time.time())
    claims = {"sub": str(user_id), "role": role, "iat": now,
              "exp": now + settings.jwt_exp_minutes * 60, "jti": uuid.uuid4().hex}
    return jwt.encode(claims, _secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError on any problem. The role claim is informational only;
    authorization always re-reads the role from the database."""
    return jwt.decode(token, _secret(), algorithms=["HS256"], options={"require": ["exp", "sub"]})
