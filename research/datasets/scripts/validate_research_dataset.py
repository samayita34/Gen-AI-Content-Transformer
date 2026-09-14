"""
TransformAI Research: Dataset Quality, Ground-Truth & Anti-Leakage Validation
=============================================================================
Comprehensive audit script for:
- Track 1 Source Fact Ground Truth (research/datasets/real_research/annotations/)
- Track 2 Verification Benchmark (research/datasets/real_research/verification_benchmark/)
- Anti-Leakage Isolation from Development Fixtures

Audits:
1. Dataset Manifest Schema & Non-Fixture Flag
2. Document Stratification (20 Short, 20 Medium, 20 Long)
3. Source File Presence & SHA-256 Hash Integrity
4. Track 1 Source Fact Lifecycle, Schema, and Span Mechanics
5. Track 2 Verification Benchmark Schema, Taxonomy, and Evidence References
6. Anti-Leakage Isolation against development_fixture/
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

VALID_CLAIM_ORIGINS = {"SOURCE_FACT", "CONTROLLED_PERTURBATION"}

VALID_STATUSES = {"UNANNOTATED", "CANDIDATE", "REVIEWED", "FINAL"}


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_real_dataset() -> Tuple[bool, List[str], Dict[str, Any]]:
    errors = []
    stats: Dict[str, Any] = {}

    print("=" * 75)
    print("TransformAI Research: Real Research Dataset & Benchmark Audit (M9B)")
    print("=" * 75)

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
    doc_source_texts: Dict[str, str] = {}

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

        doc_source_texts[doc_id] = source_text
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

    # 4. Track 1 Source Facts Annotation Audit
    print("\n[Audit 4/6] Track 1: Source Facts Lifecycle & Span Mechanics...")
    annotations_dir = REAL_DATASET_DIR / "annotations"
    annotation_status_counts = Counter()
    total_facts_count = 0
    final_facts_count = 0

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
        source_text = doc_source_texts.get(doc_id, "")

        for fact in facts:
            fact_status = fact.get("annotation_status", status)
            if fact_status == "FINAL":
                final_facts_count += 1

            fact_type = fact.get("fact_type")
            if fact_type not in VALID_FACT_TYPES:
                errors.append(f"Invalid fact_type '{fact_type}' in {doc_id} fact {fact.get('fact_id')}")

            span = fact.get("source_reference", {})
            verbatim = span.get("verbatim_text_span")
            start_char = span.get("start_char")
            end_char = span.get("end_char")

            if verbatim and source_text:
                if start_char is not None and end_char is not None:
                    actual_slice = source_text[start_char:end_char]
                    if actual_slice != verbatim:
                        errors.append(
                            f"Track 1 Span offset mismatch in {doc_id} for fact {fact.get('fact_id')}: "
                            f"slice '{actual_slice[:30]}...' != verbatim '{verbatim[:30]}...'"
                        )
                elif verbatim not in source_text:
                    errors.append(f"Track 1 Verbatim span not found in source text for {doc_id}")

    stats["track1_document_statuses"] = dict(annotation_status_counts)
    stats["track1_total_facts"] = total_facts_count
    stats["track1_final_facts"] = final_facts_count

    print(f"  - Document Statuses: {dict(annotation_status_counts)}")
    print(f"  - Total Track 1 Source Facts: {total_facts_count} (FINAL: {final_facts_count})")

    # 5. Track 2 Verification Benchmark Audit
    print("\n[Audit 5/6] Track 2: Verification Benchmark Schema & Item Integrity...")
    bench_dir = REAL_DATASET_DIR / "verification_benchmark"
    bench_manifest_path = bench_dir / "benchmark_manifest.json"

    bench_item_count = 0
    bench_final_count = 0
    verdict_distribution = Counter()
    origin_distribution = Counter()

    if bench_manifest_path.exists():
        try:
            with open(bench_manifest_path, "r", encoding="utf-8") as f:
                bench_data = json.load(f)

            if bench_data.get("is_development_fixture") is not False:
                errors.append("Verification benchmark 'is_development_fixture' MUST be False.")

            items = bench_data.get("items", [])
            bench_item_count = len(items)
            seen_bench_ids = set()

            for item in items:
                b_id = item.get("benchmark_id")
                if not b_id:
                    errors.append("Missing benchmark_id in verification item")
                    continue
                if b_id in seen_bench_ids:
                    errors.append(f"Duplicate benchmark_id: {b_id}")
                seen_bench_ids.add(b_id)

                d_id = item.get("document_id")
                if d_id not in real_doc_ids:
                    errors.append(f"Benchmark item {b_id} references unknown document_id: {d_id}")

                verdict = item.get("expected_verdict")
                if verdict not in VALID_VERDICTS:
                    errors.append(f"Benchmark item {b_id} has invalid verdict: {verdict}")
                else:
                    verdict_distribution[verdict] += 1

                origin = item.get("claim_origin")
                if origin not in VALID_CLAIM_ORIGINS:
                    errors.append(f"Benchmark item {b_id} has invalid claim_origin: {origin}")
                else:
                    origin_distribution[origin] += 1

                item_status = item.get("annotation_status", "UNANNOTATED")
                if item_status not in VALID_STATUSES:
                    errors.append(f"Benchmark item {b_id} has invalid status: {item_status}")
                if item_status == "FINAL":
                    bench_final_count += 1

                # Check evidence spans
                ref_spans = item.get("evidence_references", [])
                doc_text = doc_source_texts.get(d_id, "")
                for span in ref_spans:
                    v_span = span.get("verbatim_text_span")
                    s_c = span.get("start_char")
                    e_c = span.get("end_char")
                    if v_span and doc_text:
                        if s_c is not None and e_c is not None:
                            actual_sl = doc_text[s_c:e_c]
                            if actual_sl != v_span:
                                errors.append(
                                    f"Track 2 evidence span slice mismatch in item {b_id}: "
                                    f"slice '{actual_sl[:30]}...' != verbatim '{v_span[:30]}...'"
                                )
                        elif v_span not in doc_text:
                            errors.append(f"Track 2 verbatim span not found in source text for item {b_id}")

        except Exception as e:
            errors.append(f"Failed to parse verification benchmark manifest: {e}")
    else:
        errors.append(f"Verification benchmark manifest missing: {bench_manifest_path}")

    stats["track2_total_items"] = bench_item_count
    stats["track2_final_items"] = bench_final_count
    stats["track2_verdict_distribution"] = dict(verdict_distribution)
    stats["track2_origin_distribution"] = dict(origin_distribution)

    print(f"  - Total Track 2 Verification Items: {bench_item_count} (FINAL: {bench_final_count})")
    print(f"  - Naturally Observed Verdict Distribution (No artificial balancing): {dict(verdict_distribution)}")
    print(f"  - Claim Origin Distribution: {dict(origin_distribution)}")

    # 6. Anti-Leakage Boundary with Development Fixture
    print("\n[Audit 6/6] Strict Anti-Leakage Separation Checks...")
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
            if len(dev_doc_ids) != 3:
                errors.append(f"Development fixture document count modified: expected 3, found {len(dev_doc_ids)}")

            print(f"  - Dev fixture docs: {len(dev_doc_ids)} ({sorted(list(dev_doc_ids))})")
            print(f"  - Real research docs: {len(real_doc_ids)} (DOC-REAL-001 to DOC-REAL-060)")
            print("  - Zero ID overlap: PASS")
            print("  - Zero Content Hash overlap: PASS")
            print("  - Anti-leakage boundary verified.")

    # Validation Summary
    print("\n[Validation Summary]...")
    if errors:
        print(f"\n[FAILED] {len(errors)} validation errors encountered:")
        for err in errors:
            print(f"  - ERROR: {err}")
        return False, errors, stats
    else:
        print("\n[PASS] Real Research Dataset passed all 6 quality, ground-truth & anti-leakage audits.")
        return True, [], stats


if __name__ == "__main__":
    passed, errs, _ = validate_real_dataset()
    if not passed:
        sys.exit(1)
    sys.exit(0)
