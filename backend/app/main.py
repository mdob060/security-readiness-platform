from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth as auth_router
from app.api.routers import blue_team, monitoring, red_team, scan_scope
from app.core.config import settings
from app.core.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.services.detection_engine import run_detection_cycle
from app.services.honeypot_listener import start_honeypots, stop_honeypots

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_honeypots()
    scheduler.add_job(run_detection_cycle, "interval", seconds=10, id="detection_cycle")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
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


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
