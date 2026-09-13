# TransformAI: Gen AI Platform for Automated Content Transformation

> **SIH Problem Statement**: SIH26154  
> **Central Research Question**: *How can generative AI transform a common source document into multiple communication formats while preserving factual consistency, semantic meaning, and source-groundedness?*

---

## 1. Project Architecture Overview

```
transform-ai/
├── frontend/               # Next.js 15 (TypeScript + Tailwind CSS + Transformation Studio)
│   ├── src/
│   │   ├── app/            # App Router pages & styles
│   │   ├── components/     # UI Components (SystemStatusCard, SemanticSearchZone, TransformationWorkspace)
│   │   ├── lib/            # Type-safe API client
│   │   └── types/          # TypeScript interface definitions (document, retrieval, generation)
│   └── Dockerfile
├── backend/                # FastAPI (Python 3.13 + SQLAlchemy 2.0 async + Pydantic v2)
│   ├── app/
│   │   ├── api/            # Versioned API routes (/health, /documents, /retrieval, /generation)
│   │   ├── core/           # Configuration, Database (PostgreSQL + pgvector), Redis
│   │   ├── models/         # SQLAlchemy ORM models (Document, DocumentChunk)
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Decoupled domain services (document, embeddings, retrieval, generation)
│   │   └── workers/        # Asynchronous background job workers
│   ├── tests/              # Pytest automated test suite (37 passing tests)
│   └── Dockerfile
├── research/               # Research datasets, experiments, benchmarks, papers
│   ├── datasets/
│   ├── experiments/        # compare_chunking.py, compare_retrieval.py, compare_generation.py
│   ├── results/            # chunking_comparison.json, retrieval_comparison.json, generation_comparison.json
│   └── papers/
├── docker-compose.yml      # Orchestrates PostgreSQL (pgvector), Redis, Backend, Frontend
├── .env.example            # Environment variables template
└── README.md
```

---

## 2. Technology Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Pydantic v2, `pydantic-settings`, SQLAlchemy 2.0 (Async), `asyncpg`, `pgvector`, `redis.asyncio`
- **Database & Search**: PostgreSQL 16 with `pgvector` extension (Vector indexing & cosine similarity)
- **Cache & Message Broker**: Redis 7
- **Embeddings**: Local `SentenceTransformers` (`all-MiniLM-L6-v2`, 384 dimensions)
- **LLM Layer**: Provider-agnostic abstraction (`BaseLLMProvider` supporting Google Gemini, OpenAI-compatible APIs, and offline deterministic Mock)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX
- **Orchestration**: Docker Compose

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

## 4. RAG Retrieval & Context Normalization (Milestone 3)

The retrieval and context normalization tier bridges raw vector search with downstream generation modules:

```
QUERY ──> DENSE EMBEDDING ──> PGVECTOR COSINE SEARCH ──> RANKED CHUNKS ──> CONTEXT NORMALIZER ──> NORMALIZED CONTEXT
```

### Cosine Similarity Metric
Retrieval computes cosine distance via pgvector's `<=>` operator and converts it to a normalized similarity score:
$$\text{Cosine Similarity} = 1 - \text{Cosine Distance}$$
- **Range**: `0.0` to `1.0`.
- **Interpretation**: Higher values represent greater semantic alignment. Negative thresholds are rejected.

---

## 5. Multi-Format Generative AI (Milestone 4)

TransformAI synthesizes the same source document into four communication formats using source-grounded generation with anti-fabrication constraints:

```
SOURCE DOCUMENT ──> RETRIEVAL (pgvector) ──> NORMALIZED CONTEXT ──> GENERATION ROUTER ──> STRUCTURED FORMAT
```

### Supported Output Formats

1. **Executive Summary**:
   - High-level strategic overview, core findings, grounded facts, operational implications, and conclusions.
2. **Advisory & Briefing**:
   - Current situation, key information, risks/considerations, grounded recommended actions, and important notes.
   - *Anti-Fabrication Constraint*: If recommendations are absent from the source, the model explicitly states that no recommendations were present in the source rather than fabricating them.
3. **Presentation Deck + Speaker Notes**:
   - Slide-by-slide narrative structure with slide numbers, titles, bullet points, and presenter spoken notes.
4. **Video Script + Storyboard**:
   - Multi-scene video script with visual descriptions, voiceover narration, and on-screen text banners.

### Configurable Generation Parameters
- **Audience**: `executive`, `technical`, `general_public`, `academic`, `operational`
- **Tone**: `professional`, `concise`, `formal`, `explanatory`, `neutral`
- **Detail Level**: `brief`, `moderate`, `detailed`
- **Communication Objective**: `inform`, `brief`, `explain`, `persuade`, `prepare_action`
- **Language**: Configurable output language (default English)
- **Length Constraint**: Optional bounds (e.g. "5-7 slides", "under 300 words")

### Prompt Grounding & Injection Mitigation
- System instructions strictly isolate the source context inside `<SOURCE_DATA>` XML-like blocks, treating source text as DATA rather than executable instructions.
- Generation utilizes strict JSON schema enforcement with Pydantic validation.

> [!NOTE]
> Factual consistency and hallucination reduction are not yet experimentally established. Automated verification is planned for Milestone 6 and quantitative evaluation for Milestone 7.

---

## 6. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | **Liveness Probe**: Application metadata, version, and status. |
| `GET` | `/api/v1/health/system` | **Diagnostics Probe**: Connectivity and latency for PostgreSQL (pgvector check) and Redis. |
| `POST` | `/api/v1/documents/upload` | **Document Ingestion**: Accepts PDF, DOCX, TXT (and MD) files and queues async vectorization. |
| `GET` | `/api/v1/documents` | **Document Catalog**: Lists all ingested documents with parsing stats. |
| `GET` | `/api/v1/documents/{id}` | **Document Metadata**: Deep ingestion status, word count, character count, and page counts. |
| `GET` | `/api/v1/documents/{id}/chunks` | **Chunk Provenance**: Returns chunk texts, tokens, section titles, and page numbers. |
| `POST` | `/api/v1/retrieval/search` | **Vector Retrieval**: Performs pgvector dense cosine search with optional document scope, top-k, and threshold filtering. |
| `POST` | `/api/v1/retrieval/context` | **Normalized Context**: Returns source-grounded context model with extracted facts, entities, and citations. |
| `POST` | `/api/v1/generation/transform` | **Content Transformation**: Transforms source documents into Executive Summary, Advisory, Presentation, or Video Script. |
| `GET` | `/api/v1/generation/formats` | **Formats Catalog**: Lists available output types, audiences, tones, and parameter options. |
| `GET` | `/docs` | Interactive Swagger API Documentation. |
| `GET` | `/redoc` | OpenAPI ReDoc Documentation. |

---

## 7. Research Benchmarking & Experiments

The `research/experiments/` suite provides empirical benchmarking:

1. **Chunking Comparison** (`research/experiments/compare_chunking.py`):
   - Compares Method A (Fixed-Size) vs. Method B (Structure-Aware).
   - Output: `research/results/chunking_comparison.json`.

2. **Vector Retrieval Comparison** (`research/experiments/compare_retrieval.py`):
   - Compares retrieval latency, score distributions, and section provenance across fixed-size vs. structure-aware indices.
   - Output: `research/results/retrieval_comparison.json`.

3. **Multi-Format Generation Comparison** (`research/experiments/compare_generation.py`):
   - Evaluates:
     - **Method A**: Direct Prompting (No RAG, No Normalization)
     - **Method B**: Basic RAG (Retrieved chunks, No Normalization)
     - **Method C**: RAG + Normalized Context (Retrieved chunks + NormalizedContext)
   - Output: `research/results/generation_comparison.json`.

To run generation experiments:
```bash
python research/experiments/compare_generation.py
```

---

## 8. LLM Provider Configuration

Configure LLM settings in `.env`:

```env
# Provider Selection: "gemini", "openai_compatible", or "mock"
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here

# For OpenAI or OpenAI-Compatible APIs (Groq, Ollama, DeepSeek, vLLM):
# LLM_PROVIDER=openai_compatible
# LLM_MODEL=gpt-4o-mini
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_API_BASE=https://api.openai.com/v1
```

---

## 9. Running the Platform

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

## 10. Running Backend Automated Tests

```bash
cd backend
pytest -v
```

---

## 11. Project Roadmap

- [x] **Milestone 1**: System Foundation, Docker Compose Orchestration, Database (pgvector) & Redis Integration, Live Health Probes, and Telemetry UI.
- [x] **Milestone 2**: Document Intelligence Pipeline (PDF, DOCX, TXT ingestion, cleaning, structure detection, baseline & structure-aware chunking, SentenceTransformers local embeddings, pgvector storage, and provenance UI).
- [x] **Milestone 3**: RAG Retrieval & Context Normalization (PgVectorRetriever, cosine similarity search, deterministic ContextNormalizer, empirical compare_retrieval experiment, and semantic search UI).
- [x] **Milestone 4**: Multi-Format Generative AI (Provider-agnostic LLM layer, Executive Summary, Advisory, Presentation + Speaker Notes, Video Script + Storyboard, Transformation Studio UI, and compare_generation benchmark).
- [ ] **Milestone 5**: Verification Agent & Grounding Evaluation Pipeline.
- [ ] **Milestone 6**: End-to-End User Experience & Empirical Research Experiments.
