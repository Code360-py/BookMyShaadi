"""
Password hashing — stdlib PBKDF2-HMAC-SHA256.

Format:  pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
"""

import hashlib
import hmac
import secrets

from django.conf import settings


def hash_password(raw_password: str) -> str:
    iterations = getattr(settings, "PASSWORD_HASH_ITERATIONS", 260_000)
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${dk.hex()}"


def verify_password(raw_password: str, stored: str) -> bool:
    if not stored or not isinstance(stored, str):
        return False
    try:
        algo, iters, salt, hash_hex = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    try:
        dk = hashlib.pbkdf2_hmac(
            "sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), int(iters)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk.hex(), hash_hex)


def generate_temp_password(length: int = 12) -> str:
    """Used when admin resets a staff password."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))
