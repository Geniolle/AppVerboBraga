# OVHcloud Consumer Key Generation

**Goal:** Generate a Consumer Key for automated DNS zone management  
**Scope:** Limited to `verbodavidabraga.pt` zone ONLY  
**Security:** Credentials passed via environment, never logged  

---

## Step 1: Have Your Credentials Ready

You need:
- **OVH Application Key** (provided by you)
- **OVH Application Secret** (provided by you)

These should be generated from OVH API console at:
https://eu.api.ovh.com/createToken/

---

## Step 2: Run the Generator Script

The script is located at:
```
~/AppVerboBraga/ovh_consumer_key_generator.py
```

### Option A: Interactive (Recommended - Safer)

```bash
/tmp/ovh_auth_prompt.sh
```

This will prompt you for credentials, which are passed to the server in memory (not logged).

### Option B: Direct Command

```bash
ssh -i ~/.ssh/servidor-verbo-braga.key opc@132.226.134.7 \
  'OVH_APPLICATION_KEY="your-key-here" \
   OVH_APPLICATION_SECRET="your-secret-here" \
   python3 ~/AppVerboBraga/ovh_consumer_key_generator.py'
```

---

## Step 3: What to Expect

The script will:

1. ✓ Load your credentials from environment (not displayed)
2. ✓ Send a request to OVH API with LIMITED permissions:
   - `GET /domain/zone/verbodavidabraga.pt`
   - `GET /domain/zone/verbodavidabraga.pt/*`
   - `POST /domain/zone/verbodavidabraga.pt/*`
   - `PUT /domain/zone/verbodavidabraga.pt/*`
   - `DELETE /domain/zone/verbodavidabraga.pt/*`

3. ✓ Receive a `validationUrl`
4. ✓ Display that URL for you to authorize
5. ✓ Save the `consumerKey` securely (not displayed)

---

## Step 4: Authorize the Request

The script will show:
```
1. Open this URL in your browser:
   https://eu.api.ovh.com/auth/?credentialToken=...
```

**Action:**
1. Copy the URL
2. Open in your browser
3. Login with your OVH account
4. Review the permissions (limited to DNS zone only)
5. Click "Authorize"
6. You'll be redirected after success

---

## Step 5: Provide Consumer Key

After you authorize, the script will have saved the Consumer Key.

You can then:

1. **Option A:** Provide the Consumer Key to me to configure DNS automation
2. **Option B:** Let me know when you've authorized, and I'll read it from the server

---

## Security Notes

✓ **Application Secret is never logged**
✓ **Consumer Key is saved only to secure file (~/.ovh_consumer_key.secure)**
✓ **Permissions limited to ONE zone ONLY**
✓ **No access to billing, cloud, dedicated, or other domains**
✓ **Credentials expire based on OVH policy**

---

## What Happens Next

Once Consumer Key is authorized:

1. I will retrieve it securely from the server
2. Configure DNS automation script with all 3 credentials
3. Automatically update DNS records when you give the signal
4. Monitor and complete HTTPS setup
5. Go live with https://verbodavidabraga.pt

---

**Ready?** Run the script and authorize the validation URL.

After you've completed Step 4 (authorization), let me know and I'll proceed with DNS automation.
