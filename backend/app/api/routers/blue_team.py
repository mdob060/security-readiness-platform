import psutil
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.auth import User
from app.models.scanning import PciDssControl, SystemScan
from app.schemas.blue_team import Fail2banJailStatus, PciDssReport
from app.schemas.scanning import SystemScanCreate, SystemScanDetailResponse, SystemScanResponse
from app.services.audit import log_action
from app.services.fail2ban_status import get_jail_status
from app.services.job_runner import execute_system_scan, run_in_background
from app.services.pci_dss import evaluate_pci_dss
from app.services.tools import DEFENSIVE_TOOLS

blue_team_router = APIRouter(prefix="/api/blue-team", tags=["blue-team"])
vulnerabilities_router = APIRouter(prefix="/api/vulnerabilities", tags=["vulnerabilities"])
pci_dss_router = APIRouter(prefix="/api/pci-dss", tags=["pci-dss"])


KNOWN_CVE_CHECKLIST = [
    {"cve_id": "CVE-2021-44228", "title": "Log4Shell - Apache Log4j RCE", "severity": "critical",
     "note": "Check for vulnerable log4j-core versions < 2.17.1"},
    {"cve_id": "CVE-2014-0160", "title": "Heartbleed - OpenSSL", "severity": "critical",
     "note": "Check OpenSSL 1.0.1 - 1.0.1f are vulnerable"},
    {"cve_id": "CVE-2017-5638", "title": "Apache Struts2 RCE", "severity": "critical",
     "note": "Content-Type header OGNL injection"},
    {"cve_id": "CVE-2021-34527", "title": "PrintNightmare - Windows Print Spooler", "severity": "critical",
     "note": "Remote code execution via spooler service"},
    {"cve_id": "CVE-2019-0708", "title": "BlueKeep - RDP RCE", "severity": "critical",
     "note": "Pre-auth RCE in Remote Desktop Services"},
    {"cve_id": "CVE-2023-4863", "title": "libwebp heap buffer overflow", "severity": "high",
     "note": "Affects browsers and apps using libwebp"},
]


@blue_team_router.get("/tools")
def list_tools():
    return {"tools": sorted(DEFENSIVE_TOOLS)}


@blue_team_router.get("/system-resources")
def system_resources(user: User = Depends(get_current_user)):
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "load_average": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None,
        "boot_time": psutil.boot_time(),
    }


@blue_team_router.get("/fail2ban", response_model=Fail2banJailStatus)
def fail2ban_status(user: User = Depends(get_current_user)):
    return get_jail_status()


@blue_team_router.get("/scans", response_model=list[SystemScanResponse])
def list_scans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SystemScan).order_by(SystemScan.id.desc()).limit(100).all()


@blue_team_router.get("/scans/{scan_id}", response_model=SystemScanDetailResponse)
def get_scan(scan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scan = db.get(SystemScan, scan_id)
    if scan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")
    return scan


@blue_team_router.post("/scans", response_model=SystemScanResponse, dependencies=[Depends(require_role("analyst"))])
def create_scan(
    payload: SystemScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.tool not in DEFENSIVE_TOOLS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported tool '{payload.tool}'")
    scan = SystemScan(tool=payload.tool, started_by_id=user.id)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    log_action(db, user.id, "blue_team_scan_started", "blue_team", detail=payload.tool)
    background_tasks.add_task(run_in_background, execute_system_scan, scan.id)
    return scan


@vulnerabilities_router.get("/cve-checklist")
def cve_checklist(user: User = Depends(get_current_user)):
    return {"items": KNOWN_CVE_CHECKLIST}


@vulnerabilities_router.get("/latest-lynis-scan", response_model=SystemScanResponse | None)
def latest_lynis_scan(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(SystemScan)
        .filter(SystemScan.tool == "lynis")
        .order_by(SystemScan.id.desc())
        .first()
    )


@pci_dss_router.get("/report", response_model=PciDssReport)
def pci_dss_report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    controls = db.query(PciDssControl).all()
    percentage, results = evaluate_pci_dss(db, controls)
    return {"compliance_percentage": percentage, "controls": results}
