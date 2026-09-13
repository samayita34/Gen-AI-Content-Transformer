"""
TransformAI Research Experiment: Multimodal Ingestion Comparative Benchmark
============================================================================

SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 5: Multimodal Source Ingestion

Objective:
Empirically evaluate modality-independent normalization and pipeline throughput across
four distinct source modalities:
- MODALITY 1: Text Document (Markdown/PDF-equivalent)
- MODALITY 2: Visual Image (OCR Extraction)
- MODALITY 3: Audio Recording (Speech-to-Text Transcription)
- MODALITY 4: Video Recording (Audio Track Speech-to-Text + Sampled Scene Headers)

Telemetry Metrics Recorded:
- modality
- source_file
- extraction_method
- processing_latency_ms (parsing, chunking, embedding, total)
- number_of_extracted_elements
- number_of_chunks
- number_of_embedded_chunks
- transcription_duration_seconds (where applicable)
- ocr_metadata (where available)
- failures

NOTE ON RESEARCH RIGOR:
OCR accuracy and transcription accuracy (WER/CER) are NOT fabricated.
Unless a real ground-truth paired dataset is provided, this benchmark records
operational telemetry and representation integrity only.

Output:
Saves structured experiment results to `research/results/multimodal_ingestion_comparison.json`.
"""

import os
import sys
import json
import time
import asyncio
import wave
import io
import uuid
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image

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
from app.services.embeddings.hf_local import default_embedding_provider
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


def _create_sample_image_bytes() -> bytes:
    """Generates a small in-memory valid PNG image."""
    img = Image.new("RGB", (400, 200), color=(30, 41, 59))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_sample_wav_bytes() -> bytes:
    """Generates a small in-memory valid WAV container header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)  # 1 second of audio
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

    ocr_provider = MockOCRProvider()
    stt_provider = MockTranscriptionProvider()
    chunker = get_chunker(ChunkingStrategy.STRUCTURE_AWARE)

    modalities_config = [
        {
            "modality": "text",
            "source_file": "specification.md",
            "extraction_method": "text_stream_parser",
            "parser": TxtParser(),
            "content": SAMPLE_TEXT.encode("utf-8"),
        },
        {
            "modality": "image",
            "source_file": "architecture_diagram.png",
            "extraction_method": "pillow_container_plus_ocr_provider",
            "parser": ImageParser(ocr_provider=ocr_provider),
            "content": _create_sample_image_bytes(),
        },
        {
            "modality": "audio",
            "source_file": "keynote_briefing.wav",
            "extraction_method": "wave_container_plus_stt_provider",
            "parser": AudioParser(transcription_provider=stt_provider),
            "content": _create_sample_wav_bytes(),
        },
        {
            "modality": "video",
            "source_file": "product_demonstration.mp4",
            "extraction_method": "lightweight_audio_transcription_with_sampled_scene_headers",
            "parser": VideoParser(transcription_provider=stt_provider),
            "content": b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 200,
        },
    ]

    results: List[Dict[str, Any]] = []

    for cfg in modalities_config:
        print(f"\nEvaluating Modality: {cfg['modality'].upper()} ({cfg['source_file']})...")
        modality_name = cfg["modality"]
        source_file = cfg["source_file"]
        extraction_method = cfg["extraction_method"]
        failures: List[str] = []

        # 1. Measure Parsing & Extraction Latency
        t0 = time.perf_counter()
        try:
            parsed_doc = await cfg["parser"].parse(cfg["content"], source_file)
            cleaned_doc = cleaner.clean_parsed_document(parsed_doc)
            structured_doc = structure_detector.enrich_document_structure(cleaned_doc)
        except Exception as exc:
            failures.append(f"Parsing/Structuring error: {str(exc)}")
            structured_doc = ParsedDocument(elements=[], raw_text="", modality=SourceModality.TEXT)
        parse_latency_ms = (time.perf_counter() - t0) * 1000

        # 2. Measure Chunking Latency
        t1 = time.perf_counter()
        chunks = chunker.chunk(structured_doc)
        chunking_latency_ms = (time.perf_counter() - t1) * 1000

        # 3. Measure Embedding Latency
        t2 = time.perf_counter()
        chunk_texts = [c.content for c in chunks]
        embeddings = []
        if chunk_texts:
            try:
                embeddings = await default_embedding_provider.embed_batch(chunk_texts)
            except Exception as exc:
                failures.append(f"Embedding error: {str(exc)}")
        embedding_latency_ms = (time.perf_counter() - t2) * 1000

        total_latency_ms = parse_latency_ms + chunking_latency_ms + embedding_latency_ms

        # 4. Context Normalization & Downstream Generation Verification
        sample_doc_id = uuid.uuid4()
        retrieved_chunks = [
            RetrievedChunk(
                chunk_id=uuid.uuid4(),
                document_id=sample_doc_id,
                content=c.content,
                similarity_score=0.92,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                section_title=c.section_title,
                source_filename=source_file,
                metadata={
                    "modality": modality_name,
                    "formatted_timestamp": c.metadata.get("formatted_timestamp"),
                },
            )
            for c in chunks
        ]

        normalizer = ContextNormalizer()
        normalized_context = normalizer.build_normalized_context(
            query="TransformAI core architecture and multimodal ingestion",
            retrieved_chunks=retrieved_chunks,
        )

        gen_config = GenerationConfig(
            output_type=OutputType.EXECUTIVE_SUMMARY,
            audience=AudienceType.EXECUTIVE,
            tone=ToneType.PROFESSIONAL,
            detail_level=DetailLevel.MODERATE,
            communication_objective=CommunicationObjective.INFORM,
        )

        gen_service = default_generation_router.get_generator(OutputType.EXECUTIVE_SUMMARY)
        t3 = time.perf_counter()
        parsed_content, gen_resp = await gen_service.generate_format(
            context=normalized_context,
            config=gen_config,
            provider=MockLLMProvider(),
        )
        gen_latency_ms = (time.perf_counter() - t3) * 1000

        # OCR / Transcription specific metadata
        ocr_metadata = None
        if modality_name == "image":
            ocr_metadata = {
                "extracted_blocks": len(structured_doc.elements),
                "has_bounding_boxes": any(e.spatial_bounds is not None for e in structured_doc.elements),
                "image_dimensions": structured_doc.media_metadata.get("width", 0),
                "color_mode": structured_doc.media_metadata.get("color_mode", "UNKNOWN"),
            }

        transcription_duration = None
        if modality_name in ("audio", "video"):
            transcription_duration = structured_doc.duration_seconds or structured_doc.media_metadata.get("duration_seconds")

        entry = {
            "modality": modality_name,
            "source_file": source_file,
            "extraction_method": extraction_method,
            "number_of_extracted_elements": len(structured_doc.elements),
            "number_of_chunks": len(chunks),
            "number_of_embedded_chunks": len(embeddings),
            "total_words": structured_doc.total_word_count,
            "total_characters": structured_doc.total_character_count,
            "transcription_duration_seconds": transcription_duration,
            "ocr_metadata": ocr_metadata,
            "processing_latency_ms": {
                "parse_latency_ms": round(parse_latency_ms, 2),
                "chunking_latency_ms": round(chunking_latency_ms, 2),
                "embedding_latency_ms": round(embedding_latency_ms, 2),
                "generation_latency_ms": round(gen_latency_ms, 2),
                "total_pipeline_latency_ms": round(total_latency_ms + gen_latency_ms, 2),
            },
            "provenance": {
                "citations_retained": len(normalized_context.source_references),
                "has_temporal_timestamps": any(c.metadata.get("formatted_timestamp") is not None for c in chunks),
                "has_spatial_bounding_boxes": any(e.spatial_bounds is not None for e in structured_doc.elements),
            },
            "failures": failures,
            "generation_integration_verified": parsed_content is not None and bool(parsed_content.title),
        }
        results.append(entry)

        print(f"  - Extracted Elements: {entry['number_of_extracted_elements']}")
        print(f"  - Chunks Formed:     {entry['number_of_chunks']}")
        print(f"  - Embeddings Created:{entry['number_of_embedded_chunks']}")
        print(f"  - Total Latency:     {entry['processing_latency_ms']['total_pipeline_latency_ms']:.2f} ms")
        print(f"  - Failures:          {len(failures)}")

    output_data = {
        "metadata": {
            "experiment_name": "multimodal_ingestion_comparison",
            "milestone": "Milestone 5",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "embedding_model": default_embedding_provider.model_name,
            "embedding_dimension": default_embedding_provider.dimension,
            "ocr_provider": ocr_provider.provider_name,
            "transcription_provider": stt_provider.provider_name,
            "modalities_evaluated": [c["modality"] for c in modalities_config],
            "evaluation_notice": "Telemetry and architectural integration benchmark only. Quantitative OCR accuracy, transcription WER, and factual consistency are evaluated in Milestone 7.",
        },
        "modality_runs": results,
    }

    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_file = results_dir / "multimodal_ingestion_comparison.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSuccessfully written multimodal ingestion comparison to {output_file}")
    return output_data


if __name__ == "__main__":
    asyncio.run(run_multimodal_experiment())
