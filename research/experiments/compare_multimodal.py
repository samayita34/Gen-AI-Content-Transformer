"""
TransformAI Research Experiment: Multimodal Source Ingestion Comparative Benchmark
==================================================================================

SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 5: Multimodal Source Ingestion

Objective:
Empirically evaluate modality-independent normalization and pipeline throughput across
four distinct source modalities:
- MODALITY 1: Text Document (Markdown/PDF-equivalent)
- MODALITY 2: Visual Image (OCR Extraction)
- MODALITY 3: Audio Recording (Speech-to-Text Transcription)
- MODALITY 4: Video Recording (Audio Track Speech-to-Text + Sampled Scene Headers)

Measures (Operational Telemetry Only):
- Parsing and extraction latency (ms)
- Normalized DocumentElement count
- Chunk count and average token size
- Provenance density (retention of timestamps, section titles, and source citations)
- Vector embedding & pgvector retrieval compatibility
- Milestone 4 multi-format generation integration verification

NOTE: OCR accuracy, transcription WER/CER, retrieval precision, factual consistency,
and hallucination rate are NOT evaluated in Milestone 5 and will be benchmarked in Milestone 7.

Output:
Saves structured experiment results to `research/results/multimodal_comparison.json`.
"""

import os
import sys
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List

os.environ["TRANSFORMAI_TESTING"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.services.document.models import ParsedDocument, DocumentElement, ElementType, SourceModality
from app.services.document.cleaner import cleaner
from app.services.document.structure import structure_detector
from app.services.document.chunking import get_chunker
from app.models.document import ChunkingStrategy
from app.services.document.parsers.image import ImageParser
from app.services.document.parsers.audio import AudioParser
from app.services.document.parsers.video import VideoParser
from app.services.document.parsers.txt import TxtParser
from app.services.multimodal.providers.mock import MockOCRProvider, MockTranscriptionProvider
from app.services.embeddings.hf_local import SentenceTransformerEmbeddingProvider, default_embedding_provider
from app.services.retrieval.models import RetrievedChunk, SourceReference, NormalizedContext
from app.services.retrieval.normalizer import ContextNormalizer
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
from PIL import Image
import io


def _create_sample_image_bytes() -> bytes:
    """Generates a small in-memory valid PNG image."""
    img = Image.new("RGB", (400, 200), color=(30, 41, 59))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_sample_wav_bytes() -> bytes:
    """Generates a small in-memory valid WAV container header."""
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)  # 1 second of silence
    return buf.getvalue()


SAMPLE_TEXT = """# TransformAI Multimodal Specification
TransformAI ingests text, images, audio, and video sources into a unified normalized document representation.
The Document Intelligence layer performs structural parsing, deterministic cleaning, and semantic chunking.
Dense vector embeddings are computed via 384-dimensional SentenceTransformers and indexed in PostgreSQL with pgvector.
Downstream generation models transform normalized context into Executive Summaries, Advisories, Slides, and Video Storyboards.
"""


async def run_multimodal_experiment() -> Dict[str, Any]:
    print("=" * 80)
    print("TransformAI: Running Multimodal Ingestion Benchmark (Milestone 5)")
    print("=" * 80)

    embedding_provider = default_embedding_provider
    ocr_provider = MockOCRProvider()
    stt_provider = MockTranscriptionProvider()
    llm_provider = MockLLMProvider()
    normalizer = ContextNormalizer()
    chunker = get_chunker(ChunkingStrategy.STRUCTURE_AWARE)

    results_data: Dict[str, Any] = {
        "metadata": {
            "experiment_name": "multimodal_ingestion_comparison",
            "milestone": "Milestone 5",
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "embedding_model": embedding_provider.model_name,
            "embedding_dimension": embedding_provider.dimension,
            "ocr_provider": ocr_provider.provider_name,
            "transcription_provider": stt_provider.provider_name,
            "modalities_evaluated": ["text", "image", "audio", "video"],
            "evaluation_notice": "Telemetry and architectural integration benchmark only. Quantitative OCR accuracy, transcription WER, and factual consistency are evaluated in Milestone 7.",
        },
        "modality_runs": [],
    }

    modalities = [
        {
            "name": "Text Document",
            "modality": SourceModality.TEXT,
            "filename": "specification.md",
            "parser": TxtParser(),
            "bytes": SAMPLE_TEXT.encode("utf-8"),
        },
        {
            "name": "Visual Image (OCR)",
            "modality": SourceModality.IMAGE,
            "filename": "architecture_diagram.png",
            "parser": ImageParser(ocr_provider=ocr_provider),
            "bytes": _create_sample_image_bytes(),
        },
        {
            "name": "Audio Recording (STT)",
            "modality": SourceModality.AUDIO,
            "filename": "briefing_session.wav",
            "parser": AudioParser(transcription_provider=stt_provider),
            "bytes": _create_sample_wav_bytes(),
        },
        {
            "name": "Video Recording (Multimodal)",
            "modality": SourceModality.VIDEO,
            "filename": "tech_walkthrough.mp4",
            "parser": VideoParser(transcription_provider=stt_provider),
            "bytes": b"fake_mp4_container_bytes_for_lightweight_transcription",
        },
    ]

    for m in modalities:
        print(f"\n--- Testing Modality: {m['name']} ({m['filename']}) ---")
        
        # 1. Parsing Phase
        t0 = time.perf_counter()
        parsed_doc: ParsedDocument = await m["parser"].parse(m["bytes"], m["filename"])
        parse_latency_ms = (time.perf_counter() - t0) * 1000

        # 2. Cleaning & Structuring
        cleaned_doc = cleaner.clean_parsed_document(parsed_doc)
        structured_doc = structure_detector.enrich_document_structure(cleaned_doc)

        # 3. Chunking Phase
        t0 = time.perf_counter()
        chunks = chunker.chunk(structured_doc)
        chunking_latency_ms = (time.perf_counter() - t0) * 1000

        # 4. Dense Batch Embedding Generation
        chunk_texts = [c.content for c in chunks]
        t0 = time.perf_counter()
        embeddings = await embedding_provider.embed_batch(chunk_texts) if chunk_texts else []
        embedding_latency_ms = (time.perf_counter() - t0) * 1000

        # 5. Simulated Retrieval & Normalized Context Construction
        doc_id = uuid.uuid4()
        retrieved_chunks = [
            RetrievedChunk(
                chunk_id=uuid.uuid4(),
                document_id=doc_id,
                content=c.content,
                similarity_score=0.9250,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                section_title=c.section_title,
                chunking_strategy="structure_aware",
                source_filename=m["filename"],
                metadata=c.metadata,
            )
            for c in chunks
        ]
        norm_context = normalizer.build_normalized_context(
            query=f"Overview of content from {m['filename']}",
            retrieved_chunks=retrieved_chunks,
        )

        # 6. Milestone 4 Generation Integration Verification
        gen_config = GenerationConfig(
            output_type=OutputType.EXECUTIVE_SUMMARY,
            audience=AudienceType.EXECUTIVE,
            tone=ToneType.PROFESSIONAL,
            detail_level=DetailLevel.MODERATE,
            communication_objective=CommunicationObjective.INFORM,
        )
        generator = default_generation_router.get_generator(OutputType.EXECUTIVE_SUMMARY)
        t0 = time.perf_counter()
        transformed_output, gen_resp = await generator.generate_format(norm_context, gen_config, llm_provider)
        generation_latency_ms = (time.perf_counter() - t0) * 1000

        # Provenance metrics
        has_temporal_metadata = any(
            c.metadata.get("formatted_timestamp") is not None for c in chunks
        )
        has_spatial_metadata = any(
            e.spatial_bounds is not None for e in structured_doc.elements
        )

        run_entry = {
            "modality": m["modality"].value,
            "source_type": m["name"],
            "filename": m["filename"],
            "element_count": len(structured_doc.elements),
            "chunk_count": len(chunks),
            "total_words": structured_doc.total_word_count,
            "total_characters": structured_doc.total_character_count,
            "parse_latency_ms": round(parse_latency_ms, 2),
            "chunking_latency_ms": round(chunking_latency_ms, 2),
            "embedding_latency_ms": round(embedding_latency_ms, 2),
            "generation_latency_ms": round(generation_latency_ms, 2),
            "embeddings_generated": len(embeddings),
            "normalized_facts_extracted": len(norm_context.facts),
            "normalized_entities_extracted": len(norm_context.entities),
            "provenance": {
                "citations_retained": len(norm_context.source_references),
                "has_temporal_timestamps": has_temporal_metadata,
                "has_spatial_bounding_boxes": has_spatial_metadata,
            },
            "generation_integration_verified": transformed_output is not None,
        }

        results_data["modality_runs"].append(run_entry)
        print(f"  Elements: {run_entry['element_count']} | Chunks: {run_entry['chunk_count']} | Embeddings: {run_entry['embeddings_generated']}")
        print(f"  Parse Latency: {parse_latency_ms:.2f}ms | Embed Latency: {embedding_latency_ms:.2f}ms | Gen Latency: {generation_latency_ms:.2f}ms")
        print(f"  Generation Integration Verified: {run_entry['generation_integration_verified']}")

    out_dir = Path("research/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "multimodal_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[OK] Multimodal benchmark complete. Telemetry saved to '{out_file}'.")
    return results_data


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_multimodal_experiment())
