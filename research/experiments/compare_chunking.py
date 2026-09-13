"""Research Experiment: Baseline (Fixed-Size) vs Proposed (Structure-Aware) Chunking.

Investigates document structure preservation and chunk characteristics across
different document types to support empirical benchmarking for SIH26154.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add backend to sys.path so services can be imported directly
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.models.document import ChunkingStrategy
from app.services.document.models import ParsedDocument, DocumentElement, ElementType
from app.services.document.cleaner import TextCleaner
from app.services.document.structure import StructureDetector
from app.services.document.chunking.fixed import FixedSizeChunker
from app.services.document.chunking.structure_aware import StructureAwareChunker


def create_sample_research_dataset() -> ParsedDocument:
    """Creates a structured sample document with sections, headings, lists, and paragraphs."""
    raw_sample = """# Comprehensive Analysis of Distributed GenAI Systems

1. Executive Summary
Distributed generative AI systems present complex synchronization challenges across heterogeneous edge devices. Factual consistency across transformation formats remains a critical bottleneck.

2. System Architecture
The platform relies on a multi-tier pipeline designed for factual preservation.
The ingestion tier processes diverse document formats including PDF, DOCX, and plain text.

2.1 Vector Retrieval Layer
Dense vector indexing enables semantic search across normalized chunks.
- Sub-millisecond similarity scoring using pgvector HNSW indexing.
- Multi-query expansion to increase retrieval recall.
- Context filtering based on document metadata and temporal attributes.

2.2 Verification and Grounding
Every generated claim is mapped back to source chunks to detect hallucinated statements.
If a claim cannot be verified against source evidence, the confidence score is flagged.

3. Experimental Results
Empirical evaluation indicates that structure-aware chunking maintains semantic boundary integrity compared to naive fixed-window token slicing.

4. Conclusion and Future Roadmap
Future milestones will incorporate multimodal inputs including audio transcripts and diagrammatic extraction.
"""
    # Clean and parse text
    cleaned = TextCleaner.clean_text(raw_sample)
    elements = []
    for p in cleaned.split("\n\n"):
        p_clean = p.strip()
        if p_clean:
            elements.append(DocumentElement(text=p_clean, page_number=1))

    parsed = ParsedDocument(elements=elements, raw_text=cleaned, page_count=1)
    return StructureDetector.enrich_document_structure(parsed)


def run_comparison():
    print("=" * 70)
    print("RUNNING RESEARCH EXPERIMENT: CHUNKING STRATEGY COMPARISON")
    print("=" * 70)

    doc = create_sample_research_dataset()
    print(f"Sample Document: {doc.total_character_count} chars, {doc.total_word_count} words, {len(doc.elements)} structural elements.")

    # 1. Method A: Fixed-Size Chunker (Baseline)
    fixed_chunker = FixedSizeChunker(chunk_size=400, chunk_overlap=40)
    t0 = time.perf_counter()
    fixed_chunks = fixed_chunker.chunk(doc)
    fixed_duration = time.perf_counter() - t0

    fixed_sizes = [c.character_count for c in fixed_chunks]
    fixed_words = [c.token_count for c in fixed_chunks]

    # 2. Method B: Structure-Aware Chunker (Proposed)
    struct_chunker = StructureAwareChunker(target_chunk_size=500, max_chunk_size=800)
    t1 = time.perf_counter()
    struct_chunks = struct_chunker.chunk(doc)
    struct_duration = time.perf_counter() - t1

    struct_sizes = [c.character_count for c in struct_chunks]
    struct_words = [c.token_count for c in struct_chunks]

    # Calculate section preservation: how many chunks have explicit section provenance
    fixed_sections = sum(1 for c in fixed_chunks if c.section_title is not None)
    struct_sections = sum(1 for c in struct_chunks if c.section_title is not None)

    results = {
        "experiment_name": "chunking_strategy_comparison",
        "timestamp": time.time(),
        "document_stats": {
            "total_characters": doc.total_character_count,
            "total_words": doc.total_word_count,
            "total_elements": len(doc.elements),
        },
        "methods": {
            "method_a_fixed_size": {
                "strategy": "fixed_size",
                "total_chunks": len(fixed_chunks),
                "avg_chunk_size_chars": round(sum(fixed_sizes) / len(fixed_sizes), 2) if fixed_sizes else 0,
                "min_chunk_size_chars": min(fixed_sizes) if fixed_sizes else 0,
                "max_chunk_size_chars": max(fixed_sizes) if fixed_sizes else 0,
                "avg_words_per_chunk": round(sum(fixed_words) / len(fixed_words), 2) if fixed_words else 0,
                "section_provenance_retention_rate": round(fixed_sections / len(fixed_chunks), 2) if fixed_chunks else 0,
                "execution_duration_sec": round(fixed_duration, 6),
            },
            "method_b_structure_aware": {
                "strategy": "structure_aware",
                "total_chunks": len(struct_chunks),
                "avg_chunk_size_chars": round(sum(struct_sizes) / len(struct_sizes), 2) if struct_sizes else 0,
                "min_chunk_size_chars": min(struct_sizes) if struct_sizes else 0,
                "max_chunk_size_chars": max(struct_sizes) if struct_sizes else 0,
                "avg_words_per_chunk": round(sum(struct_words) / len(struct_words), 2) if struct_words else 0,
                "section_provenance_retention_rate": round(struct_sections / len(struct_chunks), 2) if struct_chunks else 0,
                "execution_duration_sec": round(struct_duration, 6),
            },
        },
    }

    # Save results to research/results/
    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "chunking_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults successfully saved to: {out_file}\n")
    print(f"{'Metric':<35} | {'Method A (Fixed-Size)':<22} | {'Method B (Structure-Aware)':<25}")
    print("-" * 88)
    print(f"{'Total Chunks Generated':<35} | {len(fixed_chunks):<22} | {len(struct_chunks):<25}")
    print(f"{'Avg Chunk Size (chars)':<35} | {results['methods']['method_a_fixed_size']['avg_chunk_size_chars']:<22} | {results['methods']['method_b_structure_aware']['avg_chunk_size_chars']:<25}")
    print(f"{'Min / Max Size (chars)':<35} | {min(fixed_sizes)} / {max(fixed_sizes):<18} | {min(struct_sizes)} / {max(struct_sizes):<21}")
    print(f"{'Section Provenance Retention':<35} | {results['methods']['method_a_fixed_size']['section_provenance_retention_rate'] * 100:.1f}%{'':<17} | {results['methods']['method_b_structure_aware']['section_provenance_retention_rate'] * 100:.1f}%{'':<20}")
    print(f"{'Execution Time (sec)':<35} | {fixed_duration:.6f}{'':<14} | {struct_duration:.6f}{'':<17}")
    print("=" * 88)


if __name__ == "__main__":
    run_comparison()
