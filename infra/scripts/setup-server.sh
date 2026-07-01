#!/usr/bin/env bash
# One-time provisioning script for a fresh Ubuntu 24.04 server.
# Installs system dependencies, the integrated security tools, creates the
# dira system user/database, deploys the fail2ban jail, and installs the
# systemd units. Run as root. Idempotent-ish -- safe to re-run.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INSTALL_DIR="/opt/dira"

echo "==> Installing system packages and integrated security tools"
apt-get update
apt-get install -y \
  postgresql postgresql-contrib redis-server \
  python3 python3-venv nodejs npm \
  nmap gobuster ffuf sqlmap nikto masscan whatweb hydra wpscan dnsrecon \
  lynis clamav clamav-daemon rkhunter chkrootkit fail2ban \
  golang-go ruby-full

echo "==> Building nuclei and amass (not packaged for Ubuntu)"
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest || true
go install github.com/owasp-amass/amass/v4/...@master || true
ln -sf "$HOME/go/bin/nuclei" /usr/local/bin/nuclei || true
ln -sf "$HOME/go/bin/amass" /usr/local/bin/amass || true

echo "==> Creating dira system user"
id -u dira &>/dev/null || useradd --system --create-home --shell /usr/sbin/nologin dira

echo "==> Setting up PostgreSQL role and database"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='dira'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER dira WITH PASSWORD '${DIRA_DB_PASSWORD:-changeme_set_this}';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='dira'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE dira OWNER dira;"

echo "==> Deploying application to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
rsync -a --delete "$REPO_DIR"/backend "$REPO_DIR"/frontend "$INSTALL_DIR"/
chown -R dira:dira "$INSTALL_DIR"

echo "==> Creating Python virtualenv and installing backend dependencies"
sudo -u dira python3 -m venv "$INSTALL_DIR/backend/.venv"
sudo -u dira "$INSTALL_DIR/backend/.venv/bin/pip" install --upgrade pip -q
sudo -u dira "$INSTALL_DIR/backend/.venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" -q

echo "==> Building frontend"
(cd "$INSTALL_DIR/frontend" && sudo -u dira npm ci && sudo -u dira npm run build)

echo "==> Deploying fail2ban jail configuration"
mkdir -p /var/log/dira && chown dira:dira /var/log/dira && touch /var/log/dira/auth.log && chown dira:dira /var/log/dira/auth.log
cp "$REPO_DIR/infra/fail2ban/dira-auth.filter.conf" /etc/fail2ban/filter.d/dira-auth.conf
cp "$REPO_DIR/infra/fail2ban/dira-auth.jail.conf" /etc/fail2ban/jail.d/dira-auth.conf
systemctl restart fail2ban

echo "==> Creating data/log/backup directories"
mkdir -p /var/lib/dira /var/backups/dira
chown -R dira:dira /var/lib/dira /var/backups/dira

echo "==> Installing systemd units"
cp "$REPO_DIR"/infra/systemd/*.service "$REPO_DIR"/infra/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload

cat <<'EOF'

==> Provisioning complete. Remaining manual steps:
  1. Copy backend/.env.example to /opt/dira/backend/.env and fill in real secrets
     (JWT_SECRET, DATABASE_URL password, CORS_ORIGINS).
  2. Run the DB migration/seed once: sudo -u dira /opt/dira/backend/.venv/bin/python -m app.db.init_db
     (run from /opt/dira/backend with PYTHONPATH=.)
  3. Generate a TLS certificate: ./infra/scripts/generate-self-signed-cert.sh <your-domain>
     (or install a real cert from a CA at /etc/dira/tls/{privkey,fullchain}.pem)
  4. Enable and start services:
     systemctl enable --now dira-api dira-api-https dira-monitor dira-honeypot dira-frontend dira-backup.timer
  5. Change the default admin password immediately after first login.
EOF
