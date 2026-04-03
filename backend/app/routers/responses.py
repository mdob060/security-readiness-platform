"""
Automated Response API Router
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.auto_response import auto_response_service

router = APIRouter(prefix="/api/v1/response", tags=["Automated Response"])


@router.get("/metrics")
def get_metrics():
    """Response engine metrics and statistics."""
    return auto_response_service.get_metrics()


# ── Playbook Endpoints ─────────────────────────────────────────────────────────

@router.get("/playbooks")
def list_playbooks(enabled_only: bool = Query(False)):
    return auto_response_service.get_playbooks(enabled_only=enabled_only)


@router.get("/playbooks/{playbook_id}")
def get_playbook(playbook_id: str):
    pb = auto_response_service.get_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return pb


@router.post("/playbooks/{playbook_id}/toggle")
def toggle_playbook(playbook_id: str):
    pb = auto_response_service.toggle_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return pb


@router.post("/playbooks/{playbook_id}/execute")
def execute_playbook(playbook_id: str, body: dict = {}):
    """Manually trigger a playbook execution."""
    event_id = body.get("event_id")
    triggered_by = body.get("triggered_by", "manual")

    execution = auto_response_service.execute_playbook(
        playbook_id=playbook_id,
        event_id=event_id,
        triggered_by=triggered_by,
    )
    if not execution:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return execution


# ── Execution Endpoints ────────────────────────────────────────────────────────

@router.get("/executions")
def list_executions(
    playbook_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    return auto_response_service.get_executions(playbook_id=playbook_id, limit=limit)


@router.get("/executions/{execution_id}")
def get_execution(execution_id: str):
    execution = auto_response_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
