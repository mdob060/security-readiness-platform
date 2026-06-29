from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import socket
import ssl
import json

router = APIRouter()


class ScanRequest(BaseModel):
    target: str
    scan_type: str = "basic"
    tenant_id: Optional[int] = None


def check_http_headers(url: str) -> dict:
    findings = []
    try:
        import urllib.request
        if not url.startswith("http"):
            url = f"https://{url}"
        req = urllib.request.Request(url, headers={"User-Agent": "SovereignSecurityScanner/2.0"})
        try:
            response = urllib.request.urlopen(req, timeout=10)
            headers = dict(response.headers)
            security_headers = {
                "Strict-Transport-Security": "HSTS غير مفعّل - عرضة لهجمات SSL stripping",
                "X-Frame-Options": "X-Frame-Options غائب - عرضة لـ Clickjacking",
                "X-Content-Type-Options": "X-Content-Type-Options غائب - عرضة لـ MIME sniffing",
                "Content-Security-Policy": "CSP غير مضبوط - عرضة لـ XSS",
                "X-XSS-Protection": "X-XSS-Protection غائب",
                "Referrer-Policy": "Referrer-Policy غائب",
            }
            for header, message in security_headers.items():
                if header.lower() not in {k.lower() for k in headers.keys()}:
                    findings.append({"type": "missing_header", "header": header, "message": message, "severity": "medium"})
            server = headers.get("Server", "")
            if server:
                findings.append({"type": "info_disclosure", "message": f"Server header مكشوف: {server}", "severity": "low"})
        except Exception as e:
            findings.append({"type": "error", "message": f"HTTP check failed: {str(e)}", "severity": "info"})
    except Exception as e:
        findings.append({"type": "error", "message": str(e), "severity": "info"})
    return findings


def check_dns(domain: str) -> dict:
    results = {}
    try:
        ip = socket.gethostbyname(domain)
        results["ip"] = ip
        results["resolved"] = True
    except Exception:
        results["resolved"] = False
        results["ip"] = None
    return results


def check_ssl(domain: str) -> dict:
    result = {"has_ssl": False, "issuer": None, "expiry": None, "findings": []}
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10)
            s.connect((domain, 443))
            cert = s.getpeercert()
            result["has_ssl"] = True
            issuer = dict(x[0] for x in cert.get("issuer", []))
            result["issuer"] = issuer.get("organizationName", "Unknown")
            result["expiry"] = cert.get("notAfter")
    except ssl.SSLError as e:
        result["findings"].append({"type": "ssl_error", "message": str(e), "severity": "high"})
    except Exception:
        result["findings"].append({"type": "no_ssl", "message": "لا يوجد شهادة SSL على المنفذ 443", "severity": "high"})
    return result


def run_scan(db: Session, asset_id: int, target: str, scan_type: str):
    scan = db.query(models.ScanResult).filter(
        models.ScanResult.asset_id == asset_id,
        models.ScanResult.status == "running"
    ).first()
    if not scan:
        return

    domain = target.replace("https://", "").replace("http://", "").split("/")[0]
    all_findings = []

    dns_result = check_dns(domain)
    if not dns_result.get("resolved"):
        all_findings.append({"type": "dns_fail", "message": "فشل في تحليل اسم النطاق", "severity": "info"})

    ssl_result = check_ssl(domain)
    all_findings.extend(ssl_result.get("findings", []))

    if not ssl_result.get("has_ssl"):
        all_findings.append({"type": "no_https", "message": "الموقع لا يستخدم HTTPS", "severity": "high"})

    header_findings = check_http_headers(target if target.startswith("http") else f"https://{domain}")
    all_findings.extend(header_findings)

    risk_level = "low"
    if any(f["severity"] == "critical" for f in all_findings):
        risk_level = "critical"
    elif any(f["severity"] == "high" for f in all_findings):
        risk_level = "high"
    elif any(f["severity"] == "medium" for f in all_findings):
        risk_level = "medium"

    scan.status = "completed"
    scan.completed_at = datetime.utcnow()
    scan.findings = json.dumps(all_findings, ensure_ascii=False)
    scan.risk_level = risk_level
    scan.raw_output = json.dumps({
        "dns": dns_result,
        "ssl": {k: v for k, v in ssl_result.items() if k != "findings"},
        "target": target,
    }, ensure_ascii=False)
    db.commit()


@router.post("/scan")
def start_scan(payload: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    asset = None
    if payload.tenant_id:
        asset = db.query(models.Asset).filter(
            models.Asset.tenant_id == payload.tenant_id
        ).first()

    if not asset:
        asset = models.Asset(
            name=f"Scan Target: {payload.target}",
            url=payload.target,
            asset_type="web",
            status="active",
            risk_level="medium",
            tenant_id=payload.tenant_id or 1,
        )
        db.add(asset)
        db.flush()

    scan = models.ScanResult(
        asset_id=asset.id,
        scan_type=payload.scan_type,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(run_scan, db, asset.id, payload.target, payload.scan_type)

    return {"scan_id": scan.id, "status": "running", "target": payload.target}


@router.get("/results/{scan_id}")
def get_scan_result(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.ScanResult).filter(models.ScanResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    findings = json.loads(scan.findings) if scan.findings else []
    raw = json.loads(scan.raw_output) if scan.raw_output else {}
    return {
        "id": scan.id,
        "status": scan.status,
        "scan_type": scan.scan_type,
        "risk_level": scan.risk_level,
        "findings": findings,
        "raw_output": raw,
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }


@router.get("/history")
def scan_history(db: Session = Depends(get_db)):
    scans = db.query(models.ScanResult).order_by(models.ScanResult.started_at.desc()).limit(20).all()
    return [
        {
            "id": s.id,
            "status": s.status,
            "scan_type": s.scan_type,
            "risk_level": s.risk_level,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in scans
    ]
