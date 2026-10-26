from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import auth_rate_limit, get_current_user
from app.core.config import settings
from app.core.db import get_db
from app.core.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from app.models import Role, User
from app.schemas.api import LoginIn, RegisterIn, TokenOut, UserOut
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(u: User) -> UserOut:
    return UserOut(id=u.id, email=u.email, role=u.role.value)


def _token_out(u: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(u.id, u.role.value), user=_user_out(u))


@router.post("/register", response_model=TokenOut, status_code=201, dependencies=[Depends(auth_rate_limit)])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if body.role == "professor" and not settings.allow_professor_registration:
        raise HTTPException(403, "Professor accounts must be created by an administrator.")
    email = body.email.strip().lower()
    taken = HTTPException(409, "Registration could not be completed with these details.")
    if db.scalar(select(User).where(User.email == email)):
        raise taken
    user = User(email=email, password_hash=hash_password(body.password), role=Role(body.role))
    db.add(user)
    try:
        db.flush()
        audit.record(db, user, "user_registered", "user", user.id, role=body.role)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise taken
    return _token_out(user)


@router.post("/login", response_model=TokenOut, dependencies=[Depends(auth_rate_limit)])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not (user and ok and user.is_active):
        raise HTTPException(401, "Invalid email or password.")
    return _token_out(user)


@router.post("/logout", status_code=204)
def logout(_: User = Depends(get_current_user)):
    # Tokens are stateless and short-lived; the client discards its token.
    # Server-side revocation is not implemented yet.
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
