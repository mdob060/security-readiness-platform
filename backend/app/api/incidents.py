from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class IncidentCreate(BaseModel):
    tenant_id: int
    title: str
    description: Optional[str] = None
    severity: Optional[str] = "medium"
    incident_type: Optional[str] = None
    assigned_to: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
def list_incidents(db: Session = Depends(get_db), status: Optional[str] = None, severity: Optional[str] = None):
    query = db.query(models.Incident)
    if status:
        query = query.filter(models.Incident.status == status)
    if severity:
        query = query.filter(models.Incident.severity == severity)
    incidents = query.order_by(models.Incident.created_at.desc()).all()
    result = []
    for inc in incidents:
        tenant = db.query(models.Tenant).filter(models.Tenant.id == inc.tenant_id).first()
        result.append({
            "id": inc.id,
            "title": inc.title,
            "description": inc.description,
            "severity": inc.severity,
            "status": inc.status,
            "incident_type": inc.incident_type,
            "assigned_to": inc.assigned_to,
            "tenant_name": tenant.name if tenant else "غير محدد",
            "tenant_id": inc.tenant_id,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
        })
    return result


@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    tenant = db.query(models.Tenant).filter(models.Tenant.id == inc.tenant_id).first()
    return {
        "id": inc.id,
        "title": inc.title,
        "description": inc.description,
        "severity": inc.severity,
        "status": inc.status,
        "incident_type": inc.incident_type,
        "assigned_to": inc.assigned_to,
        "tenant_name": tenant.name if tenant else "غير محدد",
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
    }


@router.post("/")
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    db_incident = models.Incident(**incident.model_dump(), status="open")
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident


@router.patch("/{incident_id}")
def update_incident(incident_id: int, update: IncidentUpdate, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if update.status:
        inc.status = update.status
        if update.status == "resolved":
            inc.resolved_at = datetime.utcnow()
    if update.assigned_to:
        inc.assigned_to = update.assigned_to
    if update.description:
        inc.description = update.description
    inc.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Incident updated", "id": incident_id}
