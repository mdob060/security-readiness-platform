from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    industry = Column(String)
    sector = Column(String)
    country = Column(String, default="LY")
    status = Column(String, default="active")
    risk_score = Column(Integer, default=50)
    contact_email = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    assets = relationship("Asset", back_populates="tenant")
    incidents = relationship("Incident", back_populates="tenant")
    vulnerabilities = relationship("Vulnerability", back_populates="tenant")
    reports = relationship("Report", back_populates="tenant")


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    name = Column(String, nullable=False)
    url = Column(String)
    ip_address = Column(String)
    asset_type = Column(String)
    status = Column(String, default="active")
    last_scan = Column(DateTime)
    risk_level = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    tenant = relationship("Tenant", back_populates="assets")
    vulnerabilities = relationship("Vulnerability", back_populates="asset")
    scan_results = relationship("ScanResult", back_populates="asset")


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(String, default="medium")
    status = Column(String, default="open")
    incident_type = Column(String)
    assigned_to = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    tenant = relationship("Tenant", back_populates="incidents")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    cve_id = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(String, default="medium")
    cvss_score = Column(Float)
    status = Column(String, default="open")
    affected_component = Column(String)
    remediation = Column(Text)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    remediated_at = Column(DateTime)
    asset = relationship("Asset", back_populates="vulnerabilities")
    tenant = relationship("Tenant", back_populates="vulnerabilities")


class ThreatIntel(Base):
    __tablename__ = "threat_intel"
    id = Column(Integer, primary_key=True, index=True)
    indicator = Column(String, nullable=False)
    indicator_type = Column(String)
    threat_type = Column(String)
    confidence = Column(Integer, default=70)
    source = Column(String)
    description = Column(Text)
    tags = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime)


class ScanResult(Base):
    __tablename__ = "scan_results"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    scan_type = Column(String)
    status = Column(String, default="pending")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    findings = Column(Text)
    raw_output = Column(Text)
    risk_level = Column(String)
    asset = relationship("Asset", back_populates="scan_results")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    title = Column(String, nullable=False)
    report_type = Column(String)
    status = Column(String, default="draft")
    content = Column(Text)
    generated_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    tenant = relationship("Tenant", back_populates="reports")


class SigmaRule(Base):
    __tablename__ = "sigma_rules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="stable")
    level = Column(String, default="medium")
    category = Column(String)
    detection = Column(Text)
    tags = Column(String)
    author = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
