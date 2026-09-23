"""
schemas.py — Pydantic models for NyayaSaathi API.

IMPORTANT: Field names here are deliberately matched to what
the existing frontend (RightsChecker.jsx / JudgmentSimplifier.jsx)
already reads. Do NOT change them without also updating the frontend.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Rights Checker — Request
# ─────────────────────────────────────────────

class RightsCheckRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="User's description of their legal situation.",
    )
    category: Optional[str] = Field(
        None,
        description="Optional legal category (Consumer, Workplace, etc.)",
    )


# ─────────────────────────────────────────────
# Rights Checker — Response (matches frontend field names exactly)
#
# Frontend reads:
#   result.situation
#   result.explanation
#   result.provisions[].{id, source, section, summary, originalText, whyUsed}
#   result.nextSteps[]
#   result.groundingNote
# ─────────────────────────────────────────────

class LegalProvision(BaseModel):
    id: str
    source: str
    section: str
    summary: str
    originalText: str       # camelCase — matches frontend
    whyUsed: str            # camelCase — matches frontend
    verified: bool = False


class RightsCheckData(BaseModel):
    situation: str
    explanation: str
    provisions: list[LegalProvision]
    nextSteps: list[str]    # camelCase — matches frontend
    groundingNote: str      # camelCase — matches frontend
    retrievalConfidence: float
    
class RightsCheckResponse(BaseModel):
    success: bool
    data: Optional[RightsCheckData] = None
    error: Optional[dict] = None


# ─────────────────────────────────────────────
# Judgment Simplifier — Response (matches frontend field names exactly)
#
# Frontend reads:
#   result.caseTitle
#   result.court
#   result.year
#   result.caseType
#   result.brief
#   result.facts
#   result.arguments
#   result.issues[]
#   result.decision
#   result.legalPrinciples[]
#   result.paragraphs[].{id, number, text}
# ─────────────────────────────────────────────

class JudgmentParagraph(BaseModel):
    id: str
    number: str
    text: str


class JudgmentData(BaseModel):
    caseTitle: str          # camelCase — matches frontend
    court: str
    year: str
    caseType: str           # camelCase — matches frontend
    brief: str
    facts: str
    arguments: str
    issues: list[str]
    decision: str
    legalPrinciples: list[str]  # camelCase — matches frontend
    paragraphs: list[JudgmentParagraph]


class JudgmentResponse(BaseModel):
    success: bool
    data: Optional[JudgmentData] = None
    error: Optional[dict] = None


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    vector_database: dict
    llm_configured: bool
