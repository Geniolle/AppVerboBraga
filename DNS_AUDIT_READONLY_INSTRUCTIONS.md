# DNS Zone Audit - READ-ONLY (No Changes)

**Goal:** Complete inventory and backup of verbodavidabraga.pt DNS configuration  
**Scope:** GET-only queries, no modifications  
**Consumer Key:** Already authorized at `/home/opc/.config/appgenesis/ovh_consumer_key`

---

## ✅ What This Audit Does

1. ✓ Tests OVH API authentication
2. ✓ Lists all DNS records in the zone
3. ✓ Creates a complete backup JSON file
4. ✓ Analyzes current configuration
5. ✓ Identifies records to protect (email, SPF, DKIM, etc)
6. ✓ Prepares change proposal
7. ✓ **NO modifications to DNS**

---

## 🔒 Security

- Credentials: Passed via environment variables (not stored)
- Consumer Key: Read from secure file `~/.config/appgenesis/ovh_consumer_key`
- Operations: GET-only (no POST, PUT, DELETE)
- Backup: Saved with 600 permissions (owner only)

---

## 🚀 How to Run

### Step 1: Have Your OVH Credentials Ready

You need:
- **OVH Application Key** (from your initial setup)
- **OVH Application Secret** (from your initial setup)

### Step 2: Execute the Audit

Run this command, replacing the placeholders with your actual credentials:

```bash
ssh -i ~/.ssh/servidor-verbo-braga.key opc@132.226.134.7 \
  'OVH_APPLICATION_KEY="your-application-key" \
   OVH_APPLICATION_SECRET="your-application-secret" \
   python3 /tmp/dns_audit.py'
```

### Or Step by Step

```bash
# 1. SSH to server
ssh -i ~/.ssh/servidor-verbo-braga.key opc@132.226.134.7

# 2. Set credentials in session
export OVH_APPLICATION_KEY="your-key-here"
export OVH_APPLICATION_SECRET="your-secret-here"

# 3. Run audit
python3 /tmp/dns_audit.py
```

---

## 📋 What to Expect

The audit will output:

1. **Authentication test** → `✓ Authentication OK`
2. **Record inventory** → "Found X records"
3. **Backup creation** → File path and confirmation
4. **Record listing** → All A, AAAA, MX, CNAME, TXT records with current targets
5. **Completion** → "✓ AUDIT COMPLETE - NO DNS CHANGES MADE"

---

## 📁 Backup Location

After successful audit, backup file is saved at:

```
~/.config/appgenesis/dns-backups/verbodavidabraga.pt-before-oracle-YYYYMMDD-HHMMSS.json
```

**Permissions:** 600 (owner only)  
**Contents:** Complete DNS record dump in JSON format

---

## 📊 Expected Output

```
DNS Zone Audit
======================================================================

✓ Authentication OK

✓ Found XX record IDs
✓ Retrieved XX records

Creating backup...
✓ Backup saved: /home/opc/.config/appgenesis/dns-backups/...

Current Records:
──────────────────────────────────────────────────────────────────

A records (N):
  @                    → current.target.ip
  www                  → current.www.target

AAAA records (N):
  ...

MX records (N):
  @                    → mx1.mail.ovh.net

TXT records (N):
  @                    → v=spf1...

======================================================================
✓ AUDIT COMPLETE - NO DNS CHANGES MADE
======================================================================
```

---

## ✅ Validation Checklist

After audit completes successfully, you should see:

- [x] "Authentication OK" message
- [x] Record count (should be > 0)
- [x] Backup file created
- [x] Record listings (A, MX, TXT, etc)
- [x] "NO DNS CHANGES MADE" confirmation

---

## 🛡️ Safety Guarantees

This audit:
- ✓ Uses Consumer Key with **GET-only permissions** 
- ✓ Makes no POST/PUT/DELETE requests
- ✓ Only reads configuration (no modifications)
- ✓ Creates backup for safety (you have recovery)
- ✓ Does not expose credentials in logs
- ✓ Clears credentials from session after execution

---

## 🚨 Troubleshooting

### "ERROR: Consumer Key not found"
- Consumer Key file missing at `~/.config/appgenesis/ovh_consumer_key`
- Make sure you authorized the Consumer Key request earlier
- Check: `ls -la ~/.config/appgenesis/`

### "ERROR: Auth failed"
- Invalid OVH Application Key
- Invalid OVH Application Secret
- Consumer Key not authorized yet
- Verify credentials are correct

### "ERROR: Could not get records"
- API connectivity issue
- Temporary OVH API outage
- Try again in a few moments

---

## 📝 Next Steps After Audit

Once audit completes successfully:

1. ✅ Review the backup file contents
2. ✅ Confirm current DNS targets
3. ✅ Note which records need to change (A @, www)
4. ✅ Mark protected records (MX, SPF, DKIM, etc)
5. ✅ Prepare for change phase (not yet executed)

---

**Ready?** Run the audit command above with your OVH credentials.

After successful completion, the audit report will show exactly what needs to change for the go-live.
