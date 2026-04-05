import os
import io
from datetime import datetime, timezone
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, send_file, jsonify, current_app)
from flask_login import login_required, current_user
from models import ExtortionCase, AuditLog, User
from database import db

anti_extortion_bp = Blueprint('anti_extortion', __name__, url_prefix='/anti-extortion')


def log_action(action, details='', severity='info'):
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module='anti_extortion',
        details=details,
        ip_address=request.remote_addr,
        severity=severity
    )
    db.session.add(log)
    db.session.commit()


def generate_case_number():
    from datetime import date
    year = date.today().year
    count = ExtortionCase.query.count() + 1
    return f"EC-{year}-{count:04d}"


@anti_extortion_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    search = request.args.get('q', '')

    query = ExtortionCase.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search:
        query = query.filter(
            db.or_(
                ExtortionCase.case_number.ilike(f'%{search}%'),
                ExtortionCase.victim_name.ilike(f'%{search}%'),
                ExtortionCase.victim_phone.ilike(f'%{search}%')
            )
        )

    cases = query.order_by(ExtortionCase.created_at.desc()).all()

    stats = {
        'total': ExtortionCase.query.count(),
        'open': ExtortionCase.query.filter_by(status='open').count(),
        'investigating': ExtortionCase.query.filter_by(status='investigating').count(),
        'closed': ExtortionCase.query.filter_by(status='closed').count(),
        'critical': ExtortionCase.query.filter_by(priority='critical').count(),
    }

    return render_template('anti_extortion/index.html',
                           cases=cases, stats=stats,
                           status_filter=status_filter,
                           priority_filter=priority_filter, search=search)


@anti_extortion_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_case():
    if request.method == 'POST':
        case = ExtortionCase(
            case_number=generate_case_number(),
            victim_name=request.form.get('victim_name'),
            victim_national_id=request.form.get('victim_national_id'),
            victim_phone=request.form.get('victim_phone'),
            victim_email=request.form.get('victim_email'),
            victim_gender=request.form.get('victim_gender'),
            victim_age=int(request.form.get('victim_age') or 0),
            incident_type=request.form.get('incident_type'),
            incident_description=request.form.get('incident_description'),
            incident_date=datetime.strptime(request.form.get('incident_date'), '%Y-%m-%d') if request.form.get('incident_date') else datetime.now(timezone.utc),
            platform_used=request.form.get('platform_used'),
            suspect_username=request.form.get('suspect_username'),
            suspect_phone=request.form.get('suspect_phone'),
            suspect_email=request.form.get('suspect_email'),
            suspect_ip=request.form.get('suspect_ip'),
            evidence_description=request.form.get('evidence_description'),
            status='open',
            priority=request.form.get('priority', 'medium'),
            created_by=current_user.id,
            notes=request.form.get('notes')
        )
        db.session.add(case)
        db.session.commit()

        log_action('CASE_CREATED', f'Case {case.case_number} created', severity='info')
        flash(f'تم إنشاء القضية {case.case_number} بنجاح', 'success')
        return redirect(url_for('anti_extortion.case_detail', case_id=case.id))

    return render_template('anti_extortion/new_case.html')


@anti_extortion_bp.route('/case/<int:case_id>')
@login_required
def case_detail(case_id):
    case = ExtortionCase.query.get_or_404(case_id)
    analysts = User.query.filter(User.role.in_(['Admin', 'Manager', 'Analyst'])).all()
    log_action('CASE_VIEW', f'Viewed case {case.case_number}')
    return render_template('anti_extortion/case_detail.html', case=case, analysts=analysts)


@anti_extortion_bp.route('/case/<int:case_id>/update', methods=['POST'])
@login_required
def update_case(case_id):
    case = ExtortionCase.query.get_or_404(case_id)
    action = request.form.get('action')

    if action == 'update_status':
        old_status = case.status
        case.status = request.form.get('status', case.status)
        case.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        log_action('CASE_STATUS_UPDATE', f'Case {case.case_number}: {old_status} -> {case.status}', severity='warning')
        flash('تم تحديث حالة القضية', 'success')

    elif action == 'assign':
        case.assigned_to = int(request.form.get('assigned_to') or 0) or None
        case.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        log_action('CASE_ASSIGNED', f'Case {case.case_number} assigned')
        flash('تم تعيين المحقق', 'success')

    elif action == 'add_note':
        note = request.form.get('note', '')
        if note:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
            existing = case.notes or ''
            case.notes = f"{existing}\n[{timestamp}] {current_user.username}: {note}".strip()
            case.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            flash('تمت إضافة الملاحظة', 'success')

    return redirect(url_for('anti_extortion.case_detail', case_id=case_id))


@anti_extortion_bp.route('/case/<int:case_id>/osint', methods=['POST'])
@login_required
def osint_lookup(case_id):
    """Simulate OSINT lookup for case data."""
    lookup_type = request.form.get('lookup_type')
    value = request.form.get('value', '').strip()

    results = {
        'lookup_type': lookup_type,
        'value': value,
        'results': []
    }

    # Simulated OSINT results
    if lookup_type == 'username':
        platforms = ['Instagram', 'Twitter/X', 'TikTok', 'Snapchat', 'Telegram', 'Facebook', 'LinkedIn']
        import random
        for p in platforms:
            found = random.choice([True, True, False])
            results['results'].append({
                'platform': p,
                'found': found,
                'url': f'https://www.{p.lower().replace("/x", "").replace("twitter", "x")}.com/{value}' if found else None,
                'status': 'موجود' if found else 'غير موجود'
            })
    elif lookup_type == 'phone':
        results['results'] = [
            {'field': 'مشغل الشبكة', 'value': 'STC / الاتصالات السعودية'},
            {'field': 'النوع', 'value': 'جوال'},
            {'field': 'المنطقة', 'value': 'الرياض، المملكة العربية السعودية'},
            {'field': 'الدولة', 'value': 'المملكة العربية السعودية (+966)'},
            {'field': 'حالة الرقم', 'value': 'نشط'},
        ]
    elif lookup_type == 'email':
        results['results'] = [
            {'field': 'مزود الخدمة', 'value': value.split('@')[-1] if '@' in value else 'غير معروف'},
            {'field': 'تسريبات البيانات', 'value': 'لا توجد تسريبات معروفة'},
            {'field': 'السجل', 'value': 'بريد إلكتروني نشط'},
        ]
    elif lookup_type == 'ip':
        results['results'] = [
            {'field': 'الدولة', 'value': 'روسيا'},
            {'field': 'المدينة', 'value': 'موسكو'},
            {'field': 'مزود الخدمة', 'value': 'AS12345 Unknown ISP'},
            {'field': 'نوع العنوان', 'value': 'VPN/Proxy محتمل'},
            {'field': 'تقييم المخاطر', 'value': 'عالي'},
        ]

    log_action('OSINT_LOOKUP', f'OSINT {lookup_type} lookup for case {case_id}')
    return jsonify(results)


@anti_extortion_bp.route('/case/<int:case_id>/report')
@login_required
def generate_report(case_id):
    """Generate legal PDF report."""
    case = ExtortionCase.query.get_or_404(case_id)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=16, spaceAfter=12, alignment=TA_CENTER)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                       fontSize=12, spaceAfter=6, textColor=colors.darkblue)
        body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                    fontSize=10, spaceAfter=4)

        # Title
        story.append(Paragraph('NATIONAL CYBER DEFENSE PLATFORM', title_style))
        story.append(Paragraph('منصة الدفاع السيبراني الوطني', title_style))
        story.append(Paragraph('ANTI-EXTORTION UNIT - LEGAL REPORT', title_style))
        story.append(Paragraph('وحدة مكافحة الابتزاز الإلكتروني - تقرير قانوني', title_style))
        story.append(HRFlowable(width='100%', thickness=2, color=colors.darkblue))
        story.append(Spacer(1, 0.5*cm))

        # Case Info Table
        story.append(Paragraph('Case Information / معلومات القضية', heading_style))
        case_data = [
            ['Field / الحقل', 'Value / القيمة'],
            ['Case Number / رقم القضية', case.case_number or 'N/A'],
            ['Date / التاريخ', datetime.now().strftime('%Y-%m-%d')],
            ['Status / الحالة', case.status.upper()],
            ['Priority / الأولوية', case.priority.upper()],
            ['Incident Type / نوع الحادثة', case.incident_type or 'N/A'],
            ['Platform / المنصة', case.platform_used or 'N/A'],
        ]
        t = Table(case_data, colWidths=[7*cm, 10*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        # Victim Info
        story.append(Paragraph('Victim Information / معلومات الضحية', heading_style))
        victim_data = [
            ['Field / الحقل', 'Value / القيمة'],
            ['Name / الاسم', case.victim_name or 'CONFIDENTIAL'],
            ['Gender / الجنس', case.victim_gender or 'N/A'],
            ['Age / العمر', str(case.victim_age) if case.victim_age else 'N/A'],
            ['Phone / الهاتف', case.victim_phone or 'N/A'],
            ['National ID / الهوية', case.victim_national_id or 'N/A'],
        ]
        t2 = Table(victim_data, colWidths=[7*cm, 10*cm])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t2)
        story.append(Spacer(1, 0.5*cm))

        # Description
        story.append(Paragraph('Incident Description / وصف الحادثة', heading_style))
        desc = case.incident_description or 'No description provided.'
        story.append(Paragraph(desc, body_style))
        story.append(Spacer(1, 0.5*cm))

        # Suspect Info
        if any([case.suspect_username, case.suspect_phone, case.suspect_email, case.suspect_ip]):
            story.append(Paragraph('Suspect Information / معلومات المشتبه به', heading_style))
            suspect_data = [
                ['Field / الحقل', 'Value / القيمة'],
                ['Username / اسم المستخدم', case.suspect_username or 'N/A'],
                ['Phone / الهاتف', case.suspect_phone or 'N/A'],
                ['Email / البريد الإلكتروني', case.suspect_email or 'N/A'],
                ['IP Address / عنوان IP', case.suspect_ip or 'N/A'],
            ]
            t3 = Table(suspect_data, colWidths=[7*cm, 10*cm])
            t3.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t3)
            story.append(Spacer(1, 0.5*cm))

        # Footer
        story.append(HRFlowable(width='100%', thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            f'Generated by National Cyber Defense Platform | {datetime.now().strftime("%Y-%m-%d %H:%M")} | CONFIDENTIAL',
            ParagraphStyle('footer', parent=styles['Normal'], fontSize=8,
                           textColor=colors.grey, alignment=TA_CENTER)
        ))

        doc.build(story)
        buf.seek(0)

        case.legal_report_generated = True
        db.session.commit()
        log_action('REPORT_GENERATED', f'PDF report for case {case.case_number}', severity='warning')

        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'report_{case.case_number}.pdf')

    except ImportError:
        flash('مكتبة إنشاء PDF غير متاحة. تأكد من تثبيت reportlab.', 'danger')
        return redirect(url_for('anti_extortion.case_detail', case_id=case_id))


@anti_extortion_bp.route('/victim-guide')
@login_required
def victim_guide():
    return render_template('anti_extortion/victim_guide.html')
