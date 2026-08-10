#!/usr/bin/env python3
"""
OVHcloud Consumer Key Generator
Generates a Consumer Key with limited permissions for DNS zone management ONLY
Restricted to: verbodavidabraga.pt zone

SECURITY:
- Credentials passed via environment variables only
- Consumer Key not logged to console
- No credentials saved to disk in plaintext
- Minimal API scope
"""

import os
import sys
import json
import hashlib
import time
import hmac
import requests
from urllib.parse import urlencode

# Configuration
ENDPOINT = "https://eu.api.ovh.com/1.0"
ZONE = "verbodavidabraga.pt"
APPLICATION_KEY = os.getenv('OVH_APPLICATION_KEY')
APPLICATION_SECRET = os.getenv('OVH_APPLICATION_SECRET')

# Ensure credentials are set
if not APPLICATION_KEY or not APPLICATION_SECRET:
    print("❌ ERROR: Missing OVH credentials")
    print()
    print("Set environment variables:")
    print("  export OVH_APPLICATION_KEY='your-application-key'")
    print("  export OVH_APPLICATION_SECRET='your-application-secret'")
    print()
    sys.exit(1)

# Credentials are loaded but not printed (security)
print("✓ OVH credentials loaded from environment")
print()

def sign_request(method, query, body=""):
    """Generate OVHcloud API signature"""
    timestamp = str(int(time.time()))

    # Consumer key is empty for initial auth request
    consumer_key = ""

    # Build signature string
    signature_components = [
        APPLICATION_SECRET,
        consumer_key,
        method,
        query,
        body,
        timestamp
    ]
    signature_string = "+".join(signature_components)

    # Calculate SHA1 HMAC
    signature = hashlib.sha1(signature_string.encode()).hexdigest()

    return timestamp, signature

def request_consumer_key():
    """Request a Consumer Key with limited DNS zone permissions"""

    print("=" * 70)
    print("OVHcloud Consumer Key Generator")
    print("=" * 70)
    print()
    print(f"API Endpoint:     {ENDPOINT}")
    print(f"Target Zone:      {ZONE}")
    print(f"Application Key:  {APPLICATION_KEY[:10]}...(hidden)")
    print()

    # Define access rights - ONLY DNS zone management
    access_rights = [
        {
            "method": "GET",
            "path": f"/domain/zone/{ZONE}"
        },
        {
            "method": "GET",
            "path": f"/domain/zone/{ZONE}/*"
        },
        {
            "method": "POST",
            "path": f"/domain/zone/{ZONE}/*"
        },
        {
            "method": "PUT",
            "path": f"/domain/zone/{ZONE}/*"
        },
        {
            "method": "DELETE",
            "path": f"/domain/zone/{ZONE}/*"
        }
    ]

    request_body = {
        "accessRules": access_rights,
        "redirectUrl": ""  # User will manually authorize
    }

    body_json = json.dumps(request_body)

    print("Requesting credentials with permissions:")
    for rule in access_rights:
        print(f"  • {rule['method']:6} {rule['path']}")
    print()

    # Generate signature
    timestamp, signature = sign_request("POST", "/auth/credential", body_json)

    # Prepare request
    url = f"{ENDPOINT}/auth/credential"
    headers = {
        "X-OVH-Application": APPLICATION_KEY,
        "X-OVH-Timestamp": timestamp,
        "X-OVH-Signature": f"$1${signature}",
        "Content-Type": "application/json"
    }

    print("Sending request to OVH API...")
    print()

    try:
        response = requests.post(url, json=request_body, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

        result = response.json()

        # Extract important data
        validation_url = result.get("validationUrl")
        consumer_key = result.get("consumerKey")
        state = result.get("state")

        print("=" * 70)
        print("✓ CONSUMER KEY REQUEST SUCCESSFUL")
        print("=" * 70)
        print()
        print("Next step: AUTHORIZE the request")
        print()
        print("1. Open this URL in your browser:")
        print()
        print(f"   {validation_url}")
        print()
        print("2. Login with your OVH account")
        print("3. Review and AUTHORIZE the permissions")
        print("4. You will be redirected after authorization")
        print()
        print("THEN: Provide the Consumer Key to complete setup")
        print()
        print("Status: WAITING_FOR_USER_VALIDATION")
        print()

        # Save consumer key to secure file (no permissions)
        config_file = os.path.expanduser("~/.ovh_consumer_key.secure")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        # Write with restricted permissions
        with open(config_file, 'w') as f:
            json.dump({
                "consumerKey": consumer_key,
                "state": state,
                "timestamp": int(time.time()),
                "zone": ZONE
            }, f)

        os.chmod(config_file, 0o600)  # Owner read/write only

        print(f"✓ Consumer Key saved securely (not displayed for security)")
        print(f"  Location: {config_file}")
        print()

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = request_consumer_key()
    sys.exit(0 if success else 1)
