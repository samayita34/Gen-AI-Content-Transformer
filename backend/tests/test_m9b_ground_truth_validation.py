"""
Unit and Integration Tests for Milestone 9B: Ground Truth and Verification Benchmark
===================================================================================
Tests Track 1 Source Facts, Track 2 Verification Benchmark models,
claim origins, lifecycle gates, span mechanics, and anti-leakage isolation.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from research.schemas.dataset import (
    AnnotationStatus,
    ClaimOrigin,
    FactType,
    GroundTruthFact,
    ImportanceLevel,
    SourceReferenceSpan,
    VerificationVerdict,
    VerificationBenchmarkItem,
    VerificationBenchmarkManifest,
)
from research.datasets.scripts.validate_research_dataset import validate_real_dataset


def test_claim_origin_enum():
    """Verify all supported claim origins."""
    assert ClaimOrigin.SOURCE_FACT.value == "SOURCE_FACT"
    assert ClaimOrigin.CONTROLLED_PERTURBATION.value == "CONTROLLED_PERTURBATION"


def test_verification_benchmark_item_model():
    """Test instantiating a valid VerificationBenchmarkItem."""
    item = VerificationBenchmarkItem(
        benchmark_id="BENCH-REAL-001",
        document_id="DOC-REAL-001",
        claim="The European Central Bank raised interest rates by 25 basis points.",
        expected_verdict=VerificationVerdict.SUPPORTED,
        evidence_references=[
            SourceReferenceSpan(
                paragraph_idx=0,
                sentence_idx=0,
                start_char=0,
                end_char=20,
                verbatim_text_span="The European Central",
            )
        ],
        annotation_status=AnnotationStatus.FINAL,
        claim_origin=ClaimOrigin.SOURCE_FACT,
        notes="Direct source fact proposition.",
    )
    assert item.benchmark_id == "BENCH-REAL-001"
    assert item.expected_verdict == VerificationVerdict.SUPPORTED
    assert item.claim_origin == ClaimOrigin.SOURCE_FACT
    assert item.annotation_status == AnnotationStatus.FINAL


def test_verification_benchmark_item_invalid_verdict():
    """Verify that an invalid verdict string is rejected by Pydantic."""
    with pytest.raises(ValidationError):
        VerificationBenchmarkItem(
            benchmark_id="BENCH-REAL-ERR",
            document_id="DOC-REAL-001",
            claim="Invalid test claim.",
            expected_verdict="TRUE",  # Not in VerificationVerdict enum
            annotation_status=AnnotationStatus.FINAL,
            claim_origin=ClaimOrigin.SOURCE_FACT,
        )


def test_verification_benchmark_item_invalid_origin():
    """Verify that an invalid claim origin is rejected by Pydantic."""
    with pytest.raises(ValidationError):
        VerificationBenchmarkItem(
            benchmark_id="BENCH-REAL-ERR",
            document_id="DOC-REAL-001",
            claim="Invalid test claim.",
            expected_verdict=VerificationVerdict.SUPPORTED,
            annotation_status=AnnotationStatus.FINAL,
            claim_origin="AUTOMATIC_GENERATION",  # Invalid origin
        )


def test_verification_benchmark_manifest_structure():
    """Test instantiating and serializing VerificationBenchmarkManifest."""
    manifest = VerificationBenchmarkManifest(
        benchmark_version="1.0.0",
        benchmark_name="TransformAI Track 2 Verification Benchmark",
        is_development_fixture=False,
        created_at="2026-09-14T17:00:00Z",
        annotation_status="UNANNOTATED",
        total_items=0,
        items=[],
    )
    assert manifest.is_development_fixture is False
    assert manifest.total_items == 0


def test_ground_truth_fact_multi_source_references():
    """Verify GroundTruthFact supports multiple discontinuous evidence references."""
    fact = GroundTruthFact(
        fact_id="FACT-REAL01-002",
        statement="B. Ramalinga Raju was the chairman of Satyam Computer Services.",
        normalized_statement="B. Ramalinga Raju chairman of Satyam Computer Services.",
        fact_type=FactType.ENTITY_RELATION,
        source_reference=SourceReferenceSpan(
            paragraph_idx=0,
            sentence_idx=0,
            start_char=0,
            end_char=24,
            verbatim_text_span="Satyam Computer Services",
        ),
        source_references=[
            SourceReferenceSpan(
                paragraph_idx=0,
                sentence_idx=0,
                start_char=0,
                end_char=24,
                verbatim_text_span="Satyam Computer Services",
            ),
            SourceReferenceSpan(
                paragraph_idx=0,
                sentence_idx=1,
                start_char=84,
                end_char=144,
                verbatim_text_span="The software services exporter's chairman, B. Ramalinga Raju",
            ),
        ],
        annotation_status=AnnotationStatus.FINAL,
        key_entities=["B. Ramalinga Raju", "Satyam Computer Services"],
    )
    assert len(fact.source_references) == 2
    assert fact.source_references[1].verbatim_text_span == "The software services exporter's chairman, B. Ramalinga Raju"


def test_dataset_validator_runs_cleanly():
    """Verify the real research dataset validator succeeds on current dataset and benchmark files."""
    passed, errors, stats = validate_real_dataset()
    assert passed is True, f"Validator failed with errors: {errors}"
    assert len(errors) == 0
    assert "track1_document_statuses" in stats
    assert "track2_verdict_distribution" in stats

