"""
Unit and Integration Tests for Milestone 9A: Dataset Quality and Validation
===========================================================================
Tests dataset schema compliance, length stratification, span mechanics,
annotation status lifecycle, and anti-leakage isolation without downloading
external datasets at test execution time.
"""

import hashlib
import json
import pytest
from pathlib import Path

from research.schemas.dataset import (
    AnnotationStatus,
    DatasetManifest,
    FactType,
    GroundTruthDocument,
    GroundTruthFact,
    ImportanceLevel,
    SourceReferenceSpan,
    VerificationVerdict,
)
from research.datasets.scripts.validate_research_dataset import validate_real_dataset


REAL_DATASET_DIR = Path("research/datasets/real_research")
DEV_DATASET_DIR = Path("research/datasets/development_fixture")


def test_schema_annotation_status_enum():
    """Verify all annotation lifecycle statuses are supported in schema."""
    assert AnnotationStatus.UNANNOTATED.value == "UNANNOTATED"
    assert AnnotationStatus.CANDIDATE.value == "CANDIDATE"
    assert AnnotationStatus.REVIEWED.value == "REVIEWED"
    assert AnnotationStatus.FINAL.value == "FINAL"


def test_schema_verification_verdicts():
    """Verify the 4 standard verification taxonomy verdicts."""
    verdicts = {v.value for v in VerificationVerdict}
    expected = {"SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE"}
    assert verdicts == expected


def test_span_coordinate_mechanics():
    """Test verbatim character offset extraction logic on a mock document."""
    sample_text = "Global emissions decreased by 4.2% in 2024. Renewable energy accounted for 30% of total power."
    start_char = sample_text.index("4.2%")
    end_char = start_char + len("4.2%")
    
    span = SourceReferenceSpan(
        paragraph_idx=0,
        sentence_idx=0,
        start_char=start_char,
        end_char=end_char,
        verbatim_text_span="4.2%",
    )
    
    assert sample_text[span.start_char:span.end_char] == span.verbatim_text_span


def test_prepared_real_research_dataset_structure():
    """Verify the prepared 60-document research dataset meets all structure requirements."""
    manifest_file = REAL_DATASET_DIR / "manifest.json"
    assert manifest_file.exists(), "Manifest file must exist"

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Schema validation via Pydantic
    manifest = DatasetManifest(**manifest_data)
    assert manifest.is_development_fixture is False, "Real research manifest MUST have is_development_fixture=False"
    assert manifest.total_documents == 60
    assert len(manifest.documents) == 60

    # Stratification check
    short_docs = [d for d in manifest.documents if d.length_category == "SHORT"]
    med_docs = [d for d in manifest.documents if d.length_category == "MEDIUM"]
    long_docs = [d for d in manifest.documents if d.length_category == "LONG"]

    assert len(short_docs) == 20, f"Expected 20 SHORT documents, got {len(short_docs)}"
    assert len(med_docs) == 20, f"Expected 20 MEDIUM documents, got {len(med_docs)}"
    assert len(long_docs) == 20, f"Expected 20 LONG documents, got {len(long_docs)}"


def test_prepared_documents_and_hashes():
    """Verify all 60 source files exist and have matching SHA-256 hashes."""
    manifest_file = REAL_DATASET_DIR / "manifest.json"
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    for doc in manifest_data["documents"]:
        source_path = REAL_DATASET_DIR / doc["file_path"]
        assert source_path.exists(), f"Source file missing: {source_path}"

        with open(source_path, "r", encoding="utf-8") as f:
            content = f.read()

        computed_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert computed_hash == doc["source_hash_sha256"], f"Hash mismatch for {doc['document_id']}"

        wc = len(content.split())
        if doc["length_category"] == "SHORT":
            assert wc < 400
        elif doc["length_category"] == "MEDIUM":
            assert 400 <= wc <= 800
        elif doc["length_category"] == "LONG":
            assert wc > 800


def test_anti_leakage_with_dev_fixture():
    """Ensure zero ID or content hash leakage between real research and development fixture."""
    dev_manifest_path = DEV_DATASET_DIR / "manifest.json"
    real_manifest_path = REAL_DATASET_DIR / "manifest.json"

    assert dev_manifest_path.exists()
    assert real_manifest_path.exists()

    with open(dev_manifest_path, "r", encoding="utf-8") as f:
        dev_manifest = json.load(f)

    with open(real_manifest_path, "r", encoding="utf-8") as f:
        real_manifest = json.load(f)

    assert dev_manifest["is_development_fixture"] is True
    assert real_manifest["is_development_fixture"] is False

    dev_ids = {d["document_id"] for d in dev_manifest["documents"]}
    real_ids = {d["document_id"] for d in real_manifest["documents"]}
    assert len(dev_ids.intersection(real_ids)) == 0, "Document ID overlap detected!"

    dev_hashes = {d["source_hash_sha256"] for d in dev_manifest["documents"]}
    real_hashes = {d["source_hash_sha256"] for d in real_manifest["documents"]}
    assert len(dev_hashes.intersection(real_hashes)) == 0, "Source content hash overlap detected!"


def test_full_dataset_validation_script_passes():
    """Run programmatic dataset validator."""
    passed, errors, stats = validate_real_dataset()
    assert passed is True, f"Dataset validation failed: {errors}"
    assert len(errors) == 0
    assert stats["bucket_counts"] == {"SHORT": 20, "MEDIUM": 20, "LONG": 20}
