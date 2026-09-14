"""
M7 Research Module: Retrieval Evaluation
========================================
Calculates retrieval metrics (Recall@K, Precision@K, MRR) strictly when
ground-truth relevance references exist. Never fabricates numbers.
"""

from typing import List, Set, Optional
from research.schemas.results import RetrievalEvaluationMetrics


def evaluate_retrieval_ranking(
    retrieved_chunk_indices: List[int],
    ground_truth_relevant_indices: Optional[Set[int]],
    k: int = 5,
) -> Optional[RetrievalEvaluationMetrics]:
    """
    Evaluates retrieval performance against ground-truth relevant chunk indices.
    If ground_truth_relevant_indices is None or empty, returns None (unannotated).
    """
    if ground_truth_relevant_indices is None or len(ground_truth_relevant_indices) == 0:
        return None

    top_k_retrieved = retrieved_chunk_indices[:k]
    retrieved_count = len(top_k_retrieved)
    total_relevant = len(ground_truth_relevant_indices)

    true_positives = sum(1 for idx in top_k_retrieved if idx in ground_truth_relevant_indices)

    recall_at_k = round(true_positives / total_relevant, 4) if total_relevant > 0 else 0.0
    precision_at_k = round(true_positives / k, 4) if k > 0 else 0.0

    # Reciprocal Rank (MRR component)
    reciprocal_rank = 0.0
    for rank, idx in enumerate(top_k_retrieved, start=1):
        if idx in ground_truth_relevant_indices:
            reciprocal_rank = round(1.0 / rank, 4)
            break

    return RetrievalEvaluationMetrics(
        k=k,
        retrieved_count=retrieved_count,
        relevant_count_in_ground_truth=total_relevant,
        true_positives=true_positives,
        recall_at_k=recall_at_k,
        precision_at_k=precision_at_k,
        reciprocal_rank=reciprocal_rank,
    )
