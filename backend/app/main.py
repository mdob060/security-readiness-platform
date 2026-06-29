from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, SessionLocal
from . import models
from .seed_data import LIBYAN_TENANTS, SAMPLE_VULNERABILITIES, SAMPLE_INCIDENTS, SIGMA_RULES, THREAT_INTEL_IOCS
from .api import dashboard, tenants, incidents, vulnerabilities, threat_intel, reports, sigma_rules, scanner
from datetime import datetime, timedelta
import random

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sovereign Security Platform API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["tenants"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(vulnerabilities.router, prefix="/api/vulnerabilities", tags=["vulnerabilities"])
app.include_router(threat_intel.router, prefix="/api/threat-intel", tags=["threat-intel"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(sigma_rules.router, prefix="/api/sigma-rules", tags=["sigma-rules"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["scanner"])


@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    try:
        if db.query(models.Tenant).count() > 0:
            return

        tenant_objs = []
        for t in LIBYAN_TENANTS:
            tenant = models.Tenant(
                name=t["name"],
                domain=t["domain"],
                industry=t["industry"],
                sector=t.get("sector", ""),
                country="LY",
                status="active",
                risk_score=t["risk_score"],
            )
            db.add(tenant)
            tenant_objs.append(tenant)
        db.flush()

        for t_obj in tenant_objs:
            asset = models.Asset(
                tenant_id=t_obj.id,
                name=f"الموقع الرئيسي - {t_obj.name}",
                url=f"https://{t_obj.domain}",
                asset_type="web",
                status="active",
                risk_level="high" if t_obj.risk_score > 80 else "medium",
            )
            db.add(asset)
        db.flush()

        assets = db.query(models.Asset).all()
        for i, vuln_data in enumerate(SAMPLE_VULNERABILITIES):
            asset = assets[i % len(assets)]
            vuln = models.Vulnerability(
                asset_id=asset.id,
                tenant_id=asset.tenant_id,
                cve_id=vuln_data["cve_id"],
                title=vuln_data["title"],
                description=vuln_data["description"],
                severity=vuln_data["severity"],
                cvss_score=vuln_data["cvss_score"],
                status="open" if i % 3 != 0 else "remediated",
                affected_component=vuln_data["affected_component"],
                remediation=vuln_data["remediation"],
                discovered_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            )
            db.add(vuln)

        for i, inc_data in enumerate(SAMPLE_INCIDENTS):
            tenant = tenant_objs[i % len(tenant_objs)]
            incident = models.Incident(
                tenant_id=tenant.id,
                title=inc_data["title"],
                description=inc_data["description"],
                severity=inc_data["severity"],
                status=inc_data["status"],
                incident_type=inc_data["incident_type"],
                assigned_to=inc_data["assigned_to"],
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            )
            db.add(incident)

        for rule_data in SIGMA_RULES:
            rule = models.SigmaRule(
                title=rule_data["title"],
                description=rule_data["description"],
                level=rule_data["level"],
                category=rule_data["category"],
                detection=rule_data["detection"],
                tags=rule_data["tags"],
                author=rule_data["author"],
                status="stable",
                is_active=True,
            )
            db.add(rule)

        for ioc_data in THREAT_INTEL_IOCS:
            ioc = models.ThreatIntel(
                indicator=ioc_data["indicator"],
                indicator_type=ioc_data["indicator_type"],
                threat_type=ioc_data["threat_type"],
                confidence=ioc_data["confidence"],
                source=ioc_data["source"],
                description=ioc_data["description"],
                tags=ioc_data["tags"],
                is_active=True,
            )
            db.add(ioc)

        for tenant in tenant_objs[:5]:
            report = models.Report(
                tenant_id=tenant.id,
                title=f"تقرير الجاهزية الأمنية - {tenant.name}",
                report_type="engagement_summary",
                status="completed",
                generated_by="النظام",
                content=f"تقرير شامل لحالة الأمن السيبراني لـ {tenant.name}",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            )
            db.add(report)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


@app.get("/")
def root():
    return {"name": "Sovereign Security Platform", "version": "2.0.0", "status": "operational"}
