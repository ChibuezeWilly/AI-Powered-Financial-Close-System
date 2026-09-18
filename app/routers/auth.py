from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.config import settings
from ..database.database import get_db
from ..schema.models import AuditEvent, RevokedSession, Role, User
from ..schemas import AccountCreate, AccountUpdate, LoginRequest, PortalLoginRequest, PortalRegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

TOKEN_TTL_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", settings.ACCESS_TOKEN_EXPIRE_MINUTES if hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES") else "60"))
JWT_SECRET = os.getenv("JWT_SECRET", settings.SECRET_KEY)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000)
    return (
        f"pbkdf2_sha256$600000${base64.urlsafe_b64encode(salt).decode()}"
        f"${base64.urlsafe_b64encode(digest).decode()}"
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt, digest = stored.split("$")
        return algorithm == "pbkdf2_sha256" and hmac.compare_digest(
            hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                base64.urlsafe_b64decode(salt),
                int(rounds),
            ),
            base64.urlsafe_b64decode(digest),
        )
    except (ValueError, TypeError):
        return False


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_token(user: User) -> tuple[str, datetime]:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
    header = b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = b64(
        json.dumps(
            {
                "sub": str(user.id),
                "role": user.role,
                "jti": secrets.token_urlsafe(24),
                "exp": int(expires.timestamp()),
            },
            separators=(",", ":"),
        ).encode()
    )
    signature = b64(hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}", expires


def decode_token(token: str) -> dict:
    try:
        header, payload, signature = token.split(".")
        expected = b64(
            hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        claims = json.loads(unb64(payload))
        if claims["exp"] <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        return claims
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )


def audit(db: Session, actor: int | None, action: str, subject: str):
    db.add(AuditEvent(actor_id=actor, action=action, subject=subject))


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = decode_token(auth.removeprefix("Bearer "))
    if db.scalar(select(RevokedSession).where(RevokedSession.token_id == claims["jti"])):
        raise HTTPException(status_code=401, detail="Session has ended")
    user = db.get(User, int(claims["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account is unavailable")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_roles(*roles: Role):
    def dependency(user: CurrentUser) -> User:
        if user.role not in {r.value for r in roles}:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission for this action",
            )
        return user

    return dependency


AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
FINANCE_ROLES = (
    Role.ADMIN,
    Role.FINANCE_ADMIN,
    Role.FINANCE_MANAGER,
    Role.ANALYST,
)
FinanceUser = Annotated[User, Depends(require_roles(*FINANCE_ROLES))]
RegularUser = Annotated[User, Depends(require_roles(Role.REGULAR_USER))]
DecisionUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.FINANCE_ADMIN, Role.FINANCE_MANAGER, Role.ANALYST))]
ManagerUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.FINANCE_MANAGER))]


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: AccountCreate, db: Session = Depends(get_db)):
    return _register(payload, "regular", db)


def _register(payload: AccountCreate, portal: str, db: Session):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    requested_role = payload.role or Role.REGULAR_USER.value
    allowed_roles = (
        {Role.REGULAR_USER.value}
        if portal == "regular"
        else {Role.ADMIN.value, Role.FINANCE_ADMIN.value, Role.FINANCE_MANAGER.value, Role.ANALYST.value}
    )
    if requested_role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Unsupported account role")
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=requested_role,
    )
    db.add(user)
    db.flush()
    audit(db, user.id, "ACCOUNT_CREATED", f"user:{user.id}")
    db.commit()
    db.refresh(user)
    token, expires = issue_token(user)
    return TokenResponse(
        access_token=token,
        expires_in=int((expires - datetime.now(timezone.utc)).total_seconds()),
        user=user,
    )


@router.post("/portal-register", response_model=TokenResponse, status_code=201)
def portal_register(payload: PortalRegisterRequest, db: Session = Depends(get_db)):
    return _register(payload, payload.portal, db)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return _login(payload, None, db)


def _login(payload: LoginRequest, portal: str | None, db: Session):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if portal == "regular" and user.role != Role.REGULAR_USER.value:
        raise HTTPException(status_code=403, detail="Use the admin portal for this account")
    if portal == "admin" and user.role == Role.REGULAR_USER.value:
        raise HTTPException(status_code=403, detail="Regular users must use the regular portal")
    audit(db, user.id, "SIGNED_IN", f"user:{user.id}")
    db.commit()
    token, expires = issue_token(user)
    return TokenResponse(
        access_token=token,
        expires_in=int((expires - datetime.now(timezone.utc)).total_seconds()),
        user=user,
    )


@router.post("/portal-login", response_model=TokenResponse)
def portal_login(payload: PortalLoginRequest, db: Session = Depends(get_db)):
    return _login(payload, payload.portal, db)


@router.post("/logout", status_code=204)
def logout(request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    claims = decode_token(request.headers["Authorization"].removeprefix("Bearer "))
    db.add(
        RevokedSession(
            token_id=claims["jti"],
            user_id=user.id,
            expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
        )
    )
    audit(db, user.id, "SIGNED_OUT", f"user:{user.id}")
    db.commit()


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser):
    return user


@router.get("/accounts", response_model=list[UserResponse])
def list_accounts(_: AdminUser, db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


@router.patch("/accounts/{account_id}", response_model=UserResponse)
def update_account(account_id: int, payload: AccountUpdate, admin: AdminUser, db: Session = Depends(get_db)):
    user = db.get(User, account_id)
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    values = payload.model_dump(exclude_unset=True)
    if "password" in values:
        user.password_hash = hash_password(values.pop("password"))
    for field, value in values.items():
        setattr(user, field, value.value if isinstance(value, Role) else value)
    audit(db, admin.id, "ACCOUNT_UPDATED", f"user:{user.id}")
    db.commit()
    db.refresh(user)
    return user


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account_id: int, admin: AdminUser, db: Session = Depends(get_db)):
    user = db.get(User, account_id)
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Administrators cannot delete their own account")
    audit(db, admin.id, "ACCOUNT_DELETED", f"user:{user.id}")
    db.delete(user)
    db.commit()
