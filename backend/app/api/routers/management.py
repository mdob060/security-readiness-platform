import secrets
import threading

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import SessionLocal, get_db
from app.models.auth import User
from app.models.management import (
    GrcControl,
    ModuleSetting,
    PhishingCampaign,
    PhishingClickEvent,
    PhishingTarget,
    ReportJob,
    RiskRegisterEntry,
)
from app.models.monitoring import Alert, Incident, SecurityEvent
from app.models.scanning import ScanJob
from app.models.tenants import Tenant
from app.schemas.management import (
    GrcControlResponse,
    GrcControlUpdate,
    ModuleSettingResponse,
    ModuleSettingUpdate,
    PhishingCampaignCreate,
    PhishingCampaignResponse,
    ReportJobCreate,
    ReportJobResponse,
    RiskRegisterCreate,
    RiskRegisterResponse,
    TenantCreate,
    TenantResponse,
)
from app.services.audit import log_action
from app.services.report_generator import generate_report_pdf

grc_router = APIRouter(prefix="/api/grc", tags=["grc"])
tenants_router = APIRouter(prefix="/api/tenants", tags=["tenants"])
analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])
reports_router = APIRouter(prefix="/api/reports", tags=["reports"])
phishing_router = APIRouter(prefix="/api/phishing", tags=["phishing"])
settings_router = APIRouter(prefix="/api/settings", tags=["settings"])


@grc_router.get("/controls", response_model=list[GrcControlResponse])
def list_controls(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(GrcControl).all()


@grc_router.patch("/controls/{control_id}", response_model=GrcControlResponse, dependencies=[Depends(require_role("analyst"))])
def update_control(control_id: int, payload: GrcControlUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    control = db.get(GrcControl, control_id)
    if control is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
    control.status = payload.status
    db.commit()
    return control


@grc_router.get("/risk-register", response_model=list[RiskRegisterResponse])
def list_risks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(RiskRegisterEntry).order_by(RiskRegisterEntry.id.desc()).all()


@grc_router.post("/risk-register", response_model=RiskRegisterResponse, dependencies=[Depends(require_role("analyst"))])
def create_risk(payload: RiskRegisterCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    risk = RiskRegisterEntry(**payload.model_dump(), owner_id=user.id)
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


@tenants_router.get("", response_model=list[TenantResponse])
def list_tenants(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Tenant).all()


@tenants_router.post("", response_model=TenantResponse, dependencies=[Depends(require_role("admin"))])
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    log_action(db, user.id, "tenant_created", "tenants", detail=payload.name)
    return tenant


@analytics_router.get("/overview")
def analytics_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from sqlalchemy import func

    events_by_source = dict(db.query(SecurityEvent.source, func.count(SecurityEvent.id)).group_by(SecurityEvent.source).all())
    alerts_by_severity = dict(db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all())
    tool_usage = dict(db.query(ScanJob.tool, func.count(ScanJob.id)).group_by(ScanJob.tool).all())

    closed_incidents = db.query(Incident).filter(Incident.closed_at.isnot(None)).all()
    if closed_incidents:
        avg_seconds = sum((i.closed_at - i.created_at).total_seconds() for i in closed_incidents) / len(closed_incidents)
        mttr_minutes = round(avg_seconds / 60, 1)
    else:
        mttr_minutes = None

    return {
        "events_by_source": events_by_source,
        "alerts_by_severity": alerts_by_severity,
        "tool_usage": tool_usage,
        "mean_time_to_resolve_minutes": mttr_minutes,
        "total_incidents": db.query(Incident).count(),
        "total_scan_jobs": db.query(ScanJob).count(),
    }


def _run_report_job(job_id: int, report_type: str) -> None:
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        job = db.get(ReportJob, job_id)
        if job is None:
            return
        file_path = generate_report_pdf(db, report_type, job_id)
        job.file_path = file_path
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


@reports_router.post("", response_model=ReportJobResponse, dependencies=[Depends(require_role("analyst"))])
def create_report(payload: ReportJobCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = ReportJob(report_type=payload.report_type, requested_by_id=user.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    threading.Thread(target=_run_report_job, args=(job.id, payload.report_type), daemon=True).start()
    return job


@reports_router.get("", response_model=list[ReportJobResponse])
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ReportJob).order_by(ReportJob.id.desc()).limit(50).all()


@phishing_router.post("/campaigns", response_model=PhishingCampaignResponse, dependencies=[Depends(require_role("analyst"))])
def create_campaign(payload: PhishingCampaignCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = PhishingCampaign(name=payload.name, template=payload.template, created_by_id=user.id)
    db.add(campaign)
    db.flush()
    for email in payload.target_emails:
        db.add(PhishingTarget(campaign_id=campaign.id, email=email, tracking_token=secrets.token_urlsafe(16)))
    db.commit()
    db.refresh(campaign)
    return campaign


@phishing_router.get("/campaigns/{campaign_id}/stats")
def campaign_stats(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    targets = db.query(PhishingTarget).filter(PhishingTarget.campaign_id == campaign_id).all()
    clicked = 0
    for t in targets:
        if db.query(PhishingClickEvent).filter(PhishingClickEvent.target_id == t.id).first():
            clicked += 1
    return {"total_targets": len(targets), "clicked": clicked, "click_rate": round(clicked / len(targets) * 100, 1) if targets else 0.0}


@phishing_router.get("/track/{token}", response_class=HTMLResponse)
def track_click(token: str, db: Session = Depends(get_db)):
    target = db.query(PhishingTarget).filter(PhishingTarget.tracking_token == token).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid tracking link")
    db.add(PhishingClickEvent(target_id=target.id))
    db.commit()
    return (
        "<html><body style='font-family:sans-serif;background:#111;color:#eee;text-align:center;padding:60px'>"
        "<h1>This was a phishing simulation</h1>"
        "<p>You clicked a link from a simulated phishing awareness exercise run by your security team.</p>"
        "<p>No credentials were captured. Please report suspicious emails like this one to your SOC.</p>"
        "</body></html>"
    )


@settings_router.get("", response_model=list[ModuleSettingResponse])
def list_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ModuleSetting).order_by(ModuleSetting.module_key).all()


@settings_router.patch("/{module_key}", response_model=ModuleSettingResponse, dependencies=[Depends(require_role("admin"))])
def update_setting(module_key: str, payload: ModuleSettingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    setting = db.query(ModuleSetting).filter(ModuleSetting.module_key == module_key).first()
    if setting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module not found")
    setting.enabled = payload.enabled
    db.commit()
    log_action(db, user.id, "module_setting_updated", "settings", detail=f"{module_key} -> enabled={payload.enabled}")
    return setting
