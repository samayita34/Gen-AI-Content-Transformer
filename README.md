# TransformAI: Gen AI Platform for Automated Content Transformation

> **SIH Problem Statement**: SIH26154  
> **Central Research Question**: *How can generative AI transform a common source document into multiple communication formats while preserving factual consistency, semantic meaning, and source-groundedness?*

---

## 1. Project Architecture Overview

```
transform-ai/
├── frontend/               # Next.js 15 (TypeScript + Tailwind CSS + Telemetry UI)
│   ├── src/
│   │   ├── app/            # App Router pages & styles
│   │   ├── components/     # UI Components (SystemStatusCard, etc.)
│   │   ├── lib/            # Type-safe API client
│   │   └── types/          # TypeScript interface definitions
│   └── Dockerfile
├── backend/                # FastAPI (Python 3.13 + SQLAlchemy 2.0 async + Pydantic v2)
│   ├── app/
│   │   ├── api/            # Versioned API routes (/api/v1/health, etc.)
│   │   ├── core/           # Configuration, Database (PostgreSQL + pgvector), Redis
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Decoupled domain services (document, embeddings, generation, verification, evaluation)
│   │   └── workers/        # Asynchronous background job workers
│   ├── tests/              # Pytest automated test suite
│   └── Dockerfile
├── research/               # Research datasets, experiments, benchmarks, papers
│   ├── datasets/
│   ├── experiments/
│   ├── results/
│   └── papers/
├── docker-compose.yml      # Orchestrates PostgreSQL (pgvector), Redis, Backend, Frontend
├── .env.example            # Environment variables template
└── README.md
```

---

## 2. Technology Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Pydantic v2, `pydantic-settings`, SQLAlchemy 2.0 (Async), `asyncpg`, `pgvector`, `redis.asyncio`
- **Database & Search**: PostgreSQL 16 with `pgvector` extension
- **Cache & Message Broker**: Redis 7
- **Testing**: Pytest, Pytest-Asyncio, HTTPX
- **Orchestration**: Docker Compose

---

---

## 3. Document Ingestion & Supported Formats

TransformAI's Document Intelligence layer ingests, cleans, extracts structure, and chunks documents for vectorization:

### Required Milestone 2 Formats
- **PDF (`.pdf`)**: Native page-aware extraction preserving page indices, physical coordinates, and headings via `pypdf`.
- **DOCX (`.docx`)**: Structural paragraph and table extraction preserving heading hierarchies (H1/H2/H3), bullet lists, and table row/column text via `python-docx`.
- **TXT (`.txt`, `.text`)**: Raw plain-text stream parsing with double-newline paragraph segmentation.

### Additional Supported Formats
- **Markdown (`.md`)**: Supported as an additional format via the text/structure ingestion pipeline, preserving markdown headings (`#`, `##`, `###`) and structured lists beyond the core required scope.

---

## 4. API Endpoints (Health & Document Intelligence)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | **Liveness Probe**: Returns basic application metadata, version, and status. |
| `GET` | `/api/v1/health/system` | **Readiness & Diagnostics Probe**: Real-time connectivity and latency checks for PostgreSQL (including `pgvector` presence check) and Redis. |
| `POST` | `/api/v1/documents/upload` | **Document Ingestion**: Accepts multipart file uploads (Required: PDF, DOCX, TXT; Additional: MD), validates format, and queues async parsing & vectorization. |
| `GET` | `/api/v1/documents` | **Document Catalog**: Lists all ingested documents with parsing stats and processing status. |
| `GET` | `/api/v1/documents/{id}` | **Document Metadata**: Returns deep status, page counts, word counts, and structural metadata. |
| `GET` | `/api/v1/documents/{id}/chunks` | **Chunk Provenance**: Returns chunk texts, character counts, token counts, section titles, and page numbers. |
| `GET` | `/docs` | Interactive Swagger API Documentation. |
| `GET` | `/redoc` | OpenAPI ReDoc Documentation. |

---

## 5. Research Benchmarking & Experiments

Milestone 2 includes empirical benchmarking comparing:
- **Method A (Baseline)**: Fixed-size sliding-window chunking (`FixedSizeChunker`).
- **Method B (Proposed)**: Semantic & structure-aware boundary chunking (`StructureAwareChunker`).

To run the comparative experiment and generate telemetry metrics:

```bash
python research/experiments/compare_chunking.py
```

Results are stored in `research/results/chunking_comparison.json`.

### Sample Response: `GET /api/v1/health/system`

```json
{
  "status": "healthy",
  "app_name": "TransformAI",
  "version": "0.1.0",
  "environment": "development",
  "database": {
    "status": "healthy",
    "connected": true,
    "latency_ms": 2.15,
    "pgvector_installed": true,
    "pgvector_version": "0.7.0",
    "error": null
  },
  "redis": {
    "status": "healthy",
    "connected": true,
    "latency_ms": 0.85,
    "error": null
  }
}
```

---

## 6. Running the Platform

### Option A: Docker Compose (Recommended)

1. **Copy Environment Variables**:
   ```bash
   cp .env.example .env
   ```
2. **Build and Start All Services**:
   ```bash
   docker compose up --build
   ```
3. **Access Services**:
   - **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Liveness**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - **System Diagnostics**: [http://localhost:8000/api/v1/health/system](http://localhost:8000/api/v1/health/system)

---

### Option B: Local Development

#### 1. Start Infrastructure (PostgreSQL + Redis)
```bash
docker compose up -d postgres redis
```

#### 2. Start Backend
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 7. Running Backend Automated Tests

```bash
cd backend
pytest -v
```

---

## 8. Project Roadmap

- [x] **Milestone 1**: System Foundation, Docker Compose Orchestration, Database (pgvector) & Redis Integration, Live Health Probes, and Telemetry UI.
- [x] **Milestone 2**: Document Intelligence Pipeline (PDF, DOCX, TXT ingestion, cleaning, structure detection, baseline & structure-aware chunking, SentenceTransformers local embeddings, pgvector storage, and provenance UI).
- [ ] **Milestone 3**: Embedding and Dense/Hybrid Retrieval Pipeline with pgvector similarity search.
- [ ] **Milestone 4**: Provider-Agnostic Generation Pipeline (Executive Summary, Advisory, Presentation + Notes, Storyboard).
- [ ] **Milestone 5**: Factual Verification and Grounding Evaluation Pipeline.
- [ ] **Milestone 6**: End-to-End User Experience & Empirical Research Experiments.
