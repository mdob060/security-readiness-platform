#!/usr/bin/env bash
# Dumps the Dir'a PostgreSQL database, keeping the last 28 backups (~7 days at
# a 6-hour cadence). Invoked by dira-backup.timer every 6 hours.
set -euo pipefail

BACKUP_DIR="${DIRA_BACKUP_DIR:-/var/backups/dira}"
DB_NAME="${DIRA_DB_NAME:-dira}"
DB_USER="${DIRA_DB_USER:-dira}"
RETAIN_COUNT=28

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="$BACKUP_DIR/dira_${TIMESTAMP}.sql.gz"

pg_dump -U "$DB_USER" -h 127.0.0.1 "$DB_NAME" | gzip > "$OUT_FILE"
echo "Backup written to $OUT_FILE"

# Prune old backups beyond the retention count.
ls -1t "$BACKUP_DIR"/dira_*.sql.gz 2>/dev/null | tail -n +$((RETAIN_COUNT + 1)) | xargs -r rm -f
