# TransformAI Research Annotation Protocol — Benchmark Ground Truth & Verification Claims

**Milestone**: M9B — Human Annotation & Ground-Truth Validation  
**Document Version**: 2.0.0  
**Status**: ACTIVE PROTOCOL  
**Target Evaluation Tracks**:
- **Track 1**: Source Fact Ground Truth for Generation Quality Evaluation ($H_1$ RAG Effect, $H_2$ Structured Context Effect)
- **Track 2**: Verification Benchmark Items for Verifier Evaluation ($H_3$ M6 Verification Quality)

---

## 1. Protocol Overview & Core Research Integrity Rules

This protocol establishes the formal methodology for constructing validated, reproducible research ground truth for both evaluation tracks.

```
                         Source Document (DOC-REAL-XXX.txt)
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
   [TRACK 1: Source Facts]                              [TRACK 2: Verification Claims]
   GroundTruthFact                                      VerificationBenchmarkItem
   - Pure source propositions                           - Contrastive claim evaluation
   - Inherent truth in document                         - 4-Class verdict taxonomy
   - Used for Source Coverage ($SC$)                    - Used for Verifier Macro-F1 ($H_3$)
     and Semantic Preservation ($SP$)
```

### Critical Rules
1. **Human Authority**: All benchmark ground truth must be human-created or human-reviewed. Automated extractions are strictly `CANDIDATE` proposals and never ground truth.
2. **Anti-Circularity in Verification ($H_3$)**: Benchmark ground-truth verification verdicts must be established independently by human annotators. **Under no circumstances may the M6 Claim Verifier, LLMs, or heuristic verifiers generate or approve benchmark ground truth.**
3. **Strict Track Separation**: Source facts (`GroundTruthFact`) and verification benchmark claims (`VerificationBenchmarkItem`) are stored in distinct directories and schemas.
4. **Natural Class Distribution**: No artificial quotas (e.g. 25/25/25/25) are imposed on the 4 verification classes. Annotators classify claims purely on empirical evidence.
5. **FINAL-Only Scoring Gate**: Only items with `annotation_status: "FINAL"` may enter M7/M9C benchmark scoring.

---

## 2. Track 1: Source Fact Annotation Protocol

### 2.1 Objective
Capture the essential factual propositions asserted by the source document to evaluate whether generative transformations preserve source facts without hallucination or omission.

### 2.2 Fact Atomicity Guidelines
1. **Single Predicate**: Each fact must assert exactly one action, property, attribute, or relation.
2. **Explicit Entities**: Replace all ambiguous pronouns ("he", "they", "it", "the firm") with unambiguous named entities (e.g., "Prime Minister Rishi Sunak").
3. **Temporal & Numerical Anchors**: Preserve verbatim numbers, currency symbols, percentages, and dates (e.g., "34.5%", "$1.2 billion", "July 14, 2024").
4. **Context Independence**: The statement must be fully understandable on its own without reading adjacent paragraphs.

### 2.3 Fact Importance & Quantity
- **Guideline**: Annotators should aim for approximately **5–12 high-value facts** per document. This is a quality guideline, not a rigid quota.
- **`HIGH` Importance**: Core thesis, main actions, central entities, critical numerical data.
- **`MEDIUM` Importance**: Supporting context, secondary actions, background details.
- **`LOW` Importance**: Minor tangential remarks, illustrative anecdotes.

### 2.4 Coordinate Mapping Mechanics
Each fact requires precise character offsets in the cleaned `.txt` file:
- `paragraph_idx`: 0-indexed paragraph.
- `sentence_idx`: 0-indexed sentence in paragraph.
- `start_char` & `end_char`: Character offsets from the start of the source file.
- `verbatim_text_span`: Must exactly match `source_text[start_char:end_char]`.

---

## 3. Track 2: Verification Claim Annotation Protocol

### 3.1 Objective
Construct an independent benchmark of atomic claims paired with gold verification verdicts to evaluate the precision, recall, and Macro-F1 of the M6 Claim Verifier ($H_3$).

### 3.2 Verification Verdict Taxonomy & Definitions

1. **`SUPPORTED`**
   - **Definition**: The claim is directly, fully, and unambiguously entailed by the source document.
   - **Criteria**: An objective reader given only the source text would confirm that all asserted predicates, entities, and numbers are verified.

2. **`CONTRADICTED`**
   - **Definition**: The source text contains evidence directly inconsistent with or refuting the claim.
   - **Criteria**: The source explicitly states $X$, but the claim asserts $\neg X$, an altered numerical value, a wrong entity, or an inverted causal relationship.

3. **`PARTIALLY_SUPPORTED`**
   - **Definition**: The claim contains multiple components where at least one is supported by the source, but another is unsupported, distorted, or inaccurate.
   - **Criteria**: The claim is neither completely true nor completely false according to the source.

4. **`INSUFFICIENT_EVIDENCE`**
   - **Definition**: The source document does not contain sufficient evidence to confirm or contradict the claim.
   - **Criteria**: The source is completely silent or lacks key details. **Important**: `INSUFFICIENT_EVIDENCE` is NOT treated as equivalent to false; it reflects an absence of verifiable evidence in the source scope.

---

### 3.3 Claim Origins & Controlled Perturbations

Claims in Track 2 originate from two methods:

#### A. `SOURCE_FACT`
- Directly derived from a finalized Track 1 `GroundTruthFact`.
- Expected Verdict: `SUPPORTED`.

#### B. `CONTROLLED_PERTURBATION`
- A human annotator takes a finalized source fact and applies a systematic, documented modification to create contrastive test cases:
  1. *Numerical Perturbation*: Altering a quantity, percentage, or currency figure (creates `CONTRADICTED`).
  2. *Entity Perturbation*: Swapping an entity with a different or distractor entity (creates `CONTRADICTED`).
  3. *Temporal Perturbation*: Altering a date, order of events, or timeframe (creates `CONTRADICTED`).
  4. *Compound Distortion*: Combining a supported fact with an unsupported assertion (creates `PARTIALLY_SUPPORTED`).
  5. *Extraneous Plausible Claim*: Asserting plausible world knowledge that is not mentioned anywhere in the source document (creates `INSUFFICIENT_EVIDENCE`).

---

## 4. Annotation File Hierarchy & Lifecycle

### 4.1 Lifecycle States
```
UNANNOTATED (Template) 
     ──> Human Extraction / Perturbation (CANDIDATE)
     ──> Peer / Lead Review (REVIEWED)
     ──> Certified Final Ground Truth (FINAL)
```

- `UNANNOTATED`: Empty template.
- `CANDIDATE`: Draft proposition or automated suggestion.
- `REVIEWED`: First-pass human annotation completed and checked.
- `FINAL`: Adjudicated and validated ground truth. Only `FINAL` records enter benchmark scoring.

### 4.2 Storage Layout
- Track 1 Source Facts: `research/datasets/real_research/annotations/DOC-REAL-XXX.facts.json`
- Track 2 Verification Items: `research/datasets/real_research/verification_benchmark/benchmark_manifest.json`

---

## 5. Quality Assurance & Validation Standards

The automated dataset validator enforces:
1. **Verbatim Slice Match**: $\text{source\_text}[\text{start\_char}:\text{end\_char}] == \text{verbatim\_text\_span}$.
2. **Taxonomy Conformance**: Fact types in `FactType`, verdicts in `VerificationVerdict`, origins in `ClaimOrigin`.
3. **Anti-Leakage**: Zero ID and hash overlap between real research files and `development_fixture/`.
4. **Natural Distribution Reporting**: Class counts are reported transparently without artificial balancing.
