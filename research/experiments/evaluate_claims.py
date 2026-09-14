"""
M7 Research Module: Claim Evaluation & Operational Metrics Scoring
==================================================================
Implements operational definitions for:
- Fully Supported Claim Rate (FSCR)
- Contradiction Rate (CR)
- Partial Support Rate (PSR)
- Insufficient Evidence Rate (IER)
- Source Groundedness (SG) with w_partial = 0.50
- Unsupported Claim Rate (UCR)
- Source Coverage (SC) against ground-truth facts
- Semantic Preservation (SP) via proposition/fact alignment

Handles edge cases (zero claims, missing ground truth) without crashing or fabricating scores.
"""

from typing import List, Dict, Any, Optional, Set
import re

from research.schemas.dataset import GroundTruthDocument, GroundTruthFact
from research.schemas.results import GenerationEvaluationMetrics
from app.services.verification.models import VerificationReport, VerificationVerdict


def compute_generation_claim_metrics(
    verification_report: Optional[VerificationReport],
    ground_truth_doc: Optional[GroundTruthDocument] = None,
    partial_weight: float = 0.50,
) -> GenerationEvaluationMetrics:
    """
    Computes operational generation quality metrics.
    
    If verification_report is None or contains 0 claims, returns a zero_claims_flag record
    where rate metrics are explicitly null.
    """
    if verification_report is None or not verification_report.claims:
        total_facts = len(ground_truth_doc.facts) if ground_truth_doc else 0
        return GenerationEvaluationMetrics(
            total_evaluated_claims=0,
            fully_supported_claims=0,
            partially_supported_claims=0,
            contradicted_claims=0,
            insufficient_evidence_claims=0,
            fully_supported_claim_rate=None,
            contradiction_rate=None,
            partial_support_rate=None,
            insufficient_evidence_rate=None,
            source_groundedness=None,
            unsupported_claim_rate=None,
            total_ground_truth_facts=total_facts,
            matched_ground_truth_facts=0,
            source_coverage=0.0 if total_facts > 0 else None,
            semantic_preservation_score=None,
            zero_claims_flag=True,
            evaluation_notes="No atomic claims extracted from generated output (zero_claims_flag=True)."
        )

    claims = verification_report.claims
    total_claims = len(claims)

    n_supported = sum(1 for c in claims if c.verdict == VerificationVerdict.SUPPORTED)
    n_contradicted = sum(1 for c in claims if c.verdict == VerificationVerdict.CONTRADICTED)
    n_partial = sum(1 for c in claims if c.verdict == VerificationVerdict.PARTIALLY_SUPPORTED)
    n_insufficient = sum(1 for c in claims if c.verdict == VerificationVerdict.INSUFFICIENT_EVIDENCE)

    # Operational metric calculations
    fscr = round(n_supported / total_claims, 4)
    cr = round(n_contradicted / total_claims, 4)
    psr = round(n_partial / total_claims, 4)
    ier = round(n_insufficient / total_claims, 4)
    
    # Source Groundedness = (Supported + w_partial * Partial) / Total
    sg = round((n_supported + (partial_weight * n_partial)) / total_claims, 4)
    
    # Unsupported Claim Rate = (Insufficient + Contradicted) / Total
    ucr = round((n_insufficient + n_contradicted) / total_claims, 4)

    # Source Coverage & Semantic Preservation against Ground Truth
    total_facts = len(ground_truth_doc.facts) if ground_truth_doc else 0
    matched_facts = 0
    source_coverage = None
    semantic_preservation = None
    sem_method = None

    if ground_truth_doc and total_facts > 0:
        matched_fact_ids = match_claims_to_ground_truth(claims, ground_truth_doc.facts)
        matched_facts = len(matched_fact_ids)
        source_coverage = round(matched_facts / total_facts, 4)
        
        # Semantic Preservation operationalized as coverage of high-importance ground-truth facts
        high_importance_facts = [f for f in ground_truth_doc.facts if f.importance == "HIGH"]
        if high_importance_facts:
            high_matched = sum(1 for f in high_importance_facts if f.fact_id in matched_fact_ids)
            semantic_preservation = round(high_matched / len(high_importance_facts), 4)
            sem_method = "PROPOSITION_ALIGNMENT_HIGH_IMPORTANCE"
        else:
            semantic_preservation = source_coverage
            sem_method = "PROPOSITION_ALIGNMENT_ALL_FACTS"

    return GenerationEvaluationMetrics(
        total_evaluated_claims=total_claims,
        fully_supported_claims=n_supported,
        partially_supported_claims=n_partial,
        contradicted_claims=n_contradicted,
        insufficient_evidence_claims=n_insufficient,
        fully_supported_claim_rate=fscr,
        contradiction_rate=cr,
        partial_support_rate=psr,
        insufficient_evidence_rate=ier,
        source_groundedness=sg,
        unsupported_claim_rate=ucr,
        total_ground_truth_facts=total_facts,
        matched_ground_truth_facts=matched_facts,
        source_coverage=source_coverage,
        semantic_preservation_score=semantic_preservation,
        semantic_evaluation_method=sem_method,
        zero_claims_flag=False,
    )


def match_claims_to_ground_truth(
    claims: List[Any],
    ground_truth_facts: List[GroundTruthFact]
) -> Set[str]:
    """
    Matches generated atomic claims against ground-truth fact propositions.
    Uses token overlap and key entity/numerical alignment.
    Deduplicates multiple claims that map to the same ground-truth fact.
    """
    matched_fact_ids: Set[str] = set()

    for gt_fact in ground_truth_facts:
        gt_tokens = tokenize(gt_fact.normalized_statement)
        gt_entities = [e.lower() for e in gt_fact.key_entities]
        gt_nums = [n.lower() for n in gt_fact.numerical_values]

        for claim in claims:
            # Only consider supported or partially supported claims as valid matches
            if getattr(claim, "verdict", None) not in (VerificationVerdict.SUPPORTED, VerificationVerdict.PARTIALLY_SUPPORTED):
                continue
            
            claim_text = getattr(claim, "statement", "")
            claim_lower = claim_text.lower()
            claim_tokens = tokenize(claim_text)
            
            if not claim_tokens or not gt_tokens:
                continue

            # Token overlap (Jaccard similarity)
            overlap = len(gt_tokens.intersection(claim_tokens)) / len(gt_tokens.union(claim_tokens))
            
            # Entity match requirement
            entity_match = all(e in claim_lower for e in gt_entities) if gt_entities else True
            # Numerical match requirement
            num_match = any(n in claim_lower for n in gt_nums) if gt_nums else True

            if (overlap >= 0.30 and entity_match) or (overlap >= 0.20 and entity_match and num_match):
                matched_fact_ids.add(gt_fact.fact_id)
                break

    return matched_fact_ids


def tokenize(text: str) -> Set[str]:
    """Simple alphanumeric tokenization for deterministic matching."""
    tokens = re.findall(r"\b\w+\b", text.lower())
    # Exclude basic stopwords
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and", "or", "with"}
    return {t for t in tokens if t not in stopwords and len(t) > 1}
