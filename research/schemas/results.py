"""
M7 Research Schemas: Results, Metrics & Ablation Models
======================================================
Defines structured schemas for:
- Track 1: Generation Quality Metrics
- Track 2: Verification Quality (4-class classification report & confusion matrix)
- Retrieval Quality Metrics
- Ablation Progression Deltas
- Statistical Test Results
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class GenerationEvaluationMetrics(BaseModel):
    total_evaluated_claims: int = 0
    fully_supported_claims: int = 0
    partially_supported_claims: int = 0
    contradicted_claims: int = 0
    insufficient_evidence_claims: int = 0
    
    # Operational Metrics (null if total_evaluated_claims == 0)
    fully_supported_claim_rate: Optional[float] = None
    contradiction_rate: Optional[float] = None
    partial_support_rate: Optional[float] = None
    insufficient_evidence_rate: Optional[float] = None
    source_groundedness: Optional[float] = None  # (supported + 0.5 * partial) / total
    unsupported_claim_rate: Optional[float] = None  # (insufficient + contradicted) / total
    
    # Ground-Truth Fact Alignment Metrics
    total_ground_truth_facts: int = 0
    matched_ground_truth_facts: int = 0
    source_coverage: Optional[float] = None  # matched_facts / total_facts
    semantic_preservation_score: Optional[float] = None
    semantic_evaluation_method: Optional[str] = None
    
    zero_claims_flag: bool = False
    evaluation_notes: Optional[str] = None


class RetrievalEvaluationMetrics(BaseModel):
    k: int
    retrieved_count: int
    relevant_count_in_ground_truth: int
    true_positives: int
    recall_at_k: Optional[float] = None
    precision_at_k: Optional[float] = None
    reciprocal_rank: Optional[float] = None


class PerClassMetrics(BaseModel):
    verdict: str
    support: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None


class VerificationClassificationReport(BaseModel):
    total_samples: int
    macro_precision: Optional[float] = None
    macro_recall: Optional[float] = None
    macro_f1: Optional[float] = None
    per_class: Dict[str, PerClassMetrics] = Field(default_factory=dict)
    confusion_matrix: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    
    # Secondary Binary Analysis: SOURCE_SUPPORTED vs NOT_SOURCE_SUPPORTED
    binary_accuracy: Optional[float] = None
    binary_f1: Optional[float] = None
    
    evaluation_notes: Optional[str] = None


class AblationDelta(BaseModel):
    metric_name: str
    baseline_value: Optional[float] = None
    experimental_value: Optional[float] = None
    delta: Optional[float] = None
    percent_change: Optional[float] = None
    direction_improved: Optional[bool] = None


class AblationStepReport(BaseModel):
    step_name: str  # e.g., "A -> B (Contribution of RAG)" or "B -> C (Contribution of Context Normalization)"
    baseline_method: str
    experimental_method: str
    deltas: List[AblationDelta] = Field(default_factory=list)


class StatisticalTestReport(BaseModel):
    metric_name: str
    comparison_name: str
    test_used: str
    sample_size: int
    test_statistic: Optional[float] = None
    p_value: Optional[float] = None
    effect_size_cohens_d: Optional[float] = None
    confidence_interval_95: Optional[List[float]] = None
    assumptions_satisfied: bool
    limitation_notes: Optional[str] = None
