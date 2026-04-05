from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone, timedelta
from models import User, AuditLog
from database import db

auth_bp = Blueprint('auth', __name__)


def log_action(user_id, username, action, module='auth', details='', ip='', severity='info'):
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        module=module,
        details=details,
        ip_address=ip,
        severity=severity
    )
    db.session.add(log)
    db.session.commit()


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        totp_code = request.form.get('totp_code', '').strip()
        ip = request.remote_addr

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
            return render_template('login.html')

        if user.is_locked():
            flash('تم قفل الحساب مؤقتاً بسبب محاولات تسجيل دخول متعددة. حاول بعد 15 دقيقة.', 'danger')
            log_action(user.id, username, 'LOGIN_LOCKED', ip=ip, severity='warning')
            return render_template('login.html')

        if not user.check_password(password):
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                flash('تم قفل الحساب بسبب 5 محاولات فاشلة. حاول بعد 15 دقيقة.', 'danger')
                log_action(user.id, username, 'ACCOUNT_LOCKED', ip=ip, severity='critical')
            else:
                remaining = 5 - user.failed_attempts
                flash(f'كلمة المرور غير صحيحة. متبقي {remaining} محاولات.', 'danger')
                log_action(user.id, username, 'LOGIN_FAILED', ip=ip, severity='warning')
            db.session.commit()
            return render_template('login.html')

        # Check 2FA if enabled
        if user.totp_enabled:
            if not totp_code:
                session['pending_user_id'] = user.id
                flash('أدخل رمز المصادقة الثنائية', 'info')
                return render_template('login.html', require_totp=True)
            import pyotp
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(totp_code):
                flash('رمز المصادقة الثنائية غير صحيح', 'danger')
                return render_template('login.html', require_totp=True)

        # Successful login
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user, remember=False)
        log_action(user.id, username, 'LOGIN_SUCCESS', ip=ip, severity='info')

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user.id, current_user.username, 'LOGOUT', ip=request.remote_addr)
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'change_password':
            current_pw = request.form.get('current_password')
            new_pw = request.form.get('new_password')
            confirm_pw = request.form.get('confirm_password')

            if not current_user.check_password(current_pw):
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
            elif new_pw != confirm_pw:
                flash('كلمات المرور الجديدة غير متطابقة', 'danger')
            elif len(new_pw) < 8:
                flash('كلمة المرور يجب أن تكون 8 أحرف على الأقل', 'danger')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                log_action(current_user.id, current_user.username, 'PASSWORD_CHANGED', ip=request.remote_addr, severity='warning')
                flash('تم تغيير كلمة المرور بنجاح', 'success')

        elif action == 'update_profile':
            current_user.full_name = request.form.get('full_name', current_user.full_name)
            current_user.email = request.form.get('email', current_user.email)
            db.session.commit()
            flash('تم تحديث الملف الشخصي', 'success')

    return render_template('profile.html')


@auth_bp.route('/setup-2fa')
@login_required
def setup_2fa():
    import pyotp
    import qrcode
    import io
    import base64

    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        db.session.commit()

    totp = pyotp.TOTP(current_user.totp_secret)
    otp_uri = totp.provisioning_uri(current_user.email, issuer_name='CyberDefense Platform')

    qr = qrcode.QRCode(version=1, box_size=6, border=4)
    qr.add_data(otp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template('setup_2fa.html', qr_code=qr_b64, secret=current_user.totp_secret)


@auth_bp.route('/enable-2fa', methods=['POST'])
@login_required
def enable_2fa():
    import pyotp
    code = request.form.get('totp_code', '').strip()
    if not current_user.totp_secret:
        flash('لم يتم إنشاء مفتاح 2FA بعد', 'danger')
        return redirect(url_for('auth.setup_2fa'))
    totp = pyotp.TOTP(current_user.totp_secret)
    if totp.verify(code):
        current_user.totp_enabled = True
        db.session.commit()
        log_action(current_user.id, current_user.username, '2FA_ENABLED', ip=request.remote_addr, severity='info')
        flash('تم تفعيل المصادقة الثنائية بنجاح', 'success')
    else:
        flash('رمز التحقق غير صحيح', 'danger')
        return redirect(url_for('auth.setup_2fa'))
    return redirect(url_for('auth.profile'))
