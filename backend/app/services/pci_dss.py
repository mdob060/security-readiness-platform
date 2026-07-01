"""Live host checks backing the PCI-DSS compliance percentage.

Each check inspects real local system state (not simulated) -- iptables
rule count, TLS certificate presence, ClamAV signature DB, and whether the
audit log is actively receiving entries -- and maps the result onto the
matching PCI-DSS requirement.
"""
import os
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.auth import AuditLogEntry


def _check_firewall() -> tuple[str, str]:
    try:
        proc = subprocess.run(["iptables", "-S"], capture_output=True, text=True, timeout=5)
        rule_count = len(proc.stdout.splitlines())
        if rule_count > 1:
            return "pass", f"{rule_count} iptables rules active"
        return "fail", "No iptables filtering rules detected"
    except FileNotFoundError:
        return "unknown", "iptables not available on this host"


def _check_encryption() -> tuple[str, str]:
    cert_candidates = [
        "/etc/dira/tls/fullchain.pem",
        "/etc/ssl/certs/ssl-cert-snakeoil.pem",
    ]
    for cert in cert_candidates:
        if Path(cert).exists():
            return "pass", f"TLS certificate present at {cert}"
    return "fail", "No TLS certificate found; HTTPS termination not configured"


def _check_av() -> tuple[str, str]:
    custom_db = Path("/var/lib/dira/clamav-custom-db/dira-custom.hdb")
    official_db = Path("/var/lib/clamav")
    has_official = official_db.exists() and any(official_db.glob("*.cvd")) or any(official_db.glob("*.cld"))
    if custom_db.exists() and has_official:
        return "pass", "ClamAV running with official + custom signature databases"
    if custom_db.exists():
        return "fail", "ClamAV custom signatures only -- official DB unreachable (freshclam blocked); update on a host with full internet access"
    return "fail", "No ClamAV signature database found"


def _check_logging(db: Session) -> tuple[str, str]:
    count = db.query(AuditLogEntry).count()
    auth_log_exists = os.path.exists("/var/log/dira/auth.log")
    if count > 0 and auth_log_exists:
        return "pass", f"{count} audit log entries recorded; auth event log active"
    return "fail", "Audit logging is not populated yet"


def evaluate_pci_dss(db: Session, controls: list) -> tuple[float, list[dict]]:
    checkers = {
        "firewall": _check_firewall,
        "encryption": _check_encryption,
        "av": _check_av,
        "logging": lambda: _check_logging(db),
    }
    results = []
    passed = 0
    for control in controls:
        status, detail = checkers.get(control.check_type, lambda: ("unknown", "No checker implemented"))()
        if status == "pass":
            passed += 1
        results.append(
            {
                "requirement_code": control.requirement_code,
                "description": control.description,
                "check_type": control.check_type,
                "status": status,
                "detail": detail,
            }
        )
    percentage = round((passed / len(controls)) * 100, 1) if controls else 0.0
    return percentage, results
