"""
Threat Intelligence Data Models
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ThreatSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatStatus(str, Enum):
    ACTIVE = "active"
    MITIGATED = "mitigated"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class IOCType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH_MD5 = "md5"
    FILE_HASH_SHA256 = "sha256"
    EMAIL = "email"
    CVE = "cve"
    YARA = "yara"


class IOC(BaseModel):
    id: str
    type: IOCType
    value: str
    severity: ThreatSeverity
    confidence: int  # 0-100
    source: str
    first_seen: str
    last_seen: str
    tags: list[str] = []
    mitre_techniques: list[str] = []
    description: str = ""
    hit_count: int = 0


class ThreatActor(BaseModel):
    id: str
    name: str
    aliases: list[str] = []
    origin: str = "Unknown"
    motivation: str = ""
    sophistication: str = ""
    active: bool = True
    mitre_groups: list[str] = []
    ttps: list[str] = []
    description: str = ""


class ThreatFeed(BaseModel):
    id: str
    name: str
    provider: str
    url: str
    enabled: bool = True
    last_updated: str
    ioc_count: int = 0
    feed_type: str = "STIX"
    description: str = ""


class ThreatEvent(BaseModel):
    id: str
    title: str
    severity: ThreatSeverity
    status: ThreatStatus
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    iocs: list[str] = []
    mitre_techniques: list[str] = []
    actor: Optional[str] = None
    timestamp: str
    description: str = ""
    raw_log: Optional[str] = None


class MitreTechnique(BaseModel):
    technique_id: str
    name: str
    tactic: str
    description: str = ""
    platforms: list[str] = []
    detection: str = ""
    mitigation: str = ""
