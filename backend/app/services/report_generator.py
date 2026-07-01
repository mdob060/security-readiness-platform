import os
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models.monitoring import Alert, Incident
from app.models.scanning import ScanJob

REPORTS_DIR = "/var/lib/dira/reports"


def generate_report_pdf(db: Session, report_type: str, job_id: int) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(REPORTS_DIR, f"report_{report_type}_{job_id}.pdf")

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    story = [
        Paragraph("Dir'a Security Operations Platform", styles["Title"]),
        Paragraph(f"Report type: {report_type}", styles["Heading2"]),
        Paragraph(f"Generated: {datetime.now(timezone.utc).isoformat()}", styles["Normal"]),
        Spacer(1, 16),
    ]

    if report_type in ("incidents", "executive"):
        incidents = db.query(Incident).order_by(Incident.id.desc()).limit(50).all()
        story.append(Paragraph("Recent Incidents", styles["Heading2"]))
        data = [["ID", "Title", "Severity", "Stage", "Created"]]
        for inc in incidents:
            data.append([str(inc.id), inc.title[:60], inc.severity, inc.stage, inc.created_at.strftime("%Y-%m-%d %H:%M")])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, "grey"), ("BACKGROUND", (0, 0), (-1, 0), "#222222")]))
        story.append(table)
        story.append(Spacer(1, 16))

    if report_type in ("compliance", "executive"):
        alerts = db.query(Alert).order_by(Alert.id.desc()).limit(50).all()
        story.append(Paragraph("Recent Alerts", styles["Heading2"]))
        data = [["ID", "Title", "Severity", "Status", "Created"]]
        for alert in alerts:
            data.append([str(alert.id), alert.title[:60], alert.severity, alert.status, alert.created_at.strftime("%Y-%m-%d %H:%M")])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, "grey"), ("BACKGROUND", (0, 0), (-1, 0), "#222222")]))
        story.append(table)
        story.append(Spacer(1, 16))

    scan_count = db.query(ScanJob).count()
    story.append(Paragraph(f"Total Red Team scan jobs executed: {scan_count}", styles["Normal"]))

    doc.build(story)
    return file_path
