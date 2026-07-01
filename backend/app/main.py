from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth as auth_router
from app.api.routers import blue_team, intelligence, management, monitoring, red_team, scan_scope, sectors
from app.core.config import settings
from app.core.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.services.detection_engine import run_detection_cycle
from app.services.honeypot_listener import start_honeypots, stop_honeypots

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.enable_embedded_honeypots:
        start_honeypots()
    if settings.enable_embedded_scheduler:
        scheduler.add_job(run_detection_cycle, "interval", seconds=10, id="detection_cycle")
        scheduler.start()
    yield
    if settings.enable_embedded_scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    if settings.enable_embedded_honeypots:
        stop_honeypots()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

app.include_router(auth_router.router)
app.include_router(scan_scope.router)
app.include_router(red_team.router)
app.include_router(blue_team.blue_team_router)
app.include_router(blue_team.vulnerabilities_router)
app.include_router(blue_team.pci_dss_router)
app.include_router(monitoring.soc_router)
app.include_router(monitoring.incidents_router)
app.include_router(monitoring.sigma_router)
app.include_router(monitoring.honeypot_router)
app.include_router(monitoring.hunting_router)
app.include_router(monitoring.pipeline_router)
app.include_router(monitoring.dashboard_router)
app.include_router(intelligence.ai_brain_router)
app.include_router(intelligence.automation_router)
app.include_router(intelligence.threat_intel_router)
app.include_router(intelligence.federation_router)
app.include_router(sectors.banking_router)
app.include_router(sectors.ot_scada_router)
app.include_router(sectors.ueba_router)
app.include_router(sectors.swift_csp_router)
app.include_router(sectors.aml_router)
app.include_router(sectors.sector_monitor_router)
app.include_router(management.grc_router)
app.include_router(management.tenants_router)
app.include_router(management.analytics_router)
app.include_router(management.reports_router)
app.include_router(management.phishing_router)
app.include_router(management.settings_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
