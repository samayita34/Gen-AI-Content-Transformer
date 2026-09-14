# Track 2 Verification Benchmark: Human Annotation Guidelines

**Version**: 1.0.0  
**Target Corpus**: Real Research Documents (`DOC-REAL-001` through `DOC-REAL-060`)  
**Standard**: Strict Textual Entailment & Multi-Span Grounding  

---

## 1. Core Principles

1. **Human Ground-Truth Authority**: All verification items, claims, verdicts, and evidence citations must be established exclusively by human annotators reading the primary source document.
2. **Zero Verifier Contamination**: Never invoke the M6 claim verifier or LLM prompting to decide or generate verdicts, claims, or evidence spans.
3. **No External Knowledge**: Evaluate claims strictly against what is contained in the source document.
4. **Natural Verdict Distribution**: Do not artificially enforce equal 25% distribution quotas among verdicts.

---

## 2. Verification Verdict Definitions

Every claim must be categorized into exactly one of four canonical verdicts:

### `SUPPORTED`
- **Definition**: The cited source text provides clear, direct, and sufficient evidence establishing the truth of the entire claim.
- **Rule**: All sub-propositions, entities, dates, numbers, and relationships in the claim must be fully entailed by the cited evidence span(s).

### `CONTRADICTED`
- **Definition**: The source text contains explicit statements or facts that directly conflict with or refute the claim.
- **Rule**: The cited evidence span must demonstrate that the claim cannot be true given the source text (e.g. claim says "15 years" while source says "7 years").

### `PARTIALLY_SUPPORTED`
- **Definition**: The source supports one substantive part of the claim, but another substantive part is either unsupported, missing, or contradictory.
- **Rule**: Used when compound or multi-aspect claims blend accurate source statements with unverified or inaccurate assertions.

### `INSUFFICIENT_EVIDENCE`
- **Definition**: The source document does not contain adequate evidence to confirm or refute the claim.
- **Rule**: This does **not** mean the claim is false in the real world; it means the source document is silent, vague, or lacks the necessary facts to establish truth or falsity.

---

## 3. Claim Origins

### `SOURCE_FACT`
- A claim directly derived from a finalized Track 1 source fact.
- Represents positive test cases where the claim reflects verified source information.
- Generally assigned `SUPPORTED`, unless modified.

### `CONTROLLED_PERTURBATION`
- A contrastive test case constructed by introducing a specific, deliberate modification into a source-derived claim.
- **Perturbation Categories**:
  - *Numerical perturbation*: altering quantities, monetary amounts, or ages (e.g. $804,000 -> $500,000).
  - *Entity perturbation*: replacing subject, organization, or location with a distractor (e.g. Satyam -> Infosys).
  - *Temporal perturbation*: altering years, dates, or sequences (e.g. 2009 -> 2015).
  - *Attributional perturbation*: attributing a statement to the wrong entity or changing direct quote context.
  - *Extrapolation / Unsupported*: adding plausible external facts not present in the source.
- **Human Adjudication Requirement**: Perturbations must be manually adjudicated. Do not assume every perturbation is automatically `CONTRADICTED`; a missing fact may yield `INSUFFICIENT_EVIDENCE` or `PARTIALLY_SUPPORTED`.

---

## 4. Evidence Reference Rules

Every benchmark item must provide `evidence_references` (`List[SourceReferenceSpan]`):
1. **Verbatim Match**: `verbatim_text_span` must be an exact substring of the referenced source document.
2. **Coordinate Exactness**: `source_text[start_char:end_char] == verbatim_text_span` must hold true with zero character drift.
3. **No Generated Citations**: Never cite generated outputs, model summaries, or external URLs.
4. **No Track 1 Citation Reuse as Source**: Citing Track 1 propositions is forbidden; evidence references must point directly to character offsets in the raw source document text.
5. **Multi-Span Continuity**: When evidence spans across discontinuous sentences or paragraphs to establish co-reference, include multiple `SourceReferenceSpan` objects in `evidence_references`.

---

## 5. Lifecycle Workflow

```
[ UNANNOTATED ] -> [ CANDIDATE ] -> [ REVIEWED ] -> [ FINAL ]
```

1. **UNANNOTATED**: Initial state in workspace.
2. **CANDIDATE**: Annotator creates claim, assigns origin, preliminary verdict, and evidence spans.
3. **REVIEWED**: Checked for exact span slices, absence of external knowledge, and logical entailment.
4. **FINAL**: Certified ground truth ready for benchmark evaluation.
