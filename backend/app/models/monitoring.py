"""Models for soc, incidents, sigma, honeypot, threat_hunting, pipeline schemas."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SOC = "soc"
INCIDENTS = "incidents"
SIGMA = "sigma"
HONEYPOT = "honeypot"
THREAT_HUNTING = "threat_hunting"
PIPELINE = "pipeline"


class SecurityEvent(Base):
    """Raw observed events (failed logins, honeypot hits, scan findings, etc.)."""

    __tablename__ = "events"
    __table_args__ = {"schema": SOC}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)  # auth, honeypot, red_team, blue_team, ueba...
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alerts = relationship("Alert", back_populates="event")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": SOC}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(f"{SOC}.events.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="low", nullable=False)  # low, medium, high, critical
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)  # open, acknowledged, closed
    rule_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(f"{SIGMA}.rules.id"), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event = relationship("SecurityEvent", back_populates="alerts")
    incidents = relationship("Incident", back_populates="alert")


class SigmaRule(Base):
    __tablename__ = "rules"
    __table_args__ = {"schema": SIGMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    yaml_definition: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = {"schema": INCIDENTS}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(f"{SOC}.alerts.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    stage: Mapped[str] = mapped_column(
        String(32), default="triage", nullable=False
    )  # triage, containment, eradication, recovery, closed
    assigned_to_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    alert = relationship("Alert", back_populates="incidents")
    timeline = relationship("IncidentTimelineEntry", back_populates="incident")


class IncidentTimelineEntry(Base):
    __tablename__ = "timeline"
    __table_args__ = {"schema": INCIDENTS}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{INCIDENTS}.incidents.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="timeline")


class HoneypotEvent(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": HONEYPOT}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listener_port: Mapped[int] = mapped_column(Integer, nullable=False)
    service_name: Mapped[str] = mapped_column(String(64), nullable=False)  # ssh, ftp, telnet, http, mysql...
    source_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_sample: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SavedHuntQuery(Base):
    __tablename__ = "saved_queries"
    __table_args__ = {"schema": THREAT_HUNTING}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PipelineEvent(Base):
    """Materialized event -> alert -> decision -> incident chain, for the Live Pipeline visualization."""

    __tablename__ = "pipeline_events"
    __table_args__ = {"schema": PIPELINE}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alert_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    incident_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)  # event, alert, decision, incident
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
