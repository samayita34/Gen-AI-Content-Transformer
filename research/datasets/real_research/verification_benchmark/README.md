# Track 2: Real Research Verification Benchmark Workspace

## 1. Overview & Research Integrity Architecture

Track 2 provides the human ground-truth benchmark for evaluating factual verification systems on the real research corpus (`DOC-REAL-001` through `DOC-REAL-060`).

### Core Separation & Protocol Boundary
- **Track 1 vs. Track 2**: Track 1 captures atomic, context-independent source facts substantiated by verbatim text spans. Track 2 consists of verification claims (both positive and negative/contrastive) paired with human-adjudicated ground-truth verdicts (`SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`) and exact source evidence spans.
- **Strict Independence from Verifier**: Ground truth in Track 2 is established exclusively through manual human annotation. No claim verifier (M6 or LLM) or automated scorer is run to generate, filter, or label verification items.
- **Strict Anti-Leakage**: The real research benchmark is completely isolated from the 3-document development fixture (`DOC-DEV-01-TECH`, `DOC-DEV-02-MED`, `DOC-DEV-03-FIN`).
- **No Artificial Balancing Quota**: Natural distribution of verdicts is preserved. Contrastive items are human-reviewed rather than fabricated to meet artificial distribution quotas.
- **Lifecycle Governance**: Items progress through `UNANNOTATED` -> `CANDIDATE` -> `REVIEWED` -> `FINAL`. Only items in `FINAL` state enter benchmark scoring.

---

## 2. Directory Structure

```
research/datasets/real_research/verification_benchmark/
├── README.md                           # This architecture overview
├── annotation_guidelines.md            # Standard operating procedure & verdict definitions
├── benchmark_manifest.json             # Canonical benchmark manifest (0 items initially)
└── batch1_annotation_workspace.json    # Human annotation workspace for Batch 1 (DOC-REAL-001 to 005)
```

---

## 3. Benchmark Item Schema Contract

Every benchmark item adheres to the canonical `VerificationBenchmarkItem` model:

```json
{
  "benchmark_id": "BENCH-REAL-001-01",
  "document_id": "DOC-REAL-001",
  "claim": "Ramalinga Raju was fined $804,000 in connection with the Satyam fraud case.",
  "expected_verdict": "SUPPORTED",
  "evidence_references": [
    {
      "paragraph_idx": 0,
      "sentence_idx": 1,
      "start_char": 183,
      "end_char": 378,
      "verbatim_text_span": "Ramalinga Raju, the former chairman of software services exporter Satyam Computers Services, was also fined $804,000, R.K. Gaur, a spokesman for India's Central Bureau of Investigation, told CNN."
    }
  ],
  "annotation_status": "UNANNOTATED",
  "claim_origin": "SOURCE_FACT",
  "notes": "Derived from Track 1 FACT-REAL01-003 with exact CBI spokesman span grounding.",
  "metadata": {
    "annotator_batch": "batch1",
    "track1_fact_id": "FACT-REAL01-003",
    "perturbation_type": null
  }
}
```

---

## 4. Lifecycle Progression

1. **`UNANNOTATED`**: Workspace template prepared with document context; no human judgment committed.
2. **`CANDIDATE`**: Claim proposition, origin, and initial evidence spans drafted by annotator.
3. **`REVIEWED`**: Secondary review verifying exact verbatim slice equality (`source_text[start:end] == verbatim`), absence of hallucinated facts, and correct verdict assignment.
4. **`FINAL`**: Certified gold item approved for benchmark evaluation.
