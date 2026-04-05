import random
import json
from datetime import datetime, timezone, timedelta
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, jsonify, Response)
from flask_login import login_required, current_user
from models import NationalAsset, AssetVulnerability, Alert, AuditLog
from database import db

assets_bp = Blueprint('assets', __name__, url_prefix='/assets')


def log_action(action, details='', severity='info'):
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module='assets',
        details=details,
        ip_address=request.remote_addr,
        severity=severity
    )
    db.session.add(log)
    db.session.commit()


def get_risk_color(score):
    if score <= 30:
        return 'success'
    elif score <= 60:
        return 'warning'
    elif score <= 80:
        return 'orange'
    else:
        return 'danger'


def get_risk_label(score):
    if score <= 30:
        return 'منخفض'
    elif score <= 60:
        return 'متوسط'
    elif score <= 80:
        return 'عالي'
    else:
        return 'حرج'


@assets_bp.route('/')
@login_required
def index():
    category_filter = request.args.get('category', '')
    criticality_filter = request.args.get('criticality', '')
    search = request.args.get('q', '')

    query = NationalAsset.query

    if category_filter:
        query = query.filter_by(category=category_filter)
    if criticality_filter:
        query = query.filter_by(criticality=criticality_filter)
    if search:
        query = query.filter(
            db.or_(
                NationalAsset.name.ilike(f'%{search}%'),
                NationalAsset.name_ar.ilike(f'%{search}%'),
                NationalAsset.domain.ilike(f'%{search}%')
            )
        )

    assets = query.order_by(NationalAsset.risk_score.desc()).all()

    # Add helper functions to each asset
    for asset in assets:
        asset.risk_color = get_risk_color(asset.risk_score)
        asset.risk_label = get_risk_label(asset.risk_score)

    stats = {
        'total': NationalAsset.query.count(),
        'critical': NationalAsset.query.filter_by(criticality='critical').count(),
        'high_risk': NationalAsset.query.filter(NationalAsset.risk_score > 70).count(),
        'categories': {}
    }

    categories = ['Ministry', 'Bank', 'Infrastructure', 'Telecom', 'Health', 'Energy']
    for cat in categories:
        stats['categories'][cat] = NationalAsset.query.filter_by(category=cat).count()

    return render_template('assets/index.html',
                           assets=assets, stats=stats,
                           category_filter=category_filter,
                           criticality_filter=criticality_filter,
                           search=search,
                           get_risk_color=get_risk_color,
                           get_risk_label=get_risk_label)


@assets_bp.route('/<int:asset_id>')
@login_required
def asset_detail(asset_id):
    asset = NationalAsset.query.get_or_404(asset_id)
    asset.risk_color = get_risk_color(asset.risk_score)
    asset.risk_label = get_risk_label(asset.risk_score)

    vulnerabilities = AssetVulnerability.query.filter_by(
        asset_id=asset_id
    ).order_by(AssetVulnerability.discovered_at.desc()).all()

    related_alerts = Alert.query.filter_by(
        asset_id=asset_id
    ).order_by(Alert.created_at.desc()).limit(10).all()

    log_action('ASSET_VIEW', f'Viewed asset: {asset.name}')
    return render_template('assets/asset_detail.html',
                           asset=asset,
                           vulnerabilities=vulnerabilities,
                           related_alerts=related_alerts,
                           get_risk_color=get_risk_color)


@assets_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_asset():
    if current_user.role not in ['Admin', 'Manager']:
        flash('ليس لديك صلاحية لإضافة الأصول', 'danger')
        return redirect(url_for('assets.index'))

    if request.method == 'POST':
        asset = NationalAsset(
            name=request.form.get('name'),
            name_ar=request.form.get('name_ar'),
            category=request.form.get('category'),
            ip_range=request.form.get('ip_range'),
            domain=request.form.get('domain'),
            criticality=request.form.get('criticality', 'medium'),
            contact_name=request.form.get('contact_name'),
            contact_email=request.form.get('contact_email'),
            contact_phone=request.form.get('contact_phone'),
            location=request.form.get('location'),
            notes=request.form.get('notes'),
            status='active',
            risk_score=0
        )
        db.session.add(asset)
        db.session.commit()
        log_action('ASSET_CREATED', f'Created asset: {asset.name}')
        flash(f'تم إضافة الأصل: {asset.name}', 'success')
        return redirect(url_for('assets.asset_detail', asset_id=asset.id))

    return render_template('assets/new_asset.html')


@assets_bp.route('/<int:asset_id>/scan', methods=['POST'])
@login_required
def run_scan(asset_id):
    """Simulate a security scan on an asset."""
    asset = NationalAsset.query.get_or_404(asset_id)

    # Simulate scan results
    old_score = asset.risk_score
    new_score = max(0, min(100, old_score + random.randint(-10, 15)))
    asset.risk_score = new_score
    asset.last_scan = datetime.now(timezone.utc)
    db.session.commit()

    # Generate random vulnerabilities
    vuln_count = random.randint(0, 4)
    for _ in range(vuln_count):
        sev = random.choice(['critical', 'high', 'medium', 'low'])
        vuln_templates = {
            'critical': [
                ('CVE-2024-1234', 'Remote Code Execution in Apache', 9.8),
                ('CVE-2024-5678', 'SQL Injection in Web Application', 9.1),
                ('CVE-2023-9999', 'Authentication Bypass', 9.5),
            ],
            'high': [
                ('CVE-2024-2345', 'Cross-Site Scripting (XSS)', 7.5),
                ('CVE-2024-6789', 'Privilege Escalation', 7.8),
                ('CVE-2023-8888', 'Insecure Deserialization', 7.2),
            ],
            'medium': [
                ('CVE-2024-3456', 'Information Disclosure', 5.3),
                ('CVE-2024-7890', 'CSRF Vulnerability', 5.8),
                ('CVE-2023-7777', 'Directory Traversal', 5.5),
            ],
            'low': [
                ('CVE-2024-4567', 'Outdated SSL/TLS Version', 3.1),
                ('CVE-2024-8901', 'Missing Security Headers', 2.8),
                ('CVE-2023-6666', 'Verbose Error Messages', 2.5),
            ]
        }
        template = random.choice(vuln_templates[sev])
        v = AssetVulnerability(
            asset_id=asset_id,
            cve_id=template[0],
            title=template[1],
            description=f'Vulnerability detected during automated scan of {asset.name}',
            severity=sev,
            cvss_score=template[2],
            status='open'
        )
        db.session.add(v)

    # Create alert if high risk
    if new_score > 75:
        alert = Alert(
            title=f'High Risk Asset Detected: {asset.name}',
            title_ar=f'أصل عالي الخطورة: {asset.name_ar or asset.name}',
            severity='critical' if new_score > 85 else 'high',
            source='asset',
            message=f'Risk score for {asset.name} is now {new_score}/100',
            asset_id=asset_id
        )
        db.session.add(alert)

    db.session.commit()
    log_action('ASSET_SCANNED', f'Scanned asset: {asset.name}, Score: {old_score} -> {new_score}', severity='info')

    return jsonify({
        'success': True,
        'old_score': old_score,
        'new_score': new_score,
        'vulns_found': vuln_count,
        'risk_label': get_risk_label(new_score),
        'risk_color': get_risk_color(new_score),
        'message': f'الفحص اكتمل. النتيجة: {new_score}/100'
    })


@assets_bp.route('/export')
@login_required
def export_assets():
    """Export assets as CSV."""
    assets = NationalAsset.query.all()
    lines = ['Name,Name_AR,Category,Domain,IP_Range,Risk_Score,Criticality,Status']
    for a in assets:
        lines.append(f'"{a.name}","{a.name_ar or ""}","{a.category}","{a.domain or ""}","{a.ip_range or ""}",{a.risk_score},"{a.criticality}","{a.status}"')

    csv_data = '\n'.join(lines)
    log_action('ASSETS_EXPORTED', f'Exported {len(assets)} assets')
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=national_assets.csv'}
    )
