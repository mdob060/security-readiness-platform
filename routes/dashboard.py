import json
import time
from flask import Blueprint, render_template, Response, stream_with_context
from flask_login import login_required, current_user
from models import Alert, NationalAsset, Threat, ExtortionCase, AuditLog
from database import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Stats
    total_assets = NationalAsset.query.count()
    active_cases = ExtortionCase.query.filter_by(status='open').count() + \
                   ExtortionCase.query.filter_by(status='investigating').count()
    total_threats = Threat.query.filter_by(status='active').count()
    critical_alerts = Alert.query.filter_by(severity='critical', is_acknowledged=False).count()

    # Risk overview
    avg_risk = db.session.query(func.avg(NationalAsset.risk_score)).scalar() or 0
    avg_risk = round(float(avg_risk))

    # Recent alerts
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()

    # Asset risk distribution
    low_risk = NationalAsset.query.filter(NationalAsset.risk_score <= 30).count()
    medium_risk = NationalAsset.query.filter(NationalAsset.risk_score.between(31, 60)).count()
    high_risk = NationalAsset.query.filter(NationalAsset.risk_score.between(61, 80)).count()
    critical_risk = NationalAsset.query.filter(NationalAsset.risk_score > 80).count()

    # Threat categories
    threat_cats = db.session.query(
        Threat.category, func.count(Threat.id)
    ).group_by(Threat.category).all()

    # Recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()

    # High risk assets
    high_risk_assets = NationalAsset.query.filter(
        NationalAsset.risk_score > 70
    ).order_by(NationalAsset.risk_score.desc()).limit(5).all()

    return render_template('index.html',
        total_assets=total_assets,
        active_cases=active_cases,
        total_threats=total_threats,
        critical_alerts=critical_alerts,
        avg_risk=avg_risk,
        recent_alerts=recent_alerts,
        low_risk=low_risk,
        medium_risk=medium_risk,
        high_risk=high_risk,
        critical_risk=critical_risk,
        threat_cats=json.dumps(dict(threat_cats)),
        recent_logs=recent_logs,
        high_risk_assets=high_risk_assets
    )


@dashboard_bp.route('/api/sse/alerts')
@login_required
def sse_alerts():
    """Server-Sent Events endpoint for real-time alerts."""
    def generate():
        last_id = 0
        while True:
            alerts = Alert.query.filter(
                Alert.id > last_id
            ).order_by(Alert.created_at.desc()).limit(5).all()

            if alerts:
                last_id = max(a.id for a in alerts)
                for alert in reversed(alerts):
                    data = json.dumps({
                        'id': alert.id,
                        'title': alert.title,
                        'title_ar': alert.title_ar or alert.title,
                        'severity': alert.severity,
                        'source': alert.source,
                        'message': alert.message,
                        'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M:%S') if alert.created_at else ''
                    })
                    yield f"data: {data}\n\n"

            # Send heartbeat
            yield f"data: {json.dumps({'type': 'heartbeat', 'time': int(time.time())})}\n\n"
            time.sleep(10)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
