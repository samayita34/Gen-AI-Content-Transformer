"""
TransformAI Research Experiment: Verification Agent Operational Benchmark
========================================================================

SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 6: Verification Agent — Claim-Level Source-Grounded Verification

Objective:
Empirically evaluate the operational latency, independent retrieval behavior,
and verdict classification pipeline of the Claim-Level Verification Agent across
supported, contradicted, and ungrounded claim scenarios.

Operational Telemetry Recorded:
- claim_extraction_latency_ms
- evidence_retrieval_latency_ms
- verification_latency_ms
- total_verification_latency_ms
- number_of_claims
- number_of_evidence_chunks_retrieved
- verdict_distribution (raw counts: supported, contradicted, partially_supported, insufficient_evidence)
- provider / model identifier

NOTE ON RESEARCH RIGOR:
Quantitative evaluation metrics (Precision, Recall, F1, Hallucination Rate,
Factual Consistency Percentage) are NOT benchmarked or claimed in Milestone 6.
This experiment measures operational integration telemetry only.
Formal quantitative verification evaluation against labeled datasets is deferred to Milestone 7.

Output:
Saves structured experiment results to `research/results/verification_comparison.json`.
"""

import os
import sys
import json
import time
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, List

os.environ["TRANSFORMAI_TESTING"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.models.document import ChunkingStrategy
from app.services.document.models import ParsedDocument, DocumentElement, ElementType, SourceModality
from app.services.document.chunking import get_chunker
from app.services.embeddings.hf_local import default_embedding_provider
from app.services.verification.models import (
    AtomicClaim,
    ClaimType,
    EvidenceMatch,
    VerificationVerdict,
    VerificationReport,
)
from app.services.verification.extractor import ClaimExtractor
from app.services.verification.providers.mock import MockVerificationJudge


SOURCE_DOCUMENT_TEXT = """# TransformAI System Architecture
TransformAI provides automated source-grounded content transformation using generative AI.
The system uses PostgreSQL 16 with the pgvector extension for dense vector similarity search.
Embeddings are computed locally using the all-MiniLM-L6-v2 SentenceTransformer model in 384 dimensions.
The retrieval engine uses cosine distance converted to cosine similarity on a 0.0 to 1.0 scale.
The platform supports multi-format content synthesis including Executive Summaries, Advisories, Slides, and Video Scripts.
"""

TEST_CASES = [
    {
        "scenario": "Grounded Executive Summary (Fully Supported by Source)",
        "output_type": "executive_summary",
        "content": {
            "title": "Executive Summary",
            "overview": "TransformAI provides automated source-grounded content transformation using generative AI.",
            "key_points": [
                "PostgreSQL 16 with pgvector powers dense vector similarity search.",
                "Embeddings use the 384-dimensional all-MiniLM-L6-v2 model.",
            ],
            "conclusion": "The platform supports Executive Summaries, Advisories, Slides, and Video Scripts.",
        },
    },
    {
        "scenario": "Perturbed Advisory (Deliberate Contradictions Injected)",
        "output_type": "advisory",
        "content": {
            "title": "Advisory Briefing",
            "situation": "This assertion is a deliberate contradiction that conflicts with all source facts.",
            "key_information": [
                "PostgreSQL 16 with pgvector powers dense vector similarity search.",
            ],
            "conclusion": "Discrepancy detected in source operations.",
        },
    },
    {
        "scenario": "Ungrounded Presentation (External / Insufficient Evidence Facts)",
        "output_type": "presentation",
        "content": {
            "presentation_title": "Quantum Computing",
            "slides": [
                {
                    "slide_number": 1,
                    "title": "Quantum Teleportation",
                    "bullets": [
                        "Quantum supercomputers achieve teleportation at absolute zero.",
                        "Subatomic entanglement replaces standard semiconductor chips.",
                    ],
                    "speaker_notes": "Unrelated topic completely absent from the source.",
                }
            ],
        },
    },
]


async def run_verification_experiment() -> Dict[str, Any]:
    print("=" * 80)
    print("TransformAI: Running Verification Agent Benchmark (Milestone 6)")
    print("=" * 80)

    # 1. Prepare Source In-Memory Chunk Index & Dense Embeddings
    parsed_doc = ParsedDocument(
        elements=[
            DocumentElement(
                element_type=ElementType.PARAGRAPH,
                text=line.strip(),
                page_number=1,
                section_title="System Overview",
                modality=SourceModality.TEXT,
            )
            for line in SOURCE_DOCUMENT_TEXT.strip().split("\n")
            if line.strip()
        ],
        raw_text=SOURCE_DOCUMENT_TEXT,
        modality=SourceModality.TEXT,
    )
    chunker = get_chunker(ChunkingStrategy.STRUCTURE_AWARE)
    source_chunks = chunker.chunk(parsed_doc)
    chunk_texts = [c.content for c in source_chunks]
    chunk_embeddings = await default_embedding_provider.embed_batch(chunk_texts)

    judge = MockVerificationJudge()
    doc_id = uuid.uuid4()
    scenario_runs: List[Dict[str, Any]] = []

    for tc in TEST_CASES:
        scenario_name = tc["scenario"]
        output_type = tc["output_type"]
        content = tc["content"]
        print(f"\nEvaluating Scenario: {scenario_name}...")

        # A. Claim Extraction
        t0 = time.perf_counter()
        claims = ClaimExtractor.extract_from_transformation(content, output_type)
        extraction_latency_ms = (time.perf_counter() - t0) * 1000

        # B. Independent Evidence Retrieval & Verification
        retrieval_latencies: List[float] = []
        verification_latencies: List[float] = []
        claim_results: List[Dict[str, Any]] = []

        verdict_counts = {
            "supported": 0,
            "contradicted": 0,
            "partially_supported": 0,
            "insufficient_evidence": 0,
        }
        total_evidence_chunks_retrieved = 0

        for claim in claims:
            # Independent Dense Search
            t_ret = time.perf_counter()
            claim_emb = await default_embedding_provider.embed_text(claim.normalized_statement)

            # Compute Cosine Similarities against indexed source chunks
            matches: List[EvidenceMatch] = []
            for idx, (sc, sc_emb) in enumerate(zip(source_chunks, chunk_embeddings)):
                # Dot product cosine sim
                sim = sum(a * b for a, b in zip(claim_emb, sc_emb))
                sim = max(0.0, min(1.0, float(sim)))
                if sim >= 0.20:
                    matches.append(
                        EvidenceMatch(
                            chunk_id=uuid.uuid4(),
                            document_id=doc_id,
                            chunk_content=sc.content,
                            similarity_score=round(sim, 4),
                            page_number=sc.page_number,
                            section_title=sc.section_title,
                            relevance_snippet=sc.content[:200],
                        )
                    )
            matches.sort(key=lambda m: m.similarity_score, reverse=True)
            top_matches = matches[:3]
            total_evidence_chunks_retrieved += len(top_matches)
            retrieval_latencies.append((time.perf_counter() - t_ret) * 1000)

            # Claim–Evidence Verification Evaluation
            t_ver = time.perf_counter()
            verdict, confidence, explanation = await judge.evaluate_claim(claim, top_matches)
            verification_latencies.append((time.perf_counter() - t_ver) * 1000)

            verdict_counts[verdict.value] += 1
            claim_results.append(
                {
                    "statement": claim.statement,
                    "claim_type": claim.claim_type.value,
                    "source_field": claim.context_source_field,
                    "verdict": verdict.value,
                    "confidence": round(confidence, 2),
                    "explanation": explanation,
                    "evidence_matches_count": len(top_matches),
                }
            )

        avg_ret_ms = sum(retrieval_latencies) / len(retrieval_latencies) if retrieval_latencies else 0.0
        avg_ver_ms = sum(verification_latencies) / len(verification_latencies) if verification_latencies else 0.0
        total_latency_ms = extraction_latency_ms + sum(retrieval_latencies) + sum(verification_latencies)

        entry = {
            "scenario": scenario_name,
            "output_type": output_type,
            "telemetry": {
                "claim_extraction_latency_ms": round(extraction_latency_ms, 2),
                "total_evidence_retrieval_latency_ms": round(sum(retrieval_latencies), 2),
                "total_judge_verification_latency_ms": round(sum(verification_latencies), 2),
                "total_verification_pipeline_latency_ms": round(total_latency_ms, 2),
                "number_of_claims": len(claims),
                "number_of_evidence_chunks_retrieved": total_evidence_chunks_retrieved,
            },
            "verdict_distribution": verdict_counts,
            "claims": claim_results,
        }
        scenario_runs.append(entry)

        print(f"  - Extracted Claims: {len(claims)}")
        print(f"  - Verdicts: {verdict_counts}")
        print(f"  - Pipeline Latency: {total_latency_ms:.2f} ms")

    results_data = {
        "metadata": {
            "experiment_name": "verification_agent_operational_benchmark",
            "milestone": "Milestone 6",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "verification_provider": judge.judge_name,
            "embedding_model": default_embedding_provider.model_name,
            "token_usage": None,
            "evaluation_notice": "Operational verification integration benchmark only. Quantitative verification evaluation is deferred to Milestone 7.",
        },
        "scenarios": scenario_runs,
    }

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "verification_comparison.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\nSuccessfully written verification benchmark results to {out_file}")
    return results_data


if __name__ == "__main__":
    asyncio.run(run_verification_experiment())
