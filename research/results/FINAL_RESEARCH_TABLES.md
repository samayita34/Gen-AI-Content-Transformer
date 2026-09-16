# FINAL RESEARCH TABLES PACKAGE

**Project**: TransformAI — Source-Grounded Generative AI for Multi-Format Content Transformation  
**Research Track**: Milestone 7 Quantitative Evaluation Benchmark  
**Status**: Authoritative Verified Results  

---

## 1. Dataset Composition & Ground-Truth Fact Breakdown

| Document ID | Source Category | Word Count | Section Count | Total Facts | HIGH Importance | MEDIUM Importance | FINAL Status Facts |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **DOC-REAL-001** | Corporate / Legal News | 283 | 1 | 15 | 7 | 8 | 15 |
| **DOC-REAL-002** | Entertainment / Media | 290 | 1 | 12 | 7 | 5 | 12 |
| **DOC-REAL-003** | Public Sector / Governance | 388 | 1 | 14 | 8 | 6 | 14 |
| **DOC-REAL-004** | Military / Geopolitics | 339 | 1 | 13 | 7 | 6 | 13 |
| **DOC-REAL-005** | Community / Human Interest | 373 | 1 | 13 | 7 | 6 | 13 |
| **Total / Corpus** | — | **1,673** | **5** | **67** | **36** | **31** | **67** |

---

## 2. Track 1 Generation Quality — Descriptive Statistics (N = 20 per Method)

| Metric | Method A (Direct Prompting) | Method B (Basic RAG) | Method C (RAG + Context Norm) |
| :--- | :---: | :---: | :---: |
| **Fully Supported Claim Rate (FSCR)** | 0.2566 ± 0.2732 (med: 0.1840) | 0.2866 ± 0.3268 (med: 0.1483) | 0.2729 ± 0.3247 (med: 0.1225) |
| **Contradiction Rate (CR)** | 0.3743 ± 0.2822 (med: 0.4808) | 0.3504 ± 0.3096 (med: 0.4584) | 0.3692 ± 0.3247 (med: 0.4018) |
| **Partial Support Rate (PSR)** | 0.3691 ± 0.1709 (med: 0.3798) | 0.3631 ± 0.1777 (med: 0.3333) | 0.3579 ± 0.2082 (med: 0.3173) |
| **Source Groundedness (SG)** | 0.4412 ± 0.2643 (med: 0.3333) | 0.4681 ± 0.3057 (med: 0.3214) | 0.4519 ± 0.3076 (med: 0.3214) |
| **Source Coverage (SC)** | 0.1438 ± 0.1574 (med: 0.0833) | 0.1806 ± 0.1879 (med: 0.1667) | 0.1753 ± 0.1754 (med: 0.1570) |
| **Semantic Preservation (SP)** | 0.1357 ± 0.1500 (med: 0.1071) | 0.1822 ± 0.1904 (med: 0.1429) | 0.1661 ± 0.1818 (med: 0.1071) |
| **Generation Latency (seconds)** | 99.17 ± 22.56s (med: 94.80s) | 91.04 ± 17.61s (med: 89.82s) | 123.71 ± 26.15s (med: 122.41s) |

---

## 3. Track 1 Statistical Hypothesis Testing & Sensitivity Analysis

| Comparison | Metric | Mean Diff | $t$-statistic | Raw $p$ | Holm $p_{\text{adj}}$ | Cohen's $d$ | 95% Conf Interval | Wilcoxon $W$ | Wilcoxon $p$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A vs B** | FSCR | +0.0299 | 1.0151 | 0.3228 | 1.0000 | 0.2270 | [-0.0318, +0.0916] | 66.5 | 0.3483 |
| **A vs B** | Source Groundedness | +0.0269 | 1.2387 | 0.2305 | 1.0000 | 0.2770 | [-0.0186, +0.0724] | 70.0 | 0.2024 |
| **A vs B** | Source Coverage | +0.0368 | 1.4292 | 0.1692 | 1.0000 | 0.3196 | [-0.0171, +0.0907] | 35.5 | 0.0919 |
| **A vs B** | Semantic Preservation | +0.0464 | 1.8575 | 0.0788 | 0.9456 | 0.4153 | [-0.0059, +0.0988] | 28.0 | 0.0702 |
| **B vs C** | FSCR | -0.0137 | -0.4447 | 0.6616 | 1.0000 | -0.0994 | [-0.0780, +0.0506] | 88.0 | 0.7203 |
| **B vs C** | Source Groundedness | -0.0162 | -0.7406 | 0.4680 | 1.0000 | -0.1656 | [-0.0622, +0.0297] | 84.0 | 0.4662 |
| **B vs C** | Source Coverage | -0.0053 | -0.2250 | 0.8244 | 1.0000 | -0.0503 | [-0.0550, +0.0443] | 81.0 | 0.8162 |
| **B vs C** | Semantic Preservation | -0.0161 | -0.7195 | 0.4806 | 1.0000 | -0.1609 | [-0.0629, +0.0307] | 46.0 | 0.2846 |
| **A vs C** | FSCR | +0.0162 | 0.4166 | 0.6816 | 1.0000 | 0.0932 | [-0.0654, +0.0979] | 89.0 | 0.6797 |
| **A vs C** | Source Groundedness | +0.0107 | 0.4427 | 0.6630 | 1.0000 | 0.0990 | [-0.0397, +0.0611] | 95.0 | 0.7285 |
| **A vs C** | Source Coverage | +0.0314 | 1.3779 | 0.1843 | 1.0000 | 0.3081 | [-0.0163, +0.0792] | 63.0 | 0.4430 |
| **A vs C** | Semantic Preservation | +0.0303 | 1.2539 | 0.2251 | 1.0000 | 0.2804 | [-0.0203, +0.0810] | 45.0 | 0.3725 |

---

## 4. Track 2 Verification Quality — Overall Performance Metrics (N = 25)

| Metric | Score / Value | Evaluation Scope |
| :--- | :---: | :--- |
| **4-Class Accuracy** | **0.5600** (14/25) | Multi-class overall accuracy |
| **Macro Precision** | **0.2841** | Unweighted average across 4 classes |
| **Macro Recall** | **0.4688** | Unweighted average across 4 classes |
| **Macro F1-Score** | **0.3509** | Unweighted harmonic mean of Macro P & R |
| **Binary Classification Accuracy** | **0.7200** (18/25) | Source Supported vs Not Supported |
| **Binary F1-Score** | **0.6957** | Binary entailment harmonic mean |
| **Mean Verification Latency** | **32,238.8 ms** | Per-claim evaluation latency |
| **Median Verification Latency** | **30,848.8 ms** | Median per-claim latency |
| **Evaluation Success Rate** | **100.0%** (25/25) | Zero timeouts, zero unhandled errors |

---

## 5. Track 2 Verification Quality — Per-Class Metrics

| Class Verdict | Support (Gold Count) | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SUPPORTED** | 8 | 7 | 4 | 1 | 0.6364 | 0.8750 | 0.7369 |
| **CONTRADICTED** | 7 | 7 | 7 | 0 | 0.5000 | 1.0000 | 0.6667 |
| **PARTIALLY_SUPPORTED** | 4 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| **INSUFFICIENT_EVIDENCE** | 6 | 0 | 0 | 6 | 0.0000 | 0.0000 | 0.0000 |

---

## 6. Track 2 Confusion Matrix

*Rows: Gold Expected Annotations | Columns: Model Predictions*

| Gold \ Predicted | SUPPORTED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | Total Gold |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SUPPORTED** | **7** | 1 | 0 | 0 | 8 |
| **CONTRADICTED** | 0 | **7** | 0 | 0 | 7 |
| **PARTIALLY_SUPPORTED** | 1 | 3 | **0** | 0 | 4 |
| **INSUFFICIENT_EVIDENCE** | 3 | 3 | 0 | **0** | 6 |
| **Total Predicted** | 11 | 14 | 0 | 0 | 25 |

---

## 7. Track 3 Operational Telemetry & Latency Comparison

| Operational Condition | Description | Mean Latency | Median Latency | Min Latency | Max Latency | Std Dev |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Condition A** | Direct Generation (No Retrieval) | 99.17s | 94.80s | 68.32s | 148.20s | 22.56s |
| **Condition B** | Basic RAG Generation | 91.04s | 89.82s | 62.15s | 131.40s | 17.61s |
| **Condition C** | RAG + Context Normalization Generation | 123.71s | 122.41s | 82.50s | 179.30s | 26.15s |
| **Condition D** | Per-Claim Independent Verification | 32.24s | 30.85s | 25.56s | 44.74s | 5.37s |
