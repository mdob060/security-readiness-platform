from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models
from datetime import datetime, timedelta
import random

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_tenants = db.query(models.Tenant).count()
    active_incidents = db.query(models.Incident).filter(
        models.Incident.status.in_(["open", "investigating"])
    ).count()
    critical_vulns = db.query(models.Vulnerability).filter(
        models.Vulnerability.severity == "critical",
        models.Vulnerability.status == "open"
    ).count()
    total_vulns = db.query(models.Vulnerability).filter(models.Vulnerability.status == "open").count()
    threats_blocked = random.randint(1200, 1800)
    avg_risk = db.query(func.avg(models.Tenant.risk_score)).scalar() or 0
    total_assets = db.query(models.Asset).count()
    total_iocs = db.query(models.ThreatIntel).filter(models.ThreatIntel.is_active == True).count()
    active_sigma = db.query(models.SigmaRule).filter(models.SigmaRule.is_active == True).count()

    return {
        "total_tenants": total_tenants,
        "active_incidents": active_incidents,
        "critical_vulns": critical_vulns,
        "total_vulns": total_vulns,
        "threats_blocked": threats_blocked,
        "avg_risk_score": round(avg_risk, 1),
        "total_assets": total_assets,
        "total_iocs": total_iocs,
        "active_sigma_rules": active_sigma,
        "platform_status": "operational",
    }


@router.get("/threat-activity")
def get_threat_activity():
    now = datetime.utcnow()
    data = []
    for i in range(30):
        day = now - timedelta(days=29 - i)
        data.append({
            "date": day.strftime("%Y-%m-%d"),
            "threats": random.randint(20, 150),
            "blocked": random.randint(15, 140),
            "incidents": random.randint(0, 8),
        })
    return data


@router.get("/risk-by-sector")
def get_risk_by_sector(db: Session = Depends(get_db)):
    sectors = db.query(models.Tenant.sector, func.avg(models.Tenant.risk_score)).group_by(models.Tenant.sector).all()
    return [{"sector": s[0] or "أخرى", "avg_risk": round(s[1], 1)} for s in sectors]


@router.get("/recent-incidents")
def get_recent_incidents(db: Session = Depends(get_db)):
    incidents = db.query(models.Incident).order_by(models.Incident.created_at.desc()).limit(5).all()
    result = []
    for inc in incidents:
        tenant = db.query(models.Tenant).filter(models.Tenant.id == inc.tenant_id).first()
        result.append({
            "id": inc.id,
            "title": inc.title,
            "severity": inc.severity,
            "status": inc.status,
            "tenant": tenant.name if tenant else "غير محدد",
            "created_at": inc.created_at.isoformat(),
        })
    return result


@router.get("/vulnerability-summary")
def get_vuln_summary(db: Session = Depends(get_db)):
    severities = ["critical", "high", "medium", "low"]
    result = {}
    for sev in severities:
        count = db.query(models.Vulnerability).filter(
            models.Vulnerability.severity == sev,
            models.Vulnerability.status == "open"
        ).count()
        result[sev] = count
    return result
