"""
NATIONAL CYBER DEFENSE PROTOTYPE C+
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .config import settings
from .routers import threats, responses

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="SOC Platform — Threat Intelligence & Automated Response Engine",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(threats.router)
app.include_router(responses.router)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "operational",
        "system": settings.app_name,
        "version": settings.version,
        "classification": settings.classification,
    }


@app.get("/api/v1/info")
def system_info():
    return {
        "name": settings.app_name,
        "version": settings.version,
        "classification": settings.classification,
        "modules": [
            {"id": "threat-intel", "name": "Threat Intelligence", "status": "active"},
            {"id": "auto-response", "name": "Automated Response", "status": "active"},
            {"id": "mitre-attack", "name": "MITRE ATT&CK", "version": settings.mitre_attack_version, "status": "active"},
        ],
        "auto_response_enabled": settings.auto_response_enabled,
    }
