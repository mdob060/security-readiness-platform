#!/usr/bin/env bash
# Generates a self-signed TLS certificate for local/dev HTTPS testing.
# For a real deployment, replace /etc/dira/tls/{privkey,fullchain}.pem with a
# certificate from a trusted CA (e.g. certbot/Let's Encrypt) instead.
set -euo pipefail

CERT_DIR="/etc/dira/tls"
DAYS_VALID=825
COMMON_NAME="${1:-dira.local}"

mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$CERT_DIR/privkey.pem" \
  -out "$CERT_DIR/fullchain.pem" \
  -days "$DAYS_VALID" \
  -subj "/C=LY/O=Dira Security Platform/CN=${COMMON_NAME}"

chmod 600 "$CERT_DIR/privkey.pem"
chmod 644 "$CERT_DIR/fullchain.pem"

echo "Self-signed certificate written to $CERT_DIR (valid ${DAYS_VALID} days, CN=${COMMON_NAME})"
echo "Replace with a CA-issued certificate before exposing this to the internet."
