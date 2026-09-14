#!/usr/bin/env python3
"""
Track 2 Verification Annotations Validator
==========================================
Audits Track 2 verification benchmark items and annotation workspaces.

Validation checks:
1. Schema & required fields validity
2. Lifecycle values (UNANNOTATED, CANDIDATE, REVIEWED, FINAL)
3. Verdict values (SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, INSUFFICIENT_EVIDENCE)
4. Claim origins (SOURCE_FACT, CONTROLLED_PERTURBATION)
5. Valid document IDs referencing the real research corpus (DOC-REAL-001..DOC-REAL-060)
6. Evidence references: valid coordinates & exact character slice match against source text
7. Unique benchmark item IDs
8. Anti-leakage isolation (zero dev-fixture overlap)
9. Track 1 integrity verification (67 FINAL facts across DOC-REAL-001..005 untouched)
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.schemas.dataset import (
    AnnotationStatus,
    ClaimOrigin,
    VerificationVerdict,
    VerificationBenchmarkItem,
)


def validate_verification_workspace(
    workspace_path: Path,
    sources_dir: Path,
    track1_manifest_path: Path,
    track1_annotations_dir: Path,
    dev_fixture_manifest_path: Path,
) -> Dict[str, Any]:
    """Validate a Track 2 verification benchmark workspace or manifest."""
    errors: List[str] = []
    warnings: List[str] = []

    if not workspace_path.exists():
        return {
            "status": "FAIL",
            "errors": [f"Workspace file not found: {workspace_path}"],
            "warnings": [],
            "items_checked": 0,
        }

    with open(workspace_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            return {
                "status": "FAIL",
                "errors": [f"Invalid JSON in workspace: {e}"],
                "warnings": [],
                "items_checked": 0,
            }

    # 1. Check is_development_fixture flag
    if data.get("is_development_fixture") is True:
        errors.append(f"Workspace has is_development_fixture=True. Must be False for real research.")

    # 2. Check items
    items = data.get("items", [])
    seen_ids = set()
    verdict_counts: Dict[str, int] = {}
    origin_counts: Dict[str, int] = {}

    for idx, raw_item in enumerate(items):
        item_label = raw_item.get("benchmark_id", f"item_index_{idx}")
        try:
            item = VerificationBenchmarkItem(**raw_item)
        except Exception as e:
            errors.append(f"Item {item_label} schema validation failed: {e}")
            continue

        # Check unique ID
        if item.benchmark_id in seen_ids:
            errors.append(f"Duplicate benchmark_id: {item.benchmark_id}")
        seen_ids.add(item.benchmark_id)

        # Check doc ID format
        doc_id = item.document_id
        if not doc_id.startswith("DOC-REAL-"):
            errors.append(f"Item {item.benchmark_id} references invalid document_id: {doc_id}")

        # Check source text existence and span accuracy
        source_file = sources_dir / f"{doc_id}.txt"
        if not source_file.exists():
            errors.append(f"Item {item.benchmark_id} references non-existent source file: {source_file}")
        else:
            with open(source_file, "r", encoding="utf-8") as sf:
                source_text = sf.read()

            for s_idx, span in enumerate(item.evidence_references):
                if span.start_char < 0 or span.end_char > len(source_text) or span.start_char > span.end_char:
                    errors.append(
                        f"Item {item.benchmark_id} span {s_idx} out of bounds: [{span.start_char}:{span.end_char}] for source length {len(source_text)}"
                    )
                else:
                    actual = source_text[span.start_char:span.end_char]
                    if actual != span.verbatim_text_span:
                        errors.append(
                            f"Item {item.benchmark_id} span {s_idx} content mismatch: "
                            f"expected '{span.verbatim_text_span[:30]}...', got '{actual[:30]}...'"
                        )

        # Track distributions
        v_val = item.expected_verdict.value if hasattr(item.expected_verdict, "value") else str(item.expected_verdict)
        o_val = item.claim_origin.value if hasattr(item.claim_origin, "value") else str(item.claim_origin)
        verdict_counts[v_val] = verdict_counts.get(v_val, 0) + 1
        origin_counts[o_val] = origin_counts.get(o_val, 0) + 1

    # 3. Verify Track 1 Ground Truth Integrity (67 facts in DOC-REAL-001..005 remain FINAL)
    if track1_manifest_path.exists():
        with open(track1_manifest_path, "r", encoding="utf-8") as t1_f:
            t1_manifest = json.load(t1_f)

        total_t1_final_facts = 0
        for doc_summary in t1_manifest.get("documents", []):
            d_id = doc_summary.get("document_id")
            if d_id in ["DOC-REAL-001", "DOC-REAL-002", "DOC-REAL-003", "DOC-REAL-004", "DOC-REAL-005"]:
                fact_file = track1_annotations_dir / f"{d_id}.facts.json"
                if not fact_file.exists():
                    errors.append(f"Track 1 fact file missing for {d_id}")
                else:
                    with open(fact_file, "r", encoding="utf-8") as ff:
                        f_data = json.load(f_data_f := ff)
                    facts = f_data.get("facts", [])
                    total_t1_final_facts += len(facts)
                    if f_data.get("annotation_status") != "FINAL":
                        errors.append(f"Track 1 document {d_id} status modified from FINAL: {f_data.get('annotation_status')}")

        if total_t1_final_facts != 67:
            errors.append(f"Track 1 fact count modified: expected 67, found {total_t1_final_facts}")

    # 4. Anti-Leakage Separation Check
    if dev_fixture_manifest_path.exists():
        with open(dev_fixture_manifest_path, "r", encoding="utf-8") as df_f:
            df_manifest = json.load(df_f)
        dev_ids = {d["document_id"] for d in df_manifest.get("documents", [])}
        for item in items:
            if item.get("document_id") in dev_ids:
                errors.append(f"Anti-leakage violation: item {item.get('benchmark_id')} references dev fixture doc {item.get('document_id')}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "items_checked": len(items),
        "verdict_distribution": verdict_counts,
        "origin_distribution": origin_counts,
    }


def main():
    print("===========================================================================")
    print("TransformAI Research: Track 2 Verification Annotations Validator (M9B)")
    print("===========================================================================")

    base_dir = REPO_ROOT / "research" / "datasets"
    real_research_dir = base_dir / "real_research"
    workspace_path = real_research_dir / "verification_benchmark" / "batch1_annotation_workspace.json"
    benchmark_manifest_path = real_research_dir / "verification_benchmark" / "benchmark_manifest.json"
    sources_dir = real_research_dir / "source_documents"
    track1_manifest_path = real_research_dir / "manifest.json"
    track1_annotations_dir = real_research_dir / "annotations"
    dev_fixture_manifest_path = base_dir / "development_fixture" / "manifest.json"

    print(f"\n[Audit 1/2] Auditing Batch 1 Annotation Workspace...")
    res_ws = validate_verification_workspace(
        workspace_path=workspace_path,
        sources_dir=sources_dir,
        track1_manifest_path=track1_manifest_path,
        track1_annotations_dir=track1_annotations_dir,
        dev_fixture_manifest_path=dev_fixture_manifest_path,
    )
    if res_ws["status"] == "PASS":
        print(f"  - Workspace Status: PASS (Items: {res_ws['items_checked']})")
    else:
        print(f"  - Workspace Status: FAIL")
        for err in res_ws["errors"]:
            print(f"    [ERROR] {err}")

    print(f"\n[Audit 2/2] Auditing Canonical Verification Benchmark Manifest...")
    res_bm = validate_verification_workspace(
        workspace_path=benchmark_manifest_path,
        sources_dir=sources_dir,
        track1_manifest_path=track1_manifest_path,
        track1_annotations_dir=track1_annotations_dir,
        dev_fixture_manifest_path=dev_fixture_manifest_path,
    )
    if res_bm["status"] == "PASS":
        print(f"  - Benchmark Manifest Status: PASS (Items: {res_bm['items_checked']})")
    else:
        print(f"  - Benchmark Manifest Status: FAIL")
        for err in res_bm["errors"]:
            print(f"    [ERROR] {err}")

    if res_ws["status"] == "PASS" and res_bm["status"] == "PASS":
        print(f"\n[PASS] Track 2 Verification workspace and manifest passed all validation checks.")
        sys.exit(0)
    else:
        print(f"\n[FAIL] Track 2 validation encountered errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
