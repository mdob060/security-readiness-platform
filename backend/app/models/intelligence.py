"""Models for ai_brain, automation, threat_intel, federation schemas."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

AI_BRAIN = "ai_brain"
AUTOMATION = "automation"
THREAT_INTEL = "threat_intel"
FEDERATION = "federation"


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {"schema": AI_BRAIN}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New conversation", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("AiMessage", back_populates="conversation")


class AiMessage(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": AI_BRAIN}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{AI_BRAIN}.conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")


class SoarDecision(Base):
    __tablename__ = "decisions"
    __table_args__ = {"schema": AUTOMATION}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("soc.alerts.id"), nullable=True)
    recommended_action: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, approved, rejected
    reviewed_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ThreatActor(Base):
    __tablename__ = "threat_actors"
    __table_args__ = {"schema": THREAT_INTEL}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    aliases: Mapped[str | None] = mapped_column(String(500), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(128), nullable=True)
    motivation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Ioc(Base):
    __tablename__ = "iocs"
    __table_args__ = {"schema": THREAT_INTEL}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ioc_type: Mapped[str] = mapped_column(String(32), nullable=False)  # ip, domain, hash, url
    value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    threat_actor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(f"{THREAT_INTEL}.threat_actors.id"), nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FederationPeer(Base):
    """A trusted organization we exchange STIX/TAXII indicators with."""

    __tablename__ = "peers"
    __table_args__ = {"schema": FEDERATION}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    taxii_api_root: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SharedIndicator(Base):
    __tablename__ = "shared_indicators"
    __table_args__ = {"schema": FEDERATION}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    peer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(f"{FEDERATION}.peers.id"), nullable=True)
    stix_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stix_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # inbound, outbound
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
