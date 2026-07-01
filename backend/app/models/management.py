"""Models for grc, analytics, reports, phishing, settings schemas."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

GRC = "grc"
ANALYTICS = "analytics"
REPORTS = "reports"
PHISHING = "phishing"
SETTINGS = "settings"


class GrcFramework(Base):
    __tablename__ = "frameworks"
    __table_args__ = {"schema": GRC}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # ISO 27001, NIST CSF, PCI DSS


class GrcControl(Base):
    __tablename__ = "controls"
    __table_args__ = {"schema": GRC}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    framework_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{GRC}.frameworks.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="not_assessed", nullable=False)


class RiskRegisterEntry(Base):
    __tablename__ = "risk_register"
    __table_args__ = {"schema": GRC}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    likelihood: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    impact: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    owner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MetricSnapshot(Base):
    """Periodic computed analytics snapshots (alert volume, MTTR, tool usage, etc.)."""

    __tablename__ = "metric_snapshots"
    __table_args__ = {"schema": ANALYTICS}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(nullable=False)
    dimension: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReportJob(Base):
    __tablename__ = "report_jobs"
    __table_args__ = {"schema": REPORTS}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)  # incidents, compliance, executive
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PhishingCampaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = {"schema": PHISHING}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    targets = relationship("PhishingTarget", back_populates="campaign")


class PhishingTarget(Base):
    __tablename__ = "targets"
    __table_args__ = {"schema": PHISHING}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{PHISHING}.campaigns.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    tracking_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    campaign = relationship("PhishingCampaign", back_populates="targets")
    click_events = relationship("PhishingClickEvent", back_populates="target")


class PhishingClickEvent(Base):
    __tablename__ = "click_events"
    __table_args__ = {"schema": PHISHING}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{PHISHING}.targets.id"), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    target = relationship("PhishingTarget", back_populates="click_events")


class ModuleSetting(Base):
    __tablename__ = "module_settings"
    __table_args__ = {"schema": SETTINGS}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
