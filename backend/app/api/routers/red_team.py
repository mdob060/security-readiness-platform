from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.auth import User
from app.models.scanning import ScanJob, ScopeTarget
from app.schemas.scanning import ScanJobCreate, ScanJobDetailResponse, ScanJobResponse
from app.services.audit import log_action
from app.services.job_runner import execute_scan_job, run_in_background
from app.services.scan_targets import TargetValidationError, enforce_network_scope
from app.services.tools import OFFENSIVE_TOOLS

router = APIRouter(prefix="/api/red-team", tags=["red-team"])


@router.get("/tools")
def list_tools():
    return {"tools": sorted(OFFENSIVE_TOOLS)}


@router.get("/jobs", response_model=list[ScanJobResponse])
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ScanJob).order_by(ScanJob.id.desc()).limit(100).all()


@router.get("/jobs/{job_id}", response_model=ScanJobDetailResponse)
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.get(ScanJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job


@router.post("/jobs", response_model=ScanJobResponse, dependencies=[Depends(require_role("analyst"))])
def create_job(
    payload: ScanJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.tool not in OFFENSIVE_TOOLS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported tool '{payload.tool}'")

    target_row = db.get(ScopeTarget, payload.target_id)
    if target_row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan scope target not found")
    if target_row.status != "approved":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This target has not been approved in Scan Scope. Request and obtain approval before scanning.",
        )
    if target_row.expires_at and target_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Approval for this target has expired")

    try:
        enforce_network_scope(target_row.target)
    except TargetValidationError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc

    job = ScanJob(target_id=target_row.id, tool=payload.tool, started_by_id=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)

    log_action(db, user.id, "red_team_scan_started", "red_team", detail=f"{payload.tool} -> {target_row.target}")
    background_tasks.add_task(run_in_background, execute_scan_job, job.id)
    return job
