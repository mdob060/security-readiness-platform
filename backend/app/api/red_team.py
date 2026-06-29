from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models import RedTeamOp, Tenant
from ..schemas import RedTeamOpCreate, RedTeamOpResponse

router = APIRouter(prefix="/api/red-team", tags=["red-team"])

SEED_OPS = [
    {
        "title": "External Attack Surface Assessment - CBL",
        "description": "Full external attack surface assessment of Central Bank of Libya infrastructure. Includes OSINT, port scanning, web application testing, and phishing simulation.",
        "phase": "reconnaissance",
        "status": "completed",
        "operator": "Red Team Lead",
        "ttps": "T1595,T1590,T1589,T1598,T1566",
        "tenant_name": "مصرف ليبيا المركزي"
    },
    {
        "title": "Adversary Simulation - APT34 TTP Emulation",
        "description": "Emulation of APT34 tactics targeting Libyan government infrastructure. Tests defensive controls against known Iranian threat actor TTPs.",
        "phase": "execution",
        "status": "in_progress",
        "operator": "Senior Red Teamer",
        "ttps": "T1566.001,T1059.001,T1055,T1071.001,T1041",
        "tenant_name": "حكومة الوحدة الوطنية"
    },
    {
        "title": "Physical Security Assessment - NOC Facilities",
        "description": "Physical penetration testing of NOC facilities including badge cloning, tailgating, and social engineering attempts on operational staff.",
        "phase": "delivery",
        "status": "planned",
        "operator": "Physical Security Team",
        "ttps": "T1190,T1078,T1110",
        "tenant_name": "المؤسسة الوطنية للنفط"
    },
    {
        "title": "Purple Team Exercise - Ransomware Simulation",
        "description": "Collaborative purple team exercise simulating a ransomware attack chain from initial access through encryption and lateral movement.",
        "phase": "post_exploitation",
        "status": "completed",
        "operator": "Purple Team",
        "ttps": "T1486,T1490,T1489,T1070",
        "tenant_name": "وزارة المالية"
    },
    {
        "title": "Social Engineering Campaign - Telecom Staff",
        "description": "Targeted vishing and email phishing campaign against telecom sector employees to test security awareness and incident reporting procedures.",
        "phase": "initial_access",
        "status": "in_progress",
        "operator": "Social Engineering Team",
        "ttps": "T1566,T1598,T1656",
        "tenant_name": "شركة ليبيانا"
    }
]


def seed_red_team(db: Session):
    count = db.query(RedTeamOp).count()
    if count > 0:
        return
    tenants = {t.name: t.id for t in db.query(Tenant).all()}
    first_tenant_id = db.query(Tenant).first().id if db.query(Tenant).first() else None

    for op_data in SEED_OPS:
        tenant_name = op_data.pop("tenant_name", "")
        tenant_id = tenants.get(tenant_name, first_tenant_id)
        op = RedTeamOp(tenant_id=tenant_id, **op_data)
        db.add(op)
    db.commit()


@router.get("/operations", response_model=List[RedTeamOpResponse])
def list_operations(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(RedTeamOp)
    if status:
        query = query.filter(RedTeamOp.status == status)
    if phase:
        query = query.filter(RedTeamOp.phase == phase)
    return query.order_by(RedTeamOp.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/operations/{op_id}", response_model=RedTeamOpResponse)
def get_operation(op_id: int, db: Session = Depends(get_db)):
    op = db.query(RedTeamOp).filter(RedTeamOp.id == op_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


@router.post("/operations", response_model=RedTeamOpResponse, status_code=201)
def create_operation(op: RedTeamOpCreate, db: Session = Depends(get_db)):
    db_op = RedTeamOp(**op.model_dump())
    db.add(db_op)
    db.commit()
    db.refresh(db_op)
    return db_op


@router.put("/operations/{op_id}", response_model=RedTeamOpResponse)
def update_operation(op_id: int, op: RedTeamOpCreate, db: Session = Depends(get_db)):
    db_op = db.query(RedTeamOp).filter(RedTeamOp.id == op_id).first()
    if not db_op:
        raise HTTPException(status_code=404, detail="Operation not found")
    for key, value in op.model_dump(exclude_unset=True).items():
        setattr(db_op, key, value)
    db.commit()
    db.refresh(db_op)
    return db_op


@router.get("/ttps")
def get_ttp_library():
    return [
        {"id": "T1566", "name": "Phishing", "tactic": "Initial Access", "subtechniques": ["T1566.001", "T1566.002", "T1566.003"]},
        {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
        {"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution", "subtechniques": ["T1059.001", "T1059.003", "T1059.005"]},
        {"id": "T1055", "name": "Process Injection", "tactic": "Defense Evasion"},
        {"id": "T1003", "name": "OS Credential Dumping", "tactic": "Credential Access", "subtechniques": ["T1003.001", "T1003.002"]},
        {"id": "T1021", "name": "Remote Services", "tactic": "Lateral Movement", "subtechniques": ["T1021.001", "T1021.002", "T1021.006"]},
        {"id": "T1486", "name": "Data Encrypted for Impact", "tactic": "Impact"},
        {"id": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration"},
        {"id": "T1071", "name": "Application Layer Protocol", "tactic": "Command and Control"},
        {"id": "T1078", "name": "Valid Accounts", "tactic": "Privilege Escalation"},
        {"id": "T1053", "name": "Scheduled Task/Job", "tactic": "Persistence"},
        {"id": "T1547", "name": "Boot or Logon Autostart Execution", "tactic": "Persistence"},
    ]


@router.get("/stats")
def get_redteam_stats(db: Session = Depends(get_db)):
    total = db.query(RedTeamOp).count()
    by_status = {
        "planned": db.query(RedTeamOp).filter(RedTeamOp.status == "planned").count(),
        "in_progress": db.query(RedTeamOp).filter(RedTeamOp.status == "in_progress").count(),
        "completed": db.query(RedTeamOp).filter(RedTeamOp.status == "completed").count(),
    }
    return {"total": total, "by_status": by_status}
