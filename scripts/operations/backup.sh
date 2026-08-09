#!/bin/bash

# PostgreSQL Backup Script for AppVerboBraga
# Uses pg_dump with custom format (includes compression)
# Usage: ./backup.sh [output_dir] [retention_days]
# Example: ./backup.sh /backups 30

set -euo pipefail

# Configuration
OUTPUT_DIR="${1:-/backups}"
RETENTION_DAYS="${2:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${OUTPUT_DIR}/appverbo_backup_${TIMESTAMP}.dump"

# Database configuration (from environment variables)
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-app_igreja}"
DB_PASSWORD="${POSTGRES_PASSWORD}"

# Validate required variables
if [ -z "$DB_PASSWORD" ]; then
    echo "ERROR: POSTGRES_PASSWORD environment variable not set"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup of $DB_NAME..."

# Set password for pg_dump
export PGPASSWORD="$DB_PASSWORD"

# Perform backup using custom format (includes compression)
if pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -Fc \
    "$DB_NAME" > "$BACKUP_FILE"; then

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completed: $BACKUP_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Size: $(du -h "$BACKUP_FILE" | cut -f1)"

    # Verify backup integrity
    if pg_restore -l "$BACKUP_FILE" > /dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup integrity verified"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Backup integrity check failed"
        rm "$BACKUP_FILE"
        exit 1
    fi

    # Clean up old backups based on retention policy
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleaning old backups (older than $RETENTION_DAYS days)..."
    find "$OUTPUT_DIR" -name "appverbo_backup_*.dump" -type f -mtime "+$RETENTION_DAYS" -delete

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup process completed successfully"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Backup failed!"
    rm -f "$BACKUP_FILE"
    exit 1
fi
