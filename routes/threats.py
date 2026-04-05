from datetime import datetime, timezone
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, jsonify)
from flask_login import login_required, current_user
from models import Threat, IOC, Alert, AuditLog
from database import db

threats_bp = Blueprint('threats', __name__, url_prefix='/threats')


def log_action(action, details='', severity='info'):
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module='threats',
        details=details,
        ip_address=request.remote_addr,
        severity=severity
    )
    db.session.add(log)
    db.session.commit()


@threats_bp.route('/')
@login_required
def index():
    category_filter = request.args.get('category', '')
    severity_filter = request.args.get('severity', '')
    search = request.args.get('q', '')

    query = Threat.query

    if category_filter:
        query = query.filter_by(category=category_filter)
    if severity_filter:
        query = query.filter_by(severity=severity_filter)
    if search:
        query = query.filter(
            db.or_(
                Threat.title.ilike(f'%{search}%'),
                Threat.title_ar.ilike(f'%{search}%'),
                Threat.description.ilike(f'%{search}%')
            )
        )

    threats = query.order_by(Threat.created_at.desc()).all()
    iocs = IOC.query.filter_by(is_active=True).order_by(IOC.created_at.desc()).limit(20).all()

    stats = {
        'total': Threat.query.count(),
        'critical': Threat.query.filter_by(severity='critical').count(),
        'high': Threat.query.filter_by(severity='high').count(),
        'active': Threat.query.filter_by(status='active').count(),
        'iocs': IOC.query.filter_by(is_active=True).count(),
    }

    return render_template('threats/index.html',
                           threats=threats, iocs=iocs, stats=stats,
                           category_filter=category_filter,
                           severity_filter=severity_filter,
                           search=search)


@threats_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_threat():
    if current_user.role not in ['Admin', 'Manager', 'Analyst']:
        flash('ليس لديك صلاحية لإضافة التهديدات', 'danger')
        return redirect(url_for('threats.index'))

    if request.method == 'POST':
        threat = Threat(
            title=request.form.get('title'),
            title_ar=request.form.get('title_ar'),
            category=request.form.get('category'),
            severity=request.form.get('severity'),
            description=request.form.get('description'),
            source=request.form.get('source'),
            target_sector=request.form.get('target_sector'),
            confidence=int(request.form.get('confidence', 50)),
            tags=request.form.get('tags'),
            created_by=current_user.id,
            status='active'
        )
        db.session.add(threat)
        db.session.commit()

        # Add IOCs if provided
        ioc_values = request.form.getlist('ioc_value')
        ioc_types = request.form.getlist('ioc_type')
        for itype, ival in zip(ioc_types, ioc_values):
            if ival.strip():
                ioc = IOC(threat_id=threat.id, ioc_type=itype, value=ival.strip(),
                          confidence=threat.confidence)
                db.session.add(ioc)
        db.session.commit()

        # Create alert for critical/high threats
        if threat.severity in ['critical', 'high']:
            alert = Alert(
                title=f'New {threat.severity.upper()} Threat: {threat.title[:50]}',
                title_ar=f'تهديد جديد: {threat.title_ar or threat.title[:50]}',
                severity=threat.severity,
                source='threat',
                message=f'New {threat.category} threat detected targeting {threat.target_sector}',
                threat_id=threat.id
            )
            db.session.add(alert)
            db.session.commit()

        log_action('THREAT_CREATED', f'Created threat: {threat.title}', severity='warning')
        flash(f'تم إضافة التهديد: {threat.title}', 'success')
        return redirect(url_for('threats.index'))

    return render_template('threats/new_threat.html')


@threats_bp.route('/<int:threat_id>/update', methods=['POST'])
@login_required
def update_threat(threat_id):
    threat = Threat.query.get_or_404(threat_id)
    action = request.form.get('action')

    if action == 'update_status':
        threat.status = request.form.get('status', threat.status)
        db.session.commit()
        log_action('THREAT_STATUS_UPDATE', f'Threat {threat_id} status: {threat.status}')
        flash('تم تحديث حالة التهديد', 'success')

    elif action == 'add_ioc':
        ioc = IOC(
            threat_id=threat_id,
            ioc_type=request.form.get('ioc_type'),
            value=request.form.get('ioc_value', '').strip(),
            description=request.form.get('ioc_desc'),
            confidence=int(request.form.get('ioc_confidence', 70))
        )
        db.session.add(ioc)
        db.session.commit()
        log_action('IOC_ADDED', f'Added IOC to threat {threat_id}')
        flash('تمت إضافة مؤشر الاختراق', 'success')

    return redirect(url_for('threats.index'))


@threats_bp.route('/ioc/search', methods=['GET'])
@login_required
def ioc_search():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        iocs = IOC.query.filter(IOC.value.ilike(f'%{q}%')).limit(20).all()
        for ioc in iocs:
            results.append({
                'id': ioc.id,
                'type': ioc.ioc_type,
                'value': ioc.value,
                'confidence': ioc.confidence,
                'threat_id': ioc.threat_id,
                'threat_title': ioc.threat.title if ioc.threat else 'Unknown'
            })
    return jsonify(results)
