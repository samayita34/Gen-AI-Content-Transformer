# FINAL RESEARCH RESULTS REPORT

**Project**: TransformAI — Source-Grounded Generative AI for Multi-Format Content Transformation  
**Research Track**: Milestone 7 Comprehensive Empirical Evaluation  
**Evaluation Date**: September 2026  
**Status**: COMPLETE (Authoritative Final Package)

---

## 1. Executive Research Summary

This report consolidates the empirical results of the TransformAI research program, evaluating automated, source-grounded content transformation across multi-format outputs and independent claim verification. The research evaluates two empirical tracks:

1. **Track 1 (Generation Quality)**: A factorial experiment comprising $N = 60$ live generation runs (5 canonical source documents $\times$ 4 communication formats $\times$ 3 generation methods) evaluated against 67 human-annotated `FINAL` ground-truth factual propositions.
2. **Track 2 (Verification Quality)**: An independent 4-class classification benchmark comprising $N = 25$ `FINAL` benchmark items evaluated using the M6 LLM-based claim verifier.
3. **Track 3 (Operational Telemetry)**: System-level latency profiling across transformation pipelines and verification workloads.

All experiments were executed with deterministic zero-billing local execution using Ollama (`llama3.2`) and local dense vector representations (`all-MiniLM-L6-v2`).

---

## 2. Research Question

> **Primary Research Question**:  
> *How can generative AI transform a common source document into multiple communication formats while preserving factual consistency, semantic meaning, and source-groundedness?*

Sub-questions investigated:
- Does retrieval-augmented context injection (Method B) or structured context normalization (Method C) alter factual consistency and semantic preservation relative to direct prompting (Method A)?
- What is the empirical performance and failure distribution of a post-hoc LLM-based claim verifier across a 4-class verdict taxonomy (`SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`)?
- What are the operational latency trade-offs associated with multi-stage RAG, structured normalization, and per-claim verification?

---

## 3. Experimental Design

### Track 1 Experimental Matrix
A $5 \times 4 \times 3$ full-factorial design yielding 60 independent generation runs:
- **Source Documents ($N=5$)**: `DOC-REAL-001` through `DOC-REAL-005` from the curated CNN/DailyMail real research corpus.
- **Output Formats ($N=4$)**:
  1. `executive_summary`
  2. `advisory`
  3. `presentation`
  4. `video_script`
- **Architectural Generation Methods ($N=3$)**:
  - **Method A (Direct Prompting)**: Zero retrieval; full document content supplied in the primary prompt context.
  - **Method B (Basic RAG)**: Dense vector similarity search over structure-aware document chunks; top retrieved passages supplied as context.
  - **Method C (RAG + Context Normalization)**: Dense vector retrieval combined with deterministic fact extraction, entity linking, and structured proposition context normalization.

### Track 2 Experimental Matrix
- **Benchmark Sample ($N=25$)**: 5 gold items per document across `DOC-REAL-001` through `DOC-REAL-005`.
- **Taxonomy**: 4-class classification (`SUPPORTED`, `CONTRADICTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`).
- **Claim Origins**: 8 direct source facts, 17 controlled systematic perturbations (numerical mutations, entity substitutions, polarity inversions, unsupported extrapolations).

---

## 4. Dataset Description

The canonical real research dataset is drawn from news corpora with human annotations.

| Document ID | Source Category | Word Count | Section Count | Total Ground-Truth Facts | Annotation Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **DOC-REAL-001** | Corporate / Legal News | 283 | 1 | 15 | FINAL |
| **DOC-REAL-002** | Entertainment / Media | 290 | 1 | 12 | FINAL |
| **DOC-REAL-003** | Public Sector / Governance | 388 | 1 | 14 | FINAL |
| **DOC-REAL-004** | Military / Geopolitics | 339 | 1 | 13 | FINAL |
| **DOC-REAL-005** | Community / Human Interest | 373 | 1 | 13 | FINAL |
| **Total** | — | **1,673** | **5** | **67** | **FINAL** |

---

## 5. Ground-Truth Annotation Protocol

Ground-truth annotations were established prior to experiment execution under a double-annotated semantic verification protocol:
- **Fact Units**: Discrete atomic factual propositions with verbatim character offsets, normalized statements, entity tags, and importance weights (`HIGH` vs `MEDIUM`).
- **Total Facts**: 67 `FINAL` verified facts.
- **Verification Benchmark**: 25 `FINAL` claim-evidence pairs with explicit evidence span citations and expected verdicts.

---

## 6. Track 1 — Generation Quality Metrics

### Operational Metric Definitions

1. **Fully Supported Claim Rate (FSCR)**:
   $$\text{FSCR} = \frac{|\text{Claims with Verdict } \texttt{SUPPORTED}|}{|\text{Total Extracted Claims}|}$$

2. **Contradiction Rate (CR)**:
   $$\text{CR} = \frac{|\text{Claims with Verdict } \texttt{CONTRADICTED}|}{|\text{Total Extracted Claims}|}$$

3. **Partial Support Rate (PSR)**:
   $$\text{PSR} = \frac{|\text{Claims with Verdict } \texttt{PARTIALLY\_SUPPORTED}|}{|\text{Total Extracted Claims}|}$$

4. **Insufficient Evidence Rate (IER)**:
   $$\text{IER} = \frac{|\text{Claims with Verdict } \texttt{INSUFFICIENT\_EVIDENCE}|}{|\text{Total Extracted Claims}|}$$

5. **Source Groundedness (SG)**:
   $$\text{SG} = \frac{|\texttt{SUPPORTED}| + 0.5 \times |\texttt{PARTIALLY\_SUPPORTED}|}{|\text{Total Extracted Claims}|}$$

6. **Unsupported Claim Rate (UCR)**:
   $$\text{UCR} = \frac{|\texttt{CONTRADICTED}| + |\texttt{INSUFFICIENT\_EVIDENCE}|}{|\text{Total Extracted Claims}|}$$

7. **Source Coverage (SC)**:
   $$\text{SC} = \frac{|\text{Matched Ground-Truth Facts}|}{|\text{Total Ground-Truth Facts in Document}|}$$

8. **Semantic Preservation Score (SP)**:
   $$\text{SP} = \frac{|\text{Matched HIGH-Importance Facts}|}{|\text{Total HIGH-Importance Facts in Document}|}$$

---

## 7. Track 1 Descriptive Results

Descriptive statistics across $N = 20$ runs per method (5 documents $\times$ 4 formats):

| Metric | Method A (Direct) Mean (Std) | Method B (Basic RAG) Mean (Std) | Method C (RAG + Context) Mean (Std) |
| :--- | :---: | :---: | :---: |
| **Fully Supported Claim Rate (FSCR)** | 0.2566 (0.2732) | 0.2866 (0.3268) | 0.2729 (0.3247) |
| **Contradiction Rate (CR)** | 0.3743 (0.2822) | 0.3504 (0.3096) | 0.3692 (0.3247) |
| **Partial Support Rate (PSR)** | 0.3691 (0.1709) | 0.3631 (0.1777) | 0.3579 (0.2082) |
| **Source Groundedness (SG)** | 0.4412 (0.2643) | 0.4681 (0.3057) | 0.4519 (0.3076) |
| **Source Coverage (SC)** | 0.1438 (0.1574) | 0.1806 (0.1879) | 0.1753 (0.1754) |
| **Semantic Preservation (SP)** | 0.1357 (0.1500) | 0.1822 (0.1904) | 0.1661 (0.1818) |
| **Generation Latency (seconds)** | 99.17s (22.56s) | 91.04s (17.61s) | 123.71s (26.15s) |

---

## 8. Track 1 Statistical Hypothesis Testing

Two-tailed paired Student's $t$-tests ($N = 20$ paired observations per comparison):

| Comparison | Metric | Mean Difference | $t$-statistic | Raw $p$-value | Cohen's $d$ | 95% Confidence Interval |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **A vs B** | FSCR | +0.0299 | 1.0151 | 0.3228 | 0.2270 | [-0.0318, +0.0916] |
| **A vs B** | Source Groundedness | +0.0269 | 1.2387 | 0.2305 | 0.2770 | [-0.0186, +0.0724] |
| **A vs B** | Source Coverage | +0.0368 | 1.4292 | 0.1692 | 0.3196 | [-0.0171, +0.0907] |
| **A vs B** | Semantic Preservation | +0.0464 | 1.8575 | 0.0788 | 0.4153 | [-0.0059, +0.0988] |
| **B vs C** | FSCR | -0.0137 | -0.4447 | 0.6616 | -0.0994 | [-0.0780, +0.0506] |
| **B vs C** | Source Groundedness | -0.0162 | -0.7406 | 0.4680 | -0.1656 | [-0.0622, +0.0297] |
| **B vs C** | Source Coverage | -0.0053 | -0.2250 | 0.8244 | -0.0503 | [-0.0550, +0.0443] |
| **B vs C** | Semantic Preservation | -0.0161 | -0.7195 | 0.4806 | -0.1609 | [-0.0629, +0.0307] |
| **A vs C** | FSCR | +0.0162 | 0.4166 | 0.6816 | 0.0932 | [-0.0654, +0.0979] |
| **A vs C** | Source Groundedness | +0.0107 | 0.4427 | 0.6630 | 0.0990 | [-0.0397, +0.0611] |
| **A vs C** | Source Coverage | +0.0314 | 1.3779 | 0.1843 | 0.3081 | [-0.0163, +0.0792] |
| **A vs C** | Semantic Preservation | +0.0303 | 1.2539 | 0.2251 | 0.2804 | [-0.0203, +0.0810] |

---

## 9. Track 1 Sensitivity Analysis & FWER Correction

### Family-Wise Error Rate Correction (Holm-Bonferroni)
Applying step-down Holm-Bonferroni adjustment across all 12 hypothesis tests:
- Raw $p$-values range from $p = 0.0788$ to $p = 0.8244$.
- Lowest adjusted $p$-value: **A vs B (Semantic Preservation)**, $p_{\text{adj}} = \min(1.0, 12 \times 0.0788) = \mathbf{0.9456}$.
- All other 11 adjusted $p$-values are $p_{\text{adj}} = \mathbf{1.0000}$.
- **Statistical Inference**: None of the pairwise differences between Methods A, B, and C achieve statistical significance at $\alpha = 0.05$ after controlling for multiple comparisons.

### Non-Parametric Sensitivity Check (Paired Wilcoxon Signed-Rank Test)
- The Wilcoxon signed-rank tests produced the same significance decisions as the paired t-tests for all 12 comparisons, providing a non-parametric sensitivity check.
- Non-zero difference counts ranged from $N_{\text{non-zero}} = 8$ to $20$.
- Wilcoxon $p$-values ranged from $p = 0.0702$ (A vs B Semantic Preservation) to $p = 0.8162$ (B vs C Source Coverage).

---

## 10. Track 1 Retrieval-Metric Limitation

> [!WARNING]
> **Methodological Note on Retrieval Metrics**:  
> In initial exploratory analyses, Retrieval Recall@5, Precision@5, and MRR were measured against top-5 retrieved chunks. Because canonical annotations are defined at the factual text-span level rather than chunk index level, vector-chunk retrieval evaluation is tautological without independent chunk relevance ground truth. Consequently, retrieval ranking metrics are formally designated **`null` / unmeasured** in the final empirical results.

---

## 11. Track 2 — Verification Quality Evaluation

### Benchmark Overview
- **Evaluated Items**: 25 / 25 completed (100% success rate, 0 failures, 0 timeouts).
- **Execution Provider**: Local Ollama (`llama3.2`).
- **Mean Verification Latency**: **32,238.8 ms** (~32.24s per claim).

### Overall Classification Performance
- **4-Class Accuracy**: **0.5600** (14 / 25 correct predictions)
- **Macro Precision**: **0.2841**
- **Macro Recall**: **0.4688**
- **Macro F1-Score**: **0.3509**
- **Binary Classification Accuracy** (Source Supported vs Not Supported): **0.7200** (18 / 25)
- **Binary F1-Score**: **0.6957**

### Per-Class Performance Breakdown

| Class Verdict | Support (Gold) | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SUPPORTED** | 8 | 7 | 4 | 1 | 0.6364 | 0.8750 | 0.7369 |
| **CONTRADICTED** | 7 | 7 | 7 | 0 | 0.5000 | 1.0000 | 0.6667 |
| **PARTIALLY_SUPPORTED** | 4 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| **INSUFFICIENT_EVIDENCE** | 6 | 0 | 0 | 6 | 0.0000 | 0.0000 | 0.0000 |

### 4-Class Confusion Matrix

*Rows: Expected (Gold) | Columns: Predicted*

| Gold \ Predicted | SUPPORTED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SUPPORTED** | **7** | 1 | 0 | 0 | 8 |
| **CONTRADICTED** | 0 | **7** | 0 | 0 | 7 |
| **PARTIALLY_SUPPORTED** | 1 | 3 | **0** | 0 | 4 |
| **INSUFFICIENT_EVIDENCE** | 3 | 3 | 0 | **0** | 6 |
| **Total Predicted** | 11 | 14 | 0 | 0 | 25 |

### Error Analysis
1. **High Recall on Binary Polarity**: The verifier demonstrated high sensitivity for clear entailment (87.5% recall on `SUPPORTED`) and explicit factual contradiction (100.0% recall on `CONTRADICTED`).
2. **Intermediate/Null Boundary Collapse**: The verifier did not predict `PARTIALLY_SUPPORTED` or `INSUFFICIENT_EVIDENCE` for any sample, instead collapsing compound perturbations into `CONTRADICTED` (3 items) or `SUPPORTED` (1 item), and unmentioned facts into `CONTRADICTED` (3 items) or `SUPPORTED` (3 items).

---

## 12. Track 3 — Operational Telemetry

System latency profiling across execution stages:

| Architectural Condition | Pipeline Components | Mean Latency (s) | Median Latency (s) | Std Dev (s) |
| :--- | :--- | :---: | :---: | :---: |
| **Condition A** | Direct LLM Generation | 99.17s | 94.80s | 22.56s |
| **Condition B** | Dense Vector Retrieval + LLM Generation | 91.04s | 89.82s | 17.61s |
| **Condition C** | Retrieval + Context Normalization + Generation | 123.71s | 122.41s | 26.15s |
| **Condition D** | Per-Claim Independent Verification (per claim) | 32.24s | 30.85s | 5.37s |

*Note: Condition D represents the post-hoc verification workload per claim, not an alternative generation method.*

---

## 13. Development Fixture vs Real Research Results

To maintain strict methodological separation:
- **Development Fixtures (`DOC-DEV-01` to `DOC-DEV-04`)**: Used solely for unit testing, CI smoke verification, and schema validation.
- **Real Research Benchmark (`DOC-REAL-001` to `DOC-REAL-005`)**: Sourced from real-world documents with 67 human-annotated `FINAL` facts and 25 `FINAL` verification items.
- Development fixture metrics are strictly isolated and never pooled into research results.

---

## 14. Summary of Empirical Findings

1. **Generation Quality Comparison**: In this sample of 60 runs on `llama3.2`, Method B exhibited a higher sample mean FSCR (0.2866) than Method A (0.2566) and Method C (0.2729), while Method B also exhibited higher sample mean Source Coverage (0.1806 vs 0.1438 for A and 0.1753 for C). However, paired $t$-tests and Wilcoxon signed-rank tests confirmed that these differences are not statistically significant at $\alpha = 0.05$ after Holm-Bonferroni correction.
2. **Verification Agent Behavior**: The LLM claim verifier achieved 0.5600 4-class accuracy and 0.7200 binary accuracy. It exhibited high sensitivity on explicit support and contradiction, but experienced classification collapse on partial support and absence-of-evidence cases.
3. **Operational Overhead**: Structured context normalization (Method C) added an average of 32.67 seconds of latency over Basic RAG (Method B), while post-hoc verification added approximately 32.24 seconds per evaluated claim.

---

## 15. Statistical and Methodological Limitations

1. **Sample Size ($N=60$ Generation Runs, $N=25$ Verification Items)**: While adequate for evaluating directional patterns and paired non-parametric tests, larger corpora would be required to detect small effect sizes ($d < 0.30$).
2. **Model Specificity**: All quantitative measurements reflect local execution on `llama3.2` (3.2B parameters) via Ollama. Results may vary on larger parameter models.
3. **Retrieval Ground Truth**: Fact-level span annotations do not provide independent chunk-level relevance ground truth.

---

## 16. Reproducibility Information

- **Execution Environment**: Local Windows x86_64, Ollama Server `http://localhost:11434/v1`
- **Model**: `llama3.2` (temperature = 0.2, max output tokens = 4096, timeout = 300s)
- **Embeddings**: `all-MiniLM-L6-v2` (384 dimensions)
- **Raw Observations Preserved**:
  - Track 1: [`research/results/real_experiment_60run/raw/*.json`](file:///c:/genai/research/results/real_experiment_60run/raw/) (60 files)
  - Track 2: [`research/results/real_verification_25run/raw/*.json`](file:///c:/genai/research/results/real_verification_25run/raw/) (25 files)
- **Scoring Scripts**:
  - [`research/experiments/score_existing_60run_experiment.py`](file:///c:/genai/research/experiments/score_existing_60run_experiment.py)
  - [`research/experiments/run_real_verification_25run.py`](file:///c:/genai/research/experiments/run_real_verification_25run.py)
  - [`research/experiments/statistical_analysis.py`](file:///c:/genai/research/experiments/statistical_analysis.py)

---

## 17. Final Research Status

All planned empirical evaluations for Track 1 (Generation Quality), Track 2 (Verification Quality), and Track 3 (Operational Telemetry) are complete, audited, and archived with 100% data integrity.
