# TransformAI Research Evaluation Protocol (Milestone 7)

> **Document Version**: 1.0.0  
> **Milestone**: 7 — Quantitative Research Evaluation Framework  
> **Problem Statement**: SIH26154: Gen AI Platform for Automated Content Transformation  
> **Status**: Approved Protocol  

---

## 1. Central Research Question & Decoupled Tracks

### Central Research Question
> *“Does progressively adding retrieval, structured context normalization, and claim-level verification improve the factual consistency and source-groundedness of multi-format generative content compared with direct LLM prompting?”*

To evaluate this question without confounding generation-quality improvements with verification classification quality, the evaluation protocol is strictly partitioned into **two independent research tracks** and a secondary latency/operational trade-off track.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              M7 EVALUATION ARCHITECTURE                                │
├─────────────────────────────────────────┬──────────────────────────────────────────────┤
│ TRACK 1: GENERATION QUALITY             │ TRACK 2: VERIFICATION QUALITY                │
│ • Generation Architecture Progression:  │ • Verification Task:                         │
│   - Method A: Direct LLM Prompting      │   - Independent evaluation of M6 verifier    │
│   - Method B: Basic RAG                 │   - Evaluated on labeled ground-truth claims │
│   - Method C: RAG + Structured Context  │ • Metrics:                                   │
│ • Primary Ablations:                    │   - 4-Class Precision, Recall, F1            │
│   - A → B: Contribution of RAG          │   - Macro-F1                                 │
│   - B → C: Contribution of Context Norm │   - Confusion Matrix                         │
│ • Metrics: FSCR, Contradiction Rate,    │   - Per-class performance                    │
│   Partial Support, Insufficient Ev,     │ • Research Question:                         │
│   Source Coverage, Retrieval Recall@K   │   Can the verification agent correctly      │
│ • Note: Method D text is identical to C │   classify claim-evidence support?           │
├─────────────────────────────────────────┴──────────────────────────────────────────────┤
│ TRACK 3: SYSTEM LATENCY & RESOURCE TRADE-OFF                                           │
│ • Wall-clock latency (retrieval, normalization, generation, verification, total)       │
│ • Token efficiency where exposed by provider (never fabricated)                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Research Hypotheses

All hypotheses are treated as testable scientific propositions that the experimental data may support or reject:

- **Hypothesis 1 ($H_1$, Generation Track)**:  
  *Adding dense vector retrieval (Method B) improves source-groundedness and reduces hallucinated factual assertions compared with direct LLM prompting (Method A).*
- **Hypothesis 2 ($H_2$, Generation Track)**:  
  *Adding deterministic structured context normalization (Method C) improves factual consistency, entity/numerical preservation, and source coverage compared with basic RAG (Method B).*
- **Hypothesis 3 ($H_3$, Verification Track)**:  
  *The claim-level verification agent can reliably distinguish source-supported, contradicted, partially-supported, and insufficient-evidence claims when evaluated against labeled ground-truth examples.*

> **Methodological Clarification regarding Method D**:  
> In the non-corrective pipeline design, the verification agent inspects but does not alter or regenerate the generated output. Therefore, Method D's text is identical in generation architecture to Method C. Method D is evaluated as a verification-enabled system condition in Track 2 and Track 3, not as a causal text-generation improvement.

---

## 3. Operational Metric Definitions

For this study, we operationalize the quantitative metrics using the following exact mathematical formulas:

### A. Fully Supported Claim Rate (FSCR)
$$\text{FSCR} = \frac{N_{\text{supported}}}{N_{\text{total\_claims}}}$$
- **Numerator**: Number of generated claims classified as `SUPPORTED` by source evidence.
- **Denominator**: Total number of evaluated atomic claims extracted from the output.
- **Zero-Claim Handling**: If $N_{\text{total\_claims}} = 0$, the metric returns `null` and sets `zero_claims_flag = true`.

### B. Contradiction Rate (CR)
$$\text{CR} = \frac{N_{\text{contradicted}}}{N_{\text{total\_claims}}}$$
- Measures the proportion of generated claims that directly conflict with source evidence.

### C. Partial Support Rate (PSR)
$$\text{PSR} = \frac{N_{\text{partially\_supported}}}{N_{\text{total\_claims}}}$$
- Measures assertions where only a subset of compound conditions or numbers is confirmed.

### D. Insufficient Evidence Rate (IER)
$$\text{IER} = \frac{N_{\text{insufficient\_evidence}}}{N_{\text{total\_claims}}}$$
- Measures assertions that cannot be confirmed or refuted from the available source text. (Never conflated with contradiction).

### E. Source Groundedness (SG)
$$\text{SG} = \frac{N_{\text{supported}} + (w_{\text{partial}} \cdot N_{\text{partially\_supported}})}{N_{\text{total\_claims}}}$$
- **Weighting Parameter**: $w_{\text{partial}} = 0.50$.
- **Rationale**: Partial support indicates semantic grounding for part of the claim while penalizing ungrounded compound elements.

### F. Unsupported Claim Rate (UCR)
$$\text{UCR} = \frac{N_{\text{contradicted}} + N_{\text{insufficient\_evidence}}}{N_{\text{total\_claims}}}$$
- Represents the total proportion of claims lacking authoritative source grounding.

### G. Source Coverage (SC)
$$\text{SC} = \frac{|\mathcal{F}_{\text{matched}}|}{|\mathcal{F}_{\text{relevant\_ground\_truth}}|}$$
- **Matching Rule**: A ground-truth fact $f \in \mathcal{F}$ is considered matched if at least one generated atomic claim entails $f$'s normalized proposition.
- **Deduplication**: Multiple generated claims mapping to the same ground-truth fact count as a single match.

### H. Retrieval Quality Metrics
- **Recall@K**: $\frac{|\text{Relevant Chunks in Top-K}|}{|\text{Total Ground-Truth Relevant Chunks}|}$
- **Precision@K**: $\frac{|\text{Relevant Chunks in Top-K}|}{K}$
- **MRR (Mean Reciprocal Rank)**: $\frac{1}{\text{rank of first relevant chunk}}$
- *Evaluated strictly when chunk-level ground-truth relevance annotations exist.*

---

## 4. Verification Agent Multi-Class Evaluation (Track 2)

The M6 Verification Judge is evaluated against an independent benchmark of labeled claims across **4 mutually exclusive classes**:
1. `SUPPORTED`
2. `CONTRADICTED`
3. `PARTIALLY_SUPPORTED`
4. `INSUFFICIENT_EVIDENCE`

### Metrics:
- **Per-Class Precision, Recall, F1**:
  $$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Recall}_c = \frac{TP_c}{TP_c + FN_c}, \quad F1_c = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$
- **Macro-F1**:
  $$\text{Macro-F1} = \frac{1}{4} \sum_{c \in \mathcal{C}} F1_c$$
- **Confusion Matrix**: Full $4 \times 4$ contingency table mapping Gold Verdict vs Predicted Verdict.
- **Secondary Binary Analysis**: `SOURCE_SUPPORTED` (`SUPPORTED` + `PARTIALLY_SUPPORTED`) vs `NOT_SOURCE_SUPPORTED` (`CONTRADICTED` + `INSUFFICIENT_EVIDENCE`).

---

## 5. Statistical Analysis Methodology

To evaluate whether observed differences between methods represent meaningful effects:

1. **Descriptive Statistics**:
   - Compute mean, median, standard deviation, and Interquartile Range (IQR) for every metric across runs.
2. **Paired Observations**:
   - Since Methods A, B, and C are evaluated on identical source documents and output formats, evaluations are inherently paired.
3. **Assumption Verification & Test Selection**:
   - If sample size $N \ge 10$ and differences exhibit approximate normality (Shapiro-Wilk $p > 0.05$), conduct a **Paired Student's t-test**.
   - If normality is violated or sample size is moderate ($5 \le N < 10$), conduct the non-parametric **Wilcoxon Signed-Rank Test**.
   - If sample size is small ($N < 5$), report purely descriptive metrics and explicitly document small-sample limitations without manufacturing statistical significance.
4. **Effect Size**:
   - Calculate Cohen's $d$ for paired differences: $d = \frac{\bar{x}_D}{s_D}$.
5. **Ablation Deltas**:
   - $\Delta_{A \to B} = \text{Metric}(B) - \text{Metric}(A)$ (Contribution of RAG)
   - $\Delta_{B \to C} = \text{Metric}(C) - \text{Metric}(B)$ (Contribution of Context Normalization)

---

## 6. Anti-Leakage & Ground-Truth Inference Boundary

To eliminate data leakage and evaluation bias:

```
[SOURCE DOCUMENT] ──▶ [GENERATION METHOD (A, B, C)] ──▶ [GENERATED OUTPUT]
                                                                │
                                                                ▼
                                                    [CLAIM EXTRACTION (M6)]
                                                                │
                                                                ▼
                                                 [INDEPENDENT RETRIEVAL (M6)]
                                                                │
                                                                ▼
                                                   [VERIFICATION JUDGE (M6)]
                                                                │
                                                                ▼
                                                      [VERIFICATION REPORT]
                                                                │
[HELD-OUT GROUND TRUTH] ────────────────────────────────────────┴──▶ [M7 EVALUATION ENGINE]
(Strictly isolated; never passed into generation prompts,
 retrieval queries, or verification judges)
```

---

## 7. Development Fixture vs Research Dataset Policy

- Fixture files located under `research/datasets/development_fixture/` are provided strictly for unit testing, CI validation, and schema verification.
- All fixture-derived reports are prominently stamped: `DEVELOPMENT FIXTURE — NOT RESEARCH RESULT`.
- Research conclusions must only be drawn when executing over fully validated empirical datasets.
