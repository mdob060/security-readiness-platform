from datetime import datetime, timezone
from flask_login import UserMixin
from database import db
import hashlib
import secrets


def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(stored_password, provided_password):
    try:
        salt, hashed = stored_password.split(':')
        return hashlib.sha256((provided_password + salt).encode()).hexdigest() == hashed
    except Exception:
        return False


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(120))
    full_name_ar = db.Column(db.String(120))
    role = db.Column(db.String(20), default='Viewer')  # Admin, Manager, Analyst, RedTeam, Viewer
    is_active = db.Column(db.Boolean, default=True)
    totp_secret = db.Column(db.String(32))
    totp_enabled = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(self.password_hash, password)

    def is_locked(self):
        if self.locked_until and datetime.now(timezone.utc) < self.locked_until.replace(tzinfo=timezone.utc):
            return True
        return False

    def get_role_display(self):
        roles = {
            'Admin': 'مدير النظام',
            'Manager': 'مدير',
            'Analyst': 'محلل',
            'RedTeam': 'فريق أحمر',
            'Viewer': 'مشاهد'
        }
        return roles.get(self.role, self.role)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    username = db.Column(db.String(80))
    action = db.Column(db.String(200), nullable=False)
    module = db.Column(db.String(50))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    severity = db.Column(db.String(20), default='info')  # info, warning, critical

    user = db.relationship('User', backref='audit_logs', foreign_keys=[user_id])


class ExtortionCase(db.Model):
    __tablename__ = 'extortion_cases'
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True)
    victim_name = db.Column(db.String(120))
    victim_national_id = db.Column(db.String(20))
    victim_phone = db.Column(db.String(20))
    victim_email = db.Column(db.String(120))
    victim_gender = db.Column(db.String(10))
    victim_age = db.Column(db.Integer)
    incident_type = db.Column(db.String(50))  # blackmail, revenge_porn, financial, threats
    incident_description = db.Column(db.Text)
    incident_date = db.Column(db.DateTime)
    platform_used = db.Column(db.String(100))  # WhatsApp, Telegram, Instagram, etc.
    suspect_username = db.Column(db.String(100))
    suspect_phone = db.Column(db.String(20))
    suspect_email = db.Column(db.String(120))
    suspect_ip = db.Column(db.String(45))
    evidence_description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, investigating, closed, referred
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)
    legal_report_generated = db.Column(db.Boolean, default=False)

    assigned_user = db.relationship('User', foreign_keys=[assigned_to])
    creator = db.relationship('User', foreign_keys=[created_by])


class NationalAsset(db.Model):
    __tablename__ = 'national_assets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_ar = db.Column(db.String(200))
    category = db.Column(db.String(50))  # Ministry, Bank, Infrastructure, Telecom, Health, Energy
    subcategory = db.Column(db.String(100))
    ip_range = db.Column(db.String(200))
    domain = db.Column(db.String(200))
    contact_name = db.Column(db.String(120))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    risk_score = db.Column(db.Integer, default=0)  # 0-100
    last_scan = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    location = db.Column(db.String(200))
    criticality = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)

    vulnerabilities = db.relationship('AssetVulnerability', backref='asset', lazy=True)


class AssetVulnerability(db.Model):
    __tablename__ = 'asset_vulnerabilities'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('national_assets.id'))
    cve_id = db.Column(db.String(20))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    severity = db.Column(db.String(20))  # critical, high, medium, low
    cvss_score = db.Column(db.Float)
    status = db.Column(db.String(20), default='open')  # open, mitigated, accepted
    discovered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime)


class Threat(db.Model):
    __tablename__ = 'threats'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200))
    category = db.Column(db.String(50))  # APT, Ransomware, Phishing, DDoS, Insider, Malware
    severity = db.Column(db.String(20))  # critical, high, medium, low
    description = db.Column(db.Text)
    source = db.Column(db.String(100))
    target_sector = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, mitigated, monitoring
    confidence = db.Column(db.Integer, default=50)  # 0-100%
    first_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    tags = db.Column(db.String(500))

    iocs = db.relationship('IOC', backref='threat', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by])


class IOC(db.Model):
    __tablename__ = 'iocs'
    id = db.Column(db.Integer, primary_key=True)
    threat_id = db.Column(db.Integer, db.ForeignKey('threats.id'))
    ioc_type = db.Column(db.String(30))  # ip, domain, hash, email, url, file
    value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    confidence = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PentestEngagement(db.Model):
    __tablename__ = 'pentest_engagements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    target = db.Column(db.String(200))
    scope = db.Column(db.Text)
    authorization_ref = db.Column(db.String(100))
    authorized_by = db.Column(db.String(120))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='planned')  # planned, active, completed, cancelled
    methodology = db.Column(db.String(50))  # blackbox, whitebox, greybox
    findings_count = db.Column(db.Integer, default=0)
    critical_findings = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)

    creator = db.relationship('User', foreign_keys=[created_by])
    tasks = db.relationship('PentestTask', backref='engagement', lazy=True)


class PentestTask(db.Model):
    __tablename__ = 'pentest_tasks'
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('pentest_engagements.id'))
    tool = db.Column(db.String(50))
    command = db.Column(db.Text)
    target = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    output = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200))
    message = db.Column(db.Text)
    severity = db.Column(db.String(20), default='medium')
    source = db.Column(db.String(50))  # system, threat, asset, blue_team
    asset_id = db.Column(db.Integer, db.ForeignKey('national_assets.id'))
    threat_id = db.Column(db.Integer, db.ForeignKey('threats.id'))
    is_read = db.Column(db.Boolean, default=False)
    is_acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    asset = db.relationship('NationalAsset', foreign_keys=[asset_id])
    threat = db.relationship('Threat', foreign_keys=[threat_id])


class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
