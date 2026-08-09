# AppVerboBraga Production Deployment Guide

## Overview

This guide describes the procedure for deploying AppVerboBraga to Oracle Cloud for production use.

**Architecture:**
```
Internet (80/443) → Nginx (Reverse Proxy) → AppVerboBraga/Uvicorn → PostgreSQL (internal)
```

## Prerequisites

### Oracle Cloud
- VM instance (e.g., Ubuntu 22.04 LTS)
- Public IP address (reserved)
- Firewall rules for ports 80, 443
- SSH access to the instance

### Domain & DNS
- Domain registered (e.g., `example.com`)
- DNS managed at OVH
- Ability to create DNS `A` records

### Credentials & Configuration
- Generated `APP_SECRET_KEY` (see [Generating Security Keys](#generating-security-keys))
- PostgreSQL credentials (strong password)
- OAuth credentials (if using Google, Microsoft, GitHub login)
- SMTP credentials (if using email)
- WhatsApp credentials (if using WhatsApp integration)
- Google Drive service account (if using MT940 import)

## Pre-Deployment Steps

### 1. Prepare Configuration File

Copy the template and configure all required variables:

```bash
cp .env.example .env.production
```

Edit `.env.production` with your actual values:

```bash
# Database (MUST match PostgreSQL credentials)
POSTGRES_USER=appverbo_user
POSTGRES_PASSWORD=<STRONG_PASSWORD>
POSTGRES_DB=appverbo_prod
DATABASE_URL=postgresql+psycopg://appverbo_user:<STRONG_PASSWORD>@db:5432/appverbo_prod

# Security (CRITICAL)
APP_SECRET_KEY=<GENERATED_SECRET_KEY>
PRODUCTION=true

# Public URL (MUST be set before OAuth callbacks work)
APP_PUBLIC_URL=https://app.example.com

# Admin user
ADMIN_LOGIN_EMAIL=admin@example.com
ADMIN_LOGIN_PASSWORD=<INITIAL_PASSWORD>

# OAuth (optional)
GOOGLE_CLIENT_ID=<your_google_client_id>
GOOGLE_CLIENT_SECRET=<your_google_secret>
# ... other OAuth and integration credentials
```

### 2. Generating Security Keys

Generate a strong `APP_SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**IMPORTANT:**
- This key must never change after deployment (sessions/tokens become invalid)
- Store the key securely (never commit to Git)
- Ensure the key is the same across all container restarts

### 3. Prepare SSL Certificates

This guide uses Let's Encrypt with Certbot for free HTTPS certificates.

#### Option A: Manual Setup (First Time)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
# (DNS must already point to your IP)
sudo certbot certonly --standalone -d app.example.com

# Copy certificates to certs directory
sudo mkdir -p certs
sudo cp /etc/letsencrypt/live/app.example.com/fullchain.pem certs/
sudo cp /etc/letsencrypt/live/app.example.com/privkey.pem certs/
sudo chmod 644 certs/*.pem
```

#### Option B: Using Docker-based Certbot

```bash
# Generate DH parameters for stronger SSL
openssl dhparam -out nginx/dhparam.pem 2048

# Run Certbot container (with DNS already pointing to your IP)
docker run --rm -it -v $(pwd)/certs:/etc/letsencrypt certbot/certbot \
    certonly --standalone -d app.example.com
```

### 4. Generate Nginx DH Parameters

```bash
openssl dhparam -out nginx/dhparam.pem 2048
```

This improves SSL security and takes about 5 minutes.

## Deployment Steps

### Step 1: Verify DNS Resolution

Ensure your domain resolves to the Oracle Cloud IP:

```bash
nslookup app.example.com
dig app.example.com

# Should return your Oracle Cloud public IP
```

### Step 2: Start Docker Services

Before starting, verify configuration:

```bash
# Validate docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml config

# Build image
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Step 3: Verify Services

Check that all containers are running:

```bash
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# appverbobraga-db-prod        ✓ running
# appverbobraga-web-prod       ✓ running
# appverbobraga-nginx-prod     ✓ running
```

Check logs:

```bash
# Web application logs
docker-compose -f docker-compose.prod.yml logs web

# Database logs
docker-compose -f docker-compose.prod.yml logs db

# Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

### Step 4: Verify Health Endpoint

```bash
# From the server
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","version":"1.0"}

# Via Nginx (HTTP before HTTPS is configured)
curl http://app.example.com/health
```

### Step 5: Bootstrap Admin User

If not already created during initialization:

```bash
docker-compose -f docker-compose.prod.yml exec web \
    python -c "
from scripts.bootstrap_admin import main
main()
"
```

### Step 6: Enable HTTPS in Nginx

Once certificates are in place:

1. Copy/enable the HTTPS server block in `nginx/default.conf`
2. Update domain in the configuration
3. Reload Nginx:

```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Step 7: Verify HTTPS

```bash
curl https://app.example.com/health

# Should return 200 OK with health information
```

### Step 8: Configure OAuth Redirects

Update OAuth provider consoles with production URLs:

**Google Cloud Console:**
- Authorized JavaScript origins: `https://app.example.com`
- Authorized redirect URIs: `https://app.example.com/oauth/callback/google`

**Microsoft Azure:**
- Redirect URI: `https://app.example.com/oauth/callback/microsoft`

**GitHub:**
- Authorization callback URL: `https://app.example.com/oauth/callback/github`

### Step 9: Configure WhatsApp Webhook

If using WhatsApp integration:

```bash
# Configure webhook URL in WhatsApp Cloud API settings
https://app.example.com/webhooks/whatsapp

# Test webhook
curl -X POST https://app.example.com/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"1234567890"}]}}]}]}'
```

### Step 10: Set Up Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2:00 AM (adjust time as needed)
0 2 * * * docker-compose -f docker-compose.prod.yml exec -T db \
    /bin/bash -c 'bash /app/scripts/operations/backup.sh /backups 30'
```

Make sure backups directory is writable:

```bash
docker-compose -f docker-compose.prod.yml exec db chown postgres:postgres /backups
```

### Step 11: Configure Log Rotation

Create a logrotate configuration:

```bash
sudo cat > /etc/logrotate.d/appverbobraga << 'EOF'
/var/lib/docker/containers/*/*/appverbobraga-web-prod-json.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

## Database Management

### Backup Database

Manual backup:

```bash
docker-compose -f docker-compose.prod.yml exec db \
    bash /app/scripts/operations/backup.sh /backups
```

### Restore Database

List available backups:

```bash
ls -lh backups/
```

Restore from backup:

```bash
docker-compose -f docker-compose.prod.yml exec db \
    bash /app/scripts/operations/restore.sh /backups/appverbo_backup_20260809_143000.sql.gz
```

## Troubleshooting

### Application won't start

Check logs:

```bash
docker-compose -f docker-compose.prod.yml logs web
```

Common issues:
- `APP_SECRET_KEY` not set
- Database connection string invalid
- Missing required environment variables
- Database not ready (wait for healthcheck)

### Database connection failures

```bash
# Test connection
docker-compose -f docker-compose.prod.yml exec web \
    python -c "from sqlalchemy import create_engine; \
    engine = create_engine('$DATABASE_URL'); \
    print('Connected!' if engine.connect() else 'Failed')"
```

### Nginx issues

```bash
# Check Nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### HTTPS certificate issues

```bash
# Check certificate validity
openssl x509 -in certs/fullchain.pem -text -noout

# Check certificate renewal
sudo certbot renew --dry-run
```

### Performance/slowness

Check resource usage:

```bash
docker stats appverbobraga-web-prod
docker stats appverbobraga-db-prod
```

Check database connections:

```bash
docker-compose -f docker-compose.prod.yml exec db \
    psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT count(*) FROM pg_stat_activity;"
```

## Maintenance Tasks

### Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up automatic renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot should auto-renew via system timer
sudo systemctl status certbot.timer

# Manual renewal if needed
sudo certbot renew
```

After renewal, reload Nginx:

```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Database Maintenance

Run periodic maintenance:

```bash
docker-compose -f docker-compose.prod.yml exec db \
    psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"
```

### Log Cleanup

Docker logs can grow large. Rotate them:

```bash
docker-compose -f docker-compose.prod.yml logs --tail 1000 web
```

## Rollback Procedure

If you need to revert to a previous version:

### 1. Identify Previous Version

```bash
git log --oneline | head -10
docker images | grep appverbobraga
```

### 2. Stop Current Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### 3. Restore Database from Backup

```bash
# List backups
ls -1 backups/ | sort -r | head -5

# Restore
docker-compose -f docker-compose.prod.yml exec db \
    bash /app/scripts/operations/restore.sh /backups/<previous_backup>.sql.gz
```

### 4. Checkout Previous Code

```bash
git checkout <previous_commit_or_tag>
```

### 5. Rebuild and Restart

```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Security Best Practices

1. **Keep secrets secure:**
   - Never commit `.env.production` to Git
   - Restrict file permissions: `chmod 600 .env.production`
   - Use environment variables or secret management

2. **Database security:**
   - Use strong passwords (16+ characters, mixed case, numbers, symbols)
   - Keep PostgreSQL on internal network only
   - Limit database connections

3. **HTTPS/TLS:**
   - Always use HTTPS in production
   - Keep certificates updated
   - Use strong ciphers (configured in Nginx)

4. **Access control:**
   - Restrict SSH access
   - Use firewall rules
   - Monitor logs for suspicious activity

5. **Backups:**
   - Test restore procedures regularly
   - Store backups securely (off-site if possible)
   - Verify backup integrity

## Monitoring & Alerting

### Health Checks

The application exposes a health endpoint:

```bash
curl https://app.example.com/health
```

Set up external monitoring:

```bash
# Example with curl
curl -f https://app.example.com/health || send_alert
```

### Log Monitoring

Monitor application logs:

```bash
docker-compose -f docker-compose.prod.yml logs -f web
```

### Container Health

Docker provides health checks. Verify they're passing:

```bash
docker ps --format "{{.Names}}\t{{.Status}}"
```

## Support & Documentation

- Application logs: `docker-compose logs web`
- Database logs: `docker-compose logs db`
- Nginx logs: `docker-compose logs nginx`
- Configuration: `.env.production`
- Backup procedures: `scripts/operations/`

For issues, check:
1. Application logs
2. Database connectivity
3. Environment variables
4. Firewall/Security groups
5. Disk space and resources
