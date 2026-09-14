# TransformAI Research Annotation Protocol — Benchmark Ground Truth & Verification Claims

**Milestone**: M9A — Real Research Dataset & Protocol  
**Document Version**: 1.0.0  
**Status**: ACTIVE PROTOCOL  
**Target Evaluation**: $H_1$ (RAG Effect), $H_2$ (Structured Context Effect), $H_3$ (M6 Claim Verification Quality)

---

## 1. Protocol Objective & Research Integrity Principles

This protocol defines the standardized, reproducible methodology for constructing human-verified ground-truth annotations from real-world source articles in the TransformAI research dataset (`research/datasets/real_research/`).

### Critical Research Integrity Rules
1. **Human Authority**: No automated tool, LLM extraction, or heuristic script may establish final ground-truth facts. All ground-truth records MUST be created or reviewed and signed off by a human annotator.
2. **Anti-Circularity in Verification ($H_3$)**: Benchmark ground-truth verification verdicts MUST be assigned by independent human evaluation. **Under no circumstances may the M6 Claim Verifier or any LLM-based verification tool be used to generate or label the ground-truth verification test set.**
3. **Status Isolation**: Only annotations explicitly marked as `status: "FINAL"` may be ingested by the downstream M9B evaluation runner. Candidate suggestions (`*.candidates.json`) or unreviewed templates (`*.facts.json` with `UNANNOTATED` status) must never be treated as ground truth.
4. **Natural Verification Class Distribution**: Human annotators must label claims based solely on empirical evidence without forcing artificial equal-count balancing across the 4 verdict classes.

---

## 2. End-to-End Ground-Truth Annotation Pipeline

```
Source Document (DOC-REAL-XXX.txt)
    │
    ▼
[Phase 1] Human Factual Proposition Identification
    │  Identify objective, verifiable assertions
    ▼
[Phase 2] Source-Span Coordinate Mapping
    │  Extract verbatim substring & record [paragraph_idx, start_char, end_char]
    ▼
[Phase 3] Atomic Deconstruction & Normalization
    │  Split compound propositions; resolve pronouns to canonical entities
    ▼
[Phase 4] Independent Evidence Assessment (Verification Benchmark)
    │  Evaluate claim truth-value against source text independently of any model
    ▼
[Phase 5] Verdict Assignment & Status Finalization
    │  Assign SUPPORTED / CONTRADICTED / PARTIALLY_SUPPORTED / INSUFFICIENT_EVIDENCE
    ▼
Final Research Ground Truth (DOC-REAL-XXX.facts.json, status: "FINAL")
```

---

## 3. Fact Deconstruction Guidelines

### 3.1 What Constitutes an "Atomic Factual Proposition"?
An atomic fact is a minimal, self-contained statement expressing a single predicate-argument relationship that can be independently verified as true or false against the source document.

#### Requirements for Valid Atomic Facts:
1. **Single Predicate**: The statement must express exactly one event, property, or relationship. If a sentence has multiple clauses joined by conjunctions ("and", "while", "because"), it must be split into separate atomic facts.
2. **Explicit Entity References**: All pronouns (e.g., "he", "they", "the company", "it") must be replaced with the unambiguous canonical named entity (e.g., "NASA Administrator Bill Nelson").
3. **Temporal & Numerical Precision**: Explicit dates, numbers, percentages, and currencies must be preserved verbatim or mapped to standard ISO/SI units without estimation or rounding unless stated in the source.
4. **Context Independence**: A reader should be able to evaluate the fact without reading preceding or succeeding sentences.

---

### 3.2 Contrastive Examples: Good vs. Bad Fact Deconstruction

| Source Text Snippet | Bad / Invalid Annotation | Reason for Rejection | Good / Valid Atomic Fact(s) |
| :--- | :--- | :--- | :--- |
| *"On Tuesday, Pfizer announced a $43 billion acquisition of Seagen to boost its cancer drug portfolio."* | *"Pfizer bought Seagen on Tuesday for $43B to help cancer drugs."* | Compound fact, informal abbreviation, imprecise purpose clause. | **Fact 1**: Pfizer announced an acquisition of Seagen on Tuesday.<br>**Fact 2**: The announced acquisition price is $43 billion.<br>**Fact 3**: The acquisition target Seagen develops oncology drugs. |
| *"She was appointed CEO in 2021 after leading the cloud division for five years."* | *"She became CEO in 2021."* | Unresolved pronoun ("She"); missing second predicate. | **Fact 1**: [Person Name] was appointed Chief Executive Officer in 2021.<br>**Fact 2**: [Person Name] led the cloud division for five years prior to 2021. |
| *"The groundbreaking discovery could revolutionize renewable energy storage."* | *"The discovery is revolutionary."* | Subjective marketing modifier; speculative modal ("could"). | **Fact 1**: The research team published a discovery regarding renewable energy storage mechanisms. *(Marked as low importance / speculative)* |

---

## 4. Source-Span Coordinate Mechanics

Every annotated fact must be directly grounded in a continuous or clearly identifiable text span within the source document.

### Required Coordinate Fields:
- `paragraph_idx`: Integer (0-indexed) specifying the paragraph in the cleaned source text.
- `sentence_idx`: Integer (0-indexed) specifying the sentence index within the paragraph.
- `start_char`: Integer (0-indexed) character offset from the very beginning of the source text file.
- `end_char`: Integer (0-indexed) character offset where the span ends.
- `verbatim_text_span`: Exact string copy of `source_text[start_char:end_char]`.

### Verification Rule:
The validation script will assert:
$$\text{source\_text}[\text{start\_char}:\text{end\_char}] == \text{verbatim\_text\_span}$$
Any mismatch in whitespace, punctuation, or capitalization will fail validation.

---

## 5. Verification Claim Taxonomy & Labeling Rules ($H_3$)

To rigorously evaluate the M6 Claim Verifier without bias, verification claims must be classified into one of four mutually exclusive verdicts based purely on independent human evidence assessment:

### 5.1 The Four Verification Verdicts

1. **`SUPPORTED`**
   - **Definition**: The claim is directly and unambiguously entailed by the source text span. All entities, actions, numbers, and relations in the claim are confirmed by the text.
   - **Criteria**: An objective third-party reader given only the source text would agree the statement is factually true according to the text.

2. **`CONTRADICTED`**
   - **Definition**: The claim directly conflicts with or negates a factual assertion in the source text.
   - **Criteria**: The source explicitly states $X$, but the claim asserts $\neg X$, a different numerical value, a wrong entity, or an inverted causal relationship.

3. **`PARTIALLY_SUPPORTED`**
   - **Definition**: The claim contains multiple components or sub-clauses where at least one is supported by the source, but another is inaccurate, unsupported, or distorted.
   - **Criteria**: The claim cannot be affirmed as fully true, nor is it entirely false.

4. **`INSUFFICIENT_EVIDENCE`**
   - **Definition**: The claim asserts facts, statistics, or events that are neither confirmed nor refuted anywhere in the source document.
   - **Criteria**: The source document is completely silent regarding the claim or lacks crucial details needed to render a definitive verdict.

---

## 6. Annotation File Lifecycle & Separation of Concerns

To prevent accidental data leakage or unreviewed candidate ingestion:

### 6.1 Status Hierarchy
- **`UNANNOTATED`**: Initial template file created during dataset preparation. `facts` list is empty (`[]`).
- **`CANDIDATE`**: Automated / heuristic proposals generated as suggestions for human review. Stored strictly in `*.candidates.json` files and NEVER in ground-truth manifests.
- **`REVIEWED`**: Human annotator has extracted and verified facts, but second-pass quality validation is ongoing.
- **`FINAL`**: Certified research ground truth, fully validated against span coordinates and schema rules.

### 6.2 File Naming Conventions
- Clean Source Document: `research/datasets/real_research/source_documents/DOC-REAL-XXX.txt`
- Human Ground Truth: `research/datasets/real_research/annotations/DOC-REAL-XXX.facts.json`
- Optional Candidate Workspace: `research/datasets/real_research/candidates/DOC-REAL-XXX.candidates.json`

---

## 7. Inter-Annotator Agreement & Quality Assurance Protocol

For benchmark reliability:
1. **Dual Annotation Sample**: A randomly selected 20% sample (12 documents across Short, Medium, Long) will be independently annotated by two human annotators.
2. **Agreement Metric**: Inter-annotator agreement on verification verdicts will be computed using Cohen's $\kappa$ (for two annotators) or Fleiss' $\kappa$ (for $>2$ annotators). An agreement score of $\kappa \ge 0.75$ is required for final benchmark certification.
3. **Discrepancy Resolution**: Any disagreement between annotators will be resolved through adjudicated discussion with a lead researcher before marking status as `FINAL`.
