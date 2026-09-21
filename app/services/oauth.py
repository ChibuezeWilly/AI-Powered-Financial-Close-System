from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.config import settings
from ..database.database import get_db
from ..schema.models import AuditEvent, Employee, RevokedSession, Role, User


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


def issue_token(user: User | Employee) -> tuple[str, datetime]:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
    account_type = "employee" if isinstance(user, Employee) or user.role != Role.REGULAR_USER.value else "user"
    header = b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = b64(
        json.dumps(
            {
                "sub": str(user.id),
                "role": user.role,
                "account_type": account_type,
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


def current_user(request: Request, db: Session = Depends(get_db)) -> User | Employee:
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
    
    account_type = claims.get("account_type")
    user_id = int(claims["sub"])
    role = claims.get("role")

    user: User | Employee | None = None
    if account_type == "employee" or (account_type is None and role and role != Role.REGULAR_USER.value):
        user = db.get(Employee, user_id)
        if not user:
            user = db.get(User, user_id)
    else:
        user = db.get(User, user_id)
        if not user:
            user = db.get(Employee, user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account is unavailable")
    return user


CurrentUser = Annotated[User | Employee, Depends(current_user)]


def require_roles(*roles: Role):
    def dependency(user: CurrentUser) -> User | Employee:
        if user.role not in {r.value for r in roles}:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Access restricted to authorized roles.",
            )
        return user

    return dependency
