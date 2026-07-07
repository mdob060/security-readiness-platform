from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import socket, ssl, json, subprocess, shutil, re

router = APIRouter()

KALI_TOOLS = {
    "nmap":     shutil.which("nmap"),
    "nikto":    shutil.which("nikto"),
    "whatweb":  shutil.which("whatweb"),
    "gobuster": shutil.which("gobuster"),
    "wafw00f":  shutil.which("wafw00f"),
    "whois":    shutil.which("whois"),
    "dig":      shutil.which("dig"),
    "curl":     shutil.which("curl"),
}


class ScanRequest(BaseModel):
    target: str
    scan_type: str = "basic"
    tenant_id: Optional[int] = None
    options: Optional[dict] = None


def run_cmd(cmd: list, timeout: int = 60) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] الأمر تجاوز {timeout} ثانية"
    except FileNotFoundError:
        return f"[NOT FOUND] الأداة غير موجودة: {cmd[0]}"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def nmap_scan(target: str, fast: bool = True) -> dict:
    if not KALI_TOOLS["nmap"]:
        return {"available": False, "output": "nmap غير مثبّت"}
    flags = ["-sV", "-sC", "--open", "-T4"] if fast else ["-sV", "-sC", "-A", "--open", "-T3"]
    output = run_cmd(["nmap"] + flags + [target], timeout=120)
    findings = []
    open_ports = []
    for line in output.splitlines():
        if "/tcp" in line and "open" in line:
            parts = line.split()
            if len(parts) >= 3:
                port = parts[0].split("/")[0]
                service = parts[2] if len(parts) > 2 else "unknown"
                version = " ".join(parts[3:]) if len(parts) > 3 else ""
                open_ports.append({"port": port, "service": service, "version": version})
                if any(svc in service.lower() for svc in ["telnet", "ftp", "vnc", "rdp"]):
                    findings.append({"type": "dangerous_service", "message": f"خدمة خطيرة مكتشفة: {service} على المنفذ {port}", "severity": "high", "port": port})
                if service in ["http"] and port not in ["80"]:
                    findings.append({"type": "http_non_standard", "message": f"HTTP على منفذ غير قياسي: {port}", "severity": "medium", "port": port})
    if not findings and open_ports:
        findings.append({"type": "info", "message": f"تم اكتشاف {len(open_ports)} منفذ مفتوح", "severity": "info"})
    return {"available": True, "open_ports": open_ports, "findings": findings, "raw": output}


def nikto_scan(target: str) -> dict:
    if not KALI_TOOLS["nikto"]:
        return {"available": False, "output": "nikto غير مثبّت"}
    url = target if target.startswith("http") else f"http://{target}"
    output = run_cmd(["nikto", "-h", url, "-maxtime", "60", "-nointeractive"], timeout=90)
    findings = []
    for line in output.splitlines():
        if line.startswith("+ "):
            content = line[2:]
            severity = "high" if any(k in content.lower() for k in ["sql", "xss", "rce", "injection", "backdoor"]) else \
                       "medium" if any(k in content.lower() for k in ["outdated", "vulnerable", "exposed", "header"]) else "low"
            findings.append({"type": "nikto", "message": content, "severity": severity})
    return {"available": True, "findings": findings, "raw": output}


def whatweb_scan(target: str) -> dict:
    if not KALI_TOOLS["whatweb"]:
        return {"available": False, "output": "whatweb غير مثبّت"}
    url = target if target.startswith("http") else f"http://{target}"
    output = run_cmd(["whatweb", "--color=never", "-a", "3", url], timeout=30)
    findings = []
    technologies = []
    tech_patterns = [
        (r"WordPress\[([^\]]+)\]", "WordPress"),
        (r"Joomla\[([^\]]+)\]", "Joomla"),
        (r"Drupal\[([^\]]+)\]", "Drupal"),
        (r"Apache\[([^\]]+)\]", "Apache"),
        (r"nginx\[([^\]]+)\]", "nginx"),
        (r"PHP\[([^\]]+)\]", "PHP"),
        (r"jQuery\[([^\]]+)\]", "jQuery"),
        (r"Bootstrap\[([^\]]+)\]", "Bootstrap"),
    ]
    for pattern, name in tech_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            version = match.group(1)
            technologies.append({"name": name, "version": version})
            findings.append({"type": "technology", "message": f"تقنية مكتشفة: {name} {version}", "severity": "info"})
    if "X-Powered-By" in output:
        findings.append({"type": "header", "message": "X-Powered-By header مكشوف - يُكشف عن تقنيات الخادم", "severity": "low"})
    return {"available": True, "technologies": technologies, "findings": findings, "raw": output}


def wafw00f_scan(target: str) -> dict:
    if not KALI_TOOLS["wafw00f"]:
        return {"available": False, "output": "wafw00f غير مثبّت"}
    url = target if target.startswith("http") else f"http://{target}"
    output = run_cmd(["wafw00f", url], timeout=30)
    has_waf = "is behind" in output.lower() or "detected" in output.lower()
    waf_name = None
    match = re.search(r"is behind (.+)", output, re.IGNORECASE)
    if match:
        waf_name = match.group(1).strip()
    findings = []
    if has_waf:
        findings.append({"type": "waf_detected", "message": f"WAF مكتشف: {waf_name or 'غير محدد'}", "severity": "info"})
    else:
        findings.append({"type": "no_waf", "message": "لم يتم اكتشاف WAF - الموقع بدون حماية WAF", "severity": "medium"})
    return {"available": True, "has_waf": has_waf, "waf_name": waf_name, "findings": findings, "raw": output}


def whois_lookup(domain: str) -> dict:
    if not KALI_TOOLS["whois"]:
        return {"available": False}
    output = run_cmd(["whois", domain], timeout=30)
    info = {}
    for line in output.splitlines():
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()
            if "registrar" in key and "registrar" not in info:
                info["registrar"] = value
            elif "creation date" in key or "created" in key:
                info["created"] = value
            elif "expiry date" in key or "expir" in key:
                info["expires"] = value
            elif "registrant" in key and "country" in key:
                info["country"] = value
    return {"available": True, "info": info, "raw": output[:2000]}


def dns_info(domain: str) -> dict:
    result = {"resolved": False, "ip": None, "records": {}}
    try:
        ip = socket.gethostbyname(domain)
        result["resolved"] = True
        result["ip"] = ip
    except Exception:
        pass
    if KALI_TOOLS["dig"]:
        for rtype in ["A", "MX", "NS", "TXT"]:
            out = run_cmd(["dig", "+short", rtype, domain], timeout=10)
            if out.strip():
                result["records"][rtype] = [r.strip() for r in out.strip().splitlines() if r.strip()]
    return result


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
        result["findings"].append({"type": "ssl_error", "message": f"خطأ SSL: {str(e)}", "severity": "high"})
    except Exception:
        result["findings"].append({"type": "no_ssl", "message": "لا توجد شهادة SSL - الموقع غير آمن", "severity": "high"})
    return result


def check_security_headers(target: str) -> list:
    findings = []
    if not KALI_TOOLS["curl"]:
        return findings
    url = target if target.startswith("http") else f"https://{target}"
    output = run_cmd(["curl", "-sI", "--max-time", "10", "-L", url], timeout=15)
    headers_lower = output.lower()
    checks = {
        "strict-transport-security": ("HSTS غير مفعّل - عرضة لهجمات downgrade", "medium"),
        "x-frame-options": ("X-Frame-Options غائب - عرضة لـ Clickjacking", "medium"),
        "x-content-type-options": ("X-Content-Type-Options غائب - عرضة لـ MIME sniffing", "low"),
        "content-security-policy": ("Content-Security-Policy غائب - عرضة لـ XSS", "medium"),
        "referrer-policy": ("Referrer-Policy غائب", "low"),
        "permissions-policy": ("Permissions-Policy غائب", "low"),
    }
    for header, (message, severity) in checks.items():
        if header not in headers_lower:
            findings.append({"type": "missing_header", "header": header, "message": message, "severity": severity})
    server_match = re.search(r"server: (.+)", headers_lower)
    if server_match:
        findings.append({"type": "server_disclosure", "message": f"Server header مكشوف: {server_match.group(1).strip()}", "severity": "low"})
    if "x-powered-by:" in headers_lower:
        findings.append({"type": "tech_disclosure", "message": "X-Powered-By header مكشوف", "severity": "low"})
    return findings


def full_scan(db: Session, scan_id: int, target: str, scan_type: str):
    scan = db.query(models.ScanResult).filter(models.ScanResult.id == scan_id).first()
    if not scan:
        return

    domain = target.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    all_findings = []
    raw_data = {"target": target, "domain": domain, "tools": {}}

    dns = dns_info(domain)
    raw_data["dns"] = dns
    if not dns["resolved"]:
        all_findings.append({"type": "dns_fail", "message": "فشل في تحليل اسم النطاق DNS", "severity": "info"})

    ssl_result = check_ssl(domain)
    raw_data["ssl"] = {k: v for k, v in ssl_result.items() if k != "findings"}
    all_findings.extend(ssl_result.get("findings", []))
    if not ssl_result["has_ssl"]:
        all_findings.append({"type": "no_https", "message": "الموقع لا يستخدم HTTPS", "severity": "high"})

    header_findings = check_security_headers(target)
    all_findings.extend(header_findings)
    raw_data["tools"]["headers"] = f"{len(header_findings)} مشكلة مكتشفة"

    whois_result = whois_lookup(domain)
    raw_data["tools"]["whois"] = whois_result.get("info", {})

    if scan_type in ["basic", "full", "nmap"]:
        nmap_result = nmap_scan(domain, fast=(scan_type != "full"))
        raw_data["tools"]["nmap"] = {"ports": nmap_result.get("open_ports", []), "raw": nmap_result.get("raw", "")[:3000]}
        all_findings.extend(nmap_result.get("findings", []))

    if scan_type in ["web", "full", "nikto"]:
        nikto_result = nikto_scan(target)
        raw_data["tools"]["nikto"] = nikto_result.get("raw", "")[:3000]
        all_findings.extend(nikto_result.get("findings", []))

    whatweb_result = whatweb_scan(target)
    raw_data["tools"]["whatweb"] = whatweb_result.get("technologies", [])
    all_findings.extend(whatweb_result.get("findings", []))

    wafw00f_result = wafw00f_scan(target)
    raw_data["tools"]["wafw00f"] = {"has_waf": wafw00f_result.get("has_waf"), "name": wafw00f_result.get("waf_name")}
    all_findings.extend(wafw00f_result.get("findings", []))

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    all_findings.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 5))

    if any(f["severity"] == "critical" for f in all_findings):
        risk_level = "critical"
    elif any(f["severity"] == "high" for f in all_findings):
        risk_level = "high"
    elif any(f["severity"] == "medium" for f in all_findings):
        risk_level = "medium"
    else:
        risk_level = "low"

    scan.status = "completed"
    scan.completed_at = datetime.utcnow()
    scan.findings = json.dumps(all_findings, ensure_ascii=False)
    scan.raw_output = json.dumps(raw_data, ensure_ascii=False, default=str)
    scan.risk_level = risk_level
    db.commit()


@router.get("/tools-status")
def tools_status():
    return {
        tool: {"installed": bool(path), "path": path}
        for tool, path in KALI_TOOLS.items()
    }


@router.post("/scan")
def start_scan(payload: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    asset = models.Asset(
        name=f"Scan: {payload.target}", url=payload.target, asset_type="web",
        status="active", risk_level="medium", tenant_id=payload.tenant_id or 1,
    )
    db.add(asset)
    db.flush()
    scan = models.ScanResult(
        asset_id=asset.id, scan_type=payload.scan_type, status="running", started_at=datetime.utcnow()
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    background_tasks.add_task(full_scan, db, scan.id, payload.target, payload.scan_type)
    return {"scan_id": scan.id, "status": "running", "target": payload.target, "scan_type": payload.scan_type}


@router.get("/results/{scan_id}")
def get_result(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.ScanResult).filter(models.ScanResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "id": scan.id,
        "status": scan.status,
        "scan_type": scan.scan_type,
        "risk_level": scan.risk_level,
        "findings": json.loads(scan.findings) if scan.findings else [],
        "raw_output": json.loads(scan.raw_output) if scan.raw_output else {},
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }


@router.get("/history")
def scan_history(db: Session = Depends(get_db)):
    scans = db.query(models.ScanResult).order_by(models.ScanResult.started_at.desc()).limit(20).all()
    return [
        {"id": s.id, "status": s.status, "scan_type": s.scan_type, "risk_level": s.risk_level,
         "started_at": s.started_at.isoformat() if s.started_at else None,
         "completed_at": s.completed_at.isoformat() if s.completed_at else None}
        for s in scans
    ]
