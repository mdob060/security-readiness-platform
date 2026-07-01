"""Models for banking, ot_scada, ueba, swift_csp, aml, sector_monitor schemas."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

BANKING = "banking"
OT_SCADA = "ot_scada"
UEBA = "ueba"
SWIFT_CSP = "swift_csp"
AML = "aml"
SECTOR_MONITOR = "sector_monitor"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"schema": BANKING}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_from: Mapped[str] = mapped_column(String(64), nullable=False)
    account_to: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)  # atm, wire, card, mobile
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    __table_args__ = {"schema": BANKING}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{BANKING}.transactions.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OtController(Base):
    __tablename__ = "controllers"
    __table_args__ = {"schema": OT_SCADA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    protocol: Mapped[str] = mapped_column(String(32), nullable=False)  # modbus, dnp3, opcua
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="online", nullable=False)


class OtSensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = {"schema": OT_SCADA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    controller_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{OT_SCADA}.controllers.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OtAlert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": OT_SCADA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    controller_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{OT_SCADA}.controllers.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UebaEntityProfile(Base):
    __tablename__ = "entity_profiles"
    __table_args__ = {"schema": UEBA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    baseline_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UebaBehaviorEvent(Base):
    __tablename__ = "behavior_events"
    __table_args__ = {"schema": UEBA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{UEBA}.entity_profiles.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SwiftControl(Base):
    __tablename__ = "controls"
    __table_args__ = {"schema": SWIFT_CSP}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    control_code: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. 1.1, 2.3
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # restrict, detect, protect


class SwiftAssessment(Base):
    __tablename__ = "assessments"
    __table_args__ = {"schema": SWIFT_CSP}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    control_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{SWIFT_CSP}.controls.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="not_assessed", nullable=False)  # compliant, gap, not_assessed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AmlSanctionsEntry(Base):
    """Local mirror of a sanctions/PEP watchlist used for name screening."""

    __tablename__ = "sanctions_entries"
    __table_args__ = {"schema": AML}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    list_source: Mapped[str] = mapped_column(String(64), nullable=False)  # OFAC-SDN, UN, EU, local
    entity_type: Mapped[str] = mapped_column(String(16), default="individual", nullable=False)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AmlScreeningResult(Base):
    __tablename__ = "screening_results"
    __table_args__ = {"schema": AML}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_name: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_entry_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(f"{AML}.sanctions_entries.id"), nullable=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    screened_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth.users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SectorStatus(Base):
    """Rollup health/compliance snapshot per sector, for the Sector Monitor page."""

    __tablename__ = "sector_status"
    __table_args__ = {"schema": SECTOR_MONITOR}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sector: Mapped[str] = mapped_column(String(64), nullable=False)  # government, banking, payments, health, banking_software
    open_alerts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compliance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
