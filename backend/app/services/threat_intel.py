"""
Threat Intelligence Service
Manages IOCs, threat actors, feeds, and events
"""

import copy
from typing import Optional
from ..data.seed_data import IOCS, THREAT_ACTORS, THREAT_FEEDS, THREAT_EVENTS, MITRE_TECHNIQUES


class ThreatIntelService:
    def __init__(self):
        self._iocs = copy.deepcopy(IOCS)
        self._actors = copy.deepcopy(THREAT_ACTORS)
        self._feeds = copy.deepcopy(THREAT_FEEDS)
        self._events = copy.deepcopy(THREAT_EVENTS)
        self._techniques = copy.deepcopy(MITRE_TECHNIQUES)

    # ── IOC Methods ────────────────────────────────────────────────────────────

    def get_iocs(self, ioc_type: Optional[str] = None, severity: Optional[str] = None,
                 search: Optional[str] = None) -> list[dict]:
        results = self._iocs
        if ioc_type:
            results = [i for i in results if i["type"] == ioc_type]
        if severity:
            results = [i for i in results if i["severity"] == severity]
        if search:
            s = search.lower()
            results = [i for i in results if s in i["value"].lower() or s in i["description"].lower()]
        return results

    def get_ioc(self, ioc_id: str) -> Optional[dict]:
        return next((i for i in self._iocs if i["id"] == ioc_id), None)

    def add_ioc(self, ioc_data: dict) -> dict:
        ioc_data["id"] = f"ioc-{len(self._iocs) + 1:03d}"
        ioc_data["hit_count"] = 0
        self._iocs.append(ioc_data)
        return ioc_data

    def update_ioc(self, ioc_id: str, updates: dict) -> Optional[dict]:
        for i, ioc in enumerate(self._iocs):
            if ioc["id"] == ioc_id:
                self._iocs[i].update(updates)
                return self._iocs[i]
        return None

    def delete_ioc(self, ioc_id: str) -> bool:
        before = len(self._iocs)
        self._iocs = [i for i in self._iocs if i["id"] != ioc_id]
        return len(self._iocs) < before

    def search_ioc_value(self, value: str) -> Optional[dict]:
        """Check if a value matches any known IOC."""
        return next((i for i in self._iocs if i["value"].lower() == value.lower()), None)

    # ── Threat Actor Methods ───────────────────────────────────────────────────

    def get_actors(self, active_only: bool = False) -> list[dict]:
        if active_only:
            return [a for a in self._actors if a["active"]]
        return self._actors

    def get_actor(self, actor_id: str) -> Optional[dict]:
        return next((a for a in self._actors if a["id"] == actor_id), None)

    # ── Feed Methods ───────────────────────────────────────────────────────────

    def get_feeds(self) -> list[dict]:
        return self._feeds

    def get_feed(self, feed_id: str) -> Optional[dict]:
        return next((f for f in self._feeds if f["id"] == feed_id), None)

    def toggle_feed(self, feed_id: str) -> Optional[dict]:
        for f in self._feeds:
            if f["id"] == feed_id:
                f["enabled"] = not f["enabled"]
                return f
        return None

    # ── Event Methods ──────────────────────────────────────────────────────────

    def get_events(self, severity: Optional[str] = None, status: Optional[str] = None,
                   limit: int = 50) -> list[dict]:
        results = self._events
        if severity:
            results = [e for e in results if e["severity"] == severity]
        if status:
            results = [e for e in results if e["status"] == status]
        # Sort by timestamp descending
        results = sorted(results, key=lambda x: x["timestamp"], reverse=True)
        return results[:limit]

    def get_event(self, event_id: str) -> Optional[dict]:
        return next((e for e in self._events if e["id"] == event_id), None)

    def update_event_status(self, event_id: str, status: str) -> Optional[dict]:
        for e in self._events:
            if e["id"] == event_id:
                e["status"] = status
                return e
        return None

    # ── MITRE Methods ──────────────────────────────────────────────────────────

    def get_techniques(self, tactic: Optional[str] = None) -> list[dict]:
        if tactic:
            return [t for t in self._techniques if t["tactic"].lower() == tactic.lower()]
        return self._techniques

    def get_technique(self, technique_id: str) -> Optional[dict]:
        return next((t for t in self._techniques if t["technique_id"] == technique_id), None)

    # ── Dashboard Stats ────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        active_events = [e for e in self._events if e["status"] in ("active", "investigating")]
        critical_iocs = [i for i in self._iocs if i["severity"] == "critical"]
        enabled_feeds = [f for f in self._feeds if f["enabled"]]
        total_ioc_hits = sum(i["hit_count"] for i in self._iocs)

        severity_breakdown = {}
        for e in self._events:
            severity_breakdown[e["severity"]] = severity_breakdown.get(e["severity"], 0) + 1

        ioc_type_breakdown = {}
        for i in self._iocs:
            ioc_type_breakdown[i["type"]] = ioc_type_breakdown.get(i["type"], 0) + 1

        return {
            "total_iocs": len(self._iocs),
            "critical_iocs": len(critical_iocs),
            "active_threats": len(active_events),
            "total_events": len(self._events),
            "threat_actors": len(self._actors),
            "active_feeds": len(enabled_feeds),
            "total_feeds": len(self._feeds),
            "ioc_hits_total": total_ioc_hits,
            "severity_breakdown": severity_breakdown,
            "ioc_type_breakdown": ioc_type_breakdown,
            "top_techniques": self._get_top_techniques(),
        }

    def _get_top_techniques(self) -> list[dict]:
        technique_count: dict[str, int] = {}
        for event in self._events:
            for t in event.get("mitre_techniques", []):
                technique_count[t] = technique_count.get(t, 0) + 1
        sorted_techniques = sorted(technique_count.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"technique_id": tid, "count": count} for tid, count in sorted_techniques]


# Singleton instance
threat_intel_service = ThreatIntelService()
