"""
Threat Intelligence API Router
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.threat_intel import threat_intel_service

router = APIRouter(prefix="/api/v1/threats", tags=["Threat Intelligence"])


@router.get("/stats")
def get_threat_stats():
    """Dashboard statistics for threat intelligence."""
    return threat_intel_service.get_stats()


# ── IOC Endpoints ──────────────────────────────────────────────────────────────

@router.get("/iocs")
def list_iocs(
    ioc_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    return threat_intel_service.get_iocs(ioc_type=ioc_type, severity=severity, search=search)


@router.get("/iocs/{ioc_id}")
def get_ioc(ioc_id: str):
    ioc = threat_intel_service.get_ioc(ioc_id)
    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")
    return ioc


@router.post("/iocs")
def create_ioc(ioc_data: dict):
    return threat_intel_service.add_ioc(ioc_data)


@router.put("/iocs/{ioc_id}")
def update_ioc(ioc_id: str, updates: dict):
    ioc = threat_intel_service.update_ioc(ioc_id, updates)
    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")
    return ioc


@router.delete("/iocs/{ioc_id}")
def delete_ioc(ioc_id: str):
    deleted = threat_intel_service.delete_ioc(ioc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="IOC not found")
    return {"message": "IOC deleted", "id": ioc_id}


@router.get("/iocs/search/lookup")
def lookup_ioc(value: str = Query(..., description="IOC value to look up")):
    """Check if a value is a known IOC."""
    result = threat_intel_service.search_ioc_value(value)
    return {"value": value, "found": result is not None, "ioc": result}


# ── Threat Actor Endpoints ─────────────────────────────────────────────────────

@router.get("/actors")
def list_actors(active_only: bool = Query(False)):
    return threat_intel_service.get_actors(active_only=active_only)


@router.get("/actors/{actor_id}")
def get_actor(actor_id: str):
    actor = threat_intel_service.get_actor(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Threat actor not found")
    return actor


# ── Feed Endpoints ─────────────────────────────────────────────────────────────

@router.get("/feeds")
def list_feeds():
    return threat_intel_service.get_feeds()


@router.get("/feeds/{feed_id}")
def get_feed(feed_id: str):
    feed = threat_intel_service.get_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed


@router.post("/feeds/{feed_id}/toggle")
def toggle_feed(feed_id: str):
    feed = threat_intel_service.toggle_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed


# ── Event Endpoints ────────────────────────────────────────────────────────────

@router.get("/events")
def list_events(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    return threat_intel_service.get_events(severity=severity, status=status, limit=limit)


@router.get("/events/{event_id}")
def get_event(event_id: str):
    event = threat_intel_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/events/{event_id}/status")
def update_event_status(event_id: str, body: dict):
    status = body.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="status field required")
    event = threat_intel_service.update_event_status(event_id, status)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# ── MITRE ATT&CK Endpoints ─────────────────────────────────────────────────────

@router.get("/mitre/techniques")
def list_techniques(tactic: Optional[str] = Query(None)):
    return threat_intel_service.get_techniques(tactic=tactic)


@router.get("/mitre/techniques/{technique_id}")
def get_technique(technique_id: str):
    technique = threat_intel_service.get_technique(technique_id)
    if not technique:
        raise HTTPException(status_code=404, detail="Technique not found")
    return technique
