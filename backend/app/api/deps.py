import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.ratelimit import SlidingWindowLimiter
from app.core.security import decode_access_token
from app.models import Role, User

auth_limiter = SlidingWindowLimiter(settings.auth_rate_limit, 60.0)


def auth_rate_limit(request: Request) -> None:
    host = request.client.host if request.client else "unknown"
    if not auth_limiter.allow(f"{request.url.path}:{host}"):
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait a minute and try again.")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    unauth = HTTPException(status_code=401, detail="Not authenticated.", headers={"WWW-Authenticate": "Bearer"})
    if scheme.lower() != "bearer" or not token:
        raise unauth
    try:
        user = db.get(User, int(decode_access_token(token)["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauth
    if user is None or not user.is_active:
        raise unauth
    return user


def require_roles(*roles: Role):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to do this.")
        return user
    return dep
