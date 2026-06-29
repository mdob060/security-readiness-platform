from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import BlueTeamPlaybook
from ..schemas import BlueTeamPlaybookCreate, BlueTeamPlaybookResponse

router = APIRouter(prefix="/api/blue-team", tags=["blue-team"])

SEED_PLAYBOOKS = [
    {
        "title": "Ransomware Incident Response Playbook",
        "description": "Step-by-step response procedures for ransomware attacks targeting Libyan financial institutions and government entities",
        "trigger": "Ransomware detection alert, file extension changes, ransom note discovered",
        "category": "incident_response",
        "author": "IR Team",
        "steps": """1. IMMEDIATE CONTAINMENT (0-15 min):
   - Isolate affected systems from network immediately
   - Disable network shares and mapped drives
   - Block suspicious IPs at firewall level
   - Engage incident response team

2. IDENTIFICATION (15-60 min):
   - Identify ransomware family using Crypto Sheriff or No More Ransom
   - Determine patient zero and infection vector
   - Map extent of encryption across network
   - Preserve forensic evidence (memory dumps, disk images)

3. ERADICATION (1-4 hours):
   - Remove malware from all affected systems
   - Patch exploited vulnerabilities
   - Reset compromised credentials
   - Rebuild affected systems from clean images

4. RECOVERY (4-48 hours):
   - Restore from clean backups (verify integrity first)
   - Implement additional monitoring
   - Gradual return to operations with enhanced logging

5. POST-INCIDENT:
   - Document timeline and attack chain
   - Update detection rules
   - Conduct lessons learned session
   - Report to relevant authorities (CERT-LY)"""
    },
    {
        "title": "Phishing Email Investigation Playbook",
        "description": "Procedures for investigating and responding to phishing campaigns targeting Libyan organizations",
        "trigger": "User reports suspicious email, email gateway alert, credential compromise suspected",
        "category": "phishing",
        "author": "SOC Team",
        "steps": """1. TRIAGE (0-10 min):
   - Collect original email with headers (do not click links)
   - Check if multiple users received same email
   - Assess if any users clicked links or opened attachments

2. ANALYSIS (10-30 min):
   - Analyze email headers for source IP and spoofing
   - Check URLs against threat intel (VirusTotal, URLscan.io)
   - Analyze attachments in sandbox (Any.run, Hybrid Analysis)
   - Extract IOCs (IPs, domains, hashes, URLs)

3. CONTAINMENT (Parallel):
   - Block malicious URLs/domains at proxy/DNS level
   - Quarantine similar emails from all mailboxes
   - If credentials compromised: force password reset + MFA enrollment
   - Block sender domains/IPs

4. NOTIFICATION:
   - Notify affected users
   - Alert management if sensitive data at risk
   - Share IOCs with sector peers via ISAC

5. REMEDIATION:
   - Update email filtering rules
   - Block at DNS level using sinkhole
   - Add IOCs to SIEM detection rules
   - Issue security awareness communication"""
    },
    {
        "title": "DDoS Attack Mitigation Playbook",
        "description": "Response procedures for Distributed Denial of Service attacks against Libyan government and financial sector",
        "trigger": "Network monitoring alert, ISP notification, service unavailability",
        "category": "availability",
        "author": "Network Security Team",
        "steps": """1. DETECTION & CLASSIFICATION (0-5 min):
   - Identify attack type (volumetric, protocol, application layer)
   - Measure attack volume (Gbps/pps/rps)
   - Identify targeted services and IPs
   - Activate DDoS response team

2. IMMEDIATE MITIGATION (5-30 min):
   - Enable upstream DDoS scrubbing (contact ISP/DDoS provider)
   - Apply rate limiting at edge devices
   - Block attacking IP ranges at border routers
   - Redirect traffic through scrubbing center

3. TRAFFIC ANALYSIS:
   - Capture attack traffic samples (max 100MB)
   - Identify botnet C2 infrastructure
   - Check for amplification sources (DNS, NTP, SSDP)
   - Share attack signatures with ISP

4. RECOVERY:
   - Gradually restore filtered traffic
   - Monitor for attack resumption
   - Adjust ACLs and rate limits
   - Document attack timeline

5. POST-INCIDENT:
   - Report to CERT-LY and sector ISAC
   - Consider CDN/anycast deployment
   - Review BGP filtering rules"""
    },
    {
        "title": "Insider Threat Detection & Response",
        "description": "Playbook for investigating and responding to suspected insider threat activity in Libyan government and financial institutions",
        "trigger": "UEBA alert, data loss prevention alert, HR notification, anomalous access patterns",
        "category": "insider_threat",
        "author": "Threat Hunt Team",
        "steps": """1. INITIAL ASSESSMENT (Confidential):
   - Brief CISO and HR in confidence
   - Do NOT alert suspect
   - Preserve audit logs immediately (legal hold)
   - Identify scope of potential data access

2. COVERT INVESTIGATION:
   - Review DLP logs for data exfiltration attempts
   - Analyze access logs (time, location, volume anomalies)
   - Review email and communication metadata
   - Check for use of unauthorized cloud storage or USB devices

3. EVIDENCE PRESERVATION:
   - Forensic image of suspect's device (covertly if possible)
   - Preserve all relevant logs with chain of custody
   - Screenshot/video of anomalous behavior
   - Coordinate with legal team

4. ESCALATION DECISION:
   - Legal review of findings
   - HR involvement for employment action
   - Law enforcement notification if criminal activity
   - Executive briefing

5. REMEDIATION:
   - Revoke access privileges immediately upon confrontation
   - Assess and notify affected data owners
   - Review and strengthen access controls
   - Conduct access rights audit across organization"""
    },
    {
        "title": "Vulnerability Exploitation Response",
        "description": "Immediate response procedures when a critical vulnerability is being actively exploited in Libyan MSSP client environments",
        "trigger": "IDS/IPS alert, threat intel feed notification, vendor emergency advisory",
        "category": "vulnerability_management",
        "author": "Vulnerability Management Team",
        "steps": """1. RAPID ASSESSMENT (0-30 min):
   - Identify affected systems in asset inventory
   - Determine exploitation status (confirmed vs suspected)
   - Assess business impact of affected systems
   - Notify tenant security contacts

2. EMERGENCY PATCHING (if available):
   - Test patch in staging environment
   - Deploy emergency patch using jump-host
   - Verify patch application
   - Monitor for exploitation post-patch

3. WORKAROUND IMPLEMENTATION (if no patch):
   - Implement compensating controls
   - Temporarily disable vulnerable feature/service
   - Restrict network access to vulnerable systems
   - Add virtual patching rule at WAF/IPS

4. HUNT FOR EXPLOITATION:
   - Search logs for exploitation indicators
   - Check for persistence mechanisms
   - Analyze for lateral movement signs
   - Correlate with threat intel

5. TRACKING:
   - Open vulnerability ticket with SLA
   - Track patch deployment status
   - Verify remediation effectiveness
   - Update CMDB with patch status"""
    }
]


def seed_blue_team(db: Session):
    count = db.query(BlueTeamPlaybook).count()
    if count > 0:
        return
    for playbook_data in SEED_PLAYBOOKS:
        playbook = BlueTeamPlaybook(**playbook_data)
        db.add(playbook)
    db.commit()


@router.get("/playbooks", response_model=List[BlueTeamPlaybookResponse])
def list_playbooks(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BlueTeamPlaybook)
    if category:
        query = query.filter(BlueTeamPlaybook.category == category)
    return query.order_by(BlueTeamPlaybook.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/playbooks/{playbook_id}", response_model=BlueTeamPlaybookResponse)
def get_playbook(playbook_id: int, db: Session = Depends(get_db)):
    playbook = db.query(BlueTeamPlaybook).filter(BlueTeamPlaybook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.post("/playbooks", response_model=BlueTeamPlaybookResponse, status_code=201)
def create_playbook(playbook: BlueTeamPlaybookCreate, db: Session = Depends(get_db)):
    db_playbook = BlueTeamPlaybook(**playbook.model_dump())
    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)
    return db_playbook


@router.put("/playbooks/{playbook_id}", response_model=BlueTeamPlaybookResponse)
def update_playbook(playbook_id: int, playbook: BlueTeamPlaybookCreate, db: Session = Depends(get_db)):
    db_playbook = db.query(BlueTeamPlaybook).filter(BlueTeamPlaybook.id == playbook_id).first()
    if not db_playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    for key, value in playbook.model_dump(exclude_unset=True).items():
        setattr(db_playbook, key, value)
    db.commit()
    db.refresh(db_playbook)
    return db_playbook


@router.delete("/playbooks/{playbook_id}")
def delete_playbook(playbook_id: int, db: Session = Depends(get_db)):
    playbook = db.query(BlueTeamPlaybook).filter(BlueTeamPlaybook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    db.delete(playbook)
    db.commit()
    return {"message": "Playbook deleted"}


@router.get("/defense-controls")
def get_defense_controls():
    return [
        {"control": "SIEM", "status": "active", "coverage": "85%", "alerts_today": 234},
        {"control": "EDR", "status": "active", "coverage": "92%", "detections_today": 12},
        {"control": "WAF", "status": "active", "coverage": "100%", "blocks_today": 1847},
        {"control": "DLP", "status": "active", "coverage": "78%", "violations_today": 3},
        {"control": "NDR", "status": "active", "coverage": "95%", "anomalies_today": 7},
        {"control": "IDS/IPS", "status": "active", "coverage": "88%", "signatures": 45123},
        {"control": "Email Gateway", "status": "active", "coverage": "100%", "blocked_emails_today": 892},
        {"control": "DNS Firewall", "status": "active", "coverage": "100%", "blocked_domains_today": 147},
        {"control": "Threat Intel Platform", "status": "active", "ioc_count": 23847, "feeds": 12},
        {"control": "SOAR", "status": "active", "automations": 34, "tickets_auto_closed_today": 89},
    ]
