from sqlalchemy import text

from app.core.security import hash_password
from app.db.base import Base, SessionLocal, engine
from app.models import ALL_SCHEMAS
from app.models.auth import User
from app.models.management import GrcFramework, ModuleSetting
from app.models.scanning import PciDssControl
from app.models.sectors import SwiftControl
from app.models.tenants import Tenant


def create_schemas() -> None:
    with engine.begin() as conn:
        for schema in ALL_SCHEMAS:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_reference_data() -> None:
    db = SessionLocal()
    try:
        if not db.query(Tenant).first():
            db.add(Tenant(name="Default Organization", sector="government"))

        if not db.query(User).filter_by(username="admin").first():
            db.add(
                User(
                    username="admin",
                    email="admin@dira.local",
                    password_hash=hash_password("ChangeMe123!"),
                    role="admin",
                )
            )

        if not db.query(GrcFramework).first():
            db.add_all(
                [
                    GrcFramework(name="ISO 27001"),
                    GrcFramework(name="NIST CSF"),
                    GrcFramework(name="PCI DSS"),
                ]
            )

        if not db.query(PciDssControl).first():
            db.add_all(
                [
                    PciDssControl(requirement_code="1", description="Install and maintain network security controls", check_type="firewall"),
                    PciDssControl(requirement_code="3", description="Protect stored account data", check_type="encryption"),
                    PciDssControl(requirement_code="5", description="Protect all systems against malware", check_type="av"),
                    PciDssControl(requirement_code="10", description="Log and monitor all access to system components and cardholder data", check_type="logging"),
                ]
            )

        if not db.query(SwiftControl).first():
            db.add_all(
                [
                    SwiftControl(control_code="1.1", title="SWIFT Environment Protection", category="restrict"),
                    SwiftControl(control_code="2.1", title="Internal Data Flow Security", category="protect"),
                    SwiftControl(control_code="5.1", title="Logical Access Control", category="restrict"),
                    SwiftControl(control_code="6.1", title="Malware Protection", category="detect"),
                    SwiftControl(control_code="7.1", title="Cyber Incident Response Planning", category="detect"),
                ]
            )

        if not db.query(ModuleSetting).first():
            for module_key in [
                "red_team", "blue_team", "soc", "honeypot", "ai_brain", "automation",
                "threat_intel", "federation", "banking", "ot_scada", "ueba",
                "swift_csp", "aml", "grc", "phishing",
            ]:
                db.add(ModuleSetting(module_key=module_key, enabled=True))

        db.commit()
    finally:
        db.close()


def init_db() -> None:
    create_schemas()
    create_tables()
    seed_reference_data()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
