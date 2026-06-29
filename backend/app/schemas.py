from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str
    email: str
    role: str = "analyst"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Tenant schemas
class TenantBase(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    country: str = "LY"
    status: str = "active"
    risk_score: float = 50.0


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[float] = None


class TenantResponse(TenantBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Asset schemas
class AssetBase(BaseModel):
    name: str
    url: Optional[str] = None
    ip_address: Optional[str] = None
    asset_type: str = "web"
    status: str = "active"
    risk_level: str = "medium"


class AssetCreate(AssetBase):
    tenant_id: int


class AssetResponse(AssetBase):
    id: int
    tenant_id: int
    last_scan: Optional[datetime] = None

    class Config:
        from_attributes = True


# Incident schemas
class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None


class IncidentCreate(IncidentBase):
    tenant_id: int


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None


class IncidentResponse(IncidentBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Vulnerability schemas
class VulnerabilityBase(BaseModel):
    cve_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    cvss_score: float = 0.0
    status: str = "open"


class VulnerabilityCreate(VulnerabilityBase):
    tenant_id: int
    asset_id: Optional[int] = None


class VulnerabilityResponse(VulnerabilityBase):
    id: int
    tenant_id: int
    asset_id: Optional[int] = None
    discovered_at: datetime
    remediated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ThreatIntel schemas
class ThreatIntelBase(BaseModel):
    indicator: str
    indicator_type: str
    threat_type: Optional[str] = None
    confidence: int = 70
    source: Optional[str] = None
    tags: Optional[str] = None


class ThreatIntelCreate(ThreatIntelBase):
    pass


class ThreatIntelResponse(ThreatIntelBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ScanResult schemas
class ScanResultBase(BaseModel):
    scan_type: str = "full"
    status: str = "pending"
    target: Optional[str] = None


class ScanResultCreate(ScanResultBase):
    asset_id: Optional[int] = None


class ScanResultResponse(ScanResultBase):
    id: int
    asset_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings: Optional[str] = None
    raw_output: Optional[str] = None

    class Config:
        from_attributes = True


# Report schemas
class ReportBase(BaseModel):
    title: str
    report_type: str = "security_assessment"
    status: str = "draft"
    generated_by: str = "system"


class ReportCreate(ReportBase):
    tenant_id: Optional[int] = None


class ReportResponse(ReportBase):
    id: int
    tenant_id: Optional[int] = None
    created_at: datetime
    content: Optional[str] = None

    class Config:
        from_attributes = True


# SigmaRule schemas
class SigmaRuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "experimental"
    level: str = "medium"
    category: Optional[str] = None
    detection: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[str] = None


class SigmaRuleCreate(SigmaRuleBase):
    pass


class SigmaRuleResponse(SigmaRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# RedTeamOp schemas
class RedTeamOpBase(BaseModel):
    title: str
    description: Optional[str] = None
    phase: str = "reconnaissance"
    status: str = "planned"
    ttps: Optional[str] = None
    operator: Optional[str] = None


class RedTeamOpCreate(RedTeamOpBase):
    tenant_id: Optional[int] = None


class RedTeamOpResponse(RedTeamOpBase):
    id: int
    tenant_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# BlueTeamPlaybook schemas
class BlueTeamPlaybookBase(BaseModel):
    title: str
    description: Optional[str] = None
    trigger: Optional[str] = None
    steps: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None


class BlueTeamPlaybookCreate(BlueTeamPlaybookBase):
    pass


class BlueTeamPlaybookResponse(BlueTeamPlaybookBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard schemas
class DashboardStats(BaseModel):
    total_tenants: int
    active_incidents: int
    critical_vulns: int
    threats_blocked: int
    risk_score: float
    recent_activity: List[dict]


class ThreatMapData(BaseModel):
    threats: List[dict]
    sources: List[dict]


# Scanner schemas
class ScanRequest(BaseModel):
    target: str
    scan_type: str = "full"
    asset_id: Optional[int] = None


class ThreatCheckRequest(BaseModel):
    indicator: str
    indicator_type: str = "ip"
