from datetime import datetime

from pydantic import BaseModel, Field


class SecurityEventResponse(BaseModel):
    id: int
    source: str
    event_type: str
    source_ip: str | None
    detail: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    event_id: int | None
    title: str
    severity: str
    status: str
    rule_id: int | None
    detail: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status: str = Field(pattern="^(open|acknowledged|closed)$")


class SigmaRuleCreate(BaseModel):
    name: str
    yaml_definition: str
    enabled: bool = True


class SigmaRuleResponse(BaseModel):
    id: int
    name: str
    yaml_definition: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: int
    alert_id: int | None
    title: str
    severity: str
    stage: str
    assigned_to_id: int | None
    created_at: datetime
    closed_at: datetime | None

    class Config:
        from_attributes = True


class IncidentUpdate(BaseModel):
    stage: str = Field(pattern="^(triage|containment|eradication|recovery|closed)$")


class IncidentTimelineCreate(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class IncidentTimelineResponse(BaseModel):
    id: int
    note: str
    author_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class HoneypotEventResponse(BaseModel):
    id: int
    listener_port: int
    service_name: str
    source_ip: str
    source_port: int | None
    payload_sample: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class HuntQuery(BaseModel):
    source: str | None = None
    event_type: str | None = None
    source_ip: str | None = None
    severity: str | None = None
    keyword: str | None = None


class SavedHuntQueryCreate(BaseModel):
    name: str
    filters: HuntQuery


class SavedHuntQueryResponse(BaseModel):
    id: int
    name: str
    filters_json: str
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineEventResponse(BaseModel):
    id: int
    event_id: int | None
    alert_id: int | None
    decision_id: int | None
    incident_id: int | None
    stage: str
    created_at: datetime

    class Config:
        from_attributes = True
