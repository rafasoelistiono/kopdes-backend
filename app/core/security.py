import hashlib
import secrets
from datetime import datetime, timedelta, timezone

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600000
TOKEN_BYTES = 32
SESSION_DAYS = 1


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != ALGORITHM:
        return False
    _algo, iterations_str, salt, expected_hex = parts
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations_str))
    return dk.hex() == expected_hex


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def token_expires_at() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
