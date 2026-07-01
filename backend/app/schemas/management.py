from datetime import datetime

from pydantic import BaseModel, Field


class GrcControlResponse(BaseModel):
    id: int
    framework_id: int
    code: str
    title: str
    status: str

    class Config:
        from_attributes = True


class GrcControlUpdate(BaseModel):
    status: str = Field(pattern="^(not_assessed|compliant|gap)$")


class RiskRegisterCreate(BaseModel):
    title: str
    description: str | None = None
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)


class RiskRegisterResponse(BaseModel):
    id: int
    title: str
    description: str | None
    likelihood: int
    impact: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TenantCreate(BaseModel):
    name: str
    sector: str | None = None


class TenantResponse(BaseModel):
    id: int
    name: str
    sector: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReportJobCreate(BaseModel):
    report_type: str = Field(pattern="^(incidents|compliance|executive)$")


class ReportJobResponse(BaseModel):
    id: int
    report_type: str
    status: str
    file_path: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class PhishingCampaignCreate(BaseModel):
    name: str
    template: str
    target_emails: list[str] = Field(default_factory=list)


class PhishingCampaignResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ModuleSettingUpdate(BaseModel):
    enabled: bool


class ModuleSettingResponse(BaseModel):
    id: int
    module_key: str
    enabled: bool
    updated_at: datetime

    class Config:
        from_attributes = True
