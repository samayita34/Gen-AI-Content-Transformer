"""
Unit and Integration Tests for Milestone 9B Track 2 Verification Workspace Validator
====================================================================================
Tests Track 2 verification benchmark workspace validation, schema checks,
coordinate bounds, verbatim span matching, anti-leakage, and lifecycle gates.
"""

import json
import pytest
from pathlib import Path

from research.schemas.dataset import (
    AnnotationStatus,
    ClaimOrigin,
    SourceReferenceSpan,
    VerificationVerdict,
    VerificationBenchmarkItem,
)
from research.datasets.scripts.validate_verification_annotations import (
    validate_verification_workspace,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_track2_empty_workspace_passes_validation():
    """Verify that the initial empty Batch 1 workspace passes validation cleanly."""
    real_research_dir = REPO_ROOT / "research" / "datasets" / "real_research"
    workspace_path = real_research_dir / "verification_benchmark" / "batch1_annotation_workspace.json"
    sources_dir = real_research_dir / "source_documents"
    track1_manifest_path = real_research_dir / "manifest.json"
    track1_annotations_dir = real_research_dir / "annotations"
    dev_fixture_manifest_path = REPO_ROOT / "research" / "datasets" / "development_fixture" / "manifest.json"

    result = validate_verification_workspace(
        workspace_path=workspace_path,
        sources_dir=sources_dir,
        track1_manifest_path=track1_manifest_path,
        track1_annotations_dir=track1_annotations_dir,
        dev_fixture_manifest_path=dev_fixture_manifest_path,
    )

    assert result["status"] == "PASS", f"Validation errors: {result['errors']}"
    assert result["items_checked"] == 0
    assert len(result["errors"]) == 0


def test_track2_valid_item_verification(tmp_path):
    """Test validator on a temporary workspace with valid item and exact span."""
    real_research_dir = REPO_ROOT / "research" / "datasets" / "real_research"
    sources_dir = real_research_dir / "source_documents"
    track1_manifest_path = real_research_dir / "manifest.json"
    track1_annotations_dir = real_research_dir / "annotations"
    dev_fixture_manifest_path = REPO_ROOT / "research" / "datasets" / "development_fixture" / "manifest.json"

    with open(sources_dir / "DOC-REAL-001.txt", "r", encoding="utf-8") as f:
        src = f.read()

    start = 0
    end = 182
    verbatim = src[start:end]

    valid_workspace = {
        "workspace_version": "1.0.0",
        "batch_id": "batch1",
        "target_documents": ["DOC-REAL-001"],
        "is_development_fixture": False,
        "items": [
            {
                "benchmark_id": "BENCH-TEST-001",
                "document_id": "DOC-REAL-001",
                "claim": "Police said an Indian software pioneer and nine others were sentenced to seven years in jail.",
                "expected_verdict": "SUPPORTED",
                "evidence_references": [
                    {
                        "paragraph_idx": 0,
                        "sentence_idx": 0,
                        "start_char": start,
                        "end_char": end,
                        "verbatim_text_span": verbatim,
                    }
                ],
                "annotation_status": "CANDIDATE",
                "claim_origin": "SOURCE_FACT",
                "notes": "Test item",
                "metadata": {"batch": "test"},
            }
        ],
    }

    ws_file = tmp_path / "test_workspace.json"
    with open(ws_file, "w", encoding="utf-8") as f:
        json.dump(valid_workspace, f)

    result = validate_verification_workspace(
        workspace_path=ws_file,
        sources_dir=sources_dir,
        track1_manifest_path=track1_manifest_path,
        track1_annotations_dir=track1_annotations_dir,
        dev_fixture_manifest_path=dev_fixture_manifest_path,
    )

    assert result["status"] == "PASS", f"Errors: {result['errors']}"
    assert result["items_checked"] == 1
    assert result["verdict_distribution"]["SUPPORTED"] == 1


def test_track2_invalid_span_mismatch_detected(tmp_path):
    """Test that character span content mismatch is detected."""
    real_research_dir = REPO_ROOT / "research" / "datasets" / "real_research"
    sources_dir = real_research_dir / "source_documents"
    track1_manifest_path = real_research_dir / "manifest.json"
    track1_annotations_dir = real_research_dir / "annotations"
    dev_fixture_manifest_path = REPO_ROOT / "research" / "datasets" / "development_fixture" / "manifest.json"

    invalid_workspace = {
        "workspace_version": "1.0.0",
        "batch_id": "batch1",
        "is_development_fixture": False,
        "items": [
            {
                "benchmark_id": "BENCH-TEST-002",
                "document_id": "DOC-REAL-001",
                "claim": "Test claim",
                "expected_verdict": "CONTRADICTED",
                "evidence_references": [
                    {
                        "paragraph_idx": 0,
                        "sentence_idx": 0,
                        "start_char": 0,
                        "end_char": 50,
                        "verbatim_text_span": "Fabricated text span that does not match",
                    }
                ],
                "annotation_status": "CANDIDATE",
                "claim_origin": "CONTROLLED_PERTURBATION",
            }
        ],
    }

    ws_file = tmp_path / "test_invalid_workspace.json"
    with open(ws_file, "w", encoding="utf-8") as f:
        json.dump(invalid_workspace, f)

    result = validate_verification_workspace(
        workspace_path=ws_file,
        sources_dir=sources_dir,
        track1_manifest_path=track1_manifest_path,
        track1_annotations_dir=track1_annotations_dir,
        dev_fixture_manifest_path=dev_fixture_manifest_path,
    )

    assert result["status"] == "FAIL"
    assert any("content mismatch" in err for err in result["errors"])


def test_track2_anti_leakage_detection(tmp_path):
    """Test that referencing a development fixture document in Track 2 fails validation."""
    real_research_dir = REPO_ROOT / "research" / "datasets" / "real_research"
    sources_dir = real_research_dir / "source_documents"
    track1_manifest_path = real_research_dir / "manifest.json"
    track1_annotations_dir = real_research_dir / "annotations"
    dev_fixture_manifest_path = REPO_ROOT / "research" / "datasets" / "development_fixture" / "manifest.json"

    leakage_workspace = {
        "workspace_version": "1.0.0",
        "batch_id": "batch1",
        "is_development_fixture": False,
        "items": [
            {
                "benchmark_id": "BENCH-LEAK-001",
                "document_id": "DOC-DEV-01-TECH",
                "claim": "Leaked dev fixture claim",
                "expected_verdict": "SUPPORTED",
                "evidence_references": [],
                "annotation_status": "CANDIDATE",
                "claim_origin": "SOURCE_FACT",
            }
        ],
    }

    ws_file = tmp_path / "test_leakage_workspace.json"
    with open(ws_file, "w", encoding="utf-8") as f:
        json.dump(leakage_workspace, f)

    result = validate_verification_workspace(
        workspace_path=ws_file,
        sources_dir=sources_dir,
        track1_manifest_path=track1_manifest_path,
        track1_annotations_dir=track1_annotations_dir,
        dev_fixture_manifest_path=dev_fixture_manifest_path,
    )

    assert result["status"] == "FAIL"
    assert any("Anti-leakage violation" in err for err in result["errors"])
