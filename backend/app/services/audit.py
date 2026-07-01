from sqlalchemy.orm import Session

from app.models.auth import AuditLogEntry


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    resource: str | None = None,
    ip_address: str | None = None,
    detail: str | None = None,
) -> None:
    entry = AuditLogEntry(
        user_id=user_id, action=action, resource=resource, ip_address=ip_address, detail=detail
    )
    db.add(entry)
    db.commit()
