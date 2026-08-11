# DNS Audit - Secure Credential Handler

**Status:** ✅ **READY FOR EXECUTION**

---

## Security Wrapper Created

**Script:** `/home/opc/.local/bin/ovh_dns_audit_prompt.sh`

### Security Features

✅ **No credentials stored** - Passed via environment variables only  
✅ **Silent input** - Application Secret uses `read -s` (not displayed)  
✅ **No shell history** - Credentials never written to terminal  
✅ **Automatic cleanup** - Variables unset after execution  
✅ **No logging** - Secrets not logged or displayed  
✅ **Permissions** - 700 (owner only)  
✅ **Syntax** - Validated with `bash -n`

---

## How to Execute

Simply run:

```bash
/home/opc/.local/bin/ovh_dns_audit_prompt.sh
```

### What It Will Prompt For

1. **OVH Application Key** (displayed as you type)
2. **OVH Application Secret** (silent input - appears as blank)

### What It Will Do

1. ✓ Verify Consumer Key exists
2. ✓ Pass credentials to Python audit script
3. ✓ Run DNS zone audit (READ-ONLY)
4. ✓ Create backup in `~/.config/appgenesis/dns-backups/`
5. ✓ Display current DNS configuration
6. ✓ Clear credentials from environment
7. ✓ Stop (no DNS changes)

---

## Validation Results

```
✓ Script exists: /home/opc/.local/bin/ovh_dns_audit_prompt.sh
✓ Bash syntax: VALID
✓ Permissions: 700 (owner only)
✓ Executable: YES
✓ No hardcoded secrets: CONFIRMED
✓ Cleanup commands: PRESENT (unset OVH_APPLICATION_KEY/SECRET)
✓ Consumer Key path: VERIFIED
```

---

## Security Workflow

```
User runs: /home/opc/.local/bin/ovh_dns_audit_prompt.sh
     ↓
[1] Prompt for OVH_APPLICATION_KEY (typed)
[2] Prompt for OVH_APPLICATION_SECRET (silent)
[3] Verify Consumer Key file exists
[4] Export credentials to environment (subprocess only)
[5] Execute: python3 /tmp/dns_audit.py
[6] Unset OVH_APPLICATION_KEY
[7] Unset OVH_APPLICATION_SECRET
[8] End
```

---

## What NOT to Do

❌ Don't run: `OVH_APPLICATION_KEY="..." python3 /tmp/dns_audit.py`  
   → Credentials would be in shell history

❌ Don't modify: `/tmp/dns_audit.py` to ask for credentials  
   → Python shouldn't prompt interactively

❌ Don't save credentials to: `.bashrc`, `.env`, files  
   → Keep them interactive only

---

## Expected Output

```
════════════════════════════════════════════════════════════════
OVHcloud DNS Zone Audit (READ-ONLY)
════════════════════════════════════════════════════════════════

This audit will:
  • Test OVH API authentication
  • Retrieve all DNS records for verbodavidabraga.pt
  • Create a secure backup
  • Display current configuration
  • Make NO modifications to DNS

Enter OVH Application Key: [you type it]

Enter OVH Application Secret (will not be displayed): [silent input]

════════════════════════════════════════════════════════════════
Executing audit (credentials will be cleared after completion)...
════════════════════════════════════════════════════════════════

Testing authentication...
✓ Authentication successful

[audit output...]

✓ AUDIT COMPLETE - NO DNS CHANGES EXECUTED

✓ Credentials cleared from environment
```

---

## After Audit Completes

The audit will:
1. Display all current DNS records
2. Show which records are GitHub Pages entries (need replacement)
3. List protected records (MX, SPF, DKIM - don't change)
4. Create backup file at: `~/.config/appgenesis/dns-backups/verbodavidabraga.pt-before-oracle-YYYYMMDD-HHMMSS.json`

---

## Troubleshooting

**"Consumer Key not found"**
- Consumer Key wasn't authorized earlier
- Check: `ls -la ~/.config/appgenesis/`

**"Authentication failed"**
- Wrong OVH Application Key
- Wrong OVH Application Secret
- Verify credentials are correct

**Script doesn't prompt**
- Make sure you're running it directly, not via pipe
- Correct: `/home/opc/.local/bin/ovh_dns_audit_prompt.sh`
- Wrong: `cat script.sh | bash`

---

## Next Steps

1. Execute: `/home/opc/.local/bin/ovh_dns_audit_prompt.sh`
2. Provide your OVH credentials when prompted
3. Review the audit output
4. Backup file will be created automatically
5. Continue to change phase once audit is reviewed

---

**Ready?** Execute `/home/opc/.local/bin/ovh_dns_audit_prompt.sh` now.
