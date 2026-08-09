#!/bin/bash

# PostgreSQL Backup Script for AppVerboBraga
# Usage: ./backup.sh [output_dir] [retention_days]
# Example: ./backup.sh /backups 30

set -e

# Configuration
OUTPUT_DIR="${1:-/backups}"
RETENTION_DAYS="${2:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${OUTPUT_DIR}/appverbo_backup_${TIMESTAMP}.sql.gz"

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

# Perform backup
if pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -F custom \
    "$DB_NAME" | gzip > "$BACKUP_FILE"; then

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completed: $BACKUP_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Size: $(du -h "$BACKUP_FILE" | cut -f1)"

    # Clean up old backups based on retention policy
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleaning old backups (older than $RETENTION_DAYS days)..."
    find "$OUTPUT_DIR" -name "appverbo_backup_*.sql.gz" -type f -mtime "+$RETENTION_DAYS" -delete

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup process completed successfully"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Backup failed!"
    exit 1
fi
