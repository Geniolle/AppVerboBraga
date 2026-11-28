#!/bin/bash
# Backup diario da BD de producao. Corre no host (timer systemd appgenesis-backup-diario).
# Mantem os ultimos KEEP backups diarios; os backups manuais "pre-*" nao sao tocados.
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/backups}"
KEEP="${KEEP:-30}"
DB_CONTAINER="${DB_CONTAINER:-appverbobraga-db-prod}"
FILE="$BACKUP_DIR/appgenesis-prod-diario-$(date +%Y%m%d-%H%M%S).sql.gz"
TMP="$FILE.partial"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
trap 'rm -f "$TMP"' EXIT

mkdir -p "$BACKUP_DIR"
sudo -n docker exec "$DB_CONTAINER" sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner' | gzip > "$TMP"
gzip -t "$TMP"
TABLES=$(zcat "$TMP" | grep -c '^COPY ' || true)
if [ "$TABLES" -lt 1 ]; then
    log "ERRO: backup sem tabelas, descartado"
    exit 1
fi
mv "$TMP" "$FILE"
log "OK $FILE $(du -h "$FILE" | cut -f1) tabelas=$TABLES"

# Retencao: apaga so os diarios alem dos KEEP mais recentes.
ls -1t "$BACKUP_DIR"/appgenesis-prod-diario-*.sql.gz | tail -n +$((KEEP + 1)) | xargs -r rm -f --
