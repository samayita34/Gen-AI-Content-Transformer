"""
TransformAI Research Experiment: Verification Methods Operational Benchmark
===========================================================================

SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 6: Verification Agent — Claim-Level Source-Grounded Verification

Objective:
Empirically evaluate and compare 3 verification architectures on operational telemetry:
- Method 0: No Verification (Baseline - zero verification overhead)
- Method 1: Retrieval-Based Evidence Collection + Whole-Output Verification (Coarse-grained)
- Method 2: Retrieval + Structured Claim Verification (Fine-grained atomic claim extraction + independent retrieval + claim-level judge)

Operational Telemetry Recorded:
- method_name
- claim_extraction_latency_ms
- evidence_retrieval_latency_ms
- verification_latency_ms
- total_verification_latency_ms
- number_of_claims
- number_of_evidence_chunks_retrieved
- verdict_distribution (raw counts: supported, contradicted, partially_supported, insufficient_evidence)
- provider_name / model_name
- token_usage (None / provider returned only, never fabricated)

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
from typing import Dict, Any, List, Optional

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
    ClaimVerificationResult,
)
from app.services.verification.extractor import MockClaimExtractor
from app.services.verification.normalizer import ClaimNormalizer
from app.services.verification.providers.mock import MockClaimVerifier


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


async def run_method_0_no_verification() -> Dict[str, Any]:
    """Method 0: No Verification (Baseline)."""
    return {
        "method_id": "method_0_none",
        "method_name": "Method 0: No Verification",
        "description": "Direct generation output without post-hoc verification.",
        "telemetry": {
            "claim_extraction_latency_ms": 0.0,
            "evidence_retrieval_latency_ms": 0.0,
            "verification_latency_ms": 0.0,
            "total_verification_latency_ms": 0.0,
            "number_of_claims": 0,
            "number_of_evidence_chunks_retrieved": 0,
            "token_usage": None,
        },
        "verdict_distribution": {
            "supported": 0,
            "contradicted": 0,
            "partially_supported": 0,
            "insufficient_evidence": 0,
        },
    }


async def run_method_1_whole_output_verification(
    content: Dict[str, Any],
    source_chunks: list,
    chunk_embeddings: list,
    verifier: MockClaimVerifier,
    doc_id: uuid.UUID,
) -> Dict[str, Any]:
    """Method 1: Retrieval-based evidence collection + whole-output verification (coarse-grained)."""
    t0 = time.perf_counter()
    full_text = json.dumps(content)

    # 1. Single coarse retrieval using full concatenated text
    t_ret = time.perf_counter()
    query_emb = await default_embedding_provider.embed_text(full_text[:300])
    matches: List[EvidenceMatch] = []
    for sc, sc_emb in zip(source_chunks, chunk_embeddings):
        sim = sum(a * b for a, b in zip(query_emb, sc_emb))
        sim = max(0.0, min(1.0, float(sim)))
        if sim >= 0.20:
            matches.append(
                EvidenceMatch(
                    chunk_id=uuid.uuid4(),
                    document_id=doc_id,
                    chunk_content=sc.content,
                    similarity_score=round(sim, 4),
                    section_title=sc.section_title,
                )
            )
    matches.sort(key=lambda m: m.similarity_score, reverse=True)
    top_matches = matches[:3]
    retrieval_latency_ms = (time.perf_counter() - t_ret) * 1000

    # 2. Single evaluation on whole output
    t_ver = time.perf_counter()
    coarse_claim = AtomicClaim(
        claim_id=uuid.uuid4(),
        text=full_text[:200],
        normalized_text=full_text[:200],
    )
    result = await verifier.verify_claim(coarse_claim, top_matches)
    verification_latency_ms = (time.perf_counter() - t_ver) * 1000
    total_latency_ms = (time.perf_counter() - t0) * 1000

    verdicts = {"supported": 0, "contradicted": 0, "partially_supported": 0, "insufficient_evidence": 0}
    verdicts[result.verdict.value] += 1

    return {
        "method_id": "method_1_whole_output",
        "method_name": "Method 1: Whole-Output Retrieval + Verification",
        "description": "Coarse-grained retrieval and verification on un-deconstructed generation output.",
        "telemetry": {
            "claim_extraction_latency_ms": 0.0,
            "evidence_retrieval_latency_ms": round(retrieval_latency_ms, 2),
            "verification_latency_ms": round(verification_latency_ms, 2),
            "total_verification_latency_ms": round(total_latency_ms, 2),
            "number_of_claims": 1,
            "number_of_evidence_chunks_retrieved": len(top_matches),
            "token_usage": None,
        },
        "verdict_distribution": verdicts,
    }


async def run_method_2_structured_claim_verification(
    content: Dict[str, Any],
    output_type: str,
    source_chunks: list,
    chunk_embeddings: list,
    extractor: MockClaimExtractor,
    verifier: MockClaimVerifier,
    doc_id: uuid.UUID,
) -> Dict[str, Any]:
    """Method 2: Retrieval + structured claim verification (fine-grained atomic claims)."""
    t0 = time.perf_counter()

    # A. Atomic Claim Extraction
    t_ext = time.perf_counter()
    claims = await extractor.extract_claims(content, output_type)
    extraction_latency_ms = (time.perf_counter() - t_ext) * 1000

    # B. Deterministic Normalization
    claims = ClaimNormalizer.normalize_claims(claims)

    # C. Per-Claim Independent Retrieval and Verification
    retrieval_latencies: List[float] = []
    verification_latencies: List[float] = []
    verdicts = {"supported": 0, "contradicted": 0, "partially_supported": 0, "insufficient_evidence": 0}
    total_evidence_retrieved = 0
    claim_details = []

    for claim in claims:
        # Independent dense vector search per claim
        t_ret = time.perf_counter()
        search_query = claim.normalized_text or claim.text
        claim_emb = await default_embedding_provider.embed_text(search_query)

        matches: List[EvidenceMatch] = []
        for sc, sc_emb in zip(source_chunks, chunk_embeddings):
            sim = sum(a * b for a, b in zip(claim_emb, sc_emb))
            sim = max(0.0, min(1.0, float(sim)))
            if sim >= 0.20:
                matches.append(
                    EvidenceMatch(
                        chunk_id=uuid.uuid4(),
                        document_id=doc_id,
                        chunk_content=sc.content,
                        similarity_score=round(sim, 4),
                        section_title=sc.section_title,
                        page_number=sc.page_number,
                    )
                )
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        top_matches = matches[:3]
        total_evidence_retrieved += len(top_matches)
        retrieval_latencies.append((time.perf_counter() - t_ret) * 1000)

        # Claim-Level Judge Evaluation
        t_ver = time.perf_counter()
        res = await verifier.verify_claim(claim, top_matches)
        verification_latencies.append((time.perf_counter() - t_ver) * 1000)

        verdicts[res.verdict.value] += 1
        claim_details.append({
            "claim_id": str(claim.claim_id),
            "text": claim.text,
            "normalized_text": claim.normalized_text,
            "verdict": res.verdict.value,
            "confidence": res.confidence,
            "explanation": res.explanation,
            "evidence_count": len(top_matches),
        })

    total_latency_ms = (time.perf_counter() - t0) * 1000

    return {
        "method_id": "method_2_structured_claims",
        "method_name": "Method 2: Structured Atomic Claim Verification",
        "description": "Fine-grained atomic claim extraction, deterministic normalization, independent vector retrieval per claim, and 4-verdict classification.",
        "telemetry": {
            "claim_extraction_latency_ms": round(extraction_latency_ms, 2),
            "evidence_retrieval_latency_ms": round(sum(retrieval_latencies), 2),
            "verification_latency_ms": round(sum(verification_latencies), 2),
            "total_verification_latency_ms": round(total_latency_ms, 2),
            "number_of_claims": len(claims),
            "number_of_evidence_chunks_retrieved": total_evidence_retrieved,
            "token_usage": None,
        },
        "verdict_distribution": verdicts,
        "claims": claim_details,
    }


async def run_verification_experiment() -> Dict[str, Any]:
    print("=" * 80)
    print("TransformAI: Running Verification Methods Comparison Benchmark (Milestone 6)")
    print("=" * 80)

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

    extractor = MockClaimExtractor()
    verifier = MockClaimVerifier()
    doc_id = uuid.uuid4()
    scenario_comparisons: List[Dict[str, Any]] = []

    for tc in TEST_CASES:
        scenario_name = tc["scenario"]
        output_type = tc["output_type"]
        content = tc["content"]
        print(f"\n[Scenario] {scenario_name}")

        m0 = await run_method_0_no_verification()
        m1 = await run_method_1_whole_output_verification(content, source_chunks, chunk_embeddings, verifier, doc_id)
        m2 = await run_method_2_structured_claim_verification(content, output_type, source_chunks, chunk_embeddings, extractor, verifier, doc_id)

        print(f"  - Method 0 (None): 0ms | 0 claims")
        print(f"  - Method 1 (Whole): {m1['telemetry']['total_verification_latency_ms']}ms | 1 chunk | {m1['verdict_distribution']}")
        print(f"  - Method 2 (Atomic Claims): {m2['telemetry']['total_verification_latency_ms']}ms | {m2['telemetry']['number_of_claims']} claims | {m2['verdict_distribution']}")

        scenario_comparisons.append({
            "scenario": scenario_name,
            "output_type": output_type,
            "methods": {
                "method_0": m0,
                "method_1": m1,
                "method_2": m2,
            }
        })

    results_data = {
        "metadata": {
            "experiment_name": "verification_methods_operational_benchmark",
            "milestone": "Milestone 6",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "verification_provider": verifier.verifier_name,
            "embedding_model": default_embedding_provider.model_name,
            "token_usage": None,
            "evaluation_notice": "Operational verification integration benchmark only. Quantitative verification evaluation (Precision, Recall, F1, Factual Consistency) is deferred to Milestone 7.",
        },
        "scenarios": scenario_comparisons,
    }

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "verification_comparison.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\nSuccessfully saved verification comparison results to {out_file}")
    return results_data


if __name__ == "__main__":
    asyncio.run(run_verification_experiment())
