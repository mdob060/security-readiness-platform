from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class VulnCreate(BaseModel):
    tenant_id: int
    asset_id: Optional[int] = None
    cve_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    cvss_score: Optional[float] = None
    affected_component: Optional[str] = None
    remediation: Optional[str] = None


@router.get("/")
def list_vulnerabilities(
    db: Session = Depends(get_db),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: Optional[int] = None,
):
    query = db.query(models.Vulnerability)
    if severity:
        query = query.filter(models.Vulnerability.severity == severity)
    if status:
        query = query.filter(models.Vulnerability.status == status)
    if tenant_id:
        query = query.filter(models.Vulnerability.tenant_id == tenant_id)
    vulns = query.order_by(models.Vulnerability.cvss_score.desc()).all()
    result = []
    for v in vulns:
        tenant = db.query(models.Tenant).filter(models.Tenant.id == v.tenant_id).first()
        asset = db.query(models.Asset).filter(models.Asset.id == v.asset_id).first() if v.asset_id else None
        result.append({
            "id": v.id,
            "cve_id": v.cve_id,
            "title": v.title,
            "description": v.description,
            "severity": v.severity,
            "cvss_score": v.cvss_score,
            "status": v.status,
            "affected_component": v.affected_component,
            "remediation": v.remediation,
            "tenant_name": tenant.name if tenant else "غير محدد",
            "asset_name": asset.name if asset else None,
            "discovered_at": v.discovered_at.isoformat() if v.discovered_at else None,
        })
    return result


@router.post("/")
def create_vulnerability(vuln: VulnCreate, db: Session = Depends(get_db)):
    db_vuln = models.Vulnerability(**vuln.model_dump(), status="open")
    db.add(db_vuln)
    db.commit()
    db.refresh(db_vuln)
    return db_vuln


@router.patch("/{vuln_id}/remediate")
def remediate_vulnerability(vuln_id: int, db: Session = Depends(get_db)):
    vuln = db.query(models.Vulnerability).filter(models.Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    vuln.status = "remediated"
    vuln.remediated_at = datetime.utcnow()
    db.commit()
    return {"message": "Vulnerability marked as remediated"}


@router.get("/stats/summary")
def vuln_stats(db: Session = Depends(get_db)):
    total = db.query(models.Vulnerability).count()
    open_count = db.query(models.Vulnerability).filter(models.Vulnerability.status == "open").count()
    critical = db.query(models.Vulnerability).filter(
        models.Vulnerability.severity == "critical", models.Vulnerability.status == "open"
    ).count()
    high = db.query(models.Vulnerability).filter(
        models.Vulnerability.severity == "high", models.Vulnerability.status == "open"
    ).count()
    return {"total": total, "open": open_count, "critical": critical, "high": high}
