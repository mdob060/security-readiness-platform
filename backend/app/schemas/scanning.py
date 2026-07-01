from datetime import datetime

from pydantic import BaseModel, Field


class ScopeTargetCreate(BaseModel):
    target: str = Field(min_length=1, max_length=255)
    justification: str = Field(min_length=10, max_length=2000)


class ScopeTargetResponse(BaseModel):
    id: int
    target: str
    justification: str
    status: str
    requested_by_id: int
    approved_by_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanJobCreate(BaseModel):
    target_id: int
    tool: str
    service: str | None = None


class ScanFindingResponse(BaseModel):
    id: int
    severity: str
    title: str
    detail: str | None

    class Config:
        from_attributes = True


class ScanJobResponse(BaseModel):
    id: int
    target_id: int
    tool: str
    status: str
    exit_code: int | None
    summary: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    class Config:
        from_attributes = True


class ScanJobDetailResponse(ScanJobResponse):
    raw_output: str | None
    findings: list[ScanFindingResponse] = []


class SystemScanCreate(BaseModel):
    tool: str


class SystemScanResponse(BaseModel):
    id: int
    tool: str
    status: str
    warnings_count: int
    hardening_index: int | None
    created_at: datetime
    finished_at: datetime | None

    class Config:
        from_attributes = True


class SystemScanDetailResponse(SystemScanResponse):
    raw_output: str | None
