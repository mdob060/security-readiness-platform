from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class TenantCreate(BaseModel):
    name: str
    domain: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    risk_score: Optional[int] = 50


@router.get("/")
def list_tenants(db: Session = Depends(get_db), industry: Optional[str] = None):
    query = db.query(models.Tenant)
    if industry:
        query = query.filter(models.Tenant.industry == industry)
    tenants = query.all()
    result = []
    for t in tenants:
        vuln_count = db.query(models.Vulnerability).filter(
            models.Vulnerability.tenant_id == t.id,
            models.Vulnerability.status == "open"
        ).count()
        incident_count = db.query(models.Incident).filter(
            models.Incident.tenant_id == t.id,
            models.Incident.status.in_(["open", "investigating"])
        ).count()
        result.append({
            "id": t.id,
            "name": t.name,
            "domain": t.domain,
            "industry": t.industry,
            "sector": t.sector,
            "status": t.status,
            "risk_score": t.risk_score,
            "contact_email": t.contact_email,
            "open_vulns": vuln_count,
            "active_incidents": incident_count,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return result


@router.get("/{tenant_id}")
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    assets = db.query(models.Asset).filter(models.Asset.tenant_id == tenant_id).all()
    vulns = db.query(models.Vulnerability).filter(
        models.Vulnerability.tenant_id == tenant_id,
        models.Vulnerability.status == "open"
    ).count()
    incidents = db.query(models.Incident).filter(
        models.Incident.tenant_id == tenant_id
    ).count()
    return {
        "id": tenant.id,
        "name": tenant.name,
        "domain": tenant.domain,
        "industry": tenant.industry,
        "sector": tenant.sector,
        "status": tenant.status,
        "risk_score": tenant.risk_score,
        "contact_email": tenant.contact_email,
        "notes": tenant.notes,
        "assets": [{"id": a.id, "name": a.name, "url": a.url, "risk_level": a.risk_level} for a in assets],
        "open_vulns": vulns,
        "total_incidents": incidents,
    }


@router.post("/")
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    db_tenant = models.Tenant(**tenant.model_dump())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


@router.put("/{tenant_id}")
def update_tenant(tenant_id: int, tenant: TenantCreate, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for key, value in tenant.model_dump().items():
        setattr(db_tenant, key, value)
    db.commit()
    return db_tenant


@router.delete("/{tenant_id}")
def delete_tenant(tenant_id: int, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    db.delete(db_tenant)
    db.commit()
    return {"message": "Tenant deleted"}
