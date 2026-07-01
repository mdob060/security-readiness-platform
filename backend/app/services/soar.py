"""SOAR-style decision generation.

Every open alert without a decision yet gets a rule-based recommended
action. Decisions sit in `pending` until a human analyst approves or
rejects them via the Automation page -- the platform never acts
autonomously on production systems.
"""
from sqlalchemy.orm import Session

from app.models.intelligence import SoarDecision
from app.models.monitoring import Alert, PipelineEvent

_ACTION_RULES = [
    (["brute-force", "brute force"], "Block source IP via fail2ban and force password reset for the affected account."),
    (["honeypot"], "Add source IP to the threat intelligence IOC list and monitor for further activity."),
    (["sigma rule matched"], "Escalate to on-call analyst for manual triage of the matched detection."),
]


def _recommend_action(alert: Alert) -> str:
    lowered = alert.title.lower()
    for keywords, action in _ACTION_RULES:
        if any(kw in lowered for kw in keywords):
            return action
    if alert.severity == "critical":
        return "Immediately isolate affected asset and open a P1 incident."
    if alert.severity == "high":
        return "Assign to an analyst for triage within 1 hour."
    return "Add to daily review queue."


def generate_pending_decisions(db: Session) -> None:
    open_alerts = db.query(Alert).filter(Alert.status == "open").all()
    for alert in open_alerts:
        existing = db.query(SoarDecision).filter(SoarDecision.alert_id == alert.id).first()
        if existing:
            continue
        decision = SoarDecision(
            alert_id=alert.id,
            recommended_action=_recommend_action(alert),
            rationale=f"Generated from alert '{alert.title}' (severity={alert.severity}).",
        )
        db.add(decision)
        db.flush()
        db.add(PipelineEvent(alert_id=alert.id, decision_id=decision.id, stage="decision"))
    db.commit()
