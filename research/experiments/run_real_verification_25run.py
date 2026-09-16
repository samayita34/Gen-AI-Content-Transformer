"""
TransformAI Research Experiment: Track 2 — Verification Benchmark Evaluation (25 Items)
========================================================================================

SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 7: Comprehensive Quantitative Evaluation Benchmark
Track 2: Verification Quality (4-Class Verdict Classification)

Evaluates the M6 LLM-based Claim Verifier independently against the 25 FINAL benchmark items:
- Canonical Dataset: research/datasets/real_research/verification_benchmark/benchmark_manifest.json
- Target Documents: DOC-REAL-001 through DOC-REAL-005 (5 items each)
- 4-Class Verdict Taxonomy: SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, INSUFFICIENT_EVIDENCE
- Provider: Local Ollama (llama3.2)
- Persistence: Incremental raw per-item persistence BEFORE scoring

Outputs:
- Raw observations: research/results/real_verification_25run/raw/{benchmark_id}.json
- Scored metrics: research/results/real_verification_25run/processed/track2_verification_metrics.json
- Summary: research/results/real_verification_25run/processed/verification_summary.json
"""

import os
import sys
import json
import time
import uuid
import math
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Set workspace paths
ROOT_DIR = Path("C:/genai")
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.models.document import ChunkingStrategy
from app.services.document.models import ParsedDocument, DocumentElement, ElementType, SourceModality
from app.services.document.chunking import get_chunker
from app.services.generation.providers.factory import get_llm_provider
from app.services.verification.providers.llm import LLMClaimVerifier
from app.services.verification.models import (
    AtomicClaim,
    EvidenceMatch,
    ClaimVerificationResult,
    VerificationVerdict,
)
from research.experiments.evaluate_verification import evaluate_verification_predictions, CLASSES


def compute_dense_sim_vector(text: str, dim: int = 384) -> List[float]:
    """Deterministic normalized vector representation for dense chunk matching."""
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vec
    for word in words:
        h1 = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        h2 = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        for i in range(4):
            idx = (h1 + i * 31) % dim
            weight = ((h2 >> (i * 8)) & 0xFF) / 255.0 - 0.5
            vec[idx] += weight
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def cosine_sim(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    return max(0.0, min(1.0, float(dot)))


def default_json_serializer(obj: Any) -> Any:
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, (uuid.UUID, Path)):
        return str(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


async def run_track2_verification_benchmark():
    print("=" * 80)
    print("TransformAI: Track 2 — Verification Quality Benchmark Evaluation (25 Items)")
    print("=" * 80)

    # 1. Load Canonical Benchmark Manifest
    manifest_path = ROOT_DIR / "research" / "datasets" / "real_research" / "verification_benchmark" / "benchmark_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Canonical benchmark manifest not found at: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if manifest.get("annotation_status") != "FINAL":
        raise ValueError(f"Benchmark annotation status is not FINAL: {manifest.get('annotation_status')}")

    items = manifest.get("items", [])
    total_items = len(items)
    print(f"Loaded {total_items} FINAL benchmark items from {manifest_path.name}")
    print(f"Benchmark Version: {manifest.get('benchmark_version')} | Created: {manifest.get('created_at')}")
    print(f"Expected Distribution: {manifest.get('verdict_distribution')}")

    # 2. Setup Directories
    results_dir = ROOT_DIR / "research" / "results" / "real_verification_25run"
    raw_dir = results_dir / "raw"
    processed_dir = results_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 3. Setup LLM Provider & Verifier
    provider = get_llm_provider("ollama")
    verifier = LLMClaimVerifier(llm_provider=provider)
    chunker = get_chunker(ChunkingStrategy.STRUCTURE_AWARE, chunk_size=512, chunk_overlap=64)
    print(f"Provider: {provider.provider_name} | Model: {provider.model}")
    print(f"Verifier: {verifier.verifier_name}")
    print(f"Raw Output Dir: {raw_dir}")
    print(f"Processed Output Dir: {processed_dir}")
    print("-" * 80)

    # 4. Pre-load and chunk source documents
    dataset_dir = ROOT_DIR / "research" / "datasets" / "real_research"
    doc_cache: Dict[str, Dict[str, Any]] = {}

    for doc_id in ["DOC-REAL-001", "DOC-REAL-002", "DOC-REAL-003", "DOC-REAL-004", "DOC-REAL-005"]:
        doc_file = dataset_dir / "source_documents" / f"{doc_id}.txt"
        if not doc_file.exists():
            raise FileNotFoundError(f"Source document not found: {doc_file}")
        with open(doc_file, "r", encoding="utf-8") as f:
            source_text = f.read()

        parsed_doc = ParsedDocument(
            raw_text=source_text,
            modality=SourceModality.TEXT,
            elements=[
                DocumentElement(
                    element_type=ElementType.PARAGRAPH,
                    text=p.strip(),
                    page_number=1,
                    section_title=f"Section {idx+1}",
                )
                for idx, p in enumerate(source_text.strip().split("\n\n"))
                if p.strip()
            ],
        )
        chunks = chunker.chunk(parsed_doc)
        chunk_embeddings = [compute_dense_sim_vector(c.content) for c in chunks]
        doc_cache[doc_id] = {
            "source_text": source_text,
            "chunks": chunks,
            "embeddings": chunk_embeddings,
            "doc_uuid": uuid.uuid4(),
        }

    # 5. Run Verification on each benchmark item
    raw_records: List[Dict[str, Any]] = []
    gold_verdicts: List[str] = []
    pred_verdicts: List[str] = []
    latencies: List[float] = []
    failures: List[Dict[str, Any]] = []

    pacing_seconds = float(os.getenv("LLM_REQUEST_PACING_SECONDS", "1.5"))

    for idx, item in enumerate(items, start=1):
        b_id = item["benchmark_id"]
        doc_id = item["document_id"]
        claim_text = item["claim"]
        expected_verdict = item["expected_verdict"]

        print(f"\n[{idx:02d}/{total_items:02d}] Evaluating {b_id} ({doc_id})...")
        print(f"  Claim: \"{claim_text[:90]}...\"")
        print(f"  Expected: {expected_verdict}")

        # Independent retrieval against the source document chunks
        doc_info = doc_cache[doc_id]
        chunks = doc_info["chunks"]
        chunk_embs = doc_info["embeddings"]
        claim_vec = compute_dense_sim_vector(claim_text)

        # Rank chunks by similarity
        scored_chunks = []
        for c, c_emb in zip(chunks, chunk_embs):
            sim = cosine_sim(claim_vec, c_emb)
            scored_chunks.append((sim, c))
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:3]

        evidence_matches = [
            EvidenceMatch(
                chunk_id=uuid.uuid4(),
                document_id=doc_info["doc_uuid"],
                chunk_content=c.content,
                similarity_score=round(sim, 4),
                section_title=c.section_title or "Overview",
                page_number=c.page_number or 1,
            )
            for sim, c in top_chunks
        ]

        atomic_claim = AtomicClaim(
            claim_id=uuid.uuid4(),
            text=claim_text,
            normalized_text=claim_text,
        )

        t0 = time.perf_counter()
        status = "SUCCESS"
        error_msg = None
        pred_verdict_str = "INSUFFICIENT_EVIDENCE"
        confidence = None
        explanation = ""

        try:
            res = await verifier.verify_claim(atomic_claim, evidence_matches)
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            pred_verdict_str = res.verdict.value.upper()
            confidence = res.confidence
            explanation = res.explanation
        except Exception as exc:
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            status = "FAILED"
            error_msg = str(exc)
            pred_verdict_str = "INSUFFICIENT_EVIDENCE"
            explanation = f"Verification execution failed: {exc}"
            failures.append({
                "benchmark_id": b_id,
                "document_id": doc_id,
                "error": error_msg,
            })
            print(f"  [ERROR] Verification failed for {b_id}: {exc}")

        is_correct = (pred_verdict_str == expected_verdict)
        latencies.append(latency_ms)
        gold_verdicts.append(expected_verdict)
        pred_verdicts.append(pred_verdict_str)

        print(f"  Predicted: {pred_verdict_str} | Match: {'CORRECT' if is_correct else 'INCORRECT'} | Latency: {latency_ms:.1f}ms")

        # Create raw observation record
        raw_record = {
            "benchmark_id": b_id,
            "document_id": doc_id,
            "claim": claim_text,
            "expected_verdict": expected_verdict,
            "predicted_verdict": pred_verdict_str,
            "is_correct": is_correct,
            "confidence": confidence,
            "explanation": explanation,
            "evidence_matches": [
                {
                    "similarity_score": em.similarity_score,
                    "section_title": em.section_title,
                    "page_number": em.page_number,
                    "content_preview": em.chunk_content[:200] + ("..." if len(em.chunk_content) > 200 else ""),
                }
                for em in evidence_matches
            ],
            "claim_origin": item.get("claim_origin"),
            "notes": item.get("notes"),
            "metadata": item.get("metadata"),
            "status": status,
            "error": error_msg,
            "latency_ms": latency_ms,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "provider": provider.provider_name,
            "model": provider.model,
        }

        # 5. Persist raw per-item output IMMEDIATELY
        raw_file = raw_dir / f"{b_id}.json"
        with open(raw_file, "w", encoding="utf-8") as rf:
            json.dump(raw_record, rf, indent=2, default=default_json_serializer)

        raw_records.append(raw_record)

        if pacing_seconds > 0 and idx < total_items:
            await asyncio.sleep(pacing_seconds)

    print("\n" + "=" * 80)
    print("All 25 Track 2 Verification Items Processed. Scoring predictions...")
    print("=" * 80)

    # 6. Compute 4-Class Classification Metrics
    report = evaluate_verification_predictions(gold_verdicts, pred_verdicts)

    # Calculate overall accuracy
    correct_count = sum(1 for g, p in zip(gold_verdicts, pred_verdicts) if g == p)
    accuracy = round(correct_count / total_items, 4) if total_items > 0 else 0.0

    # Latency summary
    mean_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    sorted_lat = sorted(latencies)
    median_lat = sorted_lat[len(sorted_lat) // 2] if sorted_lat else 0.0
    min_lat = min(latencies) if latencies else 0.0
    max_lat = max(latencies) if latencies else 0.0

    metrics_payload = {
        "benchmark_name": manifest.get("benchmark_name"),
        "total_items": total_items,
        "evaluated_items": len(raw_records),
        "successful_items": len(raw_records) - len(failures),
        "failed_items": len(failures),
        "failures": failures,
        "accuracy": accuracy,
        "correct_predictions": correct_count,
        "macro_precision": report.macro_precision,
        "macro_recall": report.macro_recall,
        "macro_f1": report.macro_f1,
        "per_class": {
            cls_name: {
                "verdict": m.verdict,
                "support": m.support,
                "true_positives": m.true_positives,
                "false_positives": m.false_positives,
                "false_negatives": m.false_negatives,
                "precision": m.precision,
                "recall": m.recall,
                "f1_score": m.f1_score,
            }
            for cls_name, m in report.per_class.items()
        },
        "confusion_matrix": report.confusion_matrix,
        "binary_analysis": {
            "binary_accuracy": report.binary_accuracy,
            "binary_f1": report.binary_f1,
            "description": "SOURCE_SUPPORTED (SUPPORTED + PARTIALLY_SUPPORTED) vs NOT_SOURCE_SUPPORTED (CONTRADICTED + INSUFFICIENT_EVIDENCE)",
        },
        "telemetry": {
            "mean_latency_ms": mean_lat,
            "median_latency_ms": median_lat,
            "min_latency_ms": min_lat,
            "max_latency_ms": max_lat,
            "total_latency_ms": round(sum(latencies), 2),
            "provider": provider.provider_name,
            "model": provider.model,
        },
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    # 7. Persist Processed Results
    metrics_file = processed_dir / "track2_verification_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as mf:
        json.dump(metrics_payload, mf, indent=2)

    summary_file = processed_dir / "verification_summary.json"
    summary_payload = {
        "benchmark_items": raw_records,
        "metrics": metrics_payload,
    }
    with open(summary_file, "w", encoding="utf-8") as sf:
        json.dump(summary_payload, sf, indent=2, default=default_json_serializer)

    print(f"\nSaved Track 2 metrics to: {metrics_file}")
    print(f"Saved complete summary to: {summary_file}")

    # 8. Print Results Summary
    print("\n" + "=" * 80)
    print("TRACK 2 VERIFICATION QUALITY BENCHMARK RESULTS")
    print("=" * 80)
    print(f"Total Benchmark Items: {total_items}")
    print(f"Overall Accuracy:      {accuracy:.4f} ({correct_count}/{total_items})")
    print(f"Macro Precision:       {report.macro_precision:.4f}")
    print(f"Macro Recall:          {report.macro_recall:.4f}")
    print(f"Macro F1:              {report.macro_f1:.4f}")
    print(f"Binary Accuracy:       {report.binary_accuracy:.4f}")
    print(f"Binary F1:             {report.binary_f1:.4f}")
    print(f"Mean Latency:          {mean_lat:.1f}ms (Median: {median_lat:.1f}ms)")
    print("-" * 80)
    print("PER-CLASS CLASSIFICATION METRICS:")
    print(f"{'Class':<25} {'Support':<10} {'Precision':<12} {'Recall':<12} {'F1-Score':<12}")
    for cls_name, m in report.per_class.items():
        print(f"{cls_name:<25} {m.support:<10} {m.precision:<12.4f} {m.recall:<12.4f} {m.f1_score:<12.4f}")
    print("-" * 80)
    print("CONFUSION MATRIX (Rows: Gold, Columns: Predicted):")
    print(f"{'Gold \\ Pred':<25} " + " ".join(f"{c[:10]:<12}" for c in CLASSES))
    for gold_cls in CLASSES:
        row = " ".join(f"{report.confusion_matrix[gold_cls][pred_cls]:<12}" for pred_cls in CLASSES)
        print(f"{gold_cls:<25} {row}")
    print("=" * 80)

    return metrics_payload


if __name__ == "__main__":
    asyncio.run(run_track2_verification_benchmark())
