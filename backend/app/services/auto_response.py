"""
Automated Response Engine
Manages playbooks and executes response actions
"""

import copy
import random
import uuid
from datetime import datetime
from typing import Optional
from ..data.seed_data import PLAYBOOKS


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


# Simulated action execution results
ACTION_OUTPUTS = {
    "block_ip": [
        "IP {target} successfully added to firewall deny list on all perimeter devices.",
        "Firewall rule created: DROP from {target} to ANY. Rule ID: FW-{rid}",
    ],
    "block_domain": [
        "Domain {target} added to DNS sinkhole. All queries will return NXDOMAIN.",
        "Web proxy category updated. Domain {target} blocked organization-wide.",
    ],
    "isolate_host": [
        "Host {target} isolated via VLAN quarantine. Network access revoked.",
        "EDR agent confirmed host isolation. All network interfaces disabled except management.",
    ],
    "kill_process": [
        "Process terminated successfully. PID {pid} killed on {target}.",
        "3 malicious processes identified and terminated. Event logged to SIEM.",
    ],
    "quarantine_file": [
        "File moved to quarantine vault. Hash logged: {hash}",
        "Malicious file quarantined and removed from {count} endpoints.",
    ],
    "send_alert": [
        "Alert dispatched to {recipient} via email and Slack.",
        "PagerDuty incident created. On-call analyst notified.",
    ],
    "create_ticket": [
        "Incident ticket #{ticket_id} created in ServiceNow with priority {priority}.",
        "JIRA ticket SEC-{ticket_id} created and assigned to SOC queue.",
    ],
    "collect_forensics": [
        "Forensic artifacts collected: memory dump (4.2GB), event logs (847MB), registry hive.",
        "Evidence package uploaded to secure forensics vault. Case ID: FOR-{case_id}",
    ],
    "reset_credentials": [
        "Credentials reset for {count} affected accounts. Users notified via secondary email.",
        "Active sessions terminated. Password reset tokens sent to {count} users.",
    ],
    "enrich_ioc": [
        "IOC enriched: VirusTotal (47/72 detections), Shodan (open ports: 22,80,443), AbuseIPDB (score: 92/100).",
        "Reputation lookup complete. IOC classified as HIGH RISK. WHOIS: Registered {days} days ago.",
    ],
    "notify_team": [
        "SOC team notified via Slack #critical-incidents. CISO escalation email sent.",
        "Emergency notification sent to on-call team. Response acknowledged by 3 analysts.",
    ],
    "snapshot_system": [
        "System snapshot completed. Disk image: 127GB, stored in evidence vault.",
        "Memory capture (64GB) and full disk snapshot preserved for forensic analysis.",
    ],
}


def _simulate_action(action: dict) -> dict:
    """Simulate executing a response action and return result."""
    action_type = action["action_type"]
    templates = ACTION_OUTPUTS.get(action_type, ["Action executed successfully."])
    template = random.choice(templates)

    # Fill in template placeholders
    output = template.format(
        target=action["parameters"].get("target", "10.1.45.23"),
        recipient=action["parameters"].get("recipient", "soc-team"),
        priority=action["parameters"].get("priority", "P2"),
        pid=random.randint(1000, 65535),
        rid=random.randint(10000, 99999),
        hash="3b4c5d6e...2a3b4c",
        count=random.randint(1, 15),
        ticket_id=random.randint(10000, 99999),
        case_id=random.randint(1000, 9999),
        days=random.randint(3, 90),
    )

    # 95% success rate simulation
    success = random.random() < 0.95
    duration = random.randint(50, 2500)

    return {
        **action,
        "result": "success" if success else "failed",
        "output": output if success else f"ERROR: Action failed - timeout connecting to enforcement point. Duration: {duration}ms",
        "duration_ms": duration,
    }


class AutoResponseService:
    def __init__(self):
        self._playbooks = copy.deepcopy(PLAYBOOKS)
        self._executions: list[dict] = []
        self._metrics = {
            "total_executions": 284,
            "successful": 279,
            "failed": 5,
            "avg_response_time_ms": 3420,
            "threats_blocked": 847,
            "hosts_isolated": 23,
            "ips_blocked": 312,
            "alerts_sent": 1204,
        }

    # ── Playbook Methods ───────────────────────────────────────────────────────

    def get_playbooks(self, enabled_only: bool = False) -> list[dict]:
        if enabled_only:
            return [p for p in self._playbooks if p["enabled"]]
        return self._playbooks

    def get_playbook(self, playbook_id: str) -> Optional[dict]:
        return next((p for p in self._playbooks if p["id"] == playbook_id), None)

    def toggle_playbook(self, playbook_id: str) -> Optional[dict]:
        for p in self._playbooks:
            if p["id"] == playbook_id:
                p["enabled"] = not p["enabled"]
                return p
        return None

    # ── Execution Methods ──────────────────────────────────────────────────────

    def execute_playbook(self, playbook_id: str, event_id: Optional[str] = None,
                         triggered_by: str = "manual") -> Optional[dict]:
        playbook = self.get_playbook(playbook_id)
        if not playbook:
            return None

        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        started_at = _now()

        # Simulate executing each action sequentially
        executed_actions = []
        total_duration = 0
        all_success = True

        for action in playbook["actions"]:
            result = _simulate_action(copy.deepcopy(action))
            executed_actions.append(result)
            total_duration += result["duration_ms"]
            if result["result"] == "failed" and action.get("required", True):
                all_success = False
                break

        status = "completed" if all_success else "failed"

        execution = {
            "execution_id": execution_id,
            "playbook_id": playbook_id,
            "playbook_name": playbook["name"],
            "status": status,
            "triggered_by": triggered_by,
            "triggered_at": started_at,
            "completed_at": _now(),
            "actions": executed_actions,
            "event_id": event_id,
            "notes": f"Automated execution via {triggered_by}",
            "total_duration_ms": total_duration,
        }

        self._executions.append(execution)

        # Update playbook stats
        for p in self._playbooks:
            if p["id"] == playbook_id:
                p["run_count"] += 1
                p["last_run"] = started_at
                total_runs = p["run_count"]
                prev_success = round(p["success_rate"] * (total_runs - 1) / 100)
                new_success = prev_success + (1 if all_success else 0)
                p["success_rate"] = round((new_success / total_runs) * 100, 1)

        # Update global metrics
        self._metrics["total_executions"] += 1
        if all_success:
            self._metrics["successful"] += 1
        else:
            self._metrics["failed"] += 1
        self._metrics["avg_response_time_ms"] = (
            self._metrics["avg_response_time_ms"] + total_duration
        ) // 2

        return execution

    def get_executions(self, playbook_id: Optional[str] = None,
                       limit: int = 20) -> list[dict]:
        results = self._executions
        if playbook_id:
            results = [e for e in results if e["playbook_id"] == playbook_id]
        results = sorted(results, key=lambda x: x["triggered_at"], reverse=True)
        return results[:limit]

    def get_execution(self, execution_id: str) -> Optional[dict]:
        return next((e for e in self._executions if e["execution_id"] == execution_id), None)

    # ── Metrics ────────────────────────────────────────────────────────────────

    def get_metrics(self) -> dict:
        return {
            **self._metrics,
            "active_playbooks": len([p for p in self._playbooks if p["enabled"]]),
            "total_playbooks": len(self._playbooks),
            "auto_execute_count": len([p for p in self._playbooks if p.get("auto_execute")]),
            "recent_executions": len(self._executions),
        }


# Singleton instance
auto_response_service = AutoResponseService()
