from datetime import datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    account_from: str
    account_to: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    channel: str = Field(pattern="^(atm|wire|card|mobile)$")


class TransactionResponse(BaseModel):
    id: int
    account_from: str
    account_to: str
    amount: float
    currency: str
    channel: str
    risk_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class FraudAlertResponse(BaseModel):
    id: int
    transaction_id: int
    reason: str
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


class ControllerCreate(BaseModel):
    name: str
    protocol: str = Field(pattern="^(modbus|dnp3|opcua)$")
    ip_address: str | None = None


class ControllerResponse(BaseModel):
    id: int
    name: str
    protocol: str
    ip_address: str | None
    status: str

    class Config:
        from_attributes = True


class SensorReadingCreate(BaseModel):
    controller_id: int
    metric: str
    value: float
    unit: str | None = None


class SensorReadingResponse(BaseModel):
    id: int
    controller_id: int
    metric: str
    value: float
    unit: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class OtAlertResponse(BaseModel):
    id: int
    controller_id: int
    description: str
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


class UebaEventCreate(BaseModel):
    entity_name: str
    action: str
    value: float


class UebaEntityResponse(BaseModel):
    id: int
    entity_name: str
    entity_type: str
    risk_score: float
    updated_at: datetime

    class Config:
        from_attributes = True


class SwiftAssessmentUpdate(BaseModel):
    control_id: int
    status: str = Field(pattern="^(compliant|gap|not_assessed)$")
    notes: str | None = None


class SwiftControlWithStatus(BaseModel):
    id: int
    control_code: str
    title: str
    category: str
    status: str


class AmlScreenRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)


class AmlScreenResult(BaseModel):
    query_name: str
    matched_name: str | None
    match_score: float
    list_source: str | None


class SectorStatusResponse(BaseModel):
    sector: str
    open_alerts: int
    compliance_score: float
    updated_at: datetime

    class Config:
        from_attributes = True
