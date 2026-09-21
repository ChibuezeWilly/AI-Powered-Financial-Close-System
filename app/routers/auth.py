from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..schema.models import Employee, RevokedSession, Role, User
from ..schemas import AccountCreate, AccountUpdate, LoginRequest, TokenResponse, UserResponse
from ..services.oauth import (
    CurrentUser,
    audit,
    decode_token,
    hash_password,
    issue_token,
    require_roles,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

AdminUser = Annotated[User | Employee, Depends(require_roles(Role.ADMIN))]
FINANCE_ROLES = (Role.ADMIN, Role.FINANCE_ADMIN, Role.FINANCE_MANAGER, Role.ANALYST)
FinanceUser = Annotated[User | Employee, Depends(require_roles(*FINANCE_ROLES))]
DecisionUser = FinanceUser
ManagerUser = Annotated[User | Employee, Depends(require_roles(Role.ADMIN, Role.FINANCE_ADMIN, Role.FINANCE_MANAGER))]
RegularUser = Annotated[User | Employee, Depends(require_roles(Role.REGULAR_USER))]


def _perform_login(db: Session, email: str, password: str, is_admin: bool) -> TokenResponse:
    norm_email = str(email).lower()
    model = Employee if is_admin else User
    account = db.scalar(select(model).where(model.email == norm_email))

    if not account or not verify_password(password, account.password_hash) or not account.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    audit(db, account.id, "SIGNED_IN", f"{'employee' if is_admin else 'user'}:{account.id}")
    db.commit()

    token, expires = issue_token(account)
    return TokenResponse(
        access_token=token,
        expires_in=int((expires - datetime.now(timezone.utc)).total_seconds()),
        user=account,
    )


@router.post("/admin/register", response_model=TokenResponse, status_code=201)
@router.post("/register", response_model=TokenResponse, status_code=201, include_in_schema=False)
def admin_register(payload: AccountCreate, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(Employee).where(Employee.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")

    requested_role = payload.role or Role.ADMIN.value
    allowed_roles = {r.value for r in (Role.ADMIN, Role.FINANCE_ADMIN, Role.FINANCE_MANAGER, Role.ANALYST)}
    if requested_role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Unsupported account role")

    employee = Employee(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=requested_role,
    )
    db.add(employee)
    db.flush()
    audit(db, employee.id, "ACCOUNT_CREATED", f"employee:{employee.id}")
    db.commit()
    db.refresh(employee)

    token, expires = issue_token(employee)
    return TokenResponse(
        access_token=token,
        expires_in=int((expires - datetime.now(timezone.utc)).total_seconds()),
        user=employee,
    )


@router.post("/admin/login", response_model=TokenResponse)
@router.post("/login/admin", response_model=TokenResponse, include_in_schema=False)
@router.post("/login", response_model=TokenResponse, include_in_schema=False)
def admin_login(payload: LoginRequest, db: Session = Depends(get_db)):
    return _perform_login(db, payload.email, payload.password, is_admin=True)


@router.post("/users_register", response_model=TokenResponse, status_code=201)
@router.post("/user/register", response_model=TokenResponse, status_code=201, include_in_schema=False)
@router.post("/portal-register", response_model=TokenResponse, status_code=201, include_in_schema=False)
def user_register(payload: AccountCreate, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")

    requested_role = payload.role or Role.REGULAR_USER.value
    if requested_role != Role.REGULAR_USER.value:
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


@router.post("/users_login", response_model=TokenResponse)
@router.post("/user/login", response_model=TokenResponse, include_in_schema=False)
@router.post("/portal-login", response_model=TokenResponse, include_in_schema=False)
def user_login(payload: LoginRequest, db: Session = Depends(get_db)):
    return _perform_login(db, payload.email, payload.password, is_admin=False)


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
def update_account(
    account_id: int,
    payload: AccountUpdate,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
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
