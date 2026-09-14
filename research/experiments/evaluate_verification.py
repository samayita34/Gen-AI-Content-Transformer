"""
M7 Research Module: Track 2 — Verification Quality Evaluation
============================================================
Evaluates the M6 Verification Agent independently against gold-labeled claims.
Computes:
- 4-class Confusion Matrix (SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, INSUFFICIENT_EVIDENCE)
- Per-class Precision, Recall, F1
- Macro-F1
- Secondary Binary Analysis (SOURCE_SUPPORTED vs NOT_SOURCE_SUPPORTED)
"""

from typing import List, Dict, Any, Optional
from research.schemas.results import VerificationClassificationReport, PerClassMetrics


CLASSES = [
    "SUPPORTED",
    "CONTRADICTED",
    "PARTIALLY_SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
]


def evaluate_verification_predictions(
    gold_verdicts: List[str],
    predicted_verdicts: List[str],
) -> VerificationClassificationReport:
    """
    Computes 4-class classification metrics given paired lists of gold and predicted verdicts.
    """
    if len(gold_verdicts) != len(predicted_verdicts):
        raise ValueError(
            f"Gold and predicted lengths mismatch: {len(gold_verdicts)} vs {len(predicted_verdicts)}"
        )

    total_samples = len(gold_verdicts)
    if total_samples == 0:
        return VerificationClassificationReport(
            total_samples=0,
            macro_precision=None,
            macro_recall=None,
            macro_f1=None,
            evaluation_notes="Empty prediction list evaluated.",
        )

    # Initialize confusion matrix [gold][predicted]
    conf_matrix: Dict[str, Dict[str, int]] = {
        gold_cls: {pred_cls: 0 for pred_cls in CLASSES}
        for gold_cls in CLASSES
    }

    for gold, pred in zip(gold_verdicts, predicted_verdicts):
        gold_norm = gold.upper().strip()
        pred_norm = pred.upper().strip()
        if gold_norm in conf_matrix and pred_norm in conf_matrix[gold_norm]:
            conf_matrix[gold_norm][pred_norm] += 1

    per_class: Dict[str, PerClassMetrics] = {}
    f1_list: List[float] = []
    prec_list: List[float] = []
    rec_list: List[float] = []

    for cls_name in CLASSES:
        # True Positives: gold == cls & pred == cls
        tp = conf_matrix[cls_name][cls_name]
        # False Positives: gold != cls & pred == cls
        fp = sum(conf_matrix[other_cls][cls_name] for other_cls in CLASSES if other_cls != cls_name)
        # False Negatives: gold == cls & pred != cls
        fn = sum(conf_matrix[cls_name][other_cls] for other_cls in CLASSES if other_cls != cls_name)
        # Support: total gold instances for this class
        support = sum(conf_matrix[cls_name].values())

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else (1.0 if tp == 0 and fp == 0 and support == 0 else 0.0)
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else (1.0 if support == 0 else 0.0)
        f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0

        per_class[cls_name] = PerClassMetrics(
            verdict=cls_name,
            support=support,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            f1_score=f1,
        )

        prec_list.append(precision)
        rec_list.append(recall)
        f1_list.append(f1)

    macro_precision = round(sum(prec_list) / len(prec_list), 4)
    macro_recall = round(sum(rec_list) / len(rec_list), 4)
    macro_f1 = round(sum(f1_list) / len(f1_list), 4)

    # Secondary Binary Analysis:
    # Classify {SUPPORTED, PARTIALLY_SUPPORTED} as 1 (SOURCE_SUPPORTED)
    # Classify {CONTRADICTED, INSUFFICIENT_EVIDENCE} as 0 (NOT_SOURCE_SUPPORTED)
    bin_tp = 0
    bin_fp = 0
    bin_fn = 0
    bin_tn = 0

    for gold, pred in zip(gold_verdicts, predicted_verdicts):
        g_bin = 1 if gold.upper().strip() in ("SUPPORTED", "PARTIALLY_SUPPORTED") else 0
        p_bin = 1 if pred.upper().strip() in ("SUPPORTED", "PARTIALLY_SUPPORTED") else 0
        
        if g_bin == 1 and p_bin == 1:
            bin_tp += 1
        elif g_bin == 0 and p_bin == 1:
            bin_fp += 1
        elif g_bin == 1 and p_bin == 0:
            bin_fn += 1
        else:
            bin_tn += 1

    bin_acc = round((bin_tp + bin_tn) / total_samples, 4) if total_samples > 0 else 0.0
    bin_prec = bin_tp / (bin_tp + bin_fp) if (bin_tp + bin_fp) > 0 else 0.0
    bin_rec = bin_tp / (bin_tp + bin_fn) if (bin_tp + bin_fn) > 0 else 0.0
    bin_f1 = round(2 * bin_prec * bin_rec / (bin_prec + bin_rec), 4) if (bin_prec + bin_rec) > 0 else 0.0

    return VerificationClassificationReport(
        total_samples=total_samples,
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        per_class=per_class,
        confusion_matrix=conf_matrix,
        binary_accuracy=bin_acc,
        binary_f1=bin_f1,
    )
