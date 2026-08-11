#!/bin/bash
# AppGenesis Certificate Renewal Script
# Purpose: Renew Let's Encrypt certificate via DNS-01 (OVH)
# 
# Prerequisites:
#   - acme.sh installed in ~/.acme.sh/
#   - OVH credentials in ~/.config/appgenesis/ovh.env (600 permissions)
#   - OVH Consumer Key in ~/.config/appgenesis/ovh_consumer_key (600 permissions)
#   - nginx installed on host
#
# Usage:
#   ./scripts/operations/renew_certificate.sh [domain] [domain2] ...
#
# Environment:
#   DOMAIN: Primary domain (default: verbodavidabraga.pt)
#   DOMAINS: Additional domains (default: www.verbodavidabraga.pt)
#   LOG_FILE: Log destination (default: /var/log/appgenesis-cert-renewal.log)
#   ACME_SCRIPT: Path to acme.sh (default: ~/.acme.sh/acme.sh)

set -e

# Configuration
DOMAIN="${1:-verbodavidabraga.pt}"
DOMAINS="${2:-www.verbodavidabraga.pt}"
LOG_FILE="${LOG_FILE:-/var/log/appgenesis-cert-renewal.log}"
CONFIG_DIR="$HOME/.config/appgenesis"
OVH_ENV="$CONFIG_DIR/ovh.env"
OVH_CK="$CONFIG_DIR/ovh_consumer_key"
ACME_SCRIPT="${ACME_SCRIPT:-$HOME/.acme.sh/acme.sh}"

# Validate prerequisites
if [[ ! -f "$ACME_SCRIPT" ]]; then
    echo "[ERROR] acme.sh not found at $ACME_SCRIPT" | tee -a "$LOG_FILE"
    exit 1
fi

if [[ ! -f "$OVH_ENV" ]] || [[ ! -f "$OVH_CK" ]]; then
    echo "[ERROR] OVH credentials not found" | tee -a "$LOG_FILE"
    exit 1
fi

# Load OVH credentials (from external files, never embedded)
export OVH_AK=$(grep OVH_APPLICATION_KEY "$OVH_ENV" | cut -d= -f2- | sed "s/^['\"]*//;s/['\"]*$//")
export OVH_AS=$(grep OVH_APPLICATION_SECRET "$OVH_ENV" | cut -d= -f2- | sed "s/^['\"]*//;s/['\"]*$//")
export OVH_CK=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1])).get(\"consumerKey\"))" "$OVH_CK")

if [[ -z "$OVH_AK" ]] || [[ -z "$OVH_AS" ]] || [[ -z "$OVH_CK" ]]; then
    echo "[ERROR] OVH credentials incomplete" | tee -a "$LOG_FILE"
    exit 1
fi

# Renewal process
echo "[$(date)] Starting renewal for $DOMAIN..." | tee -a "$LOG_FILE"

if "$ACME_SCRIPT" --renew -d "$DOMAIN" -d "$DOMAINS" --dns dns_ovh 2>&1 | tee -a "$LOG_FILE"; then
    echo "[$(date)] Renewal successful" >> "$LOG_FILE"
    
    # Validate Nginx before reload
    if command -v nginx &> /dev/null; then
        if nginx -t 2>&1 | tee -a "$LOG_FILE"; then
            echo "[$(date)] Nginx config valid" >> "$LOG_FILE"
            
            if command -v systemctl &> /dev/null; then
                if sudo systemctl reload nginx 2>&1 | tee -a "$LOG_FILE"; then
                    echo "[$(date)] Nginx reloaded successfully" >> "$LOG_FILE"
                else
                    echo "[ERROR] Failed to reload Nginx" | tee -a "$LOG_FILE"
                    exit 1
                fi
            elif command -v nginx &> /dev/null; then
                if sudo nginx -s reload 2>&1 | tee -a "$LOG_FILE"; then
                    echo "[$(date)] Nginx reloaded successfully" >> "$LOG_FILE"
                else
                    echo "[ERROR] Failed to reload Nginx" | tee -a "$LOG_FILE"
                    exit 1
                fi
            fi
        else
            echo "[ERROR] Nginx config invalid" | tee -a "$LOG_FILE"
            exit 1
        fi
    fi
else
    echo "[ERROR] Renewal failed" | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date)] Renewal completed successfully" >> "$LOG_FILE"
