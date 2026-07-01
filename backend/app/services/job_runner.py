"""Runs scan jobs in background threads and persists results back to Postgres.

Each call opens its own DB session because the job outlives the HTTP request
that triggered it (FastAPI BackgroundTasks run after the response is sent,
and long scans must not hold the request-scoped session open).
"""
import re
import threading
from datetime import datetime, timezone

from app.core.config import settings
from app.db.base import SessionLocal
from app.models.monitoring import SecurityEvent
from app.models.scanning import ScanFinding, ScanJob, SystemScan
from app.services.tools import run_defensive_tool, run_offensive_tool

_SEVERITY_KEYWORDS = {
    "critical": ["critical"],
    "high": ["high", "vulnerable", "sql injection", "vulnerability found"],
    "medium": ["medium", "warning", "outdated"],
}


def _guess_severity(line: str) -> str:
    lowered = line.lower()
    for severity, keywords in _SEVERITY_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return severity
    return "info"


def _extract_findings(tool: str, output: str) -> list[tuple[str, str]]:
    """Very small heuristic parser: pulls out lines that look like actionable
    results per tool so the Red Team UI has something structured to show,
    in addition to the full raw output."""
    findings: list[tuple[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if tool == "nmap" and re.match(r"^\d+/tcp\s+open", line):
            findings.append((_guess_severity(line), line))
        elif tool == "nuclei" and line.startswith("["):
            findings.append((_guess_severity(line), line))
        elif tool == "gobuster" and line.startswith("/"):
            findings.append(("info", line))
        elif tool == "ffuf" and re.search(r"Status:\s*\d+", line):
            findings.append(("info", line))
        elif tool == "nikto" and line.startswith("+"):
            findings.append((_guess_severity(line), line))
        elif tool == "whatweb" and line:
            findings.append(("info", line))
        elif tool == "wpscan" and ("[!]" in line or "[+]" in line):
            findings.append((_guess_severity(line), line))
    return findings[:200]


def execute_scan_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(ScanJob, job_id)
        if job is None:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        target = job.target_rel.target
        rc, output, argv = run_offensive_tool(
            job.tool, target, settings.scan_timeout_seconds
        )

        job.raw_output = output
        job.exit_code = rc
        job.status = "completed" if rc >= 0 else "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.summary = f"{' '.join(argv)} -> exit code {rc}"

        for severity, title in _extract_findings(job.tool, output):
            db.add(ScanFinding(job_id=job.id, severity=severity, title=title[:255]))

        db.add(
            SecurityEvent(
                source="red_team",
                event_type=f"scan_{job.tool}_completed",
                detail=f"Scan of {target} with {job.tool} finished (exit {rc})",
            )
        )
        db.commit()
    finally:
        db.close()


def execute_system_scan(scan_id: int) -> None:
    db = SessionLocal()
    try:
        scan = db.get(SystemScan, scan_id)
        if scan is None:
            return
        scan.status = "running"
        scan.started_at = datetime.now(timezone.utc)
        db.commit()

        rc, output, _argv = run_defensive_tool(scan.tool, settings.scan_timeout_seconds)

        scan.raw_output = output
        scan.status = "completed" if rc in (0, 1) else "failed"
        scan.finished_at = datetime.now(timezone.utc)

        if scan.tool == "lynis":
            match = re.search(r"hardening_index=(\d+)", _read_lynis_report())
            if match:
                scan.hardening_index = int(match.group(1))
            scan.warnings_count = output.count("[WARNING]")
        else:
            scan.warnings_count = sum(
                1 for line in output.splitlines() if "WARNING" in line.upper() or "FOUND" in line.upper()
            )

        db.add(
            SecurityEvent(
                source="blue_team",
                event_type=f"scan_{scan.tool}_completed",
                detail=f"{scan.tool} scan finished with {scan.warnings_count} warning(s)",
            )
        )
        db.commit()
    finally:
        db.close()


def _read_lynis_report() -> str:
    try:
        with open("/var/log/lynis-report.dat", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def run_in_background(target_fn, *args) -> None:
    thread = threading.Thread(target=target_fn, args=args, daemon=True)
    thread.start()
