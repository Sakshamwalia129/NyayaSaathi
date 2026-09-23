"""
test_auth.py — Unit and integration tests for authentication system in NyayaSaathi.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

client = TestClient(app)

def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_lifecycle():
    data = {"sub": "999"}
    token = create_access_token(data)
    assert isinstance(token, str)
    
    payload = decode_access_token(token)
    assert payload.get("sub") == "999"

def test_auth_registration_and_login_flow():
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword2026!"
    name = "Test User"
    
    # 1. Register
    reg_resp = client.post(
        "/api/auth/register",
        json={"name": name, "email": unique_email, "password": password},
    )
    assert reg_resp.status_code == 200
    reg_body = reg_resp.json()
    assert reg_body["success"] is True
    assert "access_token" in reg_body
    assert reg_body["user"]["email"] == unique_email
    assert reg_body["user"]["name"] == name
    assert "password_hash" not in reg_body["user"]
    
    token = reg_body["access_token"]
    
    # 2. Duplicate registration attempt
    dup_resp = client.post(
        "/api/auth/register",
        json={"name": name, "email": unique_email, "password": password},
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"].lower()
    
    # 3. Login with correct password
    login_resp = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_resp.status_code == 200
    login_body = login_resp.json()
    assert login_body["success"] is True
    assert "access_token" in login_body
    
    # 4. Login with invalid password
    bad_login = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    
    # 5. Access /me with Bearer token
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_body = me_resp.json()
    assert me_body["success"] is True
    assert me_body["user"]["email"] == unique_email
    
    # 6. Access /me without token or with bad token
    bad_me = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token_123"},
    )
    assert bad_me.status_code == 401
