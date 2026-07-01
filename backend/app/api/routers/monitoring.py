import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.auth import User
from app.models.monitoring import (
    Alert,
    HoneypotEvent,
    Incident,
    IncidentTimelineEntry,
    PipelineEvent,
    SavedHuntQuery,
    SecurityEvent,
    SigmaRule,
)
from app.schemas.monitoring import (
    AlertResponse,
    AlertUpdate,
    HoneypotEventResponse,
    HuntQuery,
    IncidentResponse,
    IncidentTimelineCreate,
    IncidentTimelineResponse,
    IncidentUpdate,
    PipelineEventResponse,
    SavedHuntQueryCreate,
    SavedHuntQueryResponse,
    SecurityEventResponse,
    SigmaRuleCreate,
    SigmaRuleResponse,
)
from app.services.audit import log_action

soc_router = APIRouter(prefix="/api/soc", tags=["soc"])
incidents_router = APIRouter(prefix="/api/incidents", tags=["incidents"])
sigma_router = APIRouter(prefix="/api/sigma-rules", tags=["sigma-rules"])
honeypot_router = APIRouter(prefix="/api/honeypot", tags=["honeypot"])
hunting_router = APIRouter(prefix="/api/threat-hunting", tags=["threat-hunting"])
pipeline_router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@soc_router.get("/events", response_model=list[SecurityEventResponse])
def list_events(limit: int = 100, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SecurityEvent).order_by(SecurityEvent.id.desc()).limit(min(limit, 500)).all()


@soc_router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Alert)
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    return query.order_by(Alert.id.desc()).limit(200).all()


@soc_router.patch(
    "/alerts/{alert_id}", response_model=AlertResponse, dependencies=[Depends(require_role("analyst"))]
)
def update_alert(
    alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert.status = payload.status
    db.commit()
    log_action(db, user.id, "alert_status_updated", "soc", detail=f"alert={alert_id} -> {payload.status}")
    return alert


@sigma_router.get("", response_model=list[SigmaRuleResponse])
def list_rules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SigmaRule).order_by(SigmaRule.id.desc()).all()


@sigma_router.post("", response_model=SigmaRuleResponse, dependencies=[Depends(require_role("analyst"))])
def create_rule(payload: SigmaRuleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    import yaml

    try:
        yaml.safe_load(payload.yaml_definition)
    except yaml.YAMLError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid YAML: {exc}") from exc
    rule = SigmaRule(name=payload.name, yaml_definition=payload.yaml_definition, enabled=int(payload.enabled))
    db.add(rule)
    db.commit()
    db.refresh(rule)
    log_action(db, user.id, "sigma_rule_created", "sigma", detail=payload.name)
    return rule


@incidents_router.get("", response_model=list[IncidentResponse])
def list_incidents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Incident).order_by(Incident.id.desc()).all()


@incidents_router.get("/{incident_id}/timeline", response_model=list[IncidentTimelineResponse])
def get_timeline(incident_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(IncidentTimelineEntry)
        .filter(IncidentTimelineEntry.incident_id == incident_id)
        .order_by(IncidentTimelineEntry.id)
        .all()
    )


@incidents_router.post(
    "/{incident_id}/timeline",
    response_model=IncidentTimelineResponse,
    dependencies=[Depends(require_role("analyst"))],
)
def add_timeline_entry(
    incident_id: int,
    payload: IncidentTimelineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incident not found")
    entry = IncidentTimelineEntry(incident_id=incident_id, note=payload.note, author_id=user.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@incidents_router.patch(
    "/{incident_id}", response_model=IncidentResponse, dependencies=[Depends(require_role("analyst"))]
)
def update_incident(
    incident_id: int, payload: IncidentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    from datetime import datetime, timezone

    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Incident not found")
    incident.stage = payload.stage
    if payload.stage == "closed":
        incident.closed_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, user.id, "incident_stage_updated", "incidents", detail=f"incident={incident_id} -> {payload.stage}")
    return incident


@honeypot_router.get("/events", response_model=list[HoneypotEventResponse])
def list_honeypot_events(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(HoneypotEvent).order_by(HoneypotEvent.id.desc()).limit(200).all()


@honeypot_router.get("/ports")
def honeypot_ports():
    from app.services.honeypot_listener import HONEYPOT_PORTS

    return {"listeners": [{"port": port, "service": svc[0]} for port, svc in HONEYPOT_PORTS.items()]}


@hunting_router.post("/search", response_model=list[SecurityEventResponse])
def search_events(payload: HuntQuery, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(SecurityEvent)
    if payload.source:
        query = query.filter(SecurityEvent.source == payload.source)
    if payload.event_type:
        query = query.filter(SecurityEvent.event_type.ilike(f"%{payload.event_type}%"))
    if payload.source_ip:
        query = query.filter(SecurityEvent.source_ip == payload.source_ip)
    if payload.keyword:
        query = query.filter(SecurityEvent.detail.ilike(f"%{payload.keyword}%"))
    return query.order_by(SecurityEvent.id.desc()).limit(300).all()


@hunting_router.get("/saved", response_model=list[SavedHuntQueryResponse])
def list_saved_queries(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SavedHuntQuery).order_by(SavedHuntQuery.id.desc()).all()


@hunting_router.post("/saved", response_model=SavedHuntQueryResponse)
def save_query(payload: SavedHuntQueryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = SavedHuntQuery(
        name=payload.name,
        filters_json=json.dumps(payload.filters.model_dump()),
        created_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pipeline_router.get("/recent", response_model=list[PipelineEventResponse])
def recent_pipeline(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(PipelineEvent).order_by(PipelineEvent.id.desc()).limit(100).all()


@dashboard_router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.incidents import Incident as IncidentAlias  # noqa: F401

    return {
        "total_events_24h": db.query(SecurityEvent).count(),
        "open_alerts": db.query(Alert).filter(Alert.status == "open").count(),
        "critical_alerts": db.query(Alert).filter(Alert.severity == "critical", Alert.status == "open").count(),
        "open_incidents": db.query(Incident).filter(Incident.stage != "closed").count(),
        "honeypot_hits": db.query(HoneypotEvent).count(),
    }
