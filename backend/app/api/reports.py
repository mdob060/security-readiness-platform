from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class ReportCreate(BaseModel):
    tenant_id: int
    title: str
    report_type: str = "engagement_summary"


@router.get("/")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(models.Report).order_by(models.Report.created_at.desc()).all()
    result = []
    for r in reports:
        tenant = db.query(models.Tenant).filter(models.Tenant.id == r.tenant_id).first()
        result.append({
            "id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "status": r.status,
            "tenant_name": tenant.name if tenant else "غير محدد",
            "generated_by": r.generated_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result


@router.post("/generate")
def generate_report(payload: ReportCreate, db: Session = Depends(get_db)):
    tenant = db.query(models.Tenant).filter(models.Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    vulns = db.query(models.Vulnerability).filter(
        models.Vulnerability.tenant_id == payload.tenant_id,
        models.Vulnerability.status == "open"
    ).all()
    incidents = db.query(models.Incident).filter(
        models.Incident.tenant_id == payload.tenant_id
    ).all()

    critical = sum(1 for v in vulns if v.severity == "critical")
    high = sum(1 for v in vulns if v.severity == "high")

    content = f"""
# {payload.title}

## معلومات العميل
- **الاسم**: {tenant.name}
- **النطاق**: {tenant.domain}
- **القطاع**: {tenant.sector}
- **درجة المخاطرة**: {tenant.risk_score}/100

## ملخص الثغرات
- إجمالي الثغرات المفتوحة: {len(vulns)}
- حرجة: {critical}
- عالية: {high}

## ملخص الحوادث
- إجمالي الحوادث: {len(incidents)}
- المفتوحة: {sum(1 for i in incidents if i.status == 'open')}

## التوصيات
1. معالجة الثغرات الحرجة فوراً
2. تحديث جميع الأنظمة
3. مراجعة صلاحيات الوصول
4. تفعيل المصادقة الثنائية
5. إجراء اختبار اختراق دوري
    """

    report = models.Report(
        tenant_id=payload.tenant_id,
        title=payload.title,
        report_type=payload.report_type,
        status="completed",
        content=content,
        generated_by="النظام الآلي",
        created_at=datetime.utcnow(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "title": report.title, "status": report.status, "content": content}


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    tenant = db.query(models.Tenant).filter(models.Tenant.id == report.tenant_id).first()
    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type,
        "status": report.status,
        "content": report.content,
        "tenant_name": tenant.name if tenant else "غير محدد",
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }
