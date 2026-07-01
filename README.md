# Dir'a (درع) — Unified Security Operations Platform

Dir'a ("Shield") is a unified security operations platform bringing offensive,
defensive, monitoring, intelligence, sector-specific, and governance
capabilities into a single professional dashboard, instead of running dozens
of separate tools. Built as a Bachelor of Computer Science (Network
Technology & Cybersecurity) capstone project.

## Architecture

- **Database**: PostgreSQL, organized into 27 schemas by function (auth,
  scan_scope, red_team, blue_team, soc, incidents, sigma, honeypot,
  threat_hunting, pipeline, ai_brain, automation, threat_intel, federation,
  banking, ot_scada, ueba, swift_csp, aml, sector_monitor, grc, tenants,
  analytics, reports, phishing, settings), plus Redis for fast caching.
- **Backend**: FastAPI (Python), designed to run as independent systemd
  services (main API, HTTPS API, SOC monitor, honeypot listeners) for
  resilience and clean separation of concerns.
- **Frontend**: Next.js + TypeScript + Tailwind, dark SOC-dashboard theme,
  unified sidebar navigation, live pages auto-refreshing every ~10 seconds.

## Platform security

- Bcrypt password hashing, account lockout after 5 failed attempts (5 min),
  full audit log of every login attempt.
- Role-based access control: `admin`, `analyst`, `viewer`.
- HTTPS with TLS certificates, security headers (CSP, X-Frame-Options,
  X-Content-Type-Options, Referrer-Policy) on every response.
- Request body size limit to blunt basic DoS attempts.
- `fail2ban` watches the application's own auth log and automatically bans
  repeat-offender source IPs via `iptables`.
- Automated PostgreSQL backups every 6 hours (systemd timer), 28-backup
  retention (~7 days).

## Integrated tools

- **Offensive** (gated by Scan Scope — see below): nmap, nuclei, sqlmap,
  gobuster, ffuf, whatweb, amass, hydra, wpscan, dnsrecon, nikto, masscan.
- **Defensive**: lynis, clamav, rkhunter, chkrootkit, fail2ban.

All tool adapters shell out to the real binaries (no simulated output) via
argv-list subprocess calls — never a shell string — so user input can never
be interpreted as shell syntax.

### Scan Scope: the legal/authorization gate

No offensive tool can be run against a target until that target has an
**approved** entry in Scan Scope. An analyst requests a target with a
justification; an admin approves or rejects it. As a safety net beyond the
approval workflow, the platform also refuses to scan public IP ranges unless
an administrator explicitly sets `ALLOW_PUBLIC_SCAN_TARGETS=true` after
confirming written authorization for the engagement — private ranges and
localhost are always permitted for internal testing.

## Repository layout

```
backend/    FastAPI app, SQLAlchemy models, tool adapters, services
frontend/   Next.js dashboard
infra/      docker-compose (Postgres/Redis), systemd units, fail2ban config,
            TLS + backup scripts, server provisioning script
```

## Local development

```bash
# 1. Start Postgres + Redis (or use infra/docker/docker-compose.yml)
sudo service postgresql start && sudo service redis-server start
sudo -u postgres psql -c "CREATE USER dira WITH PASSWORD 'dira_dev_password_change_me';"
sudo -u postgres psql -c "CREATE DATABASE dira OWNER dira;"

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL/JWT_SECRET as needed
PYTHONPATH=. python -m app.db.init_db     # creates schemas + seeds an admin user
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd ../frontend
npm install
npm run dev
```

Default seeded login: `admin` / `ChangeMe123!` — **change this immediately**
after first login (via `POST /api/auth/users` as another admin, or a direct
DB update, since there is no self-service password-reset flow yet).

## Running on Kali Linux

Kali is a natural fit for Dir'a — it already ships most of the integrated
tools (nmap, sqlmap, gobuster, ffuf, nikto, hydra, wpscan, dnsrecon, masscan,
whatweb, amass, and usually nuclei) out of the box. A dedicated script
handles the rest:

```bash
sudo ./infra/scripts/setup-kali.sh
```

This installs whatever Kali doesn't ship by default (Postgres, Redis,
fail2ban, clamav, rkhunter, chkrootkit — none of these are on Kali by
default), grants `nmap`/`masscan` raw-socket capabilities (via `setcap`, so
scans work without running the app as root), creates the database, builds
the frontend, and prints the two commands to start both servers. Open
`http://localhost:3000` (or your Kali VM's IP if accessing from the host
machine) and log in with `admin` / `ChangeMe123!` — change it immediately.

Pass `--systemd` to also install it as persistent background services
(`sudo ./infra/scripts/setup-kali.sh --systemd`) instead of running it
manually in a terminal — see the systemd section below, which applies to
Kali the same as any other systemd-based Linux install.

## Production deployment

See `infra/scripts/setup-server.sh` for a scripted Ubuntu 24.04 provisioning
flow (installs all tools, creates the `dira` system user/database, deploys
the fail2ban jail, installs the systemd units). After running it:

1. Fill in `backend/.env` from `.env.example` with real secrets.
2. Generate (or install a CA-issued) TLS certificate:
   `infra/scripts/generate-self-signed-cert.sh your-domain.example`
3. `systemctl enable --now dira-api dira-api-https dira-monitor dira-honeypot dira-frontend dira-backup.timer`

In this mode the main API process runs with `ENABLE_EMBEDDED_SCHEDULER=false`
and `ENABLE_EMBEDDED_HONEYPOTS=false` (set in `dira-api.service`) since the
SOC monitor and honeypot listeners run as their own independent services —
matching the platform's "separate systemd services" design.

### Known sandbox/environment limitations

Built and verified inside a network-restricted sandbox:

- `freshclam` (ClamAV's official signature updater) is blocked by the
  sandbox's egress policy; a custom signature (EICAR test file) is bundled
  so ClamAV integration is provably real end-to-end. On a host with normal
  internet access, run `freshclam` to pull the full official database.
- `Ollama` (the local LLM backing AI Brain) could not be installed in this
  sandbox (its installer's host is not on the egress allowlist here). The
  AI Brain integration is fully real — it calls Ollama's HTTP API — but
  falls back to a small offline rule-based responder when Ollama isn't
  reachable, so the feature still works end-to-end. Install Ollama normally
  on your deployment host (`curl -fsSL https://ollama.com/install.sh | sh`)
  for full local-LLM answers.
- The AML watchlist ships with clearly-labeled `DEMO-WATCHLIST` fictional
  entries. Load the real OFAC SDN / UN / EU consolidated sanctions lists
  (all public, free downloads) for production use.

## API

Every page in the frontend is backed by a real REST endpoint under `/api/*`
— see `backend/app/api/routers/` for the full set, grouped by module
(auth, scan_scope, red_team, blue_team, monitoring, intelligence, sectors,
management).
