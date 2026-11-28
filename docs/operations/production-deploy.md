# AppGenesis Production Deployment

## Servidor de produção (prd)

- **IP**: `141.147.76.187` (Oracle Cloud, Ubuntu 24.04). O IP `132.226.134.7` que aparece em docs antigas está desatualizado.
- **Login SSH**: `ubuntu@141.147.76.187` (não `opc`; `opc` é recusado).
- **Chave SSH**: `Servidor/ssh-Genesys-chavekey-2026-11-12.key` (no repo local; nunca commitar nem copiar para fora do repo; a chave `Servidor/ssh-Genesys-key-2026-11-12.key` é a outra).
- **Projeto no servidor**: `/opt/appgenesis/app` (git `origin/master` em `github.com/Geniolle/AppVerboBraga`).
- **Compose**: `/opt/appgenesis/app/docker-compose.prod.yml` (serviços `web` = `appverbobraga-web-prod`, `db` = `appverbobraga-db-prod`, Postgres 16, BD `app_igreja`, utilizador `appgenesis`).
- **Backups**: `~/backups/appgenesis-prod-pre-<commit>-<timestamp>.sql.gz` (criar antes de cada deploy) e `~/backups/appgenesis-prod-diario-<timestamp>.sql.gz` (automático, ver abaixo).
- **Docker** só com `sudo docker ...` (utilizador `ubuntu` não está no grupo docker).

### Comando SSH (a partir do PC; copiar a chave para pasta temporária com `chmod 600` se o Windows recusar permissões)

```bash
ssh -i <caminho-da-chave> -o BatchMode=yes ubuntu@141.147.76.187
```

### Passos de deploy

1. Backup da BD: `sudo docker exec appverbobraga-db-prod pg_dump -U appgenesis -d app_igreja --no-owner | gzip > ~/backups/appgenesis-prod-pre-<commit>-$(date +%Y%m%d-%H%M%S).sql.gz`
2. `cd /opt/appgenesis/app && git pull --ff-only origin master`
3. `sudo docker compose -f docker-compose.prod.yml build web && sudo docker compose -f docker-compose.prod.yml up -d web`
4. Confirmar `healthy` e `GET /health` = 200.
5. Estáticos: o volume `app_static_prod` (montado em `/app/static`) não é atualizado pelo deploy. Se o commit mudar `static/`, sincronizar com `docker cp` antes de testar.

## Backup diário automático

- Timer systemd `appgenesis-backup-diario.timer` corre todos os dias às 03:00 (Europe/Lisbon; o servidor está em UTC). `Persistent=true` corre o backup em falta se o servidor esteve desligado.
- Executa `scripts/operations/prod_daily_backup.sh` como `ubuntu`: `pg_dump` completo de `app_igreja` via `docker exec`, `gzip -t`, rejeita ficheiros sem tabelas.
- Retenção: mantém os 30 diários mais recentes (`appgenesis-prod-diario-*`). Os backups manuais `pre-*` nunca são apagados pelo script.
- Unidades versionadas em `scripts/operations/systemd/`. Instalar ou atualizar:

```bash
sudo cp /opt/appgenesis/app/scripts/operations/systemd/appgenesis-backup-diario.* /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now appgenesis-backup-diario.timer
```

- Verificar: `systemctl list-timers appgenesis-backup-diario.timer` e `journalctl -u appgenesis-backup-diario.service -n 20`.
- Correr já: `sudo systemctl start appgenesis-backup-diario.service`.
- Restaurar (destrutivo): fazer antes um backup do estado atual, parar `web`, recriar `app_igreja` vazia e depois `zcat <ficheiro>.sql.gz | sudo docker exec -i appverbobraga-db-prod psql -U appgenesis -d app_igreja`. O dump é SQL simples, sem `DROP`, por isso não restaura por cima de uma BD com tabelas.

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

/home/opc/.acme.sh/acme.sh --renew -d verbodavidabraga.pt -d www.verbodavidabraga.pt --dns dns_ovh --force

sudo nginx -t && sudo systemctl reload nginx
```

