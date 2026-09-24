"""
llm_service.py — Isolated LLM integration for NyayaSaathi.

All LLM calls go through here. The rest of the backend
never imports an LLM SDK directly.

Supports:
  - Google Gemini (default)
  - OpenAI (set LLM_PROVIDER=openai)
  - Mock mode (USE_MOCK_LLM=true) — no API key needed

Gemini reliability:
  - Primary model comes from LLM_MODEL in .env
  - Temporary 503/504 failures automatically fall back to
    stable Gemini Flash models
"""

import json
import logging

from app.config import settings
from app.services.judgment_retrieval_service import (
    retrieve_judgment_paragraphs,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# MOCK RESPONSES
# ─────────────────────────────────────────────────────────────

MOCK_RIGHTS_RESPONSE = {
    "situation": "Your Situation (Demo Mode)",
    "explanation": (
        "This is a demo response. The backend is running in mock mode "
        "(USE_MOCK_LLM=true). To get real AI-generated legal information, "
        "configure your LLM_API_KEY in the .env file and set "
        "USE_MOCK_LLM=false. In production, the system will retrieve "
        "relevant legal provisions from the vector database and generate "
        "a grounded explanation based on the actual legal text."
    ),
    "provisions": [
        {
            "id": "mock-p1",
            "source": "Sample Legal Act",
            "section": "Section 1 (Demo)",
            "summary": (
                "This is a sample legal provision shown in demo mode."
            ),
            "originalText": (
                "[DEMO] This text would contain the actual legal provision "
                "retrieved from the vector database."
            ),
            "whyUsed": (
                "This provision was selected because it is most relevant "
                "to your described situation."
            ),
        }
    ],
    "nextSteps": [
        "Configure your LLM_API_KEY in backend/.env to enable real responses.",
        "Add verified legal documents to backend/data/legal_documents/.",
        "Run the ingestion script: python scripts/ingest_documents.py",
        "Set USE_MOCK_LLM=false in backend/.env",
        "Restart the backend: uvicorn app.main:app --reload",
    ],

    # Legal Action Plan — demo/mock structure.
    "actionPlan": {
        "steps": [
            {
                "step": 1,
                "title": "Enable Real AI Responses",
                "description": (
                    "Configure the LLM API key and disable mock mode "
                    "to generate a grounded legal action plan."
                ),
            },
            {
                "step": 2,
                "title": "Add Verified Legal Sources",
                "description": (
                    "Ensure relevant verified legal documents are available "
                    "in the legal knowledge base."
                ),
            },
        ],
        "documents": [
            "Relevant documents supporting the user's situation",
            "Written communications or other available evidence",
        ],
        "authority": {
            "name": "Not identified in demo mode",
            "whenToApproach": (
                "A relevant authority can be identified only from "
                "retrieved legal context in real AI mode."
            ),
        },
    },

    "groundingNote": (
        "Demo mode is active. No real LLM generation is being performed. "
        "This response is returned to confirm the API connection is "
        "working correctly."
    ),
}


MOCK_JUDGMENT_RESPONSE = {
    "caseTitle": "Sample v. Respondent (Demo Mode)",
    "court": "Sample Court",
    "year": "2024",
    "caseType": "Demo — Backend Mock Mode",
    "brief": (
        "This is a demo response from the backend running in mock mode. "
        "Upload any real court judgment PDF/TXT to test the pipeline once "
        "the LLM is configured."
    ),
    "facts": (
        "The backend received your file upload and successfully extracted "
        "the filename. In production mode, PyMuPDF will extract full text "
        "from PDF files, segment it into paragraphs, and pass selected "
        "paragraphs to the LLM for analysis."
    ),
    "arguments": (
        "No arguments were analyzed — the backend is in demo mode. "
        "Set USE_MOCK_LLM=false and configure your LLM_API_KEY to enable "
        "real analysis."
    ),
    "issues": [
        "LLM API key is not configured yet.",
        "Set USE_MOCK_LLM=false in backend/.env to enable real processing.",
    ],
    "decision": "Demo mode active. No real analysis performed.",
    "legalPrinciples": [
        "Configure LLM_API_KEY in backend/.env",
        "Set USE_MOCK_LLM=false",
        "Restart the backend server",
        "Upload a real court judgment PDF or TXT file",
    ],
    "paragraphs": [
        {
            "id": "demo-para1",
            "number": "Paragraph 1 (Demo)",
            "text": (
                "This paragraph card confirms the Judgment Simplifier API "
                "is reachable. Real paragraph extraction from uploaded PDFs "
                "will appear here once configured."
            ),
        }
    ],
}


# ─────────────────────────────────────────────────────────────
# PROMPT TEMPLATES
# ─────────────────────────────────────────────────────────────

RIGHTS_SYSTEM_PROMPT = """
You are a legal information assistant for NyayaSaathi,
an Indian legal information platform.

STRICT RULES:

1. Answer ONLY from the legal context provided to you.
   Do NOT invent laws, sections, case names, dates, legal claims,
   authorities, procedures, deadlines, portals, helplines, or remedies.

2. If the provided context does not contain enough information,
   explicitly say so.

3. Do NOT present the response as professional legal advice.

4. Every important legal claim must be supported by one of the
   provisions returned in the "provisions" array.

5. Use numbered citations such as [1], [2], [3] inside the explanation.

6. Citation [1] must refer to the first item in the "provisions" array,
   [2] to the second item, and so on.

7. NEVER expose internal retrieval IDs such as:
   [industrial_relations_code_2020_chunk_3],
   [consumer_protection_act_2019_chunk_1],
   [SRC-001],
   or any other database/chunk identifier to the user.

8. Internal source IDs appearing in the retrieved context are for
   grounding only. Convert them into numbered user-facing citations.

9. Only include provisions that are actually supported by the
   retrieved legal context.

10. Do not quote or claim a section number unless that section is
    present in the provided context.

11. Use simple language that Indian citizens without legal training
    can understand.

12. Clearly mention important applicability limitations.
    For example, do not imply that every termination automatically
    qualifies as retrenchment.

13. Always include a disclaimer that the response provides general
    legal information only.

LEGAL ACTION PLAN RULES:

14. Create a practical "actionPlan" based on the user's situation
    and the retrieved legal context.

15. The action plan must NOT introduce a legal right, remedy,
    authority, procedure, deadline, portal, helpline, or legal
    requirement that is unsupported by the retrieved context.

16. The "steps" array should contain practical actions in a sensible
    order. Each step must contain:
      - step: sequential integer beginning at 1
      - title: short action title
      - description: simple explanation of the action

17. Do not promise an outcome or tell the user that taking a step
    will guarantee success.

18. For "documents", include only documents or evidence that are
    directly mentioned in the context or are clearly relevant to
    preserving/supporting the facts already described by the user.
    Do not invent mandatory filing requirements.

19. For "authority":
    - identify an authority only when it is supported by the
      retrieved legal context;
    - otherwise use:
      "Not identified from the available legal sources"
    - do not invent courts, commissions, departments, portals,
      helpline numbers, addresses, or filing procedures.

20. "whenToApproach" must also remain grounded in the available
    legal context. If the context does not establish when an
    authority should be approached, clearly state that this cannot
    be determined from the available legal sources.

21. The action plan is general legal information and must not be
    described as professional legal advice.

RESPONSE FORMAT — return valid JSON only, no extra text:

{
  "situation": "Brief title for this situation (5-10 words)",

  "explanation": "A clear 2-3 paragraph explanation. Use citations like [1] and [2] after the legal claims they support. Never show internal chunk IDs.",

  "provisions": [
    {
      "id": "p1",
      "source": "Full official name of the Act or legal source",
      "section": "Section number and brief title",
      "summary": "Plain-language explanation of what this provision means",
      "originalText": "Relevant text taken only from the retrieved legal context",
      "whyUsed": "Why this provision is relevant to the user's situation"
    }
  ],

  "nextSteps": [
    "Specific practical step 1",
    "Specific practical step 2"
  ],

  "actionPlan": {
    "steps": [
      {
        "step": 1,
        "title": "Short action title",
        "description": "Practical action based on the retrieved legal context"
      },
      {
        "step": 2,
        "title": "Short action title",
        "description": "Next practical action based on the retrieved legal context"
      }
    ],

    "documents": [
      "Relevant document or evidence supported by the situation/context"
    ],

    "authority": {
      "name": "Authority supported by the retrieved context, or Not identified from the available legal sources",
      "whenToApproach": "When the authority may be approached according to the context, or state that this cannot be determined from the available legal sources"
    }
  },

  "groundingNote": "Briefly explain which legal source(s) were used and any important limitations. Do not expose internal chunk IDs."
}
"""


JUDGMENT_SYSTEM_PROMPT = """
You are a legal analysis assistant for NyayaSaathi,
an Indian legal information platform.

You have been given semantically retrieved paragraphs from a court
judgment. Analyze them and return a structured summary.

STRICT RULES:

1. Only report what is ACTUALLY present in the provided judgment context.

2. For important paragraphs, reference ONLY paragraph IDs from the
   provided list.

3. Do NOT invent paragraph numbers, citations, dates, facts,
   legal principles, parties, or decisions.

4. If information cannot be determined from the provided paragraphs,
   clearly state that it is unclear from the supplied context.

5. Use plain language while preserving legal precision.

6. The "paragraphs" array must contain only paragraphs that are
   directly relevant to the important findings of the judgment.

RESPONSE FORMAT — return valid JSON only, no extra text:

{
  "caseTitle": "Full case name",
  "court": "Court name",
  "year": "Year of judgment",
  "caseType": "Type of case",
  "brief": "2-3 sentence summary of the case",
  "facts": "Key facts paragraph",
  "arguments": "Main arguments from both sides",
  "issues": ["Issue 1", "Issue 2"],
  "decision": "What the court decided and why",
  "legalPrinciples": ["Principle 1", "Principle 2"],
  "paragraphs": [
    {
      "id": "para1",
      "number": "Paragraph N",
      "text": "Exact or near-exact text from the judgment"
    }
  ]
}
"""


# ─────────────────────────────────────────────────────────────
# GEMINI HELPERS
# ─────────────────────────────────────────────────────────────

GEMINI_FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]


def _is_temporary_gemini_error(exc: Exception) -> bool:
    """
    Return True only for temporary provider availability errors.

    Authentication, permission, invalid-model, malformed-request,
    quota and other configuration errors should NOT silently
    fall back to another model.
    """

    error_text = str(exc).lower()

    return (
        "503" in error_text
        or "504" in error_text
        or "unavailable" in error_text
        or "high demand" in error_text
        or "deadline exceeded" in error_text
        or "timed out" in error_text
        or "timeout" in error_text
    )


def _gemini_model_chain() -> list[str]:
    """
    Build primary + fallback model chain without duplicates.
    """

    models = [
        settings.LLM_MODEL,
        *GEMINI_FALLBACK_MODELS,
    ]

    unique_models = []

    for model in models:
        if model and model not in unique_models:
            unique_models.append(model)

    return unique_models


# ─────────────────────────────────────────────────────────────
# LLM PROVIDER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def _call_gemini(
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Call Google Gemini using the current google-genai SDK.

    The configured LLM_MODEL is always tried first.

    If Gemini returns a temporary availability error such as
    503/504, stable fallback Flash models are tried automatically.
    """

    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.LLM_API_KEY
    )

    models = _gemini_model_chain()
    last_exception = None

    for index, model_name in enumerate(models):
        try:
            logger.info(
                "Calling Gemini model: %s",
                model_name,
            )

            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )

            if not response.text:
                raise ValueError(
                    f"Gemini model {model_name} returned an empty response."
                )

            if index > 0:
                logger.info(
                    "Gemini fallback succeeded with model: %s",
                    model_name,
                )

            return response.text

        except Exception as exc:
            last_exception = exc

            logger.warning(
                "Gemini model %s failed: %s",
                model_name,
                exc,
            )

            if not _is_temporary_gemini_error(exc):
                raise

            is_last_model = index == len(models) - 1

            if is_last_model:
                break

            logger.warning(
                "Temporary Gemini availability issue. "
                "Trying fallback model: %s",
                models[index + 1],
            )

    if last_exception is not None:
        raise last_exception

    raise ValueError(
        "No Gemini model is configured."
    )


def _call_openai(
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Call OpenAI API and return the text response.
    """

    from openai import OpenAI

    client = OpenAI(
        api_key=settings.LLM_API_KEY
    )

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        response_format={
            "type": "json_object"
        },
    )

    return response.choices[0].message.content


def generate_response(
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Call the configured LLM provider.

    Provider/API failures are converted into clean ValueError
    messages so callers can return a controlled API response
    instead of an unhandled 500 error.
    """

    if not settings.llm_configured:
        raise ValueError(
            "LLM API key is not configured. "
            "Set LLM_API_KEY in .env"
        )

    provider = settings.LLM_PROVIDER.lower()

    try:
        if provider == "openai":
            return _call_openai(
                system_prompt,
                user_message,
            )

        return _call_gemini(
            system_prompt,
            user_message,
        )

    except Exception as exc:
        logger.exception(
            "LLM call failed: %s",
            exc,
        )

        error_text = str(exc).lower()

        # -----------------------------------------------------
        # Quota / rate-limit handling
        # -----------------------------------------------------

        if (
            "429" in error_text
            or "quota" in error_text
            or "rate limit" in error_text
            or "rate-limit" in error_text
            or "resourceexhausted" in error_text
            or "resource exhausted" in error_text
        ):
            raise ValueError(
                "The AI service is temporarily rate-limited. "
                "Please wait a short while and try again."
            ) from exc

        # -----------------------------------------------------
        # Temporary provider availability
        # -----------------------------------------------------

        if (
            "503" in error_text
            or "504" in error_text
            or "unavailable" in error_text
            or "high demand" in error_text
            or "deadline exceeded" in error_text
            or "timeout" in error_text
            or "timed out" in error_text
        ):
            raise ValueError(
                "The AI service is temporarily unavailable. "
                "Please try again shortly."
            ) from exc

        # -----------------------------------------------------
        # Authentication / API-key handling
        # -----------------------------------------------------

        if (
            "401" in error_text
            or "403" in error_text
            or "api key not valid" in error_text
            or "invalid api key" in error_text
            or "permission denied" in error_text
        ):
            raise ValueError(
                "The AI service authentication failed. "
                "Please check the configured API key."
            ) from exc

        # -----------------------------------------------------
        # Model configuration errors
        # -----------------------------------------------------

        if (
            "404" in error_text
            or "model not found" in error_text
            or "not found" in error_text
        ):
            raise ValueError(
                "The configured AI model is unavailable. "
                "Please check LLM_MODEL in .env."
            ) from exc

        # -----------------------------------------------------
        # Other provider/API errors
        # -----------------------------------------------------

        raise ValueError(
            "The AI service could not process the request. "
            "Please try again."
        ) from exc


# ─────────────────────────────────────────────────────────────
# RIGHTS CHECKER
# ─────────────────────────────────────────────────────────────

def generate_rights_response(
    query: str,
    context: str,
    category: str | None,
) -> dict:
    """
    Generate a structured Rights Checker response.
    """

    if settings.USE_MOCK_LLM:
        logger.info(
            "Mock mode: returning demo rights response."
        )
        return MOCK_RIGHTS_RESPONSE

    user_message = f"""
USER QUERY:
{query}

LEGAL CATEGORY:
{category or "General"}

RETRIEVED LEGAL CONTEXT:
{context}

Generate a structured legal information response
based strictly on the context above.

In addition to the existing Rights Checker response,
generate the "actionPlan" using only the user's situation
and the retrieved legal context.

Do not invent authorities, legal procedures, deadlines,
portals, helplines, filing requirements, or remedies.
"""

    raw = generate_response(
        RIGHTS_SYSTEM_PROMPT,
        user_message,
    )

    try:
        return json.loads(raw)

    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse Rights Checker LLM JSON: %s\nRaw: %s",
            exc,
            raw[:500],
        )

        raise ValueError(
            "LLM returned an unparseable response. "
            "Please try again."
        )


# ─────────────────────────────────────────────────────────────
# JUDGMENT SIMPLIFIER
# ─────────────────────────────────────────────────────────────

def generate_judgment_response(
    judgment_text: str,
    paragraphs: list[dict],
) -> dict:
    """
    Generate a structured judgment simplification response.

    For long judgments, semantic retrieval identifies paragraphs
    relevant to metadata, facts, arguments, issues, decision,
    reasoning and legal principles before the LLM is called.
    """

    if settings.USE_MOCK_LLM:
        logger.info(
            "Mock mode: returning demo judgment response."
        )
        return MOCK_JUDGMENT_RESPONSE

    # ---------------------------------------------------------
    # Semantic paragraph retrieval
    # ---------------------------------------------------------

    selected_paragraphs = retrieve_judgment_paragraphs(
        paragraphs,
        top_k_per_query=6,
        max_total=45,
    )

    if not selected_paragraphs:
        raise ValueError(
            "No usable paragraphs were found for judgment analysis."
        )

    logger.info(
        "Judgment RAG analysis: using %s of %s extracted paragraphs.",
        len(selected_paragraphs),
        len(paragraphs),
    )

    # ---------------------------------------------------------
    # Build grounded paragraph context
    # ---------------------------------------------------------

    para_block = "\n\n".join(
        (
            f"[{paragraph['id']}] "
            f"{paragraph['text']}"
        )
        for paragraph in selected_paragraphs
    )

    user_message = f"""
DOCUMENT INFORMATION:

Total extracted characters:
{len(judgment_text)}

Total extracted paragraphs:
{len(paragraphs)}

SEMANTICALLY RETRIEVED JUDGMENT PARAGRAPHS:

{para_block}

Analyze this judgment and return the structured JSON response.

IMPORTANT:

- Base the analysis only on the paragraphs provided above.
- Only reference paragraph IDs that appear above.
- Do not invent facts, arguments, decisions, dates,
  citations, legal principles, or paragraph IDs.
- If an important detail cannot be determined from the
  provided paragraphs, explicitly say that it is unclear
  from the supplied context.
"""

    raw = generate_response(
        JUDGMENT_SYSTEM_PROMPT,
        user_message,
    )

    # ---------------------------------------------------------
    # Parse structured LLM response
    # ---------------------------------------------------------

    try:
        return json.loads(raw)

    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse Judgment LLM JSON: %s\nRaw: %s",
            exc,
            raw[:500],
        )

        raise ValueError(
            "LLM returned an unparseable response. "
            "Please try again."
        )