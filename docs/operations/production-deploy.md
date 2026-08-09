# Production Deployment Guide - Verbo da Vida Braga (Genesis)

## Overview

This guide covers the complete deployment procedure for AppVerboBraga (Genesis) on Oracle Cloud Infrastructure (OCI) with PostgreSQL 16, Docker Compose, Nginx reverse proxy, and Let's Encrypt HTTPS.

**Domain**: `verbodavidabraga.pt`

---

## Pre-Deployment Checklist

- [ ] OCI instance provisioned (Ubuntu 24.04 LTS recommended)
- [ ] SSH access to instance
- [ ] DNS A record pointing to OCI instance public IP
- [ ] Email domain/SMTP credentials (for alerts, invites)
- [ ] OAuth provider credentials (Google, Microsoft, GitHub - optional)
- [ ] WhatsApp Business API credentials (if using)
- [ ] Google Drive service account (if using MT940 imports)
- [ ] Generated strong APP_SECRET_KEY
- [ ] Docker + Docker Compose installed on instance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  OCI Instance (Ubuntu 24.04 LTS)                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Internet                                                    │
│    ↓                                                         │
│  Nginx (ports 80/443)                                       │
│    ↓                                                         │
│  FastAPI App (Uvicorn, internal network only)               │
│    ↓                                                         │
│  PostgreSQL 16 (internal network only, not exposed)         │
│                                                              │
│  Volumes:                                                    │
│  - pg_data_prod: database files                             │
│  - static_prod: CSS/JS/logos                                │
│  - certbot: Let's Encrypt certificates                      │
│  - backups: daily backup dumps                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Clone Repository

```bash
cd ~
git clone https://github.com/Geniolle/AppVerboBraga.git
cd AppVerboBraga
```

---

## Step 2: Generate Secrets

### APP_SECRET_KEY (Required for PRODUCTION=true)

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example output**: `K-5L_5rZc_3aB9pWx_Y4mN_8o7p6qRs5tU8v`

Save this value. Never commit it to git.

---

## Step 3: Create Production Environment File

```bash
cp .env.example .env.prod
```

Edit `.env.prod` with production values:

```bash
# Core
PRODUCTION=true
APP_PUBLIC_URL=https://verbodavidabraga.pt
APP_SECRET_KEY=<paste-generated-key-from-step-2>

# Database (internal only, never expose to internet)
DATABASE_URL=postgresql://postgres:YOUR_STRONG_PASSWORD@db:5432/appgenesis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_STRONG_PASSWORD
POSTGRES_DB=appgenesis

# Email (SMTP - required for password reset, invites)
SMTP_HOST=mail.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@verbodavidabraga.pt
SMTP_FROM_NAME="Verbo da Vida Braga"
SMTP_USE_TLS=true

# OAuth (optional - set to empty if not using)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# WhatsApp (optional)
WHATSAPP_GRAPH_API_VERSION=v22.0
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_TEMPLATE_NAME=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=

# Google Drive (optional for MT940)
# (configure via environment or leave empty)
```

**Security**: Store `.env.prod` securely, never commit to git.

---

## Step 4: Pull Production Image

```bash
docker pull python:3.12-slim
docker pull postgres:16-alpine
docker pull nginx:1.26-alpine
```

---

## Step 5: Build Application Image

```bash
docker build -t appverbobraga:latest .
```

Verify the build succeeded:

```bash
docker images | grep appverbobraga
```

---

## Step 6: Start Production Stack (HTTP Bootstrap Phase)

This phase runs HTTP only on port 80. Used for initial verification and ACME challenge.

```bash
# Copy production compose file
cp docker-compose.prod.yml docker-compose.yml

# Start stack
docker-compose up -d
```

Verify services are running:

```bash
docker-compose ps
```

Expected output:
- `db`: running (PostgreSQL)
- `web`: running (FastAPI)
- `nginx`: running (Nginx)

---

## Step 7: Verify Application Startup

### Check logs

```bash
docker-compose logs web
```

Expected:
```
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test health endpoint

```bash
curl -s http://localhost/health | jq .
```

Expected response:
```json
{
  "status": "ok",
  "database": "connected",
  "version": "1.0"
}
```

If database shows "not connected", check PostgreSQL logs:

```bash
docker-compose logs db
```

---

## Step 8: Run Migrations

The migrations should run automatically during startup (via `init_db.py`), but verify status:

```bash
docker-compose exec db psql -U postgres -d appgenesis -c "\dt"
```

This lists all tables. Should include `alembic_version`, `user`, `entity`, etc.

If tables are missing, manually run migrations:

```bash
docker-compose exec web alembic upgrade head
```

### Restart application to verify idempotency

```bash
docker-compose restart web
docker-compose logs web | grep -i migration
```

Should NOT show new migrations running (idempotent).

---

## Step 9: Test Health Endpoint with Database

```bash
# Database running: should return 200
curl -I http://localhost/health

# Stop database temporarily
docker-compose stop db

# Health should return 503
curl -I http://localhost/health

# Restore database
docker-compose start db

# Health should return 200 again
sleep 5
curl -I http://localhost/health
```

---

## Step 10: Access Landing Page

```bash
curl http://localhost/ | head -20
```

Should return HTML starting with `<!DOCTYPE html>` or `{% extends "base.html" %}` (template error is fine at this stage).

---

## Step 11: Verify DNS Propagation

Before requesting HTTPS certificate, ensure DNS points to instance:

```bash
nslookup verbodavidabraga.pt
# or
dig verbodavidabraga.pt
```

Should resolve to your OCI instance public IP.

---

## Step 12: ACME/Let's Encrypt Certificate (HTTP Bootstrap)

### Option A: Manual Certbot (Recommended for first cert)

Stop the application briefly:

```bash
docker-compose down
```

Run Certbot standalone:

```bash
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/log/letsencrypt:/var/log/letsencrypt \
  -p 80:80 \
  certbot/certbot certonly \
    --standalone \
    --email admin@verbodavidabraga.pt \
    -d verbodavidabraga.pt \
    --agree-tos \
    --no-eff-email
```

Verify certificate created:

```bash
ls -la /etc/letsencrypt/live/verbodavidabraga.pt/
```

Expected files: `cert.pem`, `chain.pem`, `fullchain.pem`, `privkey.pem`

### Option B: Future Auto-Renewal via Cron

Add to system crontab (`crontab -e`):

```bash
0 0 1 * * /usr/local/bin/renew-certs.sh
```

Where `/usr/local/bin/renew-certs.sh` contains:

```bash
#!/bin/bash
docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/log/letsencrypt:/var/log/letsencrypt \
  -p 80:80 \
  certbot/certbot renew --quiet
```

---

## Step 13: Restart with HTTPS (Phase 2)

Update `docker-compose.prod.yml`:

1. Uncomment the HTTPS server block in `nginx/default.conf`
2. Update paths to certificates (if different from `/etc/letsencrypt`)

Restart:

```bash
docker-compose up -d
```

Verify HTTPS works:

```bash
curl -I https://verbodavidabraga.pt/
# Should return HTTP/2 200 (or 307 redirect to non-www if configured)
```

---

## Step 14: Test Full Stack

### Login page

```bash
curl -L https://verbodavidabraga.pt/login | head -20
```

### Create first admin user (via database)

```bash
docker-compose exec db psql -U postgres -d appgenesis
```

Then SQL to insert admin user (or use existing schema if it exists).

---

## Step 15: Configure Backups

### Daily backup cron

```bash
sudo crontab -e
```

Add:

```bash
0 2 * * * /home/ubuntu/AppVerboBraga/scripts/operations/backup.sh
```

### Test backup manually

```bash
bash scripts/operations/backup.sh
```

Verify backup file created:

```bash
ls -lh appverbo_backup_*.dump
```

### Test restore (on separate database)

```bash
# Create temporary database
docker-compose exec db createdb -U postgres appgenesis_test

# Restore
bash scripts/operations/restore.sh appverbo_backup_YYYYMMDD_HHMMSS.dump appgenesis_test

# Verify data
docker-compose exec db psql -U postgres -d appgenesis_test -c "SELECT COUNT(*) FROM user;"

# Clean up
docker-compose exec db dropdb -U postgres appgenesis_test
```

---

## Step 16: Configure Logs

Application logs go to stdout/stderr. View with:

```bash
docker-compose logs -f web
```

For persistent logging, configure Docker daemon (`/etc/docker/daemon.json`):

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

---

## Step 17: Multi-Tenant Isolation (Critical)

Verify that users of Entity A cannot access Entity B data via database queries or API:

```bash
# Create test data in database
docker-compose exec db psql -U postgres -d appgenesis

-- Insert two entities
INSERT INTO entity (id, name) VALUES (1, 'Entity A'), (2, 'Entity B');

-- Insert user for Entity A
INSERT INTO user (entity_id, name, email) VALUES (1, 'User A', 'a@example.com');

-- Insert user for Entity B
INSERT INTO user (entity_id, name, email) VALUES (2, 'User B', 'b@example.com');

-- Exit psql
\q
```

Test application enforces scope (requires app running and authenticated session).

---

## Step 18: Health Monitoring

Set up monitoring for `/health` endpoint:

```bash
# Every 30 seconds, check health
watch -n 30 'curl -s http://localhost/health | jq .'
```

For production, integrate with monitoring service:
- AWS CloudWatch
- OCI Monitoring
- Datadog
- New Relic

---

## Troubleshooting

### Application won't start

1. Check logs: `docker-compose logs web`
2. Verify `APP_SECRET_KEY` is set in `.env.prod`
3. Verify `PRODUCTION=true` is set
4. Check database connectivity: `docker-compose logs db`

### Database won't migrate

1. Check database has valid schema: `docker-compose exec db pg_isready -U postgres`
2. Try manual migration: `docker-compose exec web alembic upgrade head`
3. Check Alembic status: `docker-compose exec web alembic current`

### ACME challenge fails

1. Verify DNS: `nslookup verbodavidabraga.pt`
2. Verify port 80 is open: `sudo iptables -L -n | grep 80` (or check OCI Security Lists)
3. Verify Nginx is serving `/.well-known/acme-challenge/`: `curl http://localhost/.well-known/acme-challenge/test`

### HTTPS certificate not working

1. Verify certificate files exist: `ls -la /etc/letsencrypt/live/verbodavidabraga.pt/`
2. Check Nginx config references correct paths
3. Restart Nginx: `docker-compose restart nginx`

---

## Updating Application

To deploy new version:

1. Pull code: `git pull origin main`
2. Rebuild image: `docker build -t appverbobraga:latest .`
3. Restart stack: `docker-compose up -d --force-recreate`
4. Verify health: `curl https://verbodavidabraga.pt/health`

---

## Rollback Procedure

If new version has issues:

1. Restore backup: `bash scripts/operations/restore.sh appverbo_backup_YYYYMMDD_HHMMSS.dump appgenesis`
2. Revert code: `git checkout <previous-commit>`
3. Rebuild and restart: `docker build -t appverbobraga:latest . && docker-compose up -d --force-recreate`

---

## Security Notes

- **APP_SECRET_KEY**: Never share, never commit to git
- **Database password**: Use strong password, rotate regularly
- **HTTPS only**: Ensure HTTP redirects to HTTPS in Phase 2
- **Backups**: Store backups securely, separate from instance
- **OAuth secrets**: Use service account keys, rotate per OAuth provider policies
- **Logs**: Monitor for errors, adjust log levels in production

---

## Maintenance Schedule

- **Daily**: Automated backup runs at 2 AM
- **Monthly**: Review certificate expiration (`/etc/letsencrypt/live/...`)
- **Quarterly**: Test restore procedure
- **Annually**: Audit multi-tenant isolation, update dependencies

---

**Last Updated**: 2026-08-09
**Version**: 1.0
**Status**: Ready for deployment

