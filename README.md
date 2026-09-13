# TransformAI: Gen AI Platform for Automated Content Transformation

> **SIH Problem Statement**: SIH26154  
> **Central Research Question**: *How can generative AI transform a common source document into multiple communication formats while preserving factual consistency, semantic meaning, and source-groundedness?*  
> **Multimodal Research Dimension (Milestone 5)**: *Can heterogeneous source modalities be converted into a common source representation that can be processed by the same retrieval and generation pipeline?*  
> **Verification Research Dimension (Milestone 6)**: *How can generated claims be automatically verified against source evidence?*  
> 
> *Notice: Verification assesses source-grounded entailment, contradiction, and evidence sufficiency against retrieved source passages. It does not establish absolute real-world truth or formal NLI benchmark performance.*

---

## 1. Project Architecture Overview

```
transform-ai/
├── frontend/               # Next.js 15 (TypeScript + Tailwind CSS + Transformation Studio)
│   ├── src/
│   │   ├── app/            # App Router pages & styles
│   │   ├── components/     # UI Components (SystemStatusCard, SemanticSearchZone, TransformationWorkspace, DocumentUploadZone, DocumentDetailView)
│   │   ├── lib/            # Type-safe API client
│   │   └── types/          # TypeScript interface definitions (document, retrieval, generation)
│   └── Dockerfile
├── backend/                # FastAPI (Python 3.13 + SQLAlchemy 2.0 async + Pydantic v2)
│   ├── app/
│   │   ├── api/            # Versioned API routes (/health, /documents, /retrieval, /generation)
│   │   ├── core/           # Configuration, Database (PostgreSQL + pgvector), Redis
│   │   ├── models/         # SQLAlchemy ORM models (Document, DocumentChunk)
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Decoupled domain services (document, embeddings, retrieval, generation, multimodal)
│   │   └── workers/        # Asynchronous background job workers
│   ├── tests/              # Pytest automated test suite (51 passing tests)
│   └── Dockerfile
├── research/               # Research datasets, experiments, benchmarks, papers
│   ├── datasets/
│   ├── experiments/        # compare_chunking.py, compare_retrieval.py, compare_generation.py, compare_multimodal_ingestion.py
│   ├── results/            # chunking_comparison.json, retrieval_comparison.json, generation_comparison.json, multimodal_ingestion_comparison.json
│   └── papers/
├── docker-compose.yml      # Orchestrates PostgreSQL (pgvector), Redis, Backend, Frontend
├── .env.example            # Environment variables template
└── README.md
```

---

## 2. Technology Stack & Resource Requirements

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Pydantic v2, `pydantic-settings`, SQLAlchemy 2.0 (Async), `asyncpg`, `pgvector`, `redis.asyncio`
- **Database & Search**: PostgreSQL 16 with `pgvector` extension (Vector indexing & cosine similarity)
- **Cache & Message Broker**: Redis 7
- **Embeddings**: Local `SentenceTransformers` (`all-MiniLM-L6-v2`, 384 dimensions)
- **LLM Layer**: Provider-agnostic abstraction (`BaseLLMProvider` supporting Google Gemini, OpenAI-compatible APIs, and offline deterministic Mock)
- **Multimodal Engines**: Provider-agnostic `BaseOCRProvider` and `BaseTranscriptionProvider` (supporting Gemini Vision/Audio, local providers, and offline deterministic Mocks)
- **Hardware & Resource Requirements**:
  - **CPU-Safe**: Operates completely on standard CPU environments with no GPU requirements.
  - **Offline/CI Capable**: Defaults to `mock` providers so tests and local development require zero paid API credentials.
  - **System Dependencies**: Standard Python 3.13+ runtime. System-level FFmpeg is optional for advanced media conversions, but core container decoding runs natively using standard library streams.
- **Testing**: Pytest, Pytest-Asyncio, HTTPX (65 passing tests)
- **Orchestration**: Docker Compose

---

## 3. Verification Agent Architecture (Milestone 6)

The Verification Agent independently validates claim-level groundedness of generated transformation outputs against the original source documents.

```
                  TRANSFORMATION OUTPUT
      (Executive Summary / Advisory / Presentation / Video Script)
                                │
                                ▼
                       CLAIM EXTRACTION
              - Rule-based & structural decomposition
              - Generates atomic factual propositions
                                │
                                ▼
                      CLAIM NORMALIZATION
              - Formulates independent retrieval queries
                                │
                                ▼
                 INDEPENDENT EVIDENCE RETRIEVAL
              - Queries PgVectorRetriever directly against original indexed source
              - Strict independence: DOES NOT reuse generation-time citations
                                │
                                ▼
                 CLAIM–EVIDENCE VERIFICATION
              - LLM-based claim–evidence verifier (BaseVerificationJudge)
              - Classifies into 4 mutually exclusive verdicts:
                • SUPPORTED: Evidence sufficiently entails the claim.
                • CONTRADICTED: Evidence clearly conflicts with the claim.
                • PARTIALLY_SUPPORTED: Evidence supports only part of compound assertion.
                • INSUFFICIENT_EVIDENCE: Lack of evidence to establish/refute (never treated as contradiction).
                                │
                                ▼
                       VERIFICATION REPORT
              - Operational Verification Summary (raw counts only):
                total_claims, supported_claims, contradicted_claims,
                partially_supported_claims, insufficient_evidence_claims
              - Full provenance preservation (page, timestamp, similarity score)
              - Interactive UI claim inspector with verdict filtering
```

> **Operational Notice**: Milestone 6 provides operational claim-level verification and telemetry. It intentionally exposes raw claim counts rather than pseudo-quantitative percentages or benchmark scores. Formal precision, recall, F1, and factual-consistency benchmark evaluation are deferred to Milestone 7.

---

## 4. Supported Modalities & Multimodal Ingestion Architecture

```
                               SOURCE INGESTION
 ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
 │ TEXT / DOCS  │     │    IMAGE     │     │    AUDIO     │     │    VIDEO     │
 │PDF, DOCX, TXT│     │PNG, JPG, WEBP│     │WAV, MP3, M4A │     │MP4, MOV, WEBM│
 └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
        │                    │                    │                    │
        │ Native Text        │ Pillow + OCR       │ Native + STT       │ Audio STT +
        │ Parsers            │ Engine             │ Engine             │ Scene Headers
        ▼                    ▼                    ▼                    ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                COMMON NORMALIZED REPRESENTATION (ParsedDocument)             │
 │  - elements: List[DocumentElement] (OCR_BLOCK, TRANSCRIPT_SEGMENT, etc.)    │
 │  - provenance: page_number, section_title, timestamps, bounding_boxes       │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
                      Deterministic Cleaning & Structure Detection
                                        │
                                        ▼
                           Structure-Aware Chunking
                                        │
                                        ▼
                      Dense Embeddings (SentenceTransformers)
                                        │
                                        ▼
                           PostgreSQL (pgvector)
                                        │
                                        ▼
                   Vector Retrieval + Context Normalization
                                        │
                                        ▼
                    Multi-Format Content Transformation Router
```

### Supported Source Formats

1. **Text Documents**:
   - **PDF (`.pdf`)**: Native page-aware extraction preserving page indices, physical coordinates, and headings via `pypdf`.
   - **DOCX (`.docx`)**: Structural paragraph and table extraction preserving heading hierarchies (H1/H2/H3), bullet lists, and tables via `python-docx`.
   - **TXT (`.txt`, `.text`, `.md`)**: Raw stream parsing with deterministic paragraph segmentation.

2. **Visual Images**:
   - **Formats**: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`.
   - **OCR Approach**: Technical image decoding and dimension validation via Pillow; text recognition delegated to `BaseOCRProvider`. Spatial bounding boxes and provider confidence scores are recorded only if supplied by the provider (stored as `null` otherwise without fabrication).

3. **Audio Recordings**:
   - **Formats**: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`.
   - **Speech-to-Text Approach**: Audio container metadata inspection via native modules; speech transcription delegated to `BaseTranscriptionProvider`. Timestamped segments are formatted as `[MM:SS - MM:SS]`. Speaker diarization is preserved only if exposed by the engine (stored as `null` otherwise).

4. **Video Recordings**:
   - **Formats**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`.
   - **Video Approach**: Lightweight composed pipeline transcribing the audio dialogue track and sampling key scene overview structural headers without expensive frame-by-frame analysis or full multimodal LLM video understanding.

---

## 4. Multimodal Provenance & Anti-Fabrication Guarantees

Every downstream chunk and citation retains explicit origin traceability:
- **PDF Documents**: Page numbers, section titles, and character offsets.
- **Images**: Source filename, image dimensions, spatial bounding boxes (`spatial_bounds`), and genuine OCR confidence scores.
- **Audio**: Source filename, duration, provider timestamps (`[MM:SS - MM:SS]`), and speaker identity where diarized.
- **Video**: Source filename, scene index, dialogue timestamps, and container metadata.

> [!IMPORTANT]
> **Anti-Fabrication & Strict Grounding Rules**:
> 1. Pillow and container readers are strictly used for image/audio structural inspection, never misrepresented as OCR or transcription engines.
> 2. Missing confidence scores, speaker identities, or bounding boxes remain `null`/`None` rather than being synthetically generated.
> 3. If an extraction provider fails or is inactive, the system raises `ExtractionUnavailableError` and marks the document as `FAILED` rather than silently succeeding with empty text.

---

## 5. RAG Retrieval & Context Normalization (Milestone 3)

The retrieval and context normalization tier bridges vector search with downstream generation modules:

```
QUERY ──> DENSE EMBEDDING ──> PGVECTOR COSINE SEARCH ──> RANKED CHUNKS ──> CONTEXT NORMALIZER ──> NORMALIZED CONTEXT
```

### Cosine Similarity Metric
Retrieval computes cosine distance via pgvector's `<=>` operator and converts it to a normalized similarity score:
$$\text{Cosine Similarity} = 1 - \text{Cosine Distance}$$
- **Range**: `0.0` to `1.0`.
- **Interpretation**: Higher values represent greater semantic alignment. Negative thresholds are rejected.

---

## 6. Multi-Format Generative AI (Milestone 4)

TransformAI synthesizes any ingested source document into four structured communication formats using source-grounded generation with anti-fabrication constraints:

```
SOURCE DOCUMENT ──> RETRIEVAL (pgvector) ──> NORMALIZED CONTEXT ──> GENERATION ROUTER ──> STRUCTURED FORMAT
```

### Supported Output Formats

1. **Executive Summary**:
   - High-level strategic overview, core findings, grounded facts, operational implications, and conclusions.
2. **Advisory & Briefing**:
   - Current situation, key information, risks/considerations, grounded recommended actions, and important notes.
3. **Presentation Deck + Speaker Notes**:
   - Slide-by-slide narrative structure with slide numbers, titles, bullet points, and presenter spoken notes.
4. **Video Script + Storyboard**:
   - Multi-scene video script with visual descriptions, voiceover narration, and on-screen text banners.

---

## 7. Verification Agent & Claim-Level Grounding (Milestone 6)

The Claim-Level Verification Agent independently validates synthesized multi-format outputs against original source material, ensuring verifiable grounding and eliminating ungrounded hallucinations.

```
GENERATED OUTPUT
       │
       ▼
CLAIM EXTRACTION ────────► BaseClaimExtractor (LLMClaimExtractor / MockClaimExtractor)
       │                    Extracts discrete atomic propositions
       ▼
CLAIM NORMALIZATION ─────► ClaimNormalizer (NFKC, control char removal, numbers/dates/units preserved)
       │                    Standardizes query string while preserving verbatim claim
       ▼
INDEPENDENT RETRIEVAL ───► PgVectorRetriever (Queries pgvector chunks independently per claim)
       │                    Never reuses generation-time citations or context
       ▼
VERIFICATION JUDGE ──────► BaseClaimVerifier (LLMClaimVerifier / MockClaimVerifier)
       │                    Input Sandboxing (<GENERATED_CLAIM_DATA> & <SOURCE_EVIDENCE_DATA>)
       ▼
VERIFICATION REPORT ─────► Structured Report (Raw counts: total, supported, contradicted, partial, insufficient)
```

### Why Verification is Decoupled from Generation
1. **Eliminating Self-Confirmation Bias**: A model evaluating its own ungrounded output using generation-time context suffers from circular reasoning.
2. **Independent Evidence Discovery**: The verification engine queries `pgvector` afresh using the normalized claim as an independent query, discovering corroborating or refuting chunks that were not included in the original generation prompt.
3. **Defense Against Adversarial Injections**: Treating both generated claims and retrieved passages strictly as untrusted passive data within XML sandboxes prevents prompt injection overrides.

### 4-Verdict Classification Taxonomy
- **`SUPPORTED`**: The independently retrieved source chunks fully entail the complete atomic claim.
- **`CONTRADICTED`**: The retrieved source chunks clearly refute the claim, or key factual details (numbers, percentages, dates, units, entities) conflict with established source facts.
- **`PARTIALLY_SUPPORTED`**: For compound assertions containing multiple propositions where only a subset is corroborated by source evidence.
- **`INSUFFICIENT_EVIDENCE`**: The source material does not contain enough context to confirm or refute the claim. **Lack of evidence is never treated as a contradiction.**

### Multimodal Compatibility & Unified Representation
Verification operates over the common normalized representation (`DocumentElement` / `DocumentChunk` with `pgvector`) established in Milestone 5:
- **Audio & Video Sources**: Preserves temporal provenance (`timestamp_start_sec`, `timestamp_end_sec`, `formatted_timestamp` e.g. `[01:25 - 01:55]`).
- **Image Sources**: Preserves spatial bounding boxes and OCR confidence.
- **Text & PDF Sources**: Preserves section titles and page numbers.

### Research Rigor & M7 Boundary Notice
> [!NOTE]
> Milestone 6 focuses exclusively on the independent verification architecture and operational telemetry (latencies, claim counts, chunk counts, verdict distributions). Quantitative benchmark metrics (Precision, Recall, F1, Hallucination Rate, Factual Consistency Percentage) are **deferred to Milestone 7**, which introduces labeled evaluation datasets and ground truth.

---

## 8. Security, Safe File Validation & Storage

- **Validation Beyond Extensions**: Validates file size, byte signatures, and format boundaries rather than trusting client-provided MIME strings or metadata.
- **Path Traversal Protection**: Uploaded files are stored using securely generated UUID storage keys (`uuid.uuid4().hex + ext`) via `LocalDocumentStorage` rather than raw user-supplied filesystem paths.
- **Modality-Specific File Size Limits**:
  - Text Documents: 15 MB
  - Visual Images: 20 MB
  - Audio Recordings: 50 MB
  - Video Recordings: 100 MB
- **Temporary Stream Cleanup**: Media processing uses in-memory `io.BytesIO` streams and temporary execution buffers with deterministic lifecycle cleanup, preventing disk exhaustion.

---

## 9. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | **Liveness Probe**: Application metadata, version, and status. |
| `GET` | `/api/v1/health/system` | **Diagnostics Probe**: Connectivity and latency for PostgreSQL (pgvector) and Redis. |
| `POST` | `/api/v1/documents/upload` | **Multimodal Ingestion**: Accepts Text, Image, Audio, or Video files and queues async vectorization. |
| `GET` | `/api/v1/documents` | **Document Catalog**: Lists all ingested documents with parsing stats. |
| `GET` | `/api/v1/documents/{id}` | **Document Metadata**: Deep ingestion status, modality, duration, word count, and character count. |
| `GET` | `/api/v1/documents/{id}/chunks` | **Chunk Provenance**: Returns chunk texts, tokens, section titles, timestamps, and page numbers. |
| `POST` | `/api/v1/retrieval/search` | **Vector Retrieval**: Performs pgvector dense cosine search with optional document scope, top-k, and threshold filtering. |
| `POST` | `/api/v1/retrieval/context` | **Normalized Context**: Returns source-grounded context model with extracted facts, entities, and citations. |
| `POST` | `/api/v1/generation/transform` | **Content Transformation**: Transforms source documents into Executive Summary, Advisory, Presentation, or Video Script. |
| `GET` | `/api/v1/generation/formats` | **Formats Catalog**: Lists available output types, audiences, tones, and parameter options. |
| `POST` | `/api/v1/verification/verify` | **Claim-Level Grounded Verification**: Deconstructs output into atomic claims, retrieves independent evidence from pgvector, and evaluates support/contradiction. |
| `GET` | `/api/v1/verification/options` | **Verification Options**: Lists supported verifier judges, allowed verdicts taxonomy, and extraction formats. |
| `GET` | `/docs` | Interactive Swagger API Documentation. |
| `GET` | `/redoc` | OpenAPI ReDoc Documentation. |

---

## 10. Research Benchmarking & Experiments

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

4. **Multimodal Ingestion Benchmark** (`research/experiments/compare_multimodal_ingestion.py`):
   - Measures operational telemetry, parsing latency, chunking overhead, embedding generation, and downstream generation compatibility across Text, Image, Audio, and Video sources.
   - Output: `research/results/multimodal_ingestion_comparison.json`.

5. **Verification Approaches Comparison** (`research/experiments/compare_verification.py`):
   - Compares operational latency and retrieval telemetry across:
     - **Method 0**: No Verification (Baseline)
     - **Method 1**: Whole-Output Retrieval + Verification (Coarse)
     - **Method 2**: Structured Atomic Claim Verification (Fine-Grained Claim Extraction + Independent Retrieval + 4-Verdict Classification)
   - Output: `research/results/verification_comparison.json`.

To run the verification comparison benchmark:
```bash
python research/experiments/compare_verification.py
```

---

## 10. Provider Configuration

Configure LLM, OCR, and Transcription settings in `.env`:

```env
# LLM Provider Selection: "gemini", "openai_compatible", or "mock"
LLM_PROVIDER=mock
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here

# OCR Provider: "gemini_vision", "tesseract", or "mock"
OCR_PROVIDER=mock
OCR_MODEL=gemini-2.5-flash
OCR_TIMEOUT_SECONDS=60

# Transcription Provider: "gemini_audio", "whisper", or "mock"
TRANSCRIPTION_PROVIDER=mock
TRANSCRIPTION_MODEL=gemini-2.5-flash
TRANSCRIPTION_LANGUAGE=en
TRANSCRIPTION_TIMEOUT_SECONDS=120

# Modality File Limits (in bytes)
MAX_TEXT_FILE_SIZE_BYTES=15728640     # 15 MB
MAX_IMAGE_FILE_SIZE_BYTES=20971520    # 20 MB
MAX_AUDIO_FILE_SIZE_BYTES=52428800    # 50 MB
MAX_VIDEO_FILE_SIZE_BYTES=104857600   # 100 MB
```

---

## 11. System Limitations & Scope Boundaries

The following capabilities are explicitly positioned across project milestones:
- **No Multimodal Vision-Language LLM Generation**: LLMs do not receive raw video or audio frames directly for generative synthesis; all sources are deterministically normalized into `DocumentElement`s first.
- **No Frame-by-Frame Video Vision Pipelines**: Video processing transcribes the dialogue audio track and extracts sampled scene headers without heavy per-frame computer vision.
- **No Fabricated Quality Metrics**: WER/CER, OCR accuracy, and factual consistency percentages are not computed without paired ground-truth benchmark datasets.
- **Milestone Boundaries**:
  - **Milestone 6 (Completed)**: Claim-level verification agent, independent vector evidence retrieval, 4-verdict taxonomy, and operational telemetry.
  - **Milestone 7 (Upcoming)**: Formal research evaluation, quantitative benchmarks (Precision, Recall, F1, Factual Consistency Rate), cross-modal semantic drift metrics, and research publication artifacts.

---

## 12. Running the Platform

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

## 13. Running Automated Tests

```bash
cd backend
pytest -v
```

---

## 14. Project Roadmap

- [x] **Milestone 1**: System Foundation, Docker Compose Orchestration, Database (pgvector) & Redis Integration, Live Health Probes, and Telemetry UI.
- [x] **Milestone 2**: Document Intelligence Pipeline (PDF, DOCX, TXT ingestion, cleaning, structure detection, baseline & structure-aware chunking, SentenceTransformers local embeddings, pgvector storage, and provenance UI).
- [x] **Milestone 3**: RAG Retrieval & Context Normalization (PgVectorRetriever, cosine similarity search, deterministic ContextNormalizer, empirical compare_retrieval experiment, and semantic search UI).
- [x] **Milestone 4**: Multi-Format Generative AI (Provider-agnostic LLM layer, Executive Summary, Advisory, Presentation + Speaker Notes, Video Script + Storyboard, Transformation Studio UI, and compare_generation benchmark).
- [x] **Milestone 5**: Multimodal Ingestion (Images via OCR, Audio via Speech-to-Text, Video via Audio Track Transcription + Sampled Scene Headers into Unified Common Representation).
- [x] **Milestone 6**: Verification Agent (Independent Evidence Retrieval, 4-Verdict Classification, Provenance Preservation, Verification Studio UI, and compare_verification experiment).
- [ ] **Milestone 7**: Research Evaluation & Benchmarking.
