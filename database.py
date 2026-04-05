from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_data()


def seed_data():
    from models import (User, NationalAsset, Threat, IOC, Alert,
                        ExtortionCase, PentestEngagement, SystemConfig)
    from datetime import datetime, timezone, timedelta
    import random

    # Create default admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@cyberdefense.gov',
            full_name='System Administrator',
            full_name_ar='مدير النظام',
            role='Admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Create sample users
        users_data = [
            ('analyst1', 'analyst1@cyberdefense.gov', 'Ahmed Al-Rashidi', 'أحمد الراشدي', 'Analyst'),
            ('manager1', 'manager1@cyberdefense.gov', 'Sara Al-Harbi', 'سارة الحربي', 'Manager'),
            ('redteam1', 'redteam1@cyberdefense.gov', 'Khalid Al-Zahrani', 'خالد الزهراني', 'RedTeam'),
            ('viewer1', 'viewer1@cyberdefense.gov', 'Fatima Al-Otaibi', 'فاطمة العتيبي', 'Viewer'),
        ]
        for uname, email, fname, fname_ar, role in users_data:
            u = User(username=uname, email=email, full_name=fname, full_name_ar=fname_ar, role=role)
            u.set_password('password123')
            db.session.add(u)

        db.session.commit()

    # Seed National Assets
    if not NationalAsset.query.first():
        assets = [
            ('Ministry of Interior', 'وزارة الداخلية', 'Ministry', '10.1.0.0/16', 'moi.gov.sa', 'critical', 72),
            ('Ministry of Finance', 'وزارة المالية', 'Ministry', '10.2.0.0/16', 'mof.gov.sa', 'critical', 45),
            ('Saudi Aramco', 'أرامكو السعودية', 'Energy', '10.10.0.0/14', 'aramco.com', 'critical', 88),
            ('Saudi National Bank', 'البنك الأهلي السعودي', 'Bank', '10.20.0.0/16', 'alahli.com', 'critical', 61),
            ('STC Telecom', 'الاتصالات السعودية', 'Telecom', '10.30.0.0/13', 'stc.com.sa', 'high', 55),
            ('Ministry of Health', 'وزارة الصحة', 'Health', '10.40.0.0/16', 'moh.gov.sa', 'high', 38),
            ('Saudi Electricity Company', 'شركة الكهرباء السعودية', 'Infrastructure', '10.50.0.0/15', 'se.com.sa', 'critical', 79),
            ('NEOM Smart City', 'نيوم', 'Infrastructure', '10.60.0.0/16', 'neom.com', 'high', 42),
            ('Riyad Bank', 'بنك الرياض', 'Bank', '10.21.0.0/16', 'riyadbank.com', 'critical', 53),
            ('King Fahad Medical City', 'مدينة الملك فهد الطبية', 'Health', '10.41.0.0/16', 'kfmc.med.sa', 'high', 66),
            ('Saudi Customs', 'الجمارك السعودية', 'Ministry', '10.3.0.0/16', 'zatca.gov.sa', 'high', 49),
            ('SABIC', 'سابك', 'Energy', '10.11.0.0/16', 'sabic.com', 'critical', 71),
        ]
        for name, name_ar, cat, ip, domain, crit, risk in assets:
            a = NationalAsset(
                name=name, name_ar=name_ar, category=cat,
                ip_range=ip, domain=domain, criticality=crit,
                risk_score=risk, status='active',
                last_scan=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))
            )
            db.session.add(a)
        db.session.commit()

    # Seed Threats
    if not Threat.query.first():
        admin = User.query.filter_by(username='admin').first()
        threats_data = [
            ('APT41 Campaign Against Gulf Infrastructure',
             'حملة APT41 ضد البنية التحتية الخليجية',
             'APT', 'critical',
             'Advanced persistent threat group targeting energy and government sectors with custom malware.',
             'CISA Advisory', 'Energy, Government', 95),
            ('Ransomware: BlackCat/ALPHV Variant',
             'برنامج الفدية: نوع BlackCat/ALPHV',
             'Ransomware', 'critical',
             'New ransomware variant targeting healthcare and financial institutions with double extortion.',
             'Internal Detection', 'Health, Finance', 88),
            ('Large-scale Phishing Campaign',
             'حملة تصيد احتيالي واسعة النطاق',
             'Phishing', 'high',
             'Mass phishing emails impersonating government agencies targeting citizens credentials.',
             'Threat Feed', 'Government, Citizens', 92),
            ('DDoS Attack on Telecom Infrastructure',
             'هجوم حجب الخدمة على البنية التحتية للاتصالات',
             'DDoS', 'high',
             'Coordinated DDoS attack targeting major telecom providers using botnet of 50,000+ compromised devices.',
             'CERT Alert', 'Telecom', 78),
            ('Insider Threat: Privileged Access Abuse',
             'تهديد داخلي: إساءة استخدام الوصول المميز',
             'Insider', 'medium',
             'Suspected insider threat activity involving unusual data access patterns and exfiltration attempts.',
             'SIEM Alert', 'Internal', 65),
            ('Log4Shell Exploitation Attempts',
             'محاولات استغلال ثغرة Log4Shell',
             'Malware', 'high',
             'Active exploitation attempts targeting Log4j vulnerability in enterprise applications.',
             'IDS Alert', 'All Sectors', 83),
        ]
        for title, title_ar, cat, sev, desc, src, target, conf in threats_data:
            t = Threat(
                title=title, title_ar=title_ar, category=cat,
                severity=sev, description=desc, source=src,
                target_sector=target, confidence=conf,
                created_by=admin.id if admin else 1,
                first_seen=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                last_seen=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))
            )
            db.session.add(t)
        db.session.commit()

        # Add IOCs
        threat1 = Threat.query.first()
        if threat1:
            iocs = [
                ('ip', '185.220.101.47', 'C2 Server', 90),
                ('ip', '45.142.212.100', 'Scanner IP', 85),
                ('domain', 'malicious-update.net', 'C2 Domain', 92),
                ('hash', 'a1b2c3d4e5f6789012345678901234567890abcd', 'Malware hash SHA1', 95),
                ('url', 'http://evil-site.ru/payload.exe', 'Payload delivery URL', 88),
                ('email', 'phishing@fake-gov.com', 'Phishing sender', 75),
            ]
            for itype, val, desc, conf in iocs:
                ioc = IOC(threat_id=threat1.id, ioc_type=itype, value=val,
                          description=desc, confidence=conf)
                db.session.add(ioc)
            db.session.commit()

    # Seed Extortion Cases
    if not ExtortionCase.query.first():
        admin = User.query.filter_by(username='admin').first()
        cases = [
            ('EC-2024-001', 'محمد أحمد السالم', '1234567890', '0501234567',
             'male', 32, 'blackmail', 'Social Media', 'open', 'high'),
            ('EC-2024-002', 'نورة خالد العمري', '9876543210', '0559876543',
             'female', 28, 'revenge_porn', 'WhatsApp', 'investigating', 'critical'),
            ('EC-2024-003', 'عبدالله سعد الغامدي', '5678901234', '0505678901',
             'male', 45, 'financial', 'Telegram', 'investigating', 'high'),
            ('EC-2024-004', 'سارة محمد الحربي', '3456789012', '0503456789',
             'female', 35, 'threats', 'Instagram', 'closed', 'medium'),
        ]
        for cn, vname, vid, vphone, vgender, vage, itype, platform, status, priority in cases:
            case = ExtortionCase(
                case_number=cn,
                victim_name=vname,
                victim_national_id=vid,
                victim_phone=vphone,
                victim_gender=vgender,
                victim_age=vage,
                incident_type=itype,
                platform_used=platform,
                status=status,
                priority=priority,
                created_by=admin.id if admin else 1,
                incident_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60)),
                incident_description='تم الإبلاغ عن حادثة ابتزاز إلكتروني عبر منصات التواصل الاجتماعي.'
            )
            db.session.add(case)
        db.session.commit()

    # Seed Alerts
    if not Alert.query.first():
        assets = NationalAsset.query.all()
        threats = Threat.query.all()
        alert_data = [
            ('Critical Vulnerability Detected', 'ثغرة أمنية حرجة مكتشفة', 'critical', 'asset'),
            ('Suspicious Login Attempt', 'محاولة تسجيل دخول مشبوهة', 'high', 'system'),
            ('New Threat Intelligence', 'استخبارات تهديد جديدة', 'medium', 'threat'),
            ('DDoS Traffic Spike', 'ارتفاع مشبوه في حركة المرور', 'high', 'asset'),
            ('Malware Signature Detected', 'توقيع برمجية خبيثة مكتشف', 'critical', 'threat'),
            ('Unauthorized Access Attempt', 'محاولة وصول غير مصرح به', 'high', 'system'),
        ]
        for title, title_ar, sev, src in alert_data:
            alert = Alert(
                title=title, title_ar=title_ar,
                severity=sev, source=src,
                message=f'Alert: {title} detected at {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC',
                asset_id=assets[0].id if assets and src == 'asset' else None,
                threat_id=threats[0].id if threats and src == 'threat' else None,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 300))
            )
            db.session.add(alert)
        db.session.commit()

    # Seed PentestEngagement
    if not PentestEngagement.query.first():
        admin = User.query.filter_by(username='admin').first()
        eng = PentestEngagement(
            title='Q1 2024 Infrastructure Pentest',
            target='Ministry of Finance Network',
            scope='10.2.0.0/16, mof.gov.sa subdomains',
            authorization_ref='AUTH-MOF-2024-001',
            authorized_by='Dr. Abdullah Al-Rashid, CISO',
            start_date=datetime.now(timezone.utc) - timedelta(days=10),
            end_date=datetime.now(timezone.utc) + timedelta(days=20),
            status='active',
            methodology='greybox',
            findings_count=12,
            critical_findings=3,
            created_by=admin.id if admin else 1
        )
        db.session.add(eng)
        db.session.commit()

    # Seed System Config
    if not SystemConfig.query.first():
        configs = [
            ('telegram_bot_token', '', 'Telegram Bot Token for alerts'),
            ('telegram_chat_id', '', 'Telegram Chat ID for alerts'),
            ('virustotal_api_key', '', 'VirusTotal API Key'),
            ('alert_email', 'alerts@cyberdefense.gov', 'Email for critical alerts'),
            ('scan_interval', '24', 'Asset scan interval in hours'),
            ('retention_days', '365', 'Audit log retention in days'),
        ]
        for key, val, desc in configs:
            cfg = SystemConfig(key=key, value=val, description=desc)
            db.session.add(cfg)
        db.session.commit()
