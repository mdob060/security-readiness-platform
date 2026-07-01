from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str = Field(min_length=1, max_length=4000)


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    used_local_llm: bool


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class SoarDecisionResponse(BaseModel):
    id: int
    alert_id: int | None
    recommended_action: str
    rationale: str | None
    status: str
    reviewed_by_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class SoarDecisionReview(BaseModel):
    approve: bool


class ThreatActorResponse(BaseModel):
    id: int
    name: str
    aliases: str | None
    origin: str | None
    motivation: str | None
    description: str | None

    class Config:
        from_attributes = True


class IocCreate(BaseModel):
    ioc_type: str = Field(pattern="^(ip|domain|hash|url)$")
    value: str
    threat_actor_id: int | None = None
    confidence: int = 50
    source: str | None = None


class IocResponse(BaseModel):
    id: int
    ioc_type: str
    value: str
    threat_actor_id: int | None
    confidence: int
    source: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FederationPeerCreate(BaseModel):
    name: str
    taxii_api_root: str | None = None
    trusted: bool = False


class FederationPeerResponse(BaseModel):
    id: int
    name: str
    taxii_api_root: str | None
    trusted: bool
    created_at: datetime

    class Config:
        from_attributes = True
