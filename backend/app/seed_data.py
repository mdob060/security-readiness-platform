LIBYAN_TENANTS = [
    # ===== حكومة =====
    {"name": "حكومة الوحدة الوطنية", "domain": "gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 72},
    {"name": "وزارة الخارجية والتعاون الدولي", "domain": "foreign.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 68},
    {"name": "وزارة الداخلية", "domain": "interior.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 85},
    {"name": "وزارة المالية", "domain": "finance.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 78},
    {"name": "وزارة الاقتصاد والتجارة", "domain": "economy.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 65},
    {"name": "وزارة الاتصالات وتقنية المعلومات", "domain": "moc.ly", "industry": "Government", "sector": "حكومي", "risk_score": 70},
    {"name": "وزارة التعليم", "domain": "education.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 55},
    {"name": "وزارة الصحة", "domain": "health.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 80},
    {"name": "وزارة العدل", "domain": "justice.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 62},
    {"name": "ديوان المحاسبة", "domain": "audit.gov.ly", "industry": "Government", "sector": "حكومي", "risk_score": 74},
    # ===== مصارف =====
    {"name": "مصرف ليبيا المركزي", "domain": "cbl.gov.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 90},
    {"name": "مصرف الجمهورية", "domain": "jumhouria-bank.com.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 88},
    {"name": "مصرف الوحدة", "domain": "wahdabank.com", "industry": "Banking", "sector": "مصرفي", "risk_score": 82},
    {"name": "مصرف التجارة والتنمية", "domain": "cdb.com.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 75},
    {"name": "مصرف الصحاري", "domain": "saharabank.com.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 79},
    {"name": "المصرف التجاري الوطني", "domain": "ncb.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 83},
    {"name": "مصرف أمان", "domain": "amanbank.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 71},
    {"name": "مصرف الواحة", "domain": "alwahabank.com", "industry": "Banking", "sector": "مصرفي", "risk_score": 76},
    {"name": "مصرف الادخار والاستثمار العقاري", "domain": "reib.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 69},
    {"name": "بنك الشمال الأفريقي", "domain": "nab.ly", "industry": "Banking", "sector": "مصرفي", "risk_score": 73},
    # ===== اتصالات =====
    {"name": "شركة ليبيانا للاتصالات", "domain": "libyana.ly", "industry": "Telecom", "sector": "اتصالات", "risk_score": 73},
    {"name": "شركة المدار الجديد", "domain": "almadar.ly", "industry": "Telecom", "sector": "اتصالات", "risk_score": 68},
    {"name": "شركة ليبيا للاتصالات والتقنية (LPTIC)", "domain": "lptic.ly", "industry": "Telecom", "sector": "اتصالات", "risk_score": 77},
    {"name": "شركة هاتف ليبيا", "domain": "hatif.ly", "industry": "Telecom", "sector": "اتصالات", "risk_score": 65},
    {"name": "ليبيا للاتصالات الدولية (LTT)", "domain": "ltt.net.ly", "industry": "Telecom", "sector": "اتصالات", "risk_score": 70},
    # ===== بنية تحتية حيوية =====
    {"name": "المؤسسة الوطنية للنفط (NOC)", "domain": "noc.ly", "industry": "Energy", "sector": "طاقة", "risk_score": 95},
    {"name": "الشركة العامة للكهرباء (GECOL)", "domain": "gecol.com", "industry": "Energy", "sector": "طاقة", "risk_score": 88},
    {"name": "الهيئة العامة للاتصالات والمعلوماتية", "domain": "gaticly.com", "industry": "Government", "sector": "حكومي", "risk_score": 82},
    {"name": "مطار معيتيقة الدولي", "domain": "mitiga-airport.ly", "industry": "Aviation", "sector": "طيران", "risk_score": 85},
    {"name": "المؤسسة الليبية للإعلام", "domain": "libyatv.ly", "industry": "Media", "sector": "إعلام", "risk_score": 60},
]

SAMPLE_VULNERABILITIES = [
    {"cve_id": "CVE-2021-44228", "title": "Log4Shell - Apache Log4j RCE", "severity": "critical", "cvss_score": 10.0, "description": "ثغرة تنفيذ أوامر عن بُعد في Apache Log4j", "affected_component": "Apache Log4j 2.x", "remediation": "تحديث Log4j إلى الإصدار 2.17.1 أو أحدث"},
    {"cve_id": "CVE-2022-26134", "title": "Confluence OGNL Injection", "severity": "critical", "cvss_score": 9.8, "description": "ثغرة حقن OGNL في Atlassian Confluence", "affected_component": "Confluence Server", "remediation": "تطبيق التحديث الأمني من Atlassian"},
    {"cve_id": "CVE-2023-23397", "title": "Microsoft Outlook Privilege Escalation", "severity": "critical", "cvss_score": 9.8, "description": "ثغرة في Microsoft Outlook تسمح بسرقة NTLM hash", "affected_component": "Microsoft Outlook", "remediation": "تثبيت تحديث مارس 2023 من Microsoft"},
    {"cve_id": "CVE-2021-34527", "title": "PrintNightmare - Windows Print Spooler RCE", "severity": "critical", "cvss_score": 8.8, "description": "ثغرة في خدمة Print Spooler تسمح بتنفيذ أوامر", "affected_component": "Windows Print Spooler", "remediation": "تعطيل Print Spooler أو تثبيت التحديث الأمني"},
    {"cve_id": "CVE-2020-1472", "title": "Zerologon - Netlogon Privilege Escalation", "severity": "critical", "cvss_score": 10.0, "description": "ثغرة في Netlogon تسمح بالاستيلاء على Domain Controller", "affected_component": "Windows Server Netlogon", "remediation": "تثبيت تحديث أغسطس 2020"},
    {"cve_id": "CVE-2023-44487", "title": "HTTP/2 Rapid Reset Attack", "severity": "high", "cvss_score": 7.5, "description": "هجوم DoS على خوادم HTTP/2", "affected_component": "HTTP/2 Servers", "remediation": "تحديث خادم الويب وتطبيق rate limiting"},
    {"cve_id": "CVE-2022-30190", "title": "Follina - MSDT Remote Code Execution", "severity": "high", "cvss_score": 7.8, "description": "ثغرة في MSDT تسمح بتنفيذ أوامر عبر مستندات Office", "affected_component": "Microsoft Support Diagnostic Tool", "remediation": "تعطيل MSDT أو تثبيت تحديث يونيو 2022"},
    {"cve_id": "CVE-2021-26855", "title": "ProxyLogon - Microsoft Exchange SSRF", "severity": "critical", "cvss_score": 9.8, "description": "ثغرة SSRF في Microsoft Exchange Server", "affected_component": "Microsoft Exchange Server", "remediation": "تثبيت تحديث مارس 2021 من Microsoft"},
    {"cve_id": "CVE-2023-20198", "title": "Cisco IOS XE Web UI Privilege Escalation", "severity": "critical", "cvss_score": 10.0, "description": "ثغرة في واجهة الويب لـ Cisco IOS XE", "affected_component": "Cisco IOS XE", "remediation": "تطبيق التحديث الأمني من Cisco"},
    {"cve_id": "CVE-2022-1388", "title": "F5 BIG-IP iControl REST Auth Bypass", "severity": "critical", "cvss_score": 9.8, "description": "تجاوز المصادقة في F5 BIG-IP", "affected_component": "F5 BIG-IP iControl REST", "remediation": "تثبيت الإصلاح من F5 أو تعطيل iControl REST"},
]

SAMPLE_INCIDENTS = [
    {"title": "محاولة اختراق - مصرف الجمهورية", "description": "رُصد هجوم Brute Force على بوابة VPN الخاصة بالمصرف", "severity": "high", "status": "investigating", "incident_type": "Brute Force", "assigned_to": "فريق الاستجابة A"},
    {"title": "تسرب بيانات مشتبه به - وزارة المالية", "description": "اكتُشف نقل غير مصرح به لملفات حساسة خارج الشبكة", "severity": "critical", "status": "open", "incident_type": "Data Exfiltration", "assigned_to": "فريق الاستجابة B"},
    {"title": "إصابة بـ Ransomware - شبكة داخلية", "description": "رصد تشفير ملفات على عدة أجهزة في الشبكة الداخلية", "severity": "critical", "status": "contained", "incident_type": "Ransomware", "assigned_to": "فريق الاستجابة A"},
    {"title": "هجوم Phishing - موظفي المؤسسة الوطنية للنفط", "description": "حملة تصيد إلكتروني تستهدف موظفي NOC", "severity": "medium", "status": "resolved", "incident_type": "Phishing", "assigned_to": "فريق الاستجابة C"},
    {"title": "اكتشاف C2 Traffic - شبكة ليبيانا", "description": "اكتُشف اتصال مشبوه مع خادم Command & Control خارجي", "severity": "high", "status": "investigating", "incident_type": "C2 Traffic", "assigned_to": "فريق الاستجابة B"},
    {"title": "SQL Injection - بوابة إلكترونية حكومية", "description": "محاولات حقن SQL على قاعدة بيانات الخدمات الإلكترونية", "severity": "high", "status": "open", "incident_type": "SQL Injection", "assigned_to": "فريق الاستجابة A"},
    {"title": "DDoS Attack - موقع الخارجية", "description": "هجوم حجب خدمة موزع يستهدف موقع وزارة الخارجية", "severity": "medium", "status": "resolved", "incident_type": "DDoS", "assigned_to": "فريق الاستجابة C"},
    {"title": "Insider Threat - وصول غير مصرح", "description": "موظف يصل لبيانات خارج نطاق صلاحياته", "severity": "medium", "status": "investigating", "incident_type": "Insider Threat", "assigned_to": "فريق الاستجابة B"},
]

SIGMA_RULES = [
    {"title": "Mimikatz Credential Dumping", "level": "critical", "category": "Credential Access", "description": "كشف استخدام Mimikatz لسرقة بيانات الاعتماد", "detection": "selection:\n  EventID: 4624\n  LogonType: 9\ncondition: selection", "tags": "T1003,credential-access,windows", "author": "فريق Sovereign Security"},
    {"title": "PowerShell Download Cradle", "level": "high", "category": "Execution", "description": "كشف تحميل وتنفيذ كود عبر PowerShell", "detection": "selection:\n  EventID: 4104\n  ScriptBlockText|contains:\n    - 'DownloadString'\n    - 'IEX'\ncondition: selection", "tags": "T1059.001,execution,powershell", "author": "فريق Sovereign Security"},
    {"title": "Suspicious DNS Query - Known C2", "level": "high", "category": "Command and Control", "description": "كشف استفسارات DNS لنطاقات C2 معروفة", "detection": "selection:\n  EventID: 22\n  QueryName|endswith:\n    - '.ru'\n    - '.xyz'\ncondition: selection", "tags": "T1071.004,c2,dns", "author": "فريق Sovereign Security"},
    {"title": "RDP Brute Force Detection", "level": "medium", "category": "Initial Access", "description": "كشف هجمات Brute Force على RDP", "detection": "selection:\n  EventID: 4625\n  LogonType: 10\n  count: '>= 5'\n  timespan: '5m'\ncondition: selection", "tags": "T1110,brute-force,rdp", "author": "فريق Sovereign Security"},
    {"title": "Lateral Movement via PsExec", "level": "high", "category": "Lateral Movement", "description": "كشف حركة جانبية باستخدام PsExec", "detection": "selection:\n  EventID: 7045\n  ServiceName: 'PSEXESVC'\ncondition: selection", "tags": "T1570,lateral-movement,psexec", "author": "فريق Sovereign Security"},
    {"title": "Scheduled Task Creation", "level": "medium", "category": "Persistence", "description": "كشف إنشاء مهام مجدولة مشبوهة", "detection": "selection:\n  EventID: 4698\n  TaskName|contains: 'update'\ncondition: selection", "tags": "T1053,persistence,scheduled-task", "author": "فريق Sovereign Security"},
    {"title": "Data Exfiltration via HTTP POST", "level": "high", "category": "Exfiltration", "description": "كشف تسرب بيانات عبر HTTP POST كبير الحجم", "detection": "selection:\n  EventID: 3\n  DestinationPort: 443\n  BytesSent: '>= 10000000'\ncondition: selection", "tags": "T1048,exfiltration,http", "author": "فريق Sovereign Security"},
    {"title": "Pass-the-Hash Attack", "level": "critical", "category": "Lateral Movement", "description": "كشف هجوم Pass-the-Hash", "detection": "selection:\n  EventID: 4624\n  LogonType: 3\n  AuthPackage: 'NTLM'\ncondition: selection", "tags": "T1550.002,credential-use,ntlm", "author": "فريق Sovereign Security"},
    {"title": "Ransomware File Encryption", "level": "critical", "category": "Impact", "description": "كشف نشاط تشفير ملفات يشبه الـ Ransomware", "detection": "selection:\n  EventID: 11\n  TargetFilename|endswith:\n    - '.encrypted'\n    - '.locked'\n    - '.crypto'\ncondition: selection", "tags": "T1486,ransomware,impact", "author": "فريق Sovereign Security"},
    {"title": "LSASS Memory Access", "level": "critical", "category": "Credential Access", "description": "كشف الوصول لذاكرة LSASS", "detection": "selection:\n  EventID: 10\n  TargetImage|endswith: 'lsass.exe'\n  GrantedAccess: '0x1010'\ncondition: selection", "tags": "T1003.001,credential-dumping,lsass", "author": "فريق Sovereign Security"},
]

THREAT_INTEL_IOCS = [
    {"indicator": "185.220.101.45", "indicator_type": "ip", "threat_type": "C2 Server", "confidence": 95, "source": "AlienVault OTX", "description": "خادم C2 مرتبط بمجموعة APT28", "tags": "apt28,russia,c2"},
    {"indicator": "malicious-update.xyz", "indicator_type": "domain", "threat_type": "Malware Distribution", "confidence": 90, "source": "VirusTotal", "description": "نطاق لتوزيع البرمجيات الخبيثة", "tags": "malware,phishing"},
    {"indicator": "e3b0c44298fc1c149afb", "indicator_type": "hash", "threat_type": "Ransomware", "confidence": 99, "source": "MalwareBazaar", "description": "توقيع Ransomware LockBit 3.0", "tags": "lockbit,ransomware"},
    {"indicator": "91.108.4.0/22", "indicator_type": "cidr", "threat_type": "TOR Exit Node", "confidence": 85, "source": "TOR Project", "description": "نطاق IP لعقد خروج TOR", "tags": "tor,anonymization"},
    {"indicator": "phishing-libya-bank.tk", "indicator_type": "domain", "threat_type": "Phishing", "confidence": 98, "source": "PhishTank", "description": "موقع تصيد ينتحل صفة مصرف ليبي", "tags": "phishing,banking,libya"},
    {"indicator": "45.33.32.156", "indicator_type": "ip", "threat_type": "Scanner", "confidence": 80, "source": "Shodan", "description": "IP يقوم بمسح المنافذ لأهداف ليبية", "tags": "scanning,reconnaissance"},
    {"indicator": "update-security-patch.ru", "indicator_type": "domain", "threat_type": "APT C2", "confidence": 92, "source": "Recorded Future", "description": "نطاق C2 لحملة APT تستهدف الشرق الأوسط", "tags": "apt,russia,c2,middle-east"},
    {"indicator": "10.0.0.0/8", "indicator_type": "cidr", "threat_type": "Internal Threat", "confidence": 50, "source": "Internal", "description": "مراقبة حركة شبكة داخلية", "tags": "internal,monitoring"},
]
