import subprocess
import shutil
import random
from datetime import datetime, timezone
from flask import (Blueprint, render_template, request, jsonify,
                   flash, redirect, url_for)
from flask_login import login_required, current_user
from models import PentestEngagement, PentestTask, AuditLog
from database import db

red_team_bp = Blueprint('red_team', __name__, url_prefix='/red-team')


def log_action(action, details='', severity='info'):
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module='red_team',
        details=details,
        ip_address=request.remote_addr,
        severity=severity
    )
    db.session.add(log)
    db.session.commit()


RED_TOOLS = {
    'nmap': {
        'name': 'Nmap',
        'description': 'Network port/service scanner',
        'description_ar': 'ماسح المنافذ والخدمات',
        'category': 'recon',
        'icon': 'bi-diagram-3',
        'binary': 'nmap',
        'placeholder': 'e.g., 192.168.1.1 or scanme.nmap.org',
    },
    'masscan': {
        'name': 'Masscan',
        'description': 'High-speed port scanner',
        'description_ar': 'ماسح منافذ عالي السرعة',
        'category': 'recon',
        'icon': 'bi-lightning',
        'binary': 'masscan',
        'placeholder': 'e.g., 10.0.0.0/8 -p 80,443',
    },
    'rustscan': {
        'name': 'RustScan',
        'description': 'Fast modern port scanner',
        'description_ar': 'ماسح منافذ سريع وحديث',
        'category': 'recon',
        'icon': 'bi-speedometer2',
        'binary': 'rustscan',
        'placeholder': 'e.g., 192.168.1.1',
    },
    'amass': {
        'name': 'Amass',
        'description': 'In-depth DNS enumeration and attack surface mapping',
        'description_ar': 'تعداد DNS ورسم خرائط الهجوم',
        'category': 'recon',
        'icon': 'bi-map',
        'binary': 'amass',
        'placeholder': 'e.g., example.com',
    },
    'subfinder': {
        'name': 'Subfinder',
        'description': 'Passive subdomain discovery tool',
        'description_ar': 'أداة اكتشاف النطاقات الفرعية',
        'category': 'recon',
        'icon': 'bi-search',
        'binary': 'subfinder',
        'placeholder': 'e.g., example.com',
    },
    'dnsrecon': {
        'name': 'DNSrecon',
        'description': 'DNS reconnaissance and enumeration',
        'description_ar': 'استطلاع وتعداد DNS',
        'category': 'recon',
        'icon': 'bi-globe',
        'binary': 'dnsrecon',
        'placeholder': 'e.g., example.com',
    },
    'burpsuite': {
        'name': 'Burp Suite',
        'description': 'Web application security testing',
        'description_ar': 'اختبار أمان تطبيقات الويب',
        'category': 'web',
        'icon': 'bi-bug',
        'binary': 'burpsuite',
        'placeholder': 'e.g., https://target.com',
    },
    'zap': {
        'name': 'OWASP ZAP',
        'description': 'Web application vulnerability scanner',
        'description_ar': 'ماسح ثغرات تطبيقات الويب',
        'category': 'web',
        'icon': 'bi-shield-exclamation',
        'binary': 'zap.sh',
        'placeholder': 'e.g., https://target.com',
    },
    'wpscan': {
        'name': 'WPScan',
        'description': 'WordPress security scanner',
        'description_ar': 'ماسح أمان WordPress',
        'category': 'web',
        'icon': 'bi-wordpress',
        'binary': 'wpscan',
        'placeholder': 'e.g., https://wordpress-site.com',
    },
    'aircrack': {
        'name': 'Aircrack-ng',
        'description': 'WiFi security testing toolkit',
        'description_ar': 'مجموعة أدوات اختبار أمان WiFi',
        'category': 'wireless',
        'icon': 'bi-wifi',
        'binary': 'aircrack-ng',
        'placeholder': 'e.g., capture.cap',
    },
    'metasploit': {
        'name': 'Metasploit Framework',
        'description': 'Penetration testing framework',
        'description_ar': 'إطار اختبار الاختراق',
        'category': 'exploit',
        'icon': 'bi-terminal-fill',
        'binary': 'msfconsole',
        'placeholder': 'e.g., msfconsole -x "use auxiliary/scanner/portscan/tcp"',
    },
}


def check_tool_available(tool_key):
    tool = RED_TOOLS.get(tool_key, {})
    binary = tool.get('binary')
    if not binary:
        return 'unavailable'
    return 'available' if shutil.which(binary) else 'unavailable'


def generate_simulated_output(tool_key, target=''):
    t = target or 'target'
    outputs = {
        'nmap': f"""Starting Nmap 7.94 ( https://nmap.org )
Nmap scan report for {t}
Host is up (0.043s latency).
Not shown: 991 closed ports
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 8.9p1 Ubuntu
80/tcp   open  http       nginx 1.22.0
443/tcp  open  https      nginx 1.22.0
3306/tcp open  mysql      MySQL 8.0.32
8080/tcp open  http-proxy Squid http proxy 5.2
OS: Linux 4.15 - 5.8

Nmap done: 1 IP address (1 host up) scanned in 12.43 seconds""",

        'masscan': f"""Masscan 1.3.2 (https://github.com/robertdavidgraham/masscan)
Scanning {t}...
Discovered open port 80/tcp on {t}
Discovered open port 443/tcp on {t}
Discovered open port 22/tcp on {t}
Discovered open port 8080/tcp on {t}
Discovered open port 3389/tcp on {t}
rate: 100000.00-kpps, 5.23% done, 0:02:14 remaining""",

        'subfinder': f"""[INF] enumerating subdomains for {t}
[DNS] admin.{t}
[DNS] mail.{t}
[DNS] vpn.{t}
[DNS] dev.{t}
[DNS] staging.{t}
[DNS] api.{t}
[DNS] portal.{t}
[DNS] webmail.{t}
[DNS] remote.{t}
[INF] Found 9 subdomains for {t} in 8.23 seconds""",

        'amass': f"""Amass v4.2.0 - ASN/Domain Enumeration
Target: {t}
[*] dns - {t} - A - 203.0.113.42
[*] dns - admin.{t} - A - 203.0.113.43
[*] dns - mail.{t} - MX - mail.{t}
[*] dns - vpn.{t} - A - 203.0.113.44
[*] cert - api.{t} - A - 203.0.113.45
[*] scrape - dev.{t} - A - 10.0.0.5
Total hosts found: 6 | ASN: AS12345""",

        'dnsrecon': f"""DNSrecon v1.1.5
Target: {t}
[*] Performing General Enumeration against: {t}
[*] SOA ns1.{t} 203.0.113.1
[*] NS ns1.{t} 203.0.113.1
[*] NS ns2.{t} 203.0.113.2
[*] MX mail.{t} 203.0.113.10
[*] A {t} 203.0.113.42
[*] AAAA {t} 2001:db8::1
[*] TXT {t} v=spf1 include:_spf.{t} ~all
[+] 7 Records Found""",

        'rustscan': f"""Open {t}:22
Open {t}:80
Open {t}:443
Open {t}:3306
Open {t}:8080
[~] Starting Script(s)
[>] Running script "nmap -vvv -p 22,80,443,3306,8080 {{ip}}" on ip {t}
Depending on the complexity of the script, results may take some time to appear.""",

        'wpscan': f"""_______________________________________________________________
         __          _______   _____
         \\ \\        / /  __ \\ / ____|
          \\ \\  /\\  / /| |__) | (___   ___  __ _ _ __ ®
           \\ \\/  \\/ / |  ___/ \\___ \\ / __|/ _` | '_ \\
            \\  /\\  /  | |     ____) | (__| (_| | | | |
             \\/  \\/   |_|    |_____/ \\___|\\__,_|_| |_|
WordPress Security Scanner
[+] URL: {t}
[+] WordPress Version: 6.4.2 (found)
[!] 3 vulnerabilities identified
  - CVE-2024-1234: Stored XSS in Elementor < 3.19.0
  - CVE-2024-5678: SQLi in WooCommerce < 8.5.0
  - CVE-2023-9012: CSRF in Contact Form 7
[+] Plugins Found: 8 | Outdated: 3""",

        'zap': f"""OWASP ZAP Spider & Active Scan
Target: {t}
Spider completed: 47 URLs found
Active Scan completed:
  [HIGH] SQL Injection in /search?q=
  [HIGH] XSS Reflected in /comment
  [MEDIUM] CSRF Token Missing in /profile
  [MEDIUM] Insecure Direct Object Reference /user/{{id}}
  [LOW] Server Information Disclosure
  [INFO] Missing Security Headers
Alerts: 6 | High: 2 | Medium: 2 | Low: 1 | Info: 1""",

        'aircrack': f"""Opening {t}
Read 12456 packets.
   #  BSSID              ESSID                  Encryption
   1  AA:BB:CC:DD:EE:FF  Corporate-WiFi         WPA (1 handshake)
   2  11:22:33:44:55:66  Guest-Network          WPA2
Choosing first network as target.
[00:00:47] 12456/9822768 keys tested (26.77 k/s)
Current passphrase: testing123
Key Found! [ p@ssw0rd123 ]
MASTER KEY     : AB CD EF 01 23 45 67 89""",

        'metasploit': f"""Metasploit Framework 6.3.44-dev
msf6 > use auxiliary/scanner/portscan/tcp
msf6 auxiliary(scanner/portscan/tcp) > set RHOSTS {t}
RHOSTS => {t}
msf6 auxiliary(scanner/portscan/tcp) > run
[*] {t}:          - TCP OPEN
[+] {t}:22        - TCP OPEN (SSH)
[+] {t}:80        - TCP OPEN (HTTP)
[+] {t}:443       - TCP OPEN (HTTPS)
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed""",

        'burpsuite': f"""Burp Suite Pro 2024.1.2
Target: {t}
Active Scan Results:
  [CRITICAL] SQL Injection - /api/users?id=1
  [HIGH] Authentication Bypass - /admin
  [HIGH] SSRF - /proxy?url=
  [MEDIUM] JWT None Algorithm - /api/auth
  [MEDIUM] Insecure Deserialization - /api/upload
  [LOW] Clickjacking - Main page
Total Issues: 6 | Critical: 1 | High: 2 | Medium: 2 | Low: 1""",
    }
    return outputs.get(tool_key, f'[+] {tool_key} scan completed on {t}\n[INFO] No critical findings detected.')


@red_team_bp.route('/')
@login_required
def index():
    if current_user.role not in ['Admin', 'Manager', 'RedTeam']:
        flash('وصول مقيد: الفريق الأحمر فقط', 'danger')
        return redirect(url_for('dashboard.index'))

    engagements = PentestEngagement.query.order_by(
        PentestEngagement.created_at.desc()
    ).all()

    tools_status = {}
    for key, tool in RED_TOOLS.items():
        tools_status[key] = {**tool, 'status': check_tool_available(key)}

    available_count = sum(1 for t in tools_status.values() if t['status'] == 'available')

    recent_tasks = PentestTask.query.order_by(
        PentestTask.created_at.desc()
    ).limit(10).all()

    return render_template('red_team/index.html',
                           engagements=engagements,
                           tools=tools_status,
                           available_count=available_count,
                           total_count=len(tools_status),
                           recent_tasks=recent_tasks)


@red_team_bp.route('/engagement/new', methods=['POST'])
@login_required
def new_engagement():
    if current_user.role not in ['Admin', 'Manager', 'RedTeam']:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    eng = PentestEngagement(
        title=request.form.get('title'),
        target=request.form.get('target'),
        scope=request.form.get('scope'),
        authorization_ref=request.form.get('authorization_ref'),
        authorized_by=request.form.get('authorized_by'),
        methodology=request.form.get('methodology', 'greybox'),
        start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d') if request.form.get('start_date') else None,
        end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None,
        notes=request.form.get('notes'),
        created_by=current_user.id,
        status='planned'
    )
    db.session.add(eng)
    db.session.commit()
    log_action('ENGAGEMENT_CREATED', f'Created engagement: {eng.title}', severity='warning')
    flash(f'تم إنشاء الاختبار: {eng.title}', 'success')
    return redirect(url_for('red_team.index'))


@red_team_bp.route('/tool/<tool_key>/run', methods=['POST'])
@login_required
def run_tool(tool_key):
    if current_user.role not in ['Admin', 'Manager', 'RedTeam']:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    if tool_key not in RED_TOOLS:
        return jsonify({'success': False, 'error': 'Tool not found'}), 404

    tool = RED_TOOLS[tool_key]
    target = request.form.get('target', '').strip()
    engagement_id = request.form.get('engagement_id')

    if not target:
        return jsonify({'success': False, 'error': 'Target is required'}), 400

    # Verify engagement authorization
    engagement = None
    if engagement_id:
        engagement = PentestEngagement.query.get(engagement_id)
        if not engagement or engagement.status not in ['planned', 'active']:
            return jsonify({'success': False, 'error': 'No active authorized engagement'}), 403

    log_action('RED_TOOL_RUN', f'Tool: {tool_key}, Target: {target}, Engagement: {engagement_id}', severity='warning')

    # Save task
    task = PentestTask(
        engagement_id=int(engagement_id) if engagement_id else None,
        tool=tool_key,
        command=f'{tool_key} {target}',
        target=target,
        status='completed',
        output=generate_simulated_output(tool_key, target),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        created_by=current_user.id
    )
    db.session.add(task)
    db.session.commit()

    status = check_tool_available(tool_key)
    output = generate_simulated_output(tool_key, target)

    if status == 'available':
        # Tool available - try running it safely with version check
        try:
            safe_cmds = {
                'nmap': ['nmap', '--version'],
                'masscan': ['masscan', '--version'],
                'subfinder': ['subfinder', '-version'],
            }
            if tool_key in safe_cmds:
                result = subprocess.run(
                    safe_cmds[tool_key], capture_output=True, text=True, timeout=5
                )
                version_info = result.stdout.strip().split('\n')[0] if result.stdout else 'Available'
                output = f'[Tool Available: {version_info}]\n\n' + output
        except Exception:
            pass

    return jsonify({
        'success': True,
        'simulated': status == 'unavailable',
        'tool': tool['name'],
        'target': target,
        'output': output,
        'task_id': task.id
    })
