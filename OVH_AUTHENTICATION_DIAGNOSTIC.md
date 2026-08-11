# OVH API Authentication Diagnostic

**Issue:** HTTP 400 when accessing `GET /domain/zone/verbodavidabraga.pt`

**Status:** Diagnostic tools ready - awaiting your execution with credentials

---

## ✅ Pre-Diagnostic Checks (Completed)

### System Clock
```
Local time:    Mon Aug 10 08:13:24 AM GMT 2026
UTC time:      Mon Aug 10 08:13:24 AM UTC 2026
NTP service:   active
Synchronized:  YES

OVH API time:  1786349604
Local time:    1786349604
Difference:    0 seconds ✓
```

✅ **Clock is synchronized** - not the cause of HTTP 400

### SDK Availability
```
Official OVH SDK (python-ovh): ✓ Installed
```

✅ **Official SDK available** - will use for diagnosis

---

## 🔍 Diagnostic Tools Created

### 1. Official SDK Diagnostic
**File:** `/tmp/diagnose_with_sdk.py`

Uses the official OVH Python SDK to:
- Create authenticated client
- Make GET request to `/domain/zone/verbodavidabraga.pt`
- Report HTTP status
- Display error class and message (without exposing secrets)

### 2. Secure Wrapper Script
**File:** `/home/opc/.local/bin/ovh_diagnose_auth.sh`

Wrapper that:
- Prompts for credentials interactively
- Silent input for Application Secret
- Calls diagnostic script
- Clears credentials after execution

### 3. Manual Diagnostic (Reference)
**File:** `/tmp/diagnose_auth.py`

Shows manual signature construction for comparison.

---

## 🚀 How to Run Diagnostic

```bash
/home/opc/.local/bin/ovh_diagnose_auth.sh
```

### Prompts
1. **OVH Application Key** (displayed as you type)
2. **OVH Application Secret** (silent input)

### Expected Output

**If Successful (HTTP 200):**
```
✓ SUCCESS - Zone retrieved

Zone info:
{
  "nameServers": ["ns16.ovh.net", "dns16.ovh.net"],
  ...
}
```

**If Failed (HTTP 400+):**
```
ERROR: [Error Type]
Message: [OVH error message]

Response details:
  Status: 400
  Class: [error class]
  Message: [specific error]
```

---

## What the Diagnostic Checks

1. **SDK Integration**
   - Official OVH SDK initialization
   - Client creation with all 3 credentials

2. **Authentication**
   - Application Key validity
   - Consumer Key (loaded from secure file)
   - Consumer Key authorization status

3. **Request Construction**
   - HTTP method (GET)
   - URL endpoint
   - Headers (X-OVH-Application, X-OVH-Timestamp, X-OVH-Signature)

4. **Response Analysis**
   - HTTP status code
   - Error classification (if any)
   - Detailed error message

---

## Possible HTTP 400 Causes

Based on OVH API documentation, HTTP 400 could indicate:

1. **Invalid Consumer Key** → "consumerKey not found" or "invalid"
2. **Expired Consumer Key** → "consumerKey has expired"
3. **Insufficient Permissions** → "insufficient permissions" (but our CK has GET granted)
4. **Invalid Signature** → "invalid signature" or "authentication failed"
5. **Timestamp Skew** → "invalid timestamp" (already ruled out - 0 second diff)
6. **Malformed Request** → "invalid request" or "bad request"
7. **Invalid Zone Name** → "zone not found" (unlikely - zone exists)

The diagnostic will tell us exactly which one.

---

## Security During Diagnosis

✅ Credentials entered interactively (not in shell history)
✅ Application Secret not displayed
✅ Consumer Key read from secure file (not in command)
✅ Credentials passed via environment (subprocess only)
✅ Credentials cleared after execution
✅ Error messages show class/message only (no secrets)

---

## After Diagnostic Completes

Depending on the result:

**If HTTP 200 (Success):**
- Proceed to full DNS audit
- Run `/home/opc/.local/bin/ovh_dns_audit_prompt.sh`
- Continue with backup and change planning

**If HTTP 400+ (Error):**
- Review the exact error message
- Diagnose based on error class
- Possible actions:
  - Verify Consumer Key authorization (unlikely)
  - Check OVH account status
  - Validate application credentials
  - Contact OVH support if needed

---

## Next Steps

1. Execute: `/home/opc/.local/bin/ovh_diagnose_auth.sh`
2. Provide credentials when prompted
3. Review diagnostic output
4. Identify HTTP 400 root cause
5. Report findings

**The diagnostic will take ~5 seconds and provide the exact error message from OVH.**

---

## Important Notes

- ✓ Consumer Key is NOT being regenerated
- ✓ No DNS changes will be made
- ✓ Only GET requests (READ-ONLY)
- ✓ Using official OVH SDK (more reliable than manual signatures)
- ✓ Clock is synchronized
- ✓ All security requirements maintained

Ready to diagnose. Execute the wrapper script when ready.
