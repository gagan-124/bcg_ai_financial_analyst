<<<<<<< HEAD
# BCG AI Financial Analyst

An AI-powered financial analysis platform that lets users analyze public-company financial performance through natural-language queries.

The system combines authoritative SEC EDGAR/XBRL financial data with deterministic Python-based financial calculations and an LLM reasoning layer to produce grounded financial insights, comparisons, and visualizations.

## What It Does

Users can ask questions such as:

- "Analyze Apple's financial performance"
- "Why did Microsoft's operating margin increase?"
- "Compare Apple and Microsoft revenue growth"
- "What drove Apple's revenue growth?"

The application:

1. Resolves the user's company and query intent.
2. Retrieves financial data from SEC EDGAR/XBRL.
3. Normalizes the reported financial data into a consistent structure.
4. Calculates financial metrics and trends deterministically using Python.
5. Passes verified financial context to the LLM for explanation and interpretation.
6. Uses Groq as a fallback when the primary Gemini provider experiences a transient failure.
7. Returns structured results to the React frontend.
8. Visualizes financial metrics through cards, tables, and interactive charts.

## Core Design Principle

> **The LLM explains verified financial data; it is not the source of truth for financial numbers.**

Financial values and derived metrics are calculated and validated by the backend before being provided to the LLM. This reduces the risk of hallucinated financial figures while allowing the model to provide natural-language analysis and interpretation.

## Key Capabilities

- **SEC EDGAR/XBRL Retrieval**: Direct ingestion and normalization of official 10-K and 10-Q XBRL company facts.
- **Deterministic Analytics**: Python-calculated revenue, net income, gross profit, operating margin, and diluted EPS.
- **Trend & Growth Metrics**: Year-over-Year (YoY) percentage changes and percentage-point (ppt) margin adjustments.
- **Natural-Language Understanding**: Intent detection and context routing for financial exploration.
- **Multi-Company Comparisons**: Side-by-side comparative financial analysis and multi-series charting.
- **Dual-LLM Architecture**: Google Gemini primary reasoning with automated Groq fallback orchestration.
- **Provenance & Verification**: Source provenance indicators and verification metadata on every metric.
- **Modern Web Interface**: Responsive dashboard featuring interactive Recharts visualizations and metric cards.
- **Containerized Deployment**: Reproducible Docker Compose environment with explicit secret isolation.
- **Quality Assurance**: Automated testing with Ruff, Pytest, and TypeScript build verification.

---

## Architecture & Tech Stack

### Frontend
- **Framework**: React 18 with Vite and TypeScript
- **Styling**: Tailwind CSS
- **Visualization**: Recharts
- **Icons & UI**: Lucide React

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Validation & Settings**: Pydantic v2 & `pydantic-settings`
- **Data Computation**: Pandas, NumPy
- **HTTP Clients**: HTTPX, Requests

### AI & Reasoning
- **Primary LLM**: Google Gemini (`gemini-3.6-flash`)
- **Fallback LLM**: Groq Console (`openai/gpt-oss-120b`)
- **Orchestration**: Transparent fallback with transient-error retries and secret-safe error sanitization

---

## Quickstart with Docker Compose

The fastest way to launch the full-stack application is using Docker Compose:

### 1. Configure Environment Variables
Copy the example configuration into `backend/.env`:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env` to configure your credentials:
```env
FINANCIAL_DATA_MODE=sec
SEC_USER_AGENT=BCG-AI-Financial-Analyst/1.0 contact@example.com
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

### 2. Start Containers
```bash
docker compose up -d
```
Docker Compose automatically loads configuration from `backend/.env` while keeping credentials isolated from image layers.

### 3. Verify Health & Access Application
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Local Development Setup

### Prerequisites
- Node.js (v20+)
- Python (v3.12+)
- Docker (optional, for containerized run)

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python -m pytest -v
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Testing & Quality Assurance

Run the automated test and lint suites locally:

### Backend Checks
```bash
cd backend
python -m ruff check .
python -m pytest -v
```

### Frontend Checks
```bash
cd frontend
npm run build
```

---

## Directory Structure

```text
bcg-ai-financial-analyst/
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── api/routes/       # Endpoints (analysis, chat, financials, companies)
│   │   ├── core/             # Configuration & security settings
│   │   ├── models/           # Domain entity definitions
│   │   ├── schemas/          # Pydantic validation models
│   │   └── services/         # SEC XBRL ingestion, financial math, LLM service
│   ├── tests/                # Unit and integration test suite
│   ├── Dockerfile            # Backend container definition
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React + Vite + TypeScript frontend
│   ├── src/
│   │   ├── components/       # Chat, financial cards, tables, and chart components
│   │   ├── hooks/            # Custom React hooks (useChat, useAnalysis)
│   │   ├── services/         # API integration client
│   │   └── types/            # TypeScript domain interfaces
│   ├── Dockerfile            # Frontend container definition
│   └── package.json          # Node dependencies and build scripts
├── data/
│   ├── raw/                  # Downloaded raw SEC filings
│   ├── processed/            # Cleaned financial datasets
│   └── sample/               # Offline fixture datasets
├── .github/workflows/        # CI/CD pipeline specifications
├── docker-compose.yml        # Docker Compose orchestration
└── rulebook.md               # Engineering principles & 6-stage lifecycle
```
