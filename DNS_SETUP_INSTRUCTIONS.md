# DNS Configuration Instructions - OVH Panel

**Domain:** verbodavidabraga.pt  
**New IP:** 132.226.134.7  
**DNS Provider:** OVH

---

## Current DNS Status

### Records to KEEP (Email Configuration)
```
MX 1      mx1.mail.ovh.net.
MX 5      mx2.mail.ovh.net.
MX 100    mx3.mail.ovh.net.
TXT       v=spf1 include:mx.ovh.com ~all
TXT       MS=F42778021D6E5F52D51B7BEDEC2A882BE8EA82E3
TXT       1|www.linktr.ee/verbobraga
```

### Records to UPDATE (Website)
```
BEFORE:
  A @ → 185.199.109.153, 185.199.108.153, 185.199.111.153, 185.199.110.153, 213.186.33.5
  A www → 213.186.33.5

AFTER:
  A @ → 132.226.134.7
  A www → 132.226.134.7
```

---

## Steps to Update DNS in OVH Panel

### 1. Access OVH Control Panel
- Go to: https://www.ovh.com/auth/
- Login with your account credentials
- Select: Domain → verbodavidabraga.pt

### 2. Navigate to DNS Records
- Click: "Zone DNS" or "DNS Zone"
- Look for the DNS management section

### 3. Update A Record (@)
- Find: A record with target "185.199.x.x" or "213.186.33.5"
- Click: Edit (pencil icon)
- **Change target to:** 132.226.134.7
- Click: Confirm/Save
- **Wait for propagation** (usually 5-30 minutes)

### 4. Update A Record (www)
- Find: A record for "www" with current target
- Click: Edit
- **Change target to:** 132.226.134.7
- Click: Confirm/Save
- **Wait for propagation**

### 5. Remove OLD/Conflicting Records (if any)
- If there are multiple A records for @ pointing to GitHub Pages:
  - 185.199.109.153
  - 185.199.108.153
  - 185.199.111.153
  - 185.199.110.153
  
  **DELETE THESE** - keep only the new 132.226.134.7

### 6. IPv6 Check
- Look for AAAA records
- If any exist pointing to non-OCI infrastructure:
  - Consider removing or updating to OCI IPv6 (if configured)
  - For now, recommend keeping empty if not configured

### 7. Email Configuration (VERIFY, DO NOT CHANGE)
- Confirm MX records are still:
  ```
  1 mx1.mail.ovh.net.
  5 mx2.mail.ovh.net.
  100 mx3.mail.ovh.net.
  ```
- Confirm SPF: `v=spf1 include:mx.ovh.com ~all`
- **DO NOT REMOVE or ALTER**

---

## Validation After Update

Once updated in OVH, validate with:

```bash
# Should resolve to 132.226.134.7
dig +short A verbodavidabraga.pt
dig +short A www.verbodavidabraga.pt

# Should still show OVH MX
dig +short MX verbodavidabraga.pt

# Should still show SPF
dig +short TXT verbodavidabraga.pt | grep spf
```

---

## Timeline

- **Immediately after update:** May not resolve (DNS cache)
- **5 minutes:** Some ISPs propagated
- **30 minutes:** Most ISPs propagated
- **2 hours:** Full global propagation (worst case)

**During propagation:** Some users will see old server, some new. This is normal.

---

## Troubleshooting

### If DNS doesn't update after 1 hour
1. Verify in OVH panel that change was saved
2. Check TTL (Time To Live) - if very high (3600+), wait longer
3. Try clearing local DNS cache:
   ```bash
   # On Linux
   sudo systemctl restart systemd-resolved
   
   # On Mac
   sudo dscacheutil -flushcache
   ```

### If multiple A records exist
1. OVH panel should show all A records for @
2. Delete all except the new 132.226.134.7
3. Keep www pointing to 132.226.134.7

---

**Next Step:** Once DNS is updated and propagated, server will automatically start receiving traffic on port 80 and 443.

Proceed to: [HTTPS Certificate Setup](#)
