# NATIONAL CYBER DEFENSE PROTOTYPE C+

**SOC Platform — Threat Intelligence & Automated Response Engine**

---

## Overview

A full-stack Security Operations Center (SOC) platform featuring:

- **Threat Intelligence** — IOC database, threat actor tracking, intel feeds, MITRE ATT&CK mapping
- **Automated Response** — Playbook engine with simulated response actions (block IP, isolate host, forensics, etc.)
- **SOC Dashboard** — Dark-themed real-time web interface

---

## Architecture

```
security-readiness-platform/
├── backend/                    # FastAPI REST API
│   ├── app/
│   │   ├── main.py             # App entry point
│   │   ├── config.py           # Settings
│   │   ├── models/             # Pydantic data models
│   │   │   ├── threat.py       # IOC, ThreatActor, ThreatEvent, MitreTechnique
│   │   │   └── response.py     # Playbook, PlaybookExecution, ResponseMetrics
│   │   ├── routers/            # API route handlers
│   │   │   ├── threats.py      # /api/v1/threats/*
│   │   │   └── responses.py    # /api/v1/response/*
│   │   ├── services/           # Business logic
│   │   │   ├── threat_intel.py # IOC/actor/feed/event service
│   │   │   └── auto_response.py# Playbook execution engine
│   │   └── data/
│   │       └── seed_data.py    # Pre-loaded IOCs, actors, playbooks, events
│   ├── requirements.txt
│   └── run.py
├── frontend/                   # Single-page dashboard
│   ├── index.html
│   ├── css/style.css           # Dark SOC theme
│   └── js/
│       ├── dashboard.js        # Core: nav, clock, toasts, modal
│       ├── threat-intel.js     # IOCs, events, actors, feeds, MITRE
│       └── auto-response.js    # Playbooks & execution viewer
└── docker-compose.yml
```

---

## Quick Start

### Option 1 — Python directly

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Open: http://localhost:8000

### Option 2 — Docker

```bash
docker-compose up
```

---

## API Endpoints

### Threat Intelligence  `GET /api/v1/threats/`

| Endpoint | Description |
|---|---|
| `GET /stats` | Dashboard statistics |
| `GET /iocs` | List IOCs (filter: type, severity, search) |
| `GET /iocs/{id}` | IOC detail |
| `POST /iocs` | Add new IOC |
| `DELETE /iocs/{id}` | Remove IOC |
| `GET /iocs/search/lookup?value=` | Check if value is a known IOC |
| `GET /actors` | Threat actor list |
| `GET /feeds` | Intelligence feed status |
| `POST /feeds/{id}/toggle` | Enable/disable feed |
| `GET /events` | Threat event log |
| `PUT /events/{id}/status` | Update event status |
| `GET /mitre/techniques` | MITRE ATT&CK techniques |

### Automated Response  `GET /api/v1/response/`

| Endpoint | Description |
|---|---|
| `GET /metrics` | Response engine metrics |
| `GET /playbooks` | List playbooks |
| `POST /playbooks/{id}/execute` | Execute a playbook |
| `POST /playbooks/{id}/toggle` | Enable/disable playbook |
| `GET /executions` | Execution history |
| `GET /executions/{id}` | Execution detail |

### System  `GET /api/v1/`

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /info` | System information |
| `GET /api/docs` | Interactive Swagger UI |

---

## Features

### Threat Intelligence Module
- **IOC Database** — IP, domain, URL, file hash (MD5/SHA256), email, CVE indicators
- **Confidence scoring** — 0–100% with visual bars
- **Threat feeds** — ThreatFox, AlienVault OTX, MalwareBazaar, MISP, Emerging Threats
- **Threat actors** — APT profiling with aliases, origin, TTPs (Lazarus, Sandworm, APT41, LockBit)
- **MITRE ATT&CK** — Technique cards with tactic, detection, and mitigation guidance
- **Event tracking** — Full incident timeline with IOC correlation and actor attribution

### Automated Response Engine
- **4 built-in playbooks** — Ransomware Containment, Phishing Response, Brute Force Lockout, Zero-Day Response
- **12 action types** — block_ip, block_domain, isolate_host, kill_process, quarantine_file, collect_forensics, snapshot_system, notify_team, create_ticket, enrich_ioc, send_alert, reset_credentials
- **Simulated execution** — Each run generates realistic action outputs and timings
- **Metrics tracking** — Total runs, success rate, threats blocked, IPs blocked, hosts isolated

### Dashboard
- Real-time UTC clock
- Dark SOC theme with severity color-coding
- Toast notifications for all actions
- Modal detail panels for all entities
- IOC lookup tool
- Filter/search on all data tables
