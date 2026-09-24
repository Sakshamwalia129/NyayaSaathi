# ⚖️ NyayaSaathi

### AI-Powered Indian Legal Intelligence Platform

NyayaSaathi is a full-stack AI-powered legal intelligence platform designed to make Indian legal information easier to understand and access.

Instead of functioning as a generic legal chatbot, NyayaSaathi uses a **Retrieval-Augmented Generation (RAG)** pipeline to retrieve relevant legal material before generating responses. The platform focuses on **source-grounded legal information**, judgment simplification, citation validation, and access to recent Supreme Court judgments.

> **Disclaimer:** NyayaSaathi provides legal information for educational and informational purposes only. It is not a substitute for professional legal advice.

---

## ✨ Key Features

### 🛡️ Rights Checker

Users can describe a legal problem in plain language and receive structured legal information.

The system:

- Retrieves relevant legal provisions from the legal knowledge base
- Generates a plain-language explanation
- Identifies relevant provisions and sources
- Suggests practical next steps
- Generates a structured Legal Action Plan with sequential steps, documents to keep ready, and relevant authorities
- Provides source-grounded citations
- Displays appropriate legal disclaimers
- Stores previous queries in user-specific history

---

### 📄 Judgment Simplifier

Users can upload court judgments and receive an AI-generated structured explanation.

The system extracts and organizes information such as:

- Case facts
- Legal issues
- Arguments
- Court decision
- Legal principles
- Important observations
- Relevant paragraphs
- Source references

Previous judgment analyses are stored in the authenticated user's history.

---

### 🏛️ Latest Supreme Court Judgments

NyayaSaathi automatically discovers recently published judgments from official Supreme Court sources.

Features include:

- Automatic Supreme Court judgment discovery
- Official PDF retrieval
- Duplicate detection using SHA-256
- AI-generated headline and summary
- Original official judgment link
- Automatic scheduled updates
- Failed-processing retry support
- PostgreSQL persistence

Users can filter judgments using:

- All
- Today
- Last 7 Days
- Last 30 Days
- Last 6 Months
- Custom Date Range

The original Supreme Court PDF remains available so users can verify the AI-generated information against the official source.

---

## 🔐 Authentication & Security

NyayaSaathi includes complete application authentication.

Supported authentication methods:

- Email and password
- Google Sign-In
- JWT-based authentication
- Protected frontend routes
- Protected backend APIs
- User-specific Rights history
- User-specific Judgment history

Unauthenticated users cannot access protected application functionality.

---

## 🧠 RAG Architecture

NyayaSaathi uses a custom Retrieval-Augmented Generation pipeline.

```text
User Legal Query
       │
       ▼
Text Preprocessing
       │
       ▼
Sentence Transformer Embeddings
       │
       ▼
ChromaDB Vector Search
       │
       ▼
Relevant Legal Documents
       │
       ▼
Context Construction
       │
       ▼
Gemini LLM
       │
       ▼
Structured Legal Response
       │
       ▼
Citation Validation
       │
       ▼
Source-Grounded Answer
```

The purpose of this architecture is to reduce unsupported responses by grounding generated answers in retrieved legal material.

---

## 🏗️ System Architecture

```text
                    ┌───────────────────────┐
                    │     React Frontend    │
                    │        Vite           │
                    └───────────┬───────────┘
                                │
                                │ REST API
                                ▼
                    ┌───────────────────────┐
                    │    FastAPI Backend    │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       Authentication      Legal RAG       Judgment Pipeline
              │                 │                 │
              ▼                 ▼                 ▼
             JWT           Embeddings          PDF/Text
                               │               Processing
                               ▼
                           ChromaDB
                               │
                               ▼
                         Gemini LLM
                               │
                               ▼
                      Citation Validation
                               │
                               ▼
                          PostgreSQL
```

---

## 🛠️ Tech Stack

### Frontend

- React
- Vite
- React Router
- JavaScript
- HTML5
- CSS3

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy

### AI / NLP

- Google Gemini API
- Sentence Transformers
- `all-MiniLM-L6-v2`
- Retrieval-Augmented Generation (RAG)

### Vector Database

- ChromaDB

### Application Database

- PostgreSQL

### Authentication

- JWT Authentication
- Google Sign-In
- Password hashing

### Document Processing

- PyMuPDF
- PDF text extraction
- Text preprocessing
- Document chunking

### External Legal Source

- Official Supreme Court of India judgment sources

---

## 🗄️ Database Design

NyayaSaathi uses two different storage systems for different purposes.

### PostgreSQL

Used for application data such as:

- Users
- Authentication-related data
- Rights Checker history
- Judgment analysis history
- Latest Supreme Court judgments
- Processing metadata

### ChromaDB

Used as the vector database for:

- Legal document chunks
- Embeddings
- Semantic retrieval
- RAG context generation

---

## 🔄 Latest Judgment Update Pipeline

```text
Official Supreme Court Source
            │
            ▼
Discover Judgment
            │
            ▼
Validate Official URL
            │
            ▼
Download Official PDF
            │
            ▼
SHA-256 Duplicate Check
            │
            ▼
Extract Judgment Text
            │
            ▼
AI Processing
            │
            ▼
Generate Headline + Summary
            │
            ▼
Store in PostgreSQL
            │
            ▼
Display in Latest Judgments
```

A background scheduler periodically checks for newly published judgments.

---

## 📁 Project Structure

```text
NyayaSaathi/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── health.py
│   │   │   ├── judgments.py
│   │   │   ├── latest_judgments.py
│   │   │   └── rights.py
│   │   │
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── migrations.py
│   │   │
│   │   ├── models/
│   │   │   ├── auth_schemas.py
│   │   │   ├── database_models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── services/
│   │   │   ├── embedding_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── legal_service.py
│   │   │   ├── judgment_service.py
│   │   │   ├── latest_judgment_service.py
│   │   │   └── latest_judgment_scheduler.py
│   │   │
│   │   ├── utils/
│   │   │   ├── pdf_processing.py
│   │   │   ├── security.py
│   │   │   └── text_processing.py
│   │   │
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── scripts/
│   │   └── ingest_documents.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── public/
│   └── assets/
│
├── src/
│   ├── components/
│   ├── context/
│   ├── pages/
│   ├── services/
│   └── App.jsx
│
├── .env.example
├── package.json
├── vite.config.js
└── README.md
```

---

## ⚙️ Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Sakshamwalia129/NyayaSaathi.git
cd NyayaSaathi
```

---

## 💻 Frontend Setup

Install dependencies:

```bash
npm install
```

Create a `.env` file using `.env.example`.

Example:

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
```

Start the frontend:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

## ⚙️ Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

### Windows

Activate it using:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your backend `.env` using:

```text
backend/.env.example
```

Configure the required environment variables including:

- Database connection
- JWT configuration
- Gemini API key
- Google authentication configuration
- ChromaDB configuration

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 📚 Legal Document Ingestion

Legal documents can be added to the configured legal document directories and ingested into ChromaDB.

Run:

```bash
python scripts/ingest_documents.py
```

The ingestion pipeline:

```text
Legal Document
      ↓
Text Extraction
      ↓
Cleaning
      ↓
Chunking
      ↓
Sentence Transformer Embeddings
      ↓
ChromaDB
```

---

## 🔌 Major API Endpoints

### Authentication

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Rights Explorer

```text
POST /api/rights-check
GET  /api/rights-history
```

### Judgment Intelligence

```text
POST /api/simplify-judgment
GET  /api/judgment-history
```

### Latest Supreme Court Judgments

```text
GET  /api/latest-judgments
POST /api/latest-judgments/update
POST /api/latest-judgments/{id}/analyze
```

Interactive API documentation is available through FastAPI Swagger at `/docs`.

---

## 🧪 Testing

The application has been tested for:

- Email/password authentication
- Google authentication
- Invalid password handling
- JWT-protected API access
- Protected frontend routes
- Session persistence
- User-specific Rights history
- User-specific Judgment history
- Latest Supreme Court judgment retrieval
- Official judgment PDF access
- Judgment date filtering
- Custom date filtering
- Responsive/mobile layouts

Some AI functionality depends on the availability and quota limits of the configured Gemini API account.

---

## 🛡️ Responsible AI

NyayaSaathi is designed as a **legal information system**, not a replacement for a lawyer.

Important safeguards include:

- Source-grounded generation
- Retrieval before generation
- Citation validation
- Original source references
- Clear AI-generated content labeling
- Legal disclaimers
- Official judgment PDF access

Users should verify important legal information using official sources or consult a qualified legal professional.

---

## ⚠️ Limitations

- AI-generated explanations may contain errors.
- Legal information can change over time.
- Results depend on the legal documents available in the knowledge base.
- AI features depend on external LLM API availability and quota limits.
- Judgment discovery depends on the availability and structure of official Supreme Court sources.
- The platform does not provide professional legal representation or legal advice.

---

## 🔮 Future Improvements

Possible future enhancements include:

- Larger Indian legal knowledge base
- Advanced legal reranking models
- Knowledge-graph-assisted retrieval
- Support for additional Indian courts
- Improved multilingual legal explanations
- More comprehensive RAG evaluation
- Advanced citation-grounding metrics

---

## 👨‍💻 Author

**Saksham Walia**

B.Tech Computer Science & Engineering  
Uttaranchal University

GitHub: `Sakshamwalia129`

---

## 📄 License

This project is currently intended for educational, research, and portfolio purposes.

---

### ⚖️ NyayaSaathi

**Know Your Rights. Understand the Law.**