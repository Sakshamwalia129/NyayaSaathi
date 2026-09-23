# NyayaSaathi Backend

FastAPI backend for NyayaSaathi — an AI-powered legal information and judgment intelligence platform for Indian citizens.

---

## 1. What the Backend Does

- **Rights Checker (`POST /api/rights-check`)**: Takes a user's description of a legal problem, performs semantic search across Indian legal statutes via ChromaDB, and generates plain-language explanations with cited provisions and next steps.
- **Judgment Simplifier (`POST /api/simplify-judgment`)**: Accepts uploaded court judgment files (PDF or TXT), extracts text and paragraph numbers, and produces structured case summaries with issues, decisions, and key principles.
- **Health Check (`GET /api/health`)**: Reports the service health, vector database chunk count, and LLM configuration status.

---

## 2. Folder Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── health.py        # Health check endpoint
│   │   ├── rights.py        # Rights Checker endpoint
│   │   └── judgments.py     # Judgment Simplifier endpoint
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response schemas
│   ├── services/
│   │   ├── embedding_service.py # SentenceTransformer embeddings
│   │   ├── rag_service.py       # ChromaDB vector store
│   │   ├── llm_service.py       # Gemini / OpenAI / Mock LLM
│   │   ├── legal_service.py     # Rights Checker pipeline
│   │   ├── judgment_service.py  # Judgment Simplifier pipeline
│   │   └── citation_service.py  # Citation verification
│   ├── utils/
│   │   ├── pdf_processing.py    # PyMuPDF text extraction
│   │   └── text_processing.py   # Chunking & paragraph splitting
│   ├── config.py            # Environment configuration
│   └── main.py              # FastAPI app & CORS configuration
├── data/
│   ├── legal_documents/     # Raw statutes & legal acts (by category)
│   └── judgments/           # Sample judgment documents
├── scripts/
│   └── ingest_documents.py  # Document embedding & ingestion script
├── tests/
│   └── test_api.py          # API unit tests
├── .env.example             # Example environment file
├── .env                     # Local environment variables
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 3. Getting Started (Setup & Run)

### A. Create Virtual Environment

From the `backend/` directory:

**Windows (PowerShell or CMD):**
```powershell
python -m venv venv
```

**Activate:**
```powershell
venv\Scripts\activate
```

### B. Install Dependencies

```powershell
pip install -r requirements.txt
```

### C. Configure Environment

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

By default, `USE_MOCK_LLM=true` is enabled so you can run and test everything locally without an API key.

To use real AI responses, add your API key:
```env
LLM_API_KEY=your_gemini_api_key_here
USE_MOCK_LLM=false
```

### D. Start the Backend Server

```powershell
uvicorn app.main:app --reload
```

The API will be live at: `http://localhost:8000`

### E. Verify Endpoints

- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 4. Legal Documents & Ingestion

### Adding Documents

Place legal text or PDF files into the `data/` directory:

```
backend/data/
├── legal_documents/
│   ├── consumer/         # E.g., consumer_protection_act.txt
│   ├── workplace/        # E.g., industrial_disputes_act.txt
│   └── rental/           # E.g., transfer_of_property_act.txt
└── judgments/            # Sample court judgment PDFs or TXTs
```

Each subfolder under `legal_documents/` becomes the category metadata in ChromaDB.

### Running Ingestion

Process and embed all documents into the local ChromaDB vector store:

```powershell
python scripts/ingest_documents.py
```

---

## 5. Mock Mode vs. Real LLM Mode

- **Mock Mode (`USE_MOCK_LLM=true`)**:
  Returns realistic mock responses immediately. No external LLM calls or API keys are required. Ideal for frontend testing, development, and offline demonstrations.
- **Real Mode (`USE_MOCK_LLM=false`)**:
  Requires a valid `LLM_API_KEY` (Google Gemini by default). The backend performs vector retrieval from ChromaDB, validates citations, and generates tailored legal explanations.

---

## 6. Frontend Connection

The React frontend (running at `http://localhost:5173`) communicates with this backend via:
- `VITE_API_URL=http://localhost:8000` set in the frontend `.env`
- Cross-Origin Resource Sharing (CORS) is configured in `app/main.py` using `FRONTEND_URL`.
