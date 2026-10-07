import base64
import hashlib
import hmac
import json
import os
import time

from src.core.config import settings

SECRET_KEY = getattr(settings, "SECRET_KEY", "ny_tagging_system_super_secret_key_2026_production")

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt:key hash."""
    try:
        salt_hex, key_hex = hashed_password.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta_seconds: int = 86400) -> str:
    """Creates a base64-encoded, HMAC-SHA256 signed access token."""
    payload = data.copy()
    expire = time.time() + expires_delta_seconds
    payload["exp"] = expire
    
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")
    
    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"

def decode_access_token(token: str) -> dict | None:
    """Decodes and verifies an HMAC-SHA256 signed access token."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        
        # Verify signature
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
            
        # Add padding back if necessary
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
            
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload = json.loads(payload_json)
        
        # Check expiration
        if "exp" in payload and payload["exp"] < time.time():
            return None
            
        return payload
    except Exception:
        return None
