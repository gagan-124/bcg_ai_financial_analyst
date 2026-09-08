# BCG AI Financial Analyst

BCG AI Financial Analyst is a full-stack application for exploring the financial performance of three supported public companies: Apple (AAPL), Microsoft (MSFT), and Tesla (TSLA).

The application combines company resolution, SEC EDGAR Company Facts/XBRL retrieval, deterministic financial calculations, and grounded LLM explanations. The React frontend presents the results as financial cards, trend charts, comparison tables, and source citations.

## Live Demo

**Vercel deployment:** [bcg-ai-financial-analyst.vercel.app](https://bcg-ai-financial-analyst.vercel.app)

Useful production routes:

- Dashboard: <https://bcg-ai-financial-analyst.vercel.app/>
- Health check: <https://bcg-ai-financial-analyst.vercel.app/health>
- Swagger UI: <https://bcg-ai-financial-analyst.vercel.app/docs>
- OpenAPI document: <https://bcg-ai-financial-analyst.vercel.app/openapi.json>

## Project Overview

Users can start a company analysis or ask a follow-up question in natural language. The system currently supports:

- Apple, Microsoft, and Tesla by canonical name, common aliases, or ticker
- Multi-year revenue, net income, diluted EPS, and operating margin data
- Year-over-year changes for revenue, net income, and EPS
- Percentage-point operating-margin changes
- Single-company trend visualizations
- Multi-company revenue comparisons when another supported company is mentioned
- Grounded follow-up explanations with source metadata

The analysis overview is deterministic. The LLM is used for follow-up explanations, not for producing the financial figures displayed by the application.

## Core Workflow

```text
User message
    |
    v
Frontend company and intent classification
    |
    v
FastAPI analysis route
    |
    +--> Resolve Apple, Microsoft, or Tesla
    |
    +--> Load SEC Company Facts/XBRL or configured fixture data
    |
    +--> Normalize financial periods
    |
    +--> Calculate metrics, trends, and findings in Python
    |
    +--> Build verified context for follow-up questions
    |
    +--> Gemini explanation
              |
              +--> Groq fallback on transient Gemini failure
    |
    v
Structured JSON response
    |
    v
React cards, tables, charts, and citations
```

### Data and analytics path

The backend supports three `FINANCIAL_DATA_MODE` values:

- `fixture`: use the controlled local datasets. This is the default in the backend configuration and is used by CI.
- `sec`: retrieve and normalize SEC EDGAR Company Facts data. Requests fail when SEC data cannot be retrieved.
- `sec_with_fixture_fallback`: try SEC data first, then use the local fixture when SEC retrieval fails.

Normalized periods contain revenue, net income, diluted EPS, and operating margin. The analysis service calculates the latest-period metrics, period-over-period changes, deterministic findings, historical trend data, and source metadata.

### LLM path

Follow-up questions are sent to the configured primary provider, Gemini by default. The prompt includes the verified periods, metrics, findings, and provenance information. The model is instructed to use only that context and to identify when the available data is insufficient. A configured Groq provider is used when the primary provider raises a transient error such as a timeout, rate limit, or temporary service failure. Non-transient provider errors are surfaced instead of silently falling back.

## Production Architecture

The repository is configured as a unified Vercel deployment:

```text
Browser
  |
  +--> Vercel static frontend (React + Vite)
  |
  +--> /api/*, /health, /docs, /openapi.json
          |
          +--> api/index.py
                  |
                  +--> backend/app/main.py
                          |
                          +--> SEC/XBRL or fixture data
                          +--> deterministic analysis services
                          +--> Gemini/Groq providers
```

`vercel.json` builds `frontend` into `frontend/dist`, exposes `api/index.py` as a Python serverless function, includes the backend source, and rewrites the API and documentation routes to FastAPI. For local development, Docker Compose runs separate backend and frontend containers.

## API Endpoints

### Health and documentation

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Returns service health, version, and environment |
| `GET` | `/docs` | FastAPI Swagger UI |
| `GET` | `/openapi.json` | Root alias for the generated OpenAPI document |
| `GET` | `/api/docs` | Redirects to `/docs` |

### Analysis

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/analysis` | Returns a structured company financial overview |
| `POST` | `/api/analysis/question` | Answers a grounded follow-up question and may return chart/table context |
| `POST` | `/api/v1/analysis` | Versioned alias for the company overview route |
| `POST` | `/api/v1/analysis/question` | Versioned alias for the follow-up question route |

The versioned `/api/v1/chat`, `/api/v1/financials`, and `/api/v1/companies` routers exist as placeholders but do not currently expose implemented operations.

### Example requests

```bash
curl -X POST "https://bcg-ai-financial-analyst.vercel.app/api/analysis" ^
  -H "Content-Type: application/json" ^
  -d "{\"company\":\"Apple\",\"query\":\"Show financial analysis\"}"
```

```bash
curl -X POST "https://bcg-ai-financial-analyst.vercel.app/api/analysis/question" ^
  -H "Content-Type: application/json" ^
  -d "{\"company\":\"Microsoft\",\"question\":\"Why did Microsoft's operating margin increase?\"}"
```

The analysis response includes `company`, `summary`, `metrics`, `trend`, `table`, `findings`, and `source`. Follow-up responses include `company`, `question`, `answer`, `source`, and optional structured `chart`, `table`, and `metrics` fields.

## Reliability and Grounding

The project separates numeric computation from language generation:

- Financial values are loaded from SEC Company Facts/XBRL or explicitly identified demo fixtures.
- XBRL data is normalized before it enters the analysis layer.
- Revenue, net income, EPS, margin changes, and findings are calculated in Python.
- Source metadata identifies SEC EDGAR or the demo fixture path.
- The LLM receives the calculated context and is instructed not to invent figures, unsupported causes, charts, or external facts.
- Provider errors are sanitized before they are returned to callers.
- Gemini-to-Groq fallback is limited to transient primary-provider failures.
- Unsupported companies and invalid requests return explicit HTTP errors.

Fixture data is intentionally labeled as demonstration data. It is not live market data and should not be treated as a filing.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | React 18, TypeScript, Vite |
| UI and visualization | Tailwind CSS, Recharts, Lucide React |
| Backend | FastAPI, Python 3.12+, Pydantic, pydantic-settings |
| Financial processing | Pandas, NumPy |
| HTTP and integrations | HTTPX, Requests, SEC EDGAR Company Facts |
| LLM providers | Google Gemini, Groq |
| Local orchestration | Docker Compose |
| Quality and CI | Pytest, pytest-asyncio, Ruff, TypeScript compiler, GitHub Actions |
| Hosting | Vercel |

## Local Setup

### Prerequisites

- Python 3.12 or newer
- Node.js 20 or newer
- Docker and Docker Compose, if using the containerized setup

### Native development

1. Configure the backend:

   ```bash
   cd backend
   python -m venv .venv

   # Windows PowerShell
   .venv\Scripts\Activate.ps1

   # macOS/Linux
   # source .venv/bin/activate

   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

2. Start the backend from the `backend` directory:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. In a second terminal, install and start the frontend:

   ```bash
   cd frontend
   npm install
   Copy-Item .env.example .env
   npm run dev
   ```

The frontend is available at `http://localhost:5173`. Set `VITE_API_BASE_URL=http://localhost:8000` for a separate local backend; leave it empty when the frontend and API share an origin.

## Docker

Docker Compose starts the backend on port `8000` and the Vite frontend on port `5173`.

```bash
Copy-Item backend\.env.example backend\.env
docker compose up --build
```

Open:

- Frontend: <http://localhost:5173>
- Backend health: <http://localhost:8000/health>
- Backend Swagger UI: <http://localhost:8000/docs>

The Compose file mounts the source directories for development and passes `VITE_API_BASE_URL=http://localhost:8000` to the frontend container.

## Environment Variables

Backend variables are read from `.env` and `backend/.env`. Use `backend/.env.example` as the starting point.

| Variable | Required | Description |
| --- | --- | --- |
| `FINANCIAL_DATA_MODE` | No | `fixture`, `sec`, or `sec_with_fixture_fallback`; backend default is `fixture` |
| `SEC_USER_AGENT` | In SEC modes | User-Agent sent to SEC EDGAR; include an application name and contact address |
| `GEMINI_API_KEY` | For Gemini | API key for the primary Gemini provider |
| `GEMINI_MODEL` | No | Gemini model identifier; default is `gemini-3.6-flash` |
| `GROQ_API_KEY` | For Groq fallback | API key for the fallback provider |
| `GROQ_MODEL` | No | Groq model identifier; default is `openai/gpt-oss-120b` |
| `LLM_PRIMARY_PROVIDER` | No | Primary provider setting; default is `gemini` |
| `LLM_FALLBACK_PROVIDER` | No | Fallback provider setting; default is `groq` |
| `LLM_REQUEST_TIMEOUT_SECONDS` | No | LLM request timeout; default is `30.0` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `CORS_ORIGIN_REGEX` | No | Optional regex for allowed origins |
| `ENVIRONMENT` | No | Environment label returned by the health endpoint |

The frontend reads `VITE_API_BASE_URL` from `frontend/.env.example`. Do not commit API keys or local `.env` files.

## Testing and CI/CD

Run the same checks used by the repository's GitHub Actions workflow:

```bash
cd backend
ruff check .
pytest -v

cd ..\frontend
npm ci
npm run build
```

`.github/workflows/ci.yml` runs on pushes and pull requests targeting `main` or `master`. The backend job installs Python 3.12 dependencies, sets `FINANCIAL_DATA_MODE=fixture`, runs Ruff, and executes Pytest. The frontend job installs dependencies with `npm ci` on Node.js 20 and runs the TypeScript/Vite production build.

## Deployment

The repository is configured for Vercel:

- `npm --prefix frontend run build` builds the frontend.
- `frontend/dist` is used as the static output directory.
- `api/index.py` exposes the FastAPI application to Vercel's Python runtime.
- `backend/**` is included in the serverless function bundle.
- API, health, documentation, and SPA routes are defined in `vercel.json`.

For a live SEC-backed deployment, configure `FINANCIAL_DATA_MODE=sec`, a compliant `SEC_USER_AGENT`, and the required LLM provider credentials in the Vercel project settings. A fixture-mode deployment does not represent live SEC data.

## Project Structure

```text
bcg-ai-financial-analyst/
+-- api/
|   `-- index.py                  # Vercel FastAPI entrypoint
+-- backend/
|   +-- app/
|   |   +-- api/routes/           # Analysis and placeholder routers
|   |   +-- core/                 # Settings and environment validation
|   |   +-- data/                 # Controlled financial fixtures
|   |   +-- schemas/              # Pydantic request and response models
|   |   `-- services/             # SEC/XBRL, analytics, and LLM services
|   +-- tests/                    # Backend test suite
|   +-- Dockerfile
|   +-- pyproject.toml
|   `-- requirements.txt
+-- frontend/
|   +-- src/
|   |   +-- components/           # Chat, financial, layout, and UI components
|   |   +-- data/                 # Frontend fixture data
|   |   +-- hooks/                # Chat state and API orchestration
|   |   +-- services/             # API client and response mapping
|   |   `-- types/                # TypeScript domain types
|   +-- Dockerfile
|   +-- package.json
|   `-- vite.config.ts
+-- .github/workflows/ci.yml      # Backend and frontend CI
+-- docker-compose.yml             # Local two-container orchestration
+-- requirements.txt               # Vercel Python runtime dependencies
+-- vercel.json                    # Vercel build and rewrite configuration
`-- rulebook.md                    # Repository engineering notes
```

## Design Tradeoffs

- **Deterministic calculations before LLM generation:** improves numeric reliability and auditability, while limiting the LLM to interpretation and explanation.
- **SEC mode plus controlled fixtures:** supports real SEC retrieval while keeping tests deterministic and allowing local development without network access.
- **Gemini primary with Groq fallback:** improves resilience to transient provider failures, but requires separate credentials and does not mask permanent provider errors.
- **Unified Vercel deployment:** simplifies frontend/API routing and production hosting; local development still uses separate backend and frontend processes.
- **Small supported-company set:** keeps entity resolution and data contracts explicit, but does not provide arbitrary-company coverage.
- **In-memory request processing:** keeps the current service simple and stateless; the repository does not implement persistent user accounts, saved analyses, or a database-backed cache.

## Disclaimer

This project is an educational and engineering demonstration, not investment, accounting, tax, or legal advice. SEC-backed values depend on the source data available at request time, while fixture-mode results are synthetic demonstration data. Always review the original filings and consult a qualified professional before making financial decisions.
