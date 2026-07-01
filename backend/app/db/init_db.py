from sqlalchemy import text

from app.core.security import hash_password
from app.db.base import Base, SessionLocal, engine
from app.models import ALL_SCHEMAS
from app.models.auth import User
from app.models.management import GrcControl, GrcFramework, ModuleSetting
from app.models.intelligence import ThreatActor
from app.models.scanning import PciDssControl
from app.models.sectors import AmlSanctionsEntry, SwiftControl
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
            iso = GrcFramework(name="ISO 27001")
            nist = GrcFramework(name="NIST CSF")
            pci = GrcFramework(name="PCI DSS")
            db.add_all([iso, nist, pci])
            db.flush()
        else:
            iso = db.query(GrcFramework).filter_by(name="ISO 27001").first()
            nist = db.query(GrcFramework).filter_by(name="NIST CSF").first()
            pci = db.query(GrcFramework).filter_by(name="PCI DSS").first()

        if not db.query(GrcControl).first():
            db.add_all(
                [
                    GrcControl(framework_id=iso.id, code="A.5.1", title="Policies for information security"),
                    GrcControl(framework_id=iso.id, code="A.8.1", title="Inventory of assets"),
                    GrcControl(framework_id=iso.id, code="A.9.1", title="Access control policy"),
                    GrcControl(framework_id=iso.id, code="A.12.4", title="Event logging"),
                    GrcControl(framework_id=nist.id, code="ID.AM", title="Asset Management"),
                    GrcControl(framework_id=nist.id, code="PR.AC", title="Identity Management and Access Control"),
                    GrcControl(framework_id=nist.id, code="DE.CM", title="Security Continuous Monitoring"),
                    GrcControl(framework_id=nist.id, code="RS.RP", title="Response Planning"),
                    GrcControl(framework_id=pci.id, code="Req-1", title="Install and maintain network security controls"),
                    GrcControl(framework_id=pci.id, code="Req-10", title="Log and monitor all access"),
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

        if not db.query(ThreatActor).first():
            db.add_all(
                [
                    ThreatActor(name="APT28", aliases="Fancy Bear, Sofacy", origin="Russia", motivation="Espionage",
                                description="State-sponsored group known for spear-phishing and credential harvesting."),
                    ThreatActor(name="APT29", aliases="Cozy Bear, Nobelium", origin="Russia", motivation="Espionage",
                                description="Known for supply-chain compromises and stealthy long-term access."),
                    ThreatActor(name="Lazarus Group", aliases="Hidden Cobra", origin="North Korea", motivation="Financial, Espionage",
                                description="Linked to banking heists (SWIFT) and ransomware operations."),
                    ThreatActor(name="FIN7", aliases="Carbanak", origin="Unknown", motivation="Financial",
                                description="Targets retail and hospitality payment card data."),
                    ThreatActor(name="Conti", aliases=None, origin="Unknown", motivation="Financial (ransomware)",
                                description="Ransomware-as-a-service group targeting healthcare and critical infrastructure."),
                ]
            )

        if not db.query(AmlSanctionsEntry).first():
            # Illustrative demo watchlist only. Production deployments should load the
            # real OFAC SDN / UN / EU consolidated sanctions lists (public downloads).
            db.add_all(
                [
                    AmlSanctionsEntry(full_name="Karim Al-Rashidi", list_source="DEMO-WATCHLIST", entity_type="individual", country="N/A"),
                    AmlSanctionsEntry(full_name="Northgate Trading Corp", list_source="DEMO-WATCHLIST", entity_type="entity", country="N/A"),
                    AmlSanctionsEntry(full_name="Viktor Meridian", list_source="DEMO-WATCHLIST", entity_type="individual", country="N/A"),
                    AmlSanctionsEntry(full_name="Sample Sanctioned Holdings Ltd", list_source="DEMO-WATCHLIST", entity_type="entity", country="N/A"),
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
