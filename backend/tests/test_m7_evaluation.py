"""
Unit and Integration Tests for Milestone 7 Quantitative Research Evaluation Framework
=====================================================================================
Tests:
1. Dataset and Ground-Truth schema validation & integrity
2. Operational metric calculations (FSCR, CR, PSR, IER, SG, SC, SP)
3. Edge cases: zero claims, missing ground truth, fact deduplication
4. Track 2: 4-class verification classification metrics & confusion matrix
5. Retrieval ranking evaluation (Recall@K, Precision@K, MRR)
6. Statistical analysis, paired tests, Cohen's d, and ablation deltas
7. Reproducibility metadata serialization & explicit nullability
8. End-to-end benchmark execution on development fixture
"""

import pytest
import os
import sys
import json
import uuid
from pathlib import Path

# Add backend and project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from research.schemas.dataset import (
    DatasetManifest,
    GroundTruthDocument,
    GroundTruthFact,
    FactType,
    ImportanceLevel,
)
from research.schemas.experiment import (
    MethodType,
    OutputFormat,
    ReproducibilityMetadata,
    LatencyBreakdown,
)
from research.schemas.results import (
    GenerationEvaluationMetrics,
    RetrievalEvaluationMetrics,
    VerificationClassificationReport,
)
from research.experiments.evaluate_claims import (
    compute_generation_claim_metrics,
    match_claims_to_ground_truth,
)
from research.experiments.evaluate_retrieval import evaluate_retrieval_ranking
from research.experiments.evaluate_verification import evaluate_verification_predictions
from research.experiments.statistical_analysis import (
    compute_descriptive_stats,
    compute_paired_comparison,
    compute_ablation_step,
)
from research.experiments.run_generation_evaluation import execute_m7_benchmark
from research.experiments.generate_reports_and_plots import generate_tables_and_plots

from app.services.verification.models import (
    VerificationReport,
    ClaimVerificationResult,
    AtomicClaim,
    VerificationVerdict,
    ClaimType,
)


def test_dataset_manifest_schema_validation():
    """Validates that the development fixture manifest loads and conforms to schema."""
    manifest_path = ROOT_DIR / "research" / "datasets" / "development_fixture" / "manifest.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = DatasetManifest(**data)
    assert manifest.dataset_version == "dev-fixture-1.0.0"
    assert manifest.is_development_fixture is True
    assert manifest.total_documents == 3
    assert len(manifest.documents) == 3
    assert manifest.documents[0].document_id == "DOC-DEV-01-TECH"


def test_ground_truth_document_schema_validation():
    """Validates ground truth fact schema and types."""
    facts_path = ROOT_DIR / "research" / "datasets" / "development_fixture" / "annotations" / "DOC-DEV-01-TECH.facts.json"
    assert facts_path.exists()

    with open(facts_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    gt_doc = GroundTruthDocument(**data)
    assert gt_doc.document_id == "DOC-DEV-01-TECH"
    assert len(gt_doc.facts) == 7
    assert gt_doc.facts[0].fact_type in [FactType.STATISTICAL, FactType.FACTUAL, FactType.NUMERICAL]
    assert gt_doc.facts[0].importance in [ImportanceLevel.HIGH, ImportanceLevel.MEDIUM, ImportanceLevel.LOW]


def test_operational_generation_metrics_calculation():
    """Tests exact operational formulas for FSCR, CR, PSR, IER, SG, and SC."""
    claims = [
        ClaimVerificationResult(
            claim=AtomicClaim(
                claim_id=uuid.uuid4(),
                statement="CoreSync achieved 99.98% uptime in Q3.",
                claim_type=ClaimType.FACTUAL,
            ),
            verdict=VerificationVerdict.SUPPORTED,
            explanation="Verified",
            confidence=0.95,
        ),
        ClaimVerificationResult(
            claim=AtomicClaim(
                claim_id=uuid.uuid4(),
                statement="CoreSync experienced a 10% downtime.",
                claim_type=ClaimType.FACTUAL,
            ),
            verdict=VerificationVerdict.CONTRADICTED,
            explanation="Contradiction",
            confidence=0.90,
        ),
        ClaimVerificationResult(
            claim=AtomicClaim(
                claim_id=uuid.uuid4(),
                statement="Read latency was 18 ms and storage is encrypted with AES-256.",
                claim_type=ClaimType.FACTUAL,
            ),
            verdict=VerificationVerdict.PARTIALLY_SUPPORTED,
            explanation="Partial",
            confidence=0.85,
        ),
        ClaimVerificationResult(
            claim=AtomicClaim(
                claim_id=uuid.uuid4(),
                statement="The system uses CockroachDB.",
                claim_type=ClaimType.FACTUAL,
            ),
            verdict=VerificationVerdict.INSUFFICIENT_EVIDENCE,
            explanation="No evidence",
            confidence=0.80,
        ),
    ]

    report = VerificationReport(
        document_id="doc-123",
        output_type="executive_summary",
        total_claims=4,
        supported_claims=1,
        contradicted_claims=1,
        partially_supported_claims=1,
        insufficient_evidence_claims=1,
        claims=claims,
    )

    metrics = compute_generation_claim_metrics(report, ground_truth_doc=None, partial_weight=0.50)

    assert metrics.total_evaluated_claims == 4
    assert metrics.fully_supported_claims == 1
    assert metrics.fully_supported_claim_rate == 0.25  # 1/4
    assert metrics.contradiction_rate == 0.25         # 1/4
    assert metrics.partial_support_rate == 0.25        # 1/4
    assert metrics.insufficient_evidence_rate == 0.25  # 1/4
    # Source Groundedness = (1 + 0.5 * 1) / 4 = 1.5 / 4 = 0.375
    assert metrics.source_groundedness == 0.375
    # Unsupported Claim Rate = (1 + 1) / 4 = 0.50
    assert metrics.unsupported_claim_rate == 0.50
    assert metrics.zero_claims_flag is False


def test_zero_claims_edge_case():
    """Ensures zero claims return explicit null rates without crashing."""
    report = VerificationReport(
        document_id="doc-123",
        output_type="executive_summary",
        total_claims=0,
        supported_claims=0,
        contradicted_claims=0,
        partially_supported_claims=0,
        insufficient_evidence_claims=0,
        claims=[],
    )

    metrics = compute_generation_claim_metrics(report, ground_truth_doc=None)
    assert metrics.total_evaluated_claims == 0
    assert metrics.fully_supported_claim_rate is None
    assert metrics.contradiction_rate is None
    assert metrics.source_groundedness is None
    assert metrics.unsupported_claim_rate is None
    assert metrics.zero_claims_flag is True


def test_source_coverage_deduplication():
    """Ensures multiple claims mapping to the same ground-truth fact count once."""
    gt_doc = GroundTruthDocument(
        document_id="DOC-TEST",
        title="Test Doc",
        source_hash_sha256="hash123",
        word_count=50,
        section_count=1,
        facts=[
            GroundTruthFact(
                fact_id="FACT-01",
                statement="CoreSync achieved 99.98% uptime in Q3 2025 across availability zones.",
                normalized_statement="CoreSync achieved 99.98% uptime in Q3 2025 across availability zones.",
                fact_type=FactType.STATISTICAL,
                key_entities=["CoreSync", "availability zones"],
                numerical_values=["99.98%"],
            ),
            GroundTruthFact(
                fact_id="FACT-02",
                statement="Read latency remained at 18 ms.",
                normalized_statement="Read latency remained at 18 ms.",
                fact_type=FactType.NUMERICAL,
                key_entities=["read latency"],
                numerical_values=["18 ms"],
            ),
        ],
    )

    claims = [
        ClaimVerificationResult(
            claim=AtomicClaim(
                claim_id=uuid.uuid4(),
                statement="CoreSync achieved 99.98% uptime in Q3 2025 across availability zones.",
                claim_type=ClaimType.FACTUAL,
            ),
            verdict=VerificationVerdict.SUPPORTED,
            explanation="Match 1",
            confidence=0.95,
        ),
        ClaimVerificationResult(
            claim=AtomicClaim(
                claim_id=uuid.uuid4(),
                statement="In Q3 2025, CoreSync achieved 99.98% uptime in active availability zones.",
                claim_type=ClaimType.FACTUAL,
            ),
            verdict=VerificationVerdict.SUPPORTED,
            explanation="Duplicate match",
            confidence=0.95,
        ),
    ]

    report = VerificationReport(
        document_id="DOC-TEST",
        output_type="executive_summary",
        total_claims=2,
        supported_claims=2,
        contradicted_claims=0,
        partially_supported_claims=0,
        insufficient_evidence_claims=0,
        claims=claims,
    )

    metrics = compute_generation_claim_metrics(report, ground_truth_doc=gt_doc)
    assert metrics.total_ground_truth_facts == 2
    assert metrics.matched_ground_truth_facts == 1  # Deduplicated
    assert metrics.source_coverage == 0.50          # 1/2


def test_track2_verification_evaluation():
    """Tests 4-class confusion matrix, precision, recall, and Macro-F1."""
    gold = ["SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE", "SUPPORTED"]
    pred = ["SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE", "PARTIALLY_SUPPORTED"]

    report = evaluate_verification_predictions(gold, pred)

    assert report.total_samples == 5
    assert "SUPPORTED" in report.confusion_matrix
    assert report.confusion_matrix["SUPPORTED"]["SUPPORTED"] == 1
    assert report.confusion_matrix["SUPPORTED"]["PARTIALLY_SUPPORTED"] == 1
    assert report.per_class["CONTRADICTED"].f1_score == 1.0
    assert report.macro_f1 is not None
    assert report.macro_f1 > 0.60
    assert report.binary_accuracy == 1.0  # In binary grouping, PART_SUPP and SUPP both = 1


def test_retrieval_ranking_evaluation():
    """Tests Recall@K, Precision@K, and MRR against ground truth."""
    retrieved = [1, 5, 2, 8, 9]
    gt_relevant = {2, 5}

    res = evaluate_retrieval_ranking(retrieved, gt_relevant, k=3)
    assert res is not None
    assert res.retrieved_count == 3
    assert res.relevant_count_in_ground_truth == 2
    assert res.true_positives == 2  # indices 5 and 2 are in top 3
    assert res.recall_at_k == 1.0   # 2/2
    assert res.precision_at_k == round(2 / 3, 4)
    assert res.reciprocal_rank == 0.5  # First hit is at rank 2 (index 5)

    # Test missing relevance ground truth
    assert evaluate_retrieval_ranking(retrieved, None) is None
    assert evaluate_retrieval_ranking(retrieved, set()) is None


def test_statistical_analysis_descriptive_and_paired():
    """Tests descriptive stats, paired comparison assumptions, and ablation steps."""
    scores_a = [0.40, 0.45, 0.50, 0.42, 0.48]
    scores_b = [0.70, 0.75, 0.80, 0.72, 0.78]

    desc_a = compute_descriptive_stats(scores_a)
    assert desc_a["n"] == 5
    assert desc_a["mean"] == 0.45
    assert desc_a["median"] == 0.45

    paired_res = compute_paired_comparison(
        baseline_scores=scores_a,
        experimental_scores=scores_b,
        metric_name="FSCR",
        comparison_name="Method A -> Method B",
    )

    assert paired_res.sample_size == 5
    assert paired_res.assumptions_satisfied is True
    assert paired_res.effect_size_cohens_d is not None
    assert paired_res.effect_size_cohens_d > 5.0  # Large positive effect
    assert paired_res.p_value is not None

    # Small sample test (N=3)
    small_res = compute_paired_comparison(
        baseline_scores=[0.5, 0.6, 0.7],
        experimental_scores=[0.8, 0.9, 0.85],
        metric_name="FSCR",
        comparison_name="Small N test",
    )
    assert small_res.sample_size == 3
    assert small_res.assumptions_satisfied is False
    assert "Small Sample N < 5" in small_res.test_used

    # Ablation Step Delta
    ablation = compute_ablation_step(
        baseline_metrics={"FSCR": 0.45, "latency_ms": 100.0},
        experimental_metrics={"FSCR": 0.75, "latency_ms": 150.0},
        step_name="A -> B",
        baseline_method="METHOD_A",
        experimental_method="METHOD_B",
    )
    assert len(ablation.deltas) == 2
    fscr_delta = next(d for d in ablation.deltas if d.metric_name == "FSCR")
    assert fscr_delta.delta == 0.30
    assert fscr_delta.direction_improved is True

    lat_delta = next(d for d in ablation.deltas if d.metric_name == "latency_ms")
    assert lat_delta.delta == 50.0
    assert lat_delta.direction_improved is False  # Higher latency is not improved


def test_reproducibility_metadata_contract():
    """Validates reproducibility contract guarantees explicit nullability."""
    meta = ReproducibilityMetadata(
        experiment_id="exp_test_001",
        run_number=1,
        timestamp="2026-09-14T15:00:00Z",
        dataset_version="v1.0.0",
        is_development_fixture=True,
        source_document_id="DOC-01",
        source_document_hash="hash_abc",
        method=MethodType.METHOD_A,
        output_format=OutputFormat.EXECUTIVE_SUMMARY,
        model_provider="mock",
        model_identifier="mock-llm-v1",
        model_configuration={"max_tokens": 1024},
        temperature=None,  # Explicitly null
        random_seed=None,   # Explicitly null
        chunking_configuration=None,  # Method A has no chunking
        retrieval_configuration=None, # Method A has no retrieval
        context_normalization_configuration=None,
        verification_configuration=None,
        latency=LatencyBreakdown(total_ms=45.2),
        token_usage=None,  # Explicitly null
    )

    data = meta.model_dump()
    assert data["temperature"] is None
    assert data["token_usage"] is None
    assert data["chunking_configuration"] is None
    assert data["method"] == "METHOD_A"


@pytest.mark.asyncio
async def test_end_to_end_benchmark_execution_on_fixture(tmp_path):
    """Executes the benchmark runner on the development fixture into a temporary directory."""
    fixture_dir = ROOT_DIR / "research" / "datasets" / "development_fixture"
    out_dir = tmp_path / "results"

    summary = await execute_m7_benchmark(dataset_dir=fixture_dir, output_dir=out_dir)

    assert "benchmark_metadata" in summary
    assert summary["benchmark_metadata"]["is_development_fixture"] is True
    assert summary["benchmark_metadata"]["total_runs"] == 48  # 3 docs * 4 formats * 4 methods

    assert "track_1_generation_quality" in summary
    assert "track_2_verification_quality" in summary
    assert "track_3_operational_telemetry" in summary

    # Verify processed summary JSON was written
    summary_file = out_dir / "processed" / "m7_evaluation_summary.json"
    assert summary_file.exists()

    # Verify raw runs were saved
    raw_files = list((out_dir / "raw").glob("*.json"))
    assert len(raw_files) == 48

    # Test report & plot generation from the summary
    tables_dir = out_dir / "tables"
    figures_dir = out_dir / "figures"
    generate_tables_and_plots(summary_file, tables_dir, figures_dir)

    assert (tables_dir / "track1_generation_comparison.md").exists()
    assert (tables_dir / "track1_generation_comparison.csv").exists()
    assert (tables_dir / "track2_verification_report.md").exists()
    assert (figures_dir / "track1_method_vs_fscr.png").exists()
    assert (figures_dir / "track2_verification_confusion_matrix.png").exists()
    assert (figures_dir / "track3_operational_latency.png").exists()


def test_verification_report_serializer_compatibility():
    """Validates that VerificationReport (dataclass) serializes cleanly via default_json_serializer."""
    from research.experiments.run_generation_evaluation import default_json_serializer
    doc_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    report = VerificationReport(
        document_id=doc_id,
        output_type="executive_summary",
        total_claims=1,
        supported_claims=1,
        contradicted_claims=0,
        partially_supported_claims=0,
        insufficient_evidence_claims=0,
        claim_results=[
            ClaimVerificationResult(
                claim_id=claim_id,
                claim=AtomicClaim(
                    claim_id=claim_id,
                    text="Sample statement.",
                    normalized_text="Sample statement.",
                    output_format="executive_summary",
                    claim_type=ClaimType.FACTUAL,
                ),
                verdict=VerificationVerdict.SUPPORTED,
                confidence_score=0.95,
                verdict_reasoning="Supported by source chunk.",
                matched_evidence=[],
            )
        ],
        claims=[],
        summary="Evaluated 1 claim.",
    )

    serialized = default_json_serializer(report)
    assert isinstance(serialized, dict)
    assert serialized["total_claims"] == 1
    assert serialized["supported_claims"] == 1

    # Must dump to valid JSON without error
    dumped = json.dumps(serialized, default=default_json_serializer)
    assert isinstance(dumped, str)
    assert "Sample statement." in dumped


def test_request_pacing_configuration():
    """Validates that LLM_REQUEST_PACING_SECONDS is properly configured and accessible."""
    from app.core.config import settings
    assert hasattr(settings, "LLM_REQUEST_PACING_SECONDS")
    assert isinstance(settings.LLM_REQUEST_PACING_SECONDS, float)
    assert settings.LLM_REQUEST_PACING_SECONDS >= 0.0
