#!/bin/bash

# PostgreSQL Restore Script for AppVerboBraga
# Restores from custom format dump file
# Usage: ./restore.sh <backup_file>
# Example: ./restore.sh /backups/appverbo_backup_20260809_143000.dump

set -euo pipefail

# Validate input
if [ -z "${1:-}" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /backups/appverbo_backup_20260809_143000.dump"
    exit 1
fi

BACKUP_FILE="$1"

# Validate backup file exists and is readable
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [ ! -r "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not readable: $BACKUP_FILE"
    exit 1
fi

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

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting restore from $BACKUP_FILE..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: This will overwrite the current database!"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Press Ctrl+C to cancel in the next 10 seconds..."
sleep 10

# Set password for pg_restore
export PGPASSWORD="$DB_PASSWORD"

# Verify backup format before restore
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Verifying backup format..."
if ! pg_restore -l "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "ERROR: Backup file appears to be corrupted or in wrong format"
    exit 1
fi

# Drop existing database connections
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Terminating existing connections..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    -d "postgres" \
    -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

# Drop and recreate database
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dropping existing database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    -d "postgres" \
    -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" || true

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Creating new database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    -d "postgres" \
    -c "CREATE DATABASE \"$DB_NAME\";"

# Restore from backup
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restoring database from backup..."
pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restore completed successfully"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Restore failed!"
    exit 1
fi
