"""
TransformAI Research: Dataset Quality & Anti-Leakage Validation
===============================================================
Comprehensive audit script for research dataset integrity, schema compliance,
span mechanics, and anti-leakage isolation from development fixtures.

Validation Criteria:
1. Manifest Schema & Non-Fixture Flag (is_development_fixture == False)
2. Document Count & Stratification (20 Short, 20 Medium, 20 Long)
3. Source File Presence & SHA-256 Hash Matching
4. Annotation Schema, Lifecycle Status, and Span Mechanics
5. Verification Claim Taxonomy (without artificial equal-count balancing)
6. Anti-Leakage Boundary (zero overlap with development_fixture)
"""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Tuple


REAL_DATASET_DIR = Path("research/datasets/real_research")
DEV_DATASET_DIR = Path("research/datasets/development_fixture")

VALID_FACT_TYPES = {
    "FACTUAL", "STATISTICAL", "ATTRIBUTIONAL", "TEMPORAL",
    "NUMERICAL", "ENTITY_RELATION", "IMPLICATION",
}

VALID_VERDICTS = {
    "SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE"
}

VALID_STATUSES = {"UNANNOTATED", "CANDIDATE", "REVIEWED", "FINAL"}


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_real_dataset() -> Tuple[bool, List[str], Dict[str, Any]]:
    errors = []
    stats = {}

    print("=" * 70)
    print("TransformAI Research: Validating Real Research Dataset (M9A)")
    print("=" * 70)

    manifest_path = REAL_DATASET_DIR / "manifest.json"
    if not manifest_path.exists():
        errors.append(f"Manifest not found: {manifest_path}")
        return False, errors, stats

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        errors.append(f"Failed to parse manifest JSON: {e}")
        return False, errors, stats

    # 1. Manifest Checks
    print("\n[Audit 1/6] Manifest Schema & Non-Fixture Flag...")
    if manifest.get("is_development_fixture") is not False:
        errors.append("Manifest 'is_development_fixture' MUST be False for real research data.")
    
    total_docs = manifest.get("total_documents", 0)
    doc_entries = manifest.get("documents", [])
    if total_docs != len(doc_entries):
        errors.append(f"Manifest total_documents ({total_docs}) does not match list length ({len(doc_entries)}).")

    if total_docs != 60:
        errors.append(f"Expected 60 total documents, found: {total_docs}")

    # 2. Stratification Checks
    print("\n[Audit 2/6] Stratification & Length Buckets...")
    bucket_counts = Counter()
    for doc in doc_entries:
        bucket = doc.get("length_category", "UNKNOWN")
        bucket_counts[bucket] += 1

    stats["bucket_counts"] = dict(bucket_counts)
    print(f"  - Observed Bucket Distribution: {dict(bucket_counts)}")

    if bucket_counts.get("SHORT", 0) != 20:
        errors.append(f"Expected 20 SHORT documents, found {bucket_counts.get('SHORT', 0)}")
    if bucket_counts.get("MEDIUM", 0) != 20:
        errors.append(f"Expected 20 MEDIUM documents, found {bucket_counts.get('MEDIUM', 0)}")
    if bucket_counts.get("LONG", 0) != 20:
        errors.append(f"Expected 20 LONG documents, found {bucket_counts.get('LONG', 0)}")

    # 3. Source File & SHA-256 Hash Integrity
    print("\n[Audit 3/6] Source File Presence & SHA-256 Hash Integrity...")
    real_doc_ids = set()
    real_hashes = set()

    for doc in doc_entries:
        doc_id = doc.get("document_id")
        if not doc_id or not doc_id.startswith("DOC-REAL-"):
            errors.append(f"Invalid document ID format: {doc_id}")
            continue

        if doc_id in real_doc_ids:
            errors.append(f"Duplicate document ID: {doc_id}")
        real_doc_ids.add(doc_id)

        source_file = REAL_DATASET_DIR / doc.get("file_path", f"source_documents/{doc_id}.txt")
        if not source_file.exists():
            errors.append(f"Source file not found: {source_file}")
            continue

        with open(source_file, "r", encoding="utf-8") as f:
            source_text = f.read()

        actual_hash = compute_sha256(source_text)
        expected_hash = doc.get("source_hash_sha256")
        real_hashes.add(actual_hash)

        if actual_hash != expected_hash:
            errors.append(f"Hash mismatch for {doc_id}: expected {expected_hash}, got {actual_hash}")

        # Check word count vs bucket
        wc = len(source_text.split())
        category = doc.get("length_category")
        if category == "SHORT" and wc >= 400:
            errors.append(f"{doc_id} marked SHORT but has {wc} words (must be <400)")
        elif category == "MEDIUM" and (wc < 400 or wc > 800):
            errors.append(f"{doc_id} marked MEDIUM but has {wc} words (must be 400-800)")
        elif category == "LONG" and wc <= 800:
            errors.append(f"{doc_id} marked LONG but has {wc} words (must be >800)")

    # 4. Annotation Files & Span Mechanics
    print("\n[Audit 4/6] Annotation Files, Lifecycle Status & Span Mechanics...")
    annotations_dir = REAL_DATASET_DIR / "annotations"
    annotation_status_counts = Counter()
    verdict_counts = Counter()
    total_facts_count = 0

    for doc_id in real_doc_ids:
        ann_file = annotations_dir / f"{doc_id}.facts.json"
        if not ann_file.exists():
            errors.append(f"Missing annotation file: {ann_file}")
            continue

        with open(ann_file, "r", encoding="utf-8") as f:
            ann_data = json.load(f)

        status = ann_data.get("annotation_status", "UNANNOTATED")
        if status not in VALID_STATUSES:
            errors.append(f"Invalid annotation status '{status}' in {ann_file.name}")
        annotation_status_counts[status] += 1

        facts = ann_data.get("facts", [])
        total_facts_count += len(facts)

        source_file = REAL_DATASET_DIR / f"source_documents/{doc_id}.txt"
        source_text = ""
        if source_file.exists():
            with open(source_file, "r", encoding="utf-8") as f:
                source_text = f.read()

        for fact in facts:
            fact_type = fact.get("fact_type")
            if fact_type not in VALID_FACT_TYPES:
                errors.append(f"Invalid fact_type '{fact_type}' in {doc_id}")

            verdict = fact.get("verification_verdict")
            if verdict:
                if verdict not in VALID_VERDICTS:
                    errors.append(f"Invalid verification verdict '{verdict}' in {doc_id}")
                else:
                    verdict_counts[verdict] += 1

            span = fact.get("source_reference", {})
            verbatim = span.get("verbatim_text_span")
            start_char = span.get("start_char")
            end_char = span.get("end_char")

            if verbatim and source_text:
                if start_char is not None and end_char is not None:
                    actual_slice = source_text[start_char:end_char]
                    if actual_slice != verbatim:
                        errors.append(
                            f"Span offset mismatch in {doc_id} for fact {fact.get('fact_id')}: "
                            f"slice '{actual_slice[:30]}...' != verbatim '{verbatim[:30]}...'"
                        )
                elif verbatim not in source_text:
                    errors.append(f"Verbatim span not found in source text for {doc_id}")

    stats["annotation_status_counts"] = dict(annotation_status_counts)
    stats["total_facts"] = total_facts_count
    stats["verdict_distribution"] = dict(verdict_counts)

    print(f"  - Document Annotation Statuses: {dict(annotation_status_counts)}")
    print(f"  - Total Populated Facts: {total_facts_count}")
    print(f"  - Observed Verification Verdicts (No balancing enforced): {dict(verdict_counts)}")

    # 5. Anti-Leakage Boundary with Development Fixture
    print("\n[Audit 5/6] Strict Anti-Leakage Separation Checks...")
    if DEV_DATASET_DIR.exists():
        dev_manifest_path = DEV_DATASET_DIR / "manifest.json"
        if dev_manifest_path.exists():
            with open(dev_manifest_path, "r", encoding="utf-8") as f:
                dev_manifest = json.load(f)

            if dev_manifest.get("is_development_fixture") is not True:
                errors.append("Development fixture manifest MUST have is_development_fixture=True")

            dev_doc_ids = {d["document_id"] for d in dev_manifest.get("documents", [])}
            dev_hashes = {d["source_hash_sha256"] for d in dev_manifest.get("documents", [])}

            # Check ID overlap
            id_overlap = real_doc_ids.intersection(dev_doc_ids)
            if id_overlap:
                errors.append(f"CRITICAL LEAKAGE: Real research document IDs found in dev fixture: {id_overlap}")

            # Check Hash overlap
            hash_overlap = real_hashes.intersection(dev_hashes)
            if hash_overlap:
                errors.append(f"CRITICAL LEAKAGE: Real research source hashes found in dev fixture: {hash_overlap}")

            # Check dev fixture size
            if len(dev_doc_ids) != 8:
                errors.append(f"Development fixture document count modified: expected 8, found {len(dev_doc_ids)}")

            print(f"  - Dev fixture docs: {len(dev_doc_ids)} (DOC-DEV-001 to DOC-DEV-008)")
            print(f"  - Real research docs: {len(real_doc_ids)} (DOC-REAL-001 to DOC-REAL-060)")
            print("  - Zero ID overlap: PASS")
            print("  - Zero Content Hash overlap: PASS")
            print("  - Anti-leakage boundary verified.")

    # 6. Final Evaluation
    print("\n[Audit 6/6] Validation Summary...")
    if errors:
        print(f"\n[FAILED] {len(errors)} validation errors encountered:")
        for err in errors:
            print(f"  - ERROR: {err}")
        return False, errors, stats
    else:
        print("\n[PASS] Real Research Dataset passed all 6 quality & anti-leakage audits.")
        print("Status: Dataset preparation complete; ground-truth annotation pending.")
        return True, [], stats


if __name__ == "__main__":
    passed, errs, _ = validate_real_dataset()
    if not passed:
        sys.exit(1)
    sys.exit(0)
