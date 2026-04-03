"""
Automated Response Data Models
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel


class PlaybookStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ActionType(str, Enum):
    BLOCK_IP = "block_ip"
    BLOCK_DOMAIN = "block_domain"
    ISOLATE_HOST = "isolate_host"
    KILL_PROCESS = "kill_process"
    QUARANTINE_FILE = "quarantine_file"
    SEND_ALERT = "send_alert"
    CREATE_TICKET = "create_ticket"
    COLLECT_FORENSICS = "collect_forensics"
    RESET_CREDENTIALS = "reset_credentials"
    ENRICH_IOC = "enrich_ioc"
    NOTIFY_TEAM = "notify_team"
    SNAPSHOT_SYSTEM = "snapshot_system"


class ActionResult(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


class PlaybookAction(BaseModel):
    step: int
    name: str
    action_type: ActionType
    parameters: dict[str, Any] = {}
    result: ActionResult = ActionResult.PENDING
    output: str = ""
    duration_ms: int = 0
    required: bool = True


class Playbook(BaseModel):
    id: str
    name: str
    description: str = ""
    trigger_conditions: list[str] = []
    severity_threshold: str = "high"
    actions: list[PlaybookAction] = []
    enabled: bool = True
    auto_execute: bool = False
    created_at: str
    last_run: Optional[str] = None
    run_count: int = 0
    success_rate: float = 0.0
    tags: list[str] = []


class PlaybookExecution(BaseModel):
    execution_id: str
    playbook_id: str
    playbook_name: str
    status: PlaybookStatus
    triggered_by: str
    triggered_at: str
    completed_at: Optional[str] = None
    actions: list[PlaybookAction] = []
    event_id: Optional[str] = None
    notes: str = ""
    total_duration_ms: int = 0


class ResponseMetrics(BaseModel):
    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    avg_response_time_ms: int = 0
    threats_blocked: int = 0
    hosts_isolated: int = 0
    ips_blocked: int = 0
    alerts_sent: int = 0
