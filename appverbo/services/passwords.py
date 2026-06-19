from __future__ import annotations

import base64
import hashlib
import secrets


# ###################################################################################
# (1) HASH DE PASSWORD COMPATIVEL COM O FORMATO DA APLICACAO
# ###################################################################################

def hash_password(raw_password: str) -> str:
    iterations = 390000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        raw_password.encode("utf-8"),
        salt,
        iterations,
    )
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    digest_b64 = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


def verify_password(raw_password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_text, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected_digest = base64.b64decode(digest_b64.encode("utf-8"))
    except (AttributeError, ValueError, TypeError):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        raw_password.encode("utf-8"),
        salt,
        iterations,
    )
    return secrets.compare_digest(candidate_digest, expected_digest)


__all__ = ["hash_password", "verify_password"]
