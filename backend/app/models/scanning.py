"""Models for scan_scope, red_team, and blue_team schemas."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCAN_SCOPE = "scan_scope"
RED_TEAM = "red_team"
BLUE_TEAM = "blue_team"


class ScopeTarget(Base):
    """Authorization gate: a target must exist here and be approved before any offensive tool runs."""

    __tablename__ = "targets"
    __table_args__ = {"schema": SCAN_SCOPE}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, approved, rejected, revoked
    approved_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scan_jobs = relationship("ScanJob", back_populates="target_rel")


class ScanJob(Base):
    __tablename__ = "scan_jobs"
    __table_args__ = {"schema": RED_TEAM}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SCAN_SCOPE}.targets.id"), nullable=False)
    tool: Mapped[str] = mapped_column(String(32), nullable=False)
    arguments: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)  # queued, running, completed, failed
    started_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    target_rel = relationship("ScopeTarget", back_populates="scan_jobs")
    findings = relationship("ScanFinding", back_populates="job")


class ScanFinding(Base):
    __tablename__ = "findings"
    __table_args__ = {"schema": RED_TEAM}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{RED_TEAM}.scan_jobs.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="info", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ScanJob", back_populates="findings")


class SystemScan(Base):
    """lynis / rkhunter / chkrootkit audits of the host itself."""

    __tablename__ = "system_scans"
    __table_args__ = {"schema": BLUE_TEAM}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool: Mapped[str] = mapped_column(String(32), nullable=False)  # lynis, rkhunter, chkrootkit, clamav
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    started_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hardening_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PciDssControl(Base):
    __tablename__ = "pci_dss_controls"
    __table_args__ = {"schema": BLUE_TEAM}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_code: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    check_type: Mapped[str] = mapped_column(String(32), nullable=False)  # firewall, encryption, av, logging
