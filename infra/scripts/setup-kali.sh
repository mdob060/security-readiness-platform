#!/usr/bin/env bash
# Provisioning script for Kali Linux (2023.x+, kali-rolling).
#
# Kali already ships most of the offensive tools Dir'a integrates
# (nmap, sqlmap, gobuster, ffuf, nikto, hydra, wpscan, dnsrecon, masscan,
# whatweb, amass, and usually nuclei too), so this script mostly just fills
# in whatever a minimal/custom Kali install is missing (Postgres, Redis,
# fail2ban, clamav, rkhunter/chkrootkit are NOT installed by default on Kali)
# and gets the app itself running. Run as root (or with sudo).
#
# Usage:
#   sudo ./infra/scripts/setup-kali.sh            # quick local run (no systemd, no TLS)
#   sudo ./infra/scripts/setup-kali.sh --systemd   # also install as systemd services
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INSTALL_DIR="/opt/dira"
WITH_SYSTEMD=false
[[ "${1:-}" == "--systemd" ]] && WITH_SYSTEMD=true

echo "==> Updating apt and fixing any pre-existing broken/held packages"
apt-get update
# Many Kali desktop installs end up with kali-desktop-gnome (or similar)
# stuck with an unsatisfiable dependency chain -- unrelated to this app, but
# it makes apt's resolver refuse to touch *any* install request. `apt
# --fix-broken install` only fixes half-installed (dpkg-level broken)
# packages, not this case, so explicitly hold the offending meta-package
# instead so apt's solver skips it when resolving new installs.
apt --fix-broken install -y || true
for pkg in kali-desktop-gnome kali-desktop-core kali-desktop-xfce kali-desktop-kde; do
  dpkg -l "$pkg" &>/dev/null && apt-mark hold "$pkg" || true
done

# Tools already present on most Kali installs are listed too -- apt just
# reports "already the newest version" for those, which is harmless.
# --no-install-recommends avoids pulling in unrelated desktop-environment
# recommends that can retrigger the same resolver conflict.
apt-get install -y --no-install-recommends \
  postgresql postgresql-contrib redis-server \
  python3 python3-venv python3-pip \
  nmap gobuster ffuf sqlmap nikto masscan whatweb hydra wpscan dnsrecon amass \
  lynis clamav clamav-daemon rkhunter chkrootkit fail2ban \
  golang-go rsync curl openssl

echo "==> Checking for nuclei (Kali packages it as of 2023.x; older installs need go install)"
if ! command -v nuclei &>/dev/null; then
  apt-get install -y --no-install-recommends nuclei || {
    echo "    apt package not available on this Kali version -- building from source"
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    ln -sf "$HOME/go/bin/nuclei" /usr/local/bin/nuclei
  }
fi

echo "==> Checking Node.js version (Next.js needs >= 18; Kali's default apt node may be older)"
NODE_OK=false
if command -v node &>/dev/null; then
  NODE_MAJOR="$(node -v | sed -E 's/^v([0-9]+).*/\1/')"
  [[ "$NODE_MAJOR" -ge 18 ]] && NODE_OK=true
fi
if [[ "$NODE_OK" == "false" ]]; then
  echo "    Installing Node.js 20.x from NodeSource"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y --no-install-recommends nodejs
fi

echo "==> Starting Postgres/Redis (Kali doesn't enable them by default)"
service postgresql start || systemctl start postgresql || true
service redis-server start || systemctl start redis-server || true

echo "==> Granting raw-socket capability to nmap/masscan (so scans work without running as root)"
setcap cap_net_raw,cap_net_admin+eip "$(command -v nmap)" || true
setcap cap_net_raw,cap_net_admin+eip "$(command -v masscan)" || true

echo "==> Creating dira system user"
id -u dira &>/dev/null || useradd --system --create-home --shell /usr/sbin/nologin dira

echo "==> Setting up PostgreSQL role and database"
DIRA_DB_PASSWORD="${DIRA_DB_PASSWORD:-$(openssl rand -hex 16)}"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='dira'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER dira WITH PASSWORD '${DIRA_DB_PASSWORD}';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='dira'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE dira OWNER dira;"

echo "==> Deploying application to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
rsync -a --delete --exclude node_modules --exclude .venv --exclude .next \
  "$REPO_DIR"/backend "$REPO_DIR"/frontend "$INSTALL_DIR"/
chown -R dira:dira "$INSTALL_DIR"

echo "==> Creating Python virtualenv and installing backend dependencies"
sudo -u dira python3 -m venv "$INSTALL_DIR/backend/.venv"
sudo -u dira "$INSTALL_DIR/backend/.venv/bin/pip" install --upgrade pip -q
sudo -u dira "$INSTALL_DIR/backend/.venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" -q

echo "==> Writing backend/.env"
if [[ ! -f "$INSTALL_DIR/backend/.env" ]]; then
  JWT_SECRET="$(openssl rand -hex 32)"
  cat > "$INSTALL_DIR/backend/.env" <<EOF
DATABASE_URL=postgresql+psycopg://dira:${DIRA_DB_PASSWORD}@localhost:5432/dira
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=${JWT_SECRET}
ENVIRONMENT=production
CORS_ORIGINS=["http://localhost:3000"]
EOF
  chown dira:dira "$INSTALL_DIR/backend/.env"
  chmod 600 "$INSTALL_DIR/backend/.env"
fi

echo "==> Initializing database schema + seed admin user"
(cd "$INSTALL_DIR/backend" && sudo -u dira env PYTHONPATH=. "$INSTALL_DIR/backend/.venv/bin/python" -m app.db.init_db)

echo "==> Installing frontend dependencies and building"
(cd "$INSTALL_DIR/frontend" && sudo -u dira npm ci && sudo -u dira npm run build)
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > "$INSTALL_DIR/frontend/.env.local"
chown dira:dira "$INSTALL_DIR/frontend/.env.local"

echo "==> Deploying fail2ban jail configuration"
mkdir -p /var/log/dira && chown dira:dira /var/log/dira
touch /var/log/dira/auth.log && chown dira:dira /var/log/dira/auth.log
cp "$REPO_DIR/infra/fail2ban/dira-auth.filter.conf" /etc/fail2ban/filter.d/dira-auth.conf
cp "$REPO_DIR/infra/fail2ban/dira-auth.jail.conf" /etc/fail2ban/jail.d/dira-auth.conf
service fail2ban restart || systemctl restart fail2ban || true

echo "==> Creating data/backup directories"
mkdir -p /var/lib/dira /var/backups/dira
chown -R dira:dira /var/lib/dira /var/backups/dira

if [[ "$WITH_SYSTEMD" == "true" ]]; then
  echo "==> Installing systemd units (requires a systemd-booted Kali install, not live/USB mode)"
  sed "s#/opt/dira#${INSTALL_DIR}#g" "$REPO_DIR"/infra/systemd/*.service > /dev/null 2>&1 || true
  cp "$REPO_DIR"/infra/systemd/*.service "$REPO_DIR"/infra/systemd/*.timer /etc/systemd/system/
  systemctl daemon-reload
  echo "    Enable with: systemctl enable --now dira-api dira-monitor dira-honeypot dira-frontend dira-backup.timer"
  echo "    (dira-api-https needs a TLS cert first -- see generate-self-signed-cert.sh)"
fi

cat <<EOF

==> Setup complete.

Database password (save this):  ${DIRA_DB_PASSWORD}
Default login: admin / ChangeMe123!  (change this immediately)

Quick start (no systemd -- just run it now):
  # terminal 1
  cd ${INSTALL_DIR}/backend
  sudo -u dira env PYTHONPATH=. ${INSTALL_DIR}/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

  # terminal 2
  cd ${INSTALL_DIR}/frontend
  sudo -u dira npm run start -- -p 3000

Then open http://localhost:3000 (or http://<your-kali-vm-ip>:3000 from your host machine).

For a persistent background setup instead, re-run this script with --systemd,
or see infra/systemd/*.service directly.
EOF
