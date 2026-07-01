from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import client_ip, get_current_user, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.base import get_db
from app.models.auth import LoginAttempt, User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreateRequest, UserResponse
from app.services.audit import log_action
from app.services.security_log import log_failed_login

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    user = db.query(User).filter(User.username == payload.username).first()

    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        db.add(LoginAttempt(username=payload.username, ip_address=ip, success=False))
        db.commit()
        log_failed_login(payload.username, ip)
        raise HTTPException(
            status.HTTP_423_LOCKED,
            f"Account locked until {user.locked_until.isoformat()} due to repeated failed logins",
        )

    valid = user is not None and user.is_active and verify_password(payload.password, user.password_hash)

    db.add(LoginAttempt(username=payload.username, ip_address=ip, success=valid))

    if not valid:
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= settings.failed_login_max_attempts:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.failed_login_lockout_minutes
                )
                user.failed_attempts = 0
        log_action(db, user.id if user else None, "login_failed", "auth", ip)
        db.commit()
        log_failed_login(payload.username, ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    user.failed_attempts = 0
    user.locked_until = None
    db.commit()
    log_action(db, user.id, "login_success", "auth", ip)

    token = create_access_token(subject=user.username, role=user.role, tenant_id=user.tenant_id)
    return TokenResponse(access_token=token, role=user.role, username=user.username)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_role("admin"))])
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_role("admin"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()
