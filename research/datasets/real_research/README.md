# TransformAI Real-World Research Evaluation Benchmark Dataset

**Milestone**: M9A — Real Research Dataset & Annotation Protocol  
**Dataset Version**: `real-benchmark-1.0.0`  
**Status**: Dataset preparation complete; ground-truth annotation pending.  
**Target Research Hypotheses**:
- **$H_1$**: RAG improves factual consistency & source grounding over direct prompting.
- **$H_2$**: Structured context normalization improves fact retention over basic RAG.
- **$H_3$**: Claim-level verification accurately classifies claims into four verdict categories without artificial balancing.

---

## 1. Dataset Provenance, Attribution & Multi-Tier Licensing

### 1.1 Source Benchmark
The source articles in this dataset are sampled from the official **CNN/DailyMail summarization benchmark** (`abisee/cnn_dailymail`, Version 3.0.0, `test` split).

### 1.2 Multi-Tier Licensing Details
To maintain strict research integrity and compliance, this benchmark distinguishes three licensing layers:

| Layer | Source / Scope | License / Legal Terms |
| :--- | :--- | :--- |
| **Dataset Processing Scripts & Repository** | Hugging Face / Abigail See (`abisee/cnn_dailymail`) | **Apache License 2.0** (Open source dataset preprocessing code) |
| **Underlying News Article Content** | Cable News Network (CNN) & Associated Newspapers Ltd (Daily Mail) | **Copyright © CNN & Daily Mail**. Original articles remain the property of their respective publishers and are provided for academic research and evaluation benchmarks. |
| **TransformAI Code, Schemas & Annotations** | TransformAI Project (`SIH26154`) | **MIT License** / Academic Open Source |

### 1.3 Academic Citations
If referencing this benchmark or experimental results, cite the original dataset creators:
1. **Hermann, K. M., Kocisky, T., Grefenstette, E., Espeholt, L., Kay, W., Suleyman, M., & Blunsom, P.** (2015). *Teaching machines to read and comprehend.* Advances in Neural Information Processing Systems (NeurIPS), 28, 1693–1701.
2. **See, A., Liu, P. J., & Manning, C. D.** (2017). *Get To The Point: Summarization with Pointer-Generator Networks.* Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (ACL), 1073–1083.

---

## 2. Deterministic Stratified Sampling Methodology

To ensure robust evaluation across documents of varying complexity and length, the dataset is stratified into three length buckets from the official 11,490 candidate test-set articles using deterministic pseudo-random sampling (`seed=42`).

### 2.1 Stratification Distribution

| Length Bucket | Word Count Range | Eligible Candidates in Test Split | Selected Corpus Count | Document ID Range |
| :--- | :--- | :--- | :--- | :--- |
| **SHORT** | $< 400$ words | 2,545 articles | **20 documents** | `DOC-REAL-001` – `DOC-REAL-020` |
| **MEDIUM** | $400 - 800$ words | 5,418 articles | **20 documents** | `DOC-REAL-021` – `DOC-REAL-040` |
| **LONG** | $> 800$ words | 3,527 articles | **20 documents** | `DOC-REAL-041` – `DOC-REAL-060` |
| **TOTAL** | — | **11,490 articles** | **60 documents** | `DOC-REAL-001` – `DOC-REAL-060` |

---

## 3. Directory Layout & File Structure

```
research/datasets/real_research/
├── manifest.json                  # Dataset manifest (is_development_fixture: false)
├── README.md                      # This documentation
├── source_documents/              # 60 clean source text documents
│   ├── DOC-REAL-001.txt
│   └── ...
├── annotations/                   # Human ground-truth workspaces (.facts.json)
│   ├── DOC-REAL-001.facts.json
│   └── ...
└── candidates/                    # (Optional) Candidate proposal workspaces (.candidates.json)
    └── ...
```

---

## 4. Annotation Schema & Lifecycle

### 4.1 Annotation Lifecycle
```
UNANNOTATED (Preparation) 
    ──> Human Proposition Deconstruction & Span Mapping
    ──> REVIEWED (Adjudication)
    ──> FINAL (Certified Ground Truth)
```
Only annotations marked with `status: "FINAL"` may be ingested for benchmark scoring.

### 4.2 Verification Claim Taxonomy ($H_3$)
The 4 verification categories are:
- `SUPPORTED`: Direct factual entailment from the source.
- `CONTRADICTED`: Direct contradiction or fact distortion.
- `PARTIALLY_SUPPORTED`: Mix of supported and unsupported sub-claims.
- `INSUFFICIENT_EVIDENCE`: Unverifiable from the provided source.

*Note: No artificial class balancing is enforced on the benchmark. Labels reflect empirical human annotation.*

---

## 5. Anti-Leakage Separation Guarantee

1. **Isolation from Development Fixture**:
   - `research/datasets/development_fixture/` contains strictly 3 development fixture documents (`DOC-DEV-01-TECH`, `DOC-DEV-02-MED`, `DOC-DEV-03-FIN`) with `is_development_fixture: true`.
   - `research/datasets/real_research/` contains strictly 60 research documents (`DOC-REAL-001` to `DOC-REAL-060`) with `is_development_fixture: false`.
2. **Zero Overlap**: The automated validation script verifies that real research document IDs and content hashes have zero overlap with the development fixture.

---

## 6. Reproducibility & Validation Commands

To regenerate the dataset from scratch:
```bash
python research/datasets/scripts/prepare_cnn_dailymail_dataset.py --seed 42
```

To run the quality and anti-leakage audit:
```bash
python research/datasets/scripts/validate_research_dataset.py
```
