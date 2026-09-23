"""
security.py — Security utilities for NyayaSaathi (password hashing, JWT management, Google verification).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import settings

# Initialize pwdlib with Argon2 password hasher
_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2 via pwdlib."""
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash."""
    if not hashed_password:
        return False
    try:
        return _password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token containing standard claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate a signed JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


def verify_google_token(credential: str) -> dict:
    """
    Verify a Google OAuth ID Token credential server-side.
    Returns the verified token payload if successful.
    """
    if not settings.GOOGLE_CLIENT_ID:
        # If client ID isn't set, verify without audience check (development) or raise descriptive error
        try:
            payload = id_token.verify_oauth2_token(
                credential, google_requests.Request()
            )
            return payload
        except Exception as e:
            raise ValueError(f"Google token verification failed: {str(e)}")
    
    try:
        payload = id_token.verify_oauth2_token(
            credential, google_requests.Request(), audience=settings.GOOGLE_CLIENT_ID
        )
        return payload
    except Exception as e:
        raise ValueError(f"Google token verification failed: {str(e)}")
