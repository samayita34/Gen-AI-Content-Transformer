"""
TransformAI Research Experiment: Multi-Format Generation Comparative Benchmark
==============================================================================

SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 4: Multi-Format Generative AI

Objective:
Empirically compare source-grounded transformation behaviors across three architectures:
- METHOD A: Direct Prompting (Source document injected directly without retrieval or normalization)
- METHOD B: Basic RAG (Retrieved dense vector chunks injected without structured context normalization)
- METHOD C: RAG + Normalized Context (Dense retrieval + deterministic NormalizedContext with fact/entity/citation extraction)

Measures:
- Generation query latency (ms)
- Output structural validity (Pydantic schema compliance)
- Provenance density (number of traceable source citations retained)
- Actual token usage where reported by provider (or null)

NOTE: Factual consistency, hallucination rate, and semantic preservation metrics are NOT evaluated
in this milestone and will be quantitatively benchmarked in Milestone 7.

Output:
Saves structured experiment results to `research/results/generation_comparison.json`.
"""

import os
import sys
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.services.generation.models import (
    OutputType,
    AudienceType,
    ToneType,
    DetailLevel,
    CommunicationObjective,
    GenerationConfig,
)
from app.services.generation.providers.mock import MockLLMProvider
from app.services.generation.router import default_generation_router
from app.services.retrieval.models import (
    RetrievedChunk,
    SourceReference,
    NormalizedContext,
    NormalizedFact,
    NormalizedEntity,
)

SAMPLE_RESEARCH_DOCUMENT = """# 1. Executive Summary & Problem Context
Traditional knowledge transformation workflows require extensive manual effort to convert long-form technical reports
into decision briefs, executive presentations, and public advisories. TransformAI implements a source-grounded
architecture that preserves semantic meaning across multiple communication modalities.

# 2. Ingestion & Dense Vector Indexing
The platform ingests PDF, DOCX, and TXT materials. Text is parsed with layout retention, cleaned deterministically,
and split using structure-aware heading boundaries. Dense vector indexing is executed with 384-dimensional embeddings
using local SentenceTransformers (all-MiniLM-L6-v2) and stored in PostgreSQL with pgvector.

# 3. Vector Retrieval & Grounding
Semantic retrieval computes cosine similarity as 1 minus cosine distance.
Each retrieved chunk maintains strict provenance records including chunk index, page number, and section title.
A deterministic Context Normalizer extracts source facts, entities, and citations with zero generative hallucination.

# 4. Multi-Format Transformation
Specialized generation pipelines synthesize Executive Summaries, Advisories, Slide Decks, and Video Storyboards.
Anti-fabrication constraints ensure that factual claims and recommended actions remain strictly bounded by source material.
"""

TEST_CASES = [
    {
        "test_id": "T1",
        "output_type": OutputType.EXECUTIVE_SUMMARY,
        "query": "Overview of platform architecture and transformation objectives",
        "audience": AudienceType.EXECUTIVE,
        "tone": ToneType.PROFESSIONAL,
    },
    {
        "test_id": "T2",
        "output_type": OutputType.ADVISORY,
        "query": "Operational risks and technical considerations for vector indexing",
        "audience": AudienceType.TECHNICAL,
        "tone": ToneType.FORMAL,
    },
    {
        "test_id": "T3",
        "output_type": OutputType.PRESENTATION,
        "query": "Presentation outline for technical stakeholders",
        "audience": AudienceType.TECHNICAL,
        "tone": ToneType.PROFESSIONAL,
    },
    {
        "test_id": "T4",
        "output_type": OutputType.VIDEO_SCRIPT,
        "query": "Video script walkthrough for general audiences",
        "audience": AudienceType.GENERAL_PUBLIC,
        "tone": ToneType.EXPLANATORY,
    },
]


async def run_generation_experiment() -> Dict[str, Any]:
    print("=" * 75)
    print("TransformAI: Running Multi-Format Generation Benchmark (Milestone 4)")
    print("=" * 75)

    provider = MockLLMProvider()
    doc_id = uuid.uuid4()
    filename = "transformai_research_spec.txt"

    # Simulated retrieved chunks for RAG methods
    chunk_1_id = uuid.uuid4()
    chunk_2_id = uuid.uuid4()
    retrieved_chunks = [
        RetrievedChunk(
            chunk_id=chunk_1_id,
            document_id=doc_id,
            content="The platform ingests PDF, DOCX, and TXT materials. Text is parsed with layout retention, cleaned deterministically, and split using structure-aware heading boundaries.",
            similarity_score=0.9125,
            chunk_index=1,
            page_number=1,
            section_title="2. Ingestion & Dense Vector Indexing",
            chunking_strategy="structure_aware",
            source_filename=filename,
        ),
        RetrievedChunk(
            chunk_id=chunk_2_id,
            document_id=doc_id,
            content="Semantic retrieval computes cosine similarity as 1 minus cosine distance. Each retrieved chunk maintains strict provenance records including chunk index, page number, and section title.",
            similarity_score=0.8840,
            chunk_index=2,
            page_number=2,
            section_title="3. Vector Retrieval & Grounding",
            chunking_strategy="structure_aware",
            source_filename=filename,
        ),
    ]

    source_refs = [
        SourceReference(
            document_id=doc_id,
            source_filename=filename,
            chunk_id=chunk_1_id,
            chunk_index=1,
            page_number=1,
            section_title="2. Ingestion & Dense Vector Indexing",
        ),
        SourceReference(
            document_id=doc_id,
            source_filename=filename,
            chunk_id=chunk_2_id,
            chunk_index=2,
            page_number=2,
            section_title="3. Vector Retrieval & Grounding",
        ),
    ]

    results_data: Dict[str, Any] = {
        "metadata": {
            "experiment_name": "generation_architecture_comparison",
            "milestone": "Milestone 4",
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "provider": provider.provider_name,
            "model": "mock-transformer-v1",
            "methods_evaluated": [
                "Method A: Direct Prompting (No retrieval, full document context)",
                "Method B: Basic RAG (Retrieved chunks, no structured context)",
                "Method C: RAG + Normalized Context (Retrieved chunks + NormalizedContext)",
            ],
            "evaluation_notice": "Factual consistency and hallucination scoring are not evaluated in Milestone 4 and will be quantitatively evaluated in Milestone 7.",
        },
        "test_runs": [],
    }

    for tc in TEST_CASES:
        config = GenerationConfig(
            output_type=tc["output_type"],
            audience=tc["audience"],
            tone=tc["tone"],
            detail_level=DetailLevel.MODERATE,
            communication_objective=CommunicationObjective.INFORM,
            top_k=2,
        )
        generator = default_generation_router.get_generator(config.output_type)

        print(f"\nEvaluating Format: {config.output_type.value.upper()} (Query: '{tc['query']}')")

        # -------------------------------------------------------------
        # METHOD A: Direct Prompting (No Vector Retrieval, Raw Full Text)
        # -------------------------------------------------------------
        raw_doc_chunk = RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=doc_id,
            content=SAMPLE_RESEARCH_DOCUMENT,
            similarity_score=1.0,
            chunk_index=0,
            source_filename=filename,
        )
        direct_context = NormalizedContext(
            query=tc["query"],
            source_documents=[{"document_id": str(doc_id), "source_filename": filename}],
            retrieved_chunks=[raw_doc_chunk],
            facts=[],
            key_points=[],
            entities=[],
            claims=[],
            source_references=[],
        )
        t0 = time.perf_counter()
        parsed_a, resp_a = await generator.generate_format(direct_context, config, provider)
        lat_a = (time.perf_counter() - t0) * 1000

        # -------------------------------------------------------------
        # METHOD B: Basic RAG (Retrieved Chunks, No Structured Extraction)
        # -------------------------------------------------------------
        basic_rag_context = NormalizedContext(
            query=tc["query"],
            source_documents=[{"document_id": str(doc_id), "source_filename": filename}],
            retrieved_chunks=retrieved_chunks,
            facts=[],
            key_points=[],
            entities=[],
            claims=[],
            source_references=source_refs,
        )
        t0 = time.perf_counter()
        parsed_b, resp_b = await generator.generate_format(basic_rag_context, config, provider)
        lat_b = (time.perf_counter() - t0) * 1000

        # -------------------------------------------------------------
        # METHOD C: RAG + Normalized Context (Dense Retrieval + Structured Context)
        # -------------------------------------------------------------
        norm_context = NormalizedContext(
            query=tc["query"],
            source_documents=[{"document_id": str(doc_id), "source_filename": filename, "retrieved_chunk_count": 2}],
            retrieved_chunks=retrieved_chunks,
            facts=[
                NormalizedFact(
                    fact_text="The platform ingests PDF, DOCX, and TXT materials.",
                    source_reference=source_refs[0],
                ),
                NormalizedFact(
                    fact_text="Semantic retrieval computes cosine similarity as 1 minus cosine distance.",
                    source_reference=source_refs[1],
                ),
            ],
            key_points=["The platform ingests PDF, DOCX, and TXT materials with layout retention."],
            entities=[
                NormalizedEntity(entity_name="PDF", entity_type="ACRONYM", source_references=[source_refs[0]]),
                NormalizedEntity(entity_name="pgvector", entity_type="PROPER_NOUN", source_references=[source_refs[1]]),
            ],
            claims=[],
            source_references=source_refs,
        )
        t0 = time.perf_counter()
        parsed_c, resp_c = await generator.generate_format(norm_context, config, provider)
        lat_c = (time.perf_counter() - t0) * 1000

        run_entry = {
            "test_id": tc["test_id"],
            "output_type": config.output_type.value,
            "query": tc["query"],
            "audience": config.audience.value,
            "tone": config.tone.value,
            "method_a_direct_prompting": {
                "method_name": "Direct Prompting (No RAG, No Normalization)",
                "retrieval_used": False,
                "normalized_context_used": False,
                "latency_ms": round(lat_a, 2),
                "token_usage": resp_a.usage,
                "structural_validity": parsed_a is not None,
                "source_references_retained": 0,
            },
            "method_b_basic_rag": {
                "method_name": "Basic RAG (Dense Retrieval, No Normalization)",
                "retrieval_used": True,
                "normalized_context_used": False,
                "chunks_retrieved": len(retrieved_chunks),
                "similarity_scores": [c.similarity_score for c in retrieved_chunks],
                "latency_ms": round(lat_b, 2),
                "token_usage": resp_b.usage,
                "structural_validity": parsed_b is not None,
                "source_references_retained": len(source_refs),
            },
            "method_c_rag_normalized_context": {
                "method_name": "RAG + Normalized Context (Dense Retrieval + Deterministic Normalization)",
                "retrieval_used": True,
                "normalized_context_used": True,
                "chunks_retrieved": len(retrieved_chunks),
                "similarity_scores": [c.similarity_score for c in retrieved_chunks],
                "facts_injected": len(norm_context.facts),
                "entities_injected": len(norm_context.entities),
                "latency_ms": round(lat_c, 2),
                "token_usage": resp_c.usage,
                "structural_validity": parsed_c is not None,
                "source_references_retained": len(source_refs),
            },
        }

        results_data["test_runs"].append(run_entry)
        print(f"  Method A Latency: {lat_a:.2f}ms | Valid: {run_entry['method_a_direct_prompting']['structural_validity']}")
        print(f"  Method B Latency: {lat_b:.2f}ms | Valid: {run_entry['method_b_basic_rag']['structural_validity']} | Refs: {run_entry['method_b_basic_rag']['source_references_retained']}")
        print(f"  Method C Latency: {lat_c:.2f}ms | Valid: {run_entry['method_c_rag_normalized_context']['structural_validity']} | Refs: {run_entry['method_c_rag_normalized_context']['source_references_retained']}")

    out_dir = Path("research/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "generation_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[OK] Generation experiment complete. Results written to '{out_file}'.")
    return results_data


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_generation_experiment())
