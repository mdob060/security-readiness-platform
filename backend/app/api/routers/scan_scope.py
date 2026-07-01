from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import client_ip, get_current_user, require_role
from app.db.base import get_db
from app.models.auth import User
from app.models.scanning import ScopeTarget
from app.schemas.scanning import ScopeTargetCreate, ScopeTargetResponse
from app.services.audit import log_action
from app.services.scan_targets import TargetValidationError, validate_target_syntax

router = APIRouter(prefix="/api/scan-scope", tags=["scan-scope"])


@router.get("/targets", response_model=list[ScopeTargetResponse])
def list_targets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ScopeTarget).order_by(ScopeTarget.id.desc()).all()


@router.post("/targets", response_model=ScopeTargetResponse, dependencies=[Depends(require_role("analyst"))])
def request_target(
    payload: ScopeTargetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        target = validate_target_syntax(payload.target)
    except TargetValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    row = ScopeTarget(target=target, justification=payload.justification, requested_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_action(db, user.id, "scope_target_requested", "scan_scope", detail=target)
    return row


@router.post(
    "/targets/{target_id}/approve",
    response_model=ScopeTargetResponse,
    dependencies=[Depends(require_role("admin"))],
)
def approve_target(
    target_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(ScopeTarget, target_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target not found")
    row.status = "approved"
    row.approved_by_id = user.id
    row.approved_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, user.id, "scope_target_approved", "scan_scope", client_ip(request), detail=row.target)
    return row


@router.post(
    "/targets/{target_id}/reject",
    response_model=ScopeTargetResponse,
    dependencies=[Depends(require_role("admin"))],
)
def reject_target(
    target_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(ScopeTarget, target_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target not found")
    row.status = "rejected"
    row.approved_by_id = user.id
    row.approved_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, user.id, "scope_target_rejected", "scan_scope", client_ip(request), detail=row.target)
    return row


@router.post(
    "/targets/{target_id}/revoke",
    response_model=ScopeTargetResponse,
    dependencies=[Depends(require_role("admin"))],
)
def revoke_target(target_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(ScopeTarget, target_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target not found")
    row.status = "revoked"
    db.commit()
    log_action(db, user.id, "scope_target_revoked", "scan_scope", detail=row.target)
    return row
