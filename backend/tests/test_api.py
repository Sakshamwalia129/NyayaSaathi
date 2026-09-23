"""
test_api.py — Basic API tests using FastAPI's TestClient.

Run:
    cd backend
    pytest tests/
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_auth_headers():
    unique_email = f"api_test_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = client.post(
        "/api/auth/register",
        json={"name": "API Test User", "email": unique_email, "password": "TestPassword2026!"},
    )
    token = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────
def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "NyayaSaathi Backend"
    assert "vector_database" in body
    assert "llm_configured" in body


# ─────────────────────────────────────────────
# Rights Checker — validation
# ─────────────────────────────────────────────
def test_rights_check_empty_query():
    """Should return 422 validation error for empty query."""
    headers = get_auth_headers()
    response = client.post("/api/rights-check", json={"query": ""}, headers=headers)
    assert response.status_code == 422


def test_rights_check_short_query():
    """Should return 422 validation error for very short query."""
    headers = get_auth_headers()
    response = client.post("/api/rights-check", json={"query": "hi"}, headers=headers)
    assert response.status_code == 422


def test_rights_check_valid_query():
    """Should return 200 with mock data (assuming USE_MOCK_LLM=true)."""
    headers = get_auth_headers()
    response = client.post(
        "/api/rights-check",
        json={
            "query": "My landlord has not returned my security deposit after I vacated.",
            "category": "Consumer",
        },
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "success" in body
    if body.get("success"):
        data = body["data"]
        assert "situation" in data
        assert "explanation" in data
        assert "provisions" in data
        assert "nextSteps" in data
        assert "groundingNote" in data


def test_rights_check_no_category():
    """Category is optional — should work without it."""
    headers = get_auth_headers()
    response = client.post(
        "/api/rights-check",
        json={"query": "My employer fired me without any notice or reason."},
        headers=headers,
    )
    assert response.status_code == 200


# ─────────────────────────────────────────────
# Judgment Simplifier — validation
# ─────────────────────────────────────────────
def test_simplify_invalid_file_type():
    """Should return 415 for unsupported file types."""
    headers = get_auth_headers()
    response = client.post(
        "/api/simplify-judgment",
        files={"file": ("test.docx", b"fake docx content", "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 415


def test_simplify_empty_file():
    """Should return 400 for empty file."""
    headers = get_auth_headers()
    response = client.post(
        "/api/simplify-judgment",
        files={"file": ("test.txt", b"", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 400


def test_simplify_txt_file():
    """Should process a TXT file and return structured response."""
    headers = get_auth_headers()
    sample_text = """Lucknow Development Authority v. M.K. Gupta

Supreme Court of India, 1993

FACTS:
The appellant booked a flat with the housing authority and paid in full.
Possession was delayed for several years without explanation.

JUDGMENT:
The Court held that housing authorities providing services fall under
the Consumer Protection Act. The delay constituted deficiency in service.

The Commission has wide powers to grant relief to consumers who suffer
due to such deficiency in service by statutory bodies.
"""
    response = client.post(
        "/api/simplify-judgment",
        files={"file": ("sample.txt", sample_text.encode("utf-8"), "text/plain")},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "success" in body
    if body.get("success"):
        data = body["data"]
        assert "caseTitle" in data
        assert "paragraphs" in data
        assert isinstance(data["paragraphs"], list)
