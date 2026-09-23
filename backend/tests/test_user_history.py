"""
test_user_history.py — Tests for user-specific history isolation and authentication protection.
"""

import sys
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.db.database import SessionLocal
from app.models.database_models import RightsQuery, JudgmentAnalysis, User

client = TestClient(app)


def helper_create_user(name_prefix: str, provider: str = "local"):
    """Helper to create a test user with a clean token."""
    unique_email = f"{name_prefix}_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword2026!"
    
    if provider == "google":
        reg_resp = client.post(
            "/api/auth/register",
            json={"name": name_prefix, "email": unique_email, "password": password},
        )
        token = reg_resp.json()["access_token"]
        user_id = reg_resp.json()["user"]["id"]
        
        db = SessionLocal()
        u = db.query(User).filter(User.id == user_id).first()
        u.auth_provider = "google"
        u.google_sub = f"google_sub_{uuid.uuid4().hex[:8]}"
        db.commit()
        db.close()
        return token, user_id, unique_email
    elif provider == "hybrid":
        reg_resp = client.post(
            "/api/auth/register",
            json={"name": name_prefix, "email": unique_email, "password": password},
        )
        token = reg_resp.json()["access_token"]
        user_id = reg_resp.json()["user"]["id"]
        
        db = SessionLocal()
        u = db.query(User).filter(User.id == user_id).first()
        u.auth_provider = "hybrid"
        u.google_sub = f"google_sub_{uuid.uuid4().hex[:8]}"
        db.commit()
        db.close()
        return token, user_id, unique_email
    else:
        reg_resp = client.post(
            "/api/auth/register",
            json={"name": name_prefix, "email": unique_email, "password": password},
        )
        token = reg_resp.json()["access_token"]
        user_id = reg_resp.json()["user"]["id"]
        return token, user_id, unique_email


# ─────────────────────────────────────────────
# 1-4. Unauthenticated Endpoints Protection (401)
# ─────────────────────────────────────────────

def test_unauthenticated_rights_post_rejected():
    """1. Unauthenticated Rights POST -> 401"""
    resp = client.post("/api/rights-check", json={"query": "Unauthenticated test query."})
    assert resp.status_code == 401


def test_unauthenticated_rights_history_rejected():
    """2. Unauthenticated Rights history -> 401"""
    resp = client.get("/api/rights-history")
    assert resp.status_code == 401


def test_unauthenticated_judgment_post_rejected():
    """3. Unauthenticated Judgment POST -> 401"""
    resp = client.post(
        "/api/simplify-judgment",
        files={"file": ("test.txt", b"Sample legal judgment text.", "text/plain")},
    )
    assert resp.status_code == 401


def test_unauthenticated_judgment_history_rejected():
    """4. Unauthenticated Judgment history -> 401"""
    resp = client.get("/api/judgment-history")
    assert resp.status_code == 401


# ─────────────────────────────────────────────
# 5-8. Rights History User Isolation (User A vs User B)
# ─────────────────────────────────────────────

def test_rights_history_user_isolation():
    """5-8. User A and User B submission and history isolation."""
    token_a, user_id_a, _ = helper_create_user("UserA")
    token_b, user_id_b, _ = helper_create_user("UserB")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    query_a_text = f"User A dispute query {uuid.uuid4().hex[:6]}"
    query_b_text = f"User B dispute query {uuid.uuid4().hex[:6]}"

    # Add records explicitly tagged with user_id_a and user_id_b
    db = SessionLocal()
    db.add(RightsQuery(user_id=user_id_a, query=query_a_text, category="Consumer", response={"success": True}))
    db.add(RightsQuery(user_id=user_id_b, query=query_b_text, category="Consumer", response={"success": True}))
    db.commit()
    db.close()

    # Verify User A history contains query A and NOT query B
    hist_a = client.get("/api/rights-history", headers=headers_a).json()
    assert hist_a["success"] is True
    queries_a = [item["query"] for item in hist_a["data"]]
    assert query_a_text in queries_a
    assert query_b_text not in queries_a

    # Verify User B history contains query B and NOT query A
    hist_b = client.get("/api/rights-history", headers=headers_b).json()
    assert hist_b["success"] is True
    queries_b = [item["query"] for item in hist_b["data"]]
    assert query_b_text in queries_b
    assert query_a_text not in queries_b


# ─────────────────────────────────────────────
# 9. Judgment History User Isolation
# ─────────────────────────────────────────────

def test_judgment_history_user_isolation():
    """9. Judgment history isolation between User A and User B."""
    token_a, user_id_a, _ = helper_create_user("UserA_Judg")
    token_b, user_id_b, _ = helper_create_user("UserB_Judg")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    filename_a = f"judgment_A_{uuid.uuid4().hex[:4]}.txt"
    filename_b = f"judgment_B_{uuid.uuid4().hex[:4]}.txt"

    # Add records explicitly tagged with user_id_a and user_id_b
    db = SessionLocal()
    db.add(JudgmentAnalysis(user_id=user_id_a, filename=filename_a, response={"success": True}))
    db.add(JudgmentAnalysis(user_id=user_id_b, filename=filename_b, response={"success": True}))
    db.commit()
    db.close()

    # User A history check
    hist_a = client.get("/api/judgment-history", headers=headers_a).json()
    files_a = [item["filename"] for item in hist_a["data"]]
    assert filename_a in files_a
    assert filename_b not in files_a

    # User B history check
    hist_b = client.get("/api/judgment-history", headers=headers_b).json()
    files_b = [item["filename"] for item in hist_b["data"]]
    assert filename_b in files_b
    assert filename_a not in files_b


# ─────────────────────────────────────────────
# 10. Legacy user_id = NULL rows exclusion
# ─────────────────────────────────────────────

def test_legacy_null_user_id_records_not_returned():
    """10. Legacy records with user_id = NULL are not returned to authenticated users."""
    token, user_id, _ = helper_create_user("LegacyCheckUser")
    headers = {"Authorization": f"Bearer {token}"}

    # Inject legacy NULL row
    db = SessionLocal()
    legacy_query = RightsQuery(
        user_id=None,
        query="Legacy query with null user_id",
        category="General",
        response={"success": True, "data": {}},
    )
    legacy_judgment = JudgmentAnalysis(
        user_id=None,
        filename="legacy_null_judgment.txt",
        response={"success": True, "data": {}},
    )
    db.add(legacy_query)
    db.add(legacy_judgment)
    db.commit()
    db.close()

    # User history requests
    r_hist = client.get("/api/rights-history", headers=headers).json()
    j_hist = client.get("/api/judgment-history", headers=headers).json()

    # Verify NULL user_id records do not leak
    r_queries = [item["query"] for item in r_hist["data"]]
    j_files = [item["filename"] for item in j_hist["data"]]

    assert "Legacy query with null user_id" not in r_queries
    assert "legacy_null_judgment.txt" not in j_files


# ─────────────────────────────────────────────
# 11. Provider Compatibility (Local, Google, Hybrid)
# ─────────────────────────────────────────────

def test_provider_compatibility():
    """11. Local, Google, and Hybrid users behave identically after NyayaSaathi authentication."""
    token_google, user_id_g, _ = helper_create_user("GoogleUser", provider="google")
    token_hybrid, user_id_h, _ = helper_create_user("HybridUser", provider="hybrid")

    db = SessionLocal()
    q_google = f"Google user query {uuid.uuid4().hex[:4]}"
    q_hybrid = f"Hybrid user query {uuid.uuid4().hex[:4]}"
    db.add(RightsQuery(user_id=user_id_g, query=q_google, category="Workplace", response={"success": True}))
    db.add(RightsQuery(user_id=user_id_h, query=q_hybrid, category="Workplace", response={"success": True}))
    db.commit()
    db.close()

    # Google user history check
    h_google = client.get("/api/rights-history", headers={"Authorization": f"Bearer {token_google}"}).json()
    assert h_google["success"] is True
    queries_g = [item["query"] for item in h_google["data"]]
    assert q_google in queries_g

    # Hybrid user history check
    h_hybrid = client.get("/api/rights-history", headers={"Authorization": f"Bearer {token_hybrid}"}).json()
    assert h_hybrid["success"] is True
    queries_h = [item["query"] for item in h_hybrid["data"]]
    assert q_hybrid in queries_h
