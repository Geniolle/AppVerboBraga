# AppGenesis Production Deployment

## Certificate Management

### Current Setup
- **Certificate Authority**: Let's Encrypt (YE2)
- **Validation Method**: DNS-01 via OVH API
- **Domains**: verbodavidabraga.pt, www.verbodavidabraga.pt
- **Renewal Window**: 2026-10-10T09:00:00Z (30 days before expiry)

### Certificate Paths
- Issued: `/home/opc/.acme.sh/verbodavidabraga.pt_ecc/`
- Active: `/etc/letsencrypt/live/verbodavidabraga.pt/`
  - `fullchain.pem` (public)
  - `privkey.pem` (600 permissions, never commit)

### Renewal Process

#### Automatic (systemd timer)
```bash
systemctl list-timers appgenesis-cert-renewal.timer
```

Executes: `/home/opc/.local/bin/renew_appgenesis_certificate.sh`
- Renews via acme.sh + DNS-01
- Validates Nginx config
- Reloads Nginx if config valid
- Logs to `/var/log/appgenesis-cert-renewal.log`

#### Manual Renewal
```bash
/home/opc/.local/bin/renew_appgenesis_certificate.sh
```

#### DNS-01 Process
1. acme.sh creates `_acme-challenge.verbodavidabraga.pt` TXT record
2. Loads OVH credentials from `~/.config/appgenesis/ovh.env`
3. Waits for DNS propagation
4. Let's Encrypt validates challenge
5. TXT record automatically removed
6. Certificate files updated

### Credentials Storage
- OVH Application Key/Secret: `~/.config/appgenesis/ovh.env` (600 permissions)
- OVH Consumer Key: `~/.config/appgenesis/ovh_consumer_key` (600 permissions)
- Never committed to Git

### Nginx Configuration
- HTTP (80): Redirects to HTTPS
- HTTPS (443): Serves via Let's Encrypt certificate

### Firewall Status
- **External**: Ports 80/443 blocked by Oracle Cloud NSG
- **Internal**: All services respond correctly
- DNS-01 validation works (uses DNS, not HTTP)

### Monitoring
```bash
# Check timer status
sudo systemctl list-timers appgenesis-cert-renewal.timer

# View renewal logs
tail -f /var/log/appgenesis-cert-renewal.log

# Verify certificate
openssl x509 -in /etc/letsencrypt/live/verbodavidabraga.pt/fullchain.pem -noout -text

# Test renewal (staging)
/home/opc/.acme.sh/acme.sh --renew -d verbodavidabraga.pt --dns dns_ovh --test
```

### Known Issues
- External access blocked (Oracle NSG) - requires NSG rule update for full functionality
- DNS-01 validation works via internal DNS query

### Emergency: Manual Certificate
```bash
export OVH_AK=$(grep OVH_APPLICATION_KEY ~/.config/appgenesis/ovh.env | cut -d= -f2-)
export OVH_AS=$(grep OVH_APPLICATION_SECRET ~/.config/appgenesis/ovh.env | cut -d= -f2-)
export OVH_CK=$(python3 -c "import json; print(json.load(open(~/.config/appgenesis/ovh_consumer_key)).get(consumerKey))")

/home/opc/.acme.sh/acme.sh --renew -d verbodavidavidabraga.pt -d www.verbodavidabraga.pt --dns dns_ovh --force

sudo nginx -t && sudo systemctl reload nginx
```

