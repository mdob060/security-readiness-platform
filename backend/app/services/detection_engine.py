"""The SOC Center's detection loop.

Runs periodically (see app/main.py scheduler). Three real, DB-driven passes:

1. Brute-force detection over auth.login_attempts.
2. Sigma-style rule matching over soc.events (simplified YAML subset:
   logsource.source + detection.selection field/substring matches).
3. Auto-opening incidents.incidents for any high/critical alert that
   doesn't have one yet.
"""
import logging
from datetime import datetime, timedelta, timezone

import yaml
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.auth import LoginAttempt
from app.models.monitoring import Alert, Incident, PipelineEvent, SecurityEvent, SigmaRule
from app.services.soar import generate_pending_decisions

logger = logging.getLogger("dira.detection")

BRUTE_FORCE_WINDOW_MINUTES = 5
BRUTE_FORCE_THRESHOLD = 5


def detect_bruteforce(db: Session) -> None:
    window_start = datetime.now(timezone.utc) - timedelta(minutes=BRUTE_FORCE_WINDOW_MINUTES)
    rows = (
        db.query(LoginAttempt.ip_address, func.count(LoginAttempt.id))
        .filter(LoginAttempt.success.is_(False), LoginAttempt.created_at >= window_start)
        .group_by(LoginAttempt.ip_address)
        .having(func.count(LoginAttempt.id) >= BRUTE_FORCE_THRESHOLD)
        .all()
    )
    for ip_address, fail_count in rows:
        already_alerted = (
            db.query(Alert)
            .filter(Alert.title.like(f"%{ip_address}%"), Alert.created_at >= window_start)
            .first()
        )
        if already_alerted:
            continue
        event = SecurityEvent(
            source="auth",
            event_type="bruteforce_attempt",
            source_ip=ip_address,
            detail=f"{fail_count} failed logins from {ip_address} in {BRUTE_FORCE_WINDOW_MINUTES} minutes",
        )
        db.add(event)
        db.flush()
        alert = Alert(
            event_id=event.id,
            title=f"Possible brute-force login attempt from {ip_address}",
            severity="high",
            detail=f"{fail_count} failed login attempts observed within {BRUTE_FORCE_WINDOW_MINUTES} minutes.",
        )
        db.add(alert)
        db.flush()
        db.add(PipelineEvent(event_id=event.id, alert_id=alert.id, stage="alert"))
    db.commit()


def _selection_matches(event: SecurityEvent, selection: dict) -> bool:
    for key, expected in selection.items():
        actual = getattr(event, key, None)
        if actual is None:
            return False
        if isinstance(expected, list):
            if not any(str(v).lower() in str(actual).lower() for v in expected):
                return False
        elif str(expected).lower() not in str(actual).lower():
            return False
    return True


def apply_sigma_rules(db: Session) -> None:
    rules = db.query(SigmaRule).filter(SigmaRule.enabled == 1).all()
    if not rules:
        return
    recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    recent_events = db.query(SecurityEvent).filter(SecurityEvent.created_at >= recent_cutoff).all()

    for rule in rules:
        try:
            parsed = yaml.safe_load(rule.yaml_definition) or {}
        except yaml.YAMLError:
            continue
        detection = parsed.get("detection", {})
        selection = detection.get("selection", {})
        level = parsed.get("level", "medium")
        if not selection:
            continue
        for event in recent_events:
            if not _selection_matches(event, selection):
                continue
            exists = db.query(Alert).filter(Alert.rule_id == rule.id, Alert.event_id == event.id).first()
            if exists:
                continue
            alert = Alert(
                event_id=event.id,
                rule_id=rule.id,
                title=f"Sigma rule matched: {rule.name}",
                severity=level,
                detail=f"Event #{event.id} ({event.event_type}) matched rule '{rule.name}'",
            )
            db.add(alert)
            db.flush()
            db.add(PipelineEvent(event_id=event.id, alert_id=alert.id, stage="alert"))
    db.commit()


def auto_open_incidents(db: Session) -> None:
    candidate_alerts = (
        db.query(Alert)
        .filter(Alert.severity.in_(["high", "critical"]), Alert.status == "open")
        .all()
    )
    for alert in candidate_alerts:
        existing = db.query(Incident).filter(Incident.alert_id == alert.id).first()
        if existing:
            continue
        incident = Incident(alert_id=alert.id, title=alert.title, severity=alert.severity)
        db.add(incident)
        db.flush()
        db.add(PipelineEvent(alert_id=alert.id, incident_id=incident.id, stage="incident"))
    db.commit()


def run_detection_cycle() -> None:
    from app.db.base import SessionLocal

    db = SessionLocal()
    try:
        detect_bruteforce(db)
        apply_sigma_rules(db)
        auto_open_incidents(db)
        generate_pending_decisions(db)
    except Exception:
        logger.exception("Detection cycle failed")
        db.rollback()
    finally:
        db.close()
