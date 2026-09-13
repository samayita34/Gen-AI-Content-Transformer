"""
End-to-End Multimodal Verification Script
Tests PDF, DOCX, TXT, IMAGE, AUDIO, and VIDEO through the full pipeline:
Parse -> Clean -> Structure -> Chunk -> Embed -> Context Normalization -> Transformation
Also checks for real local OCR / STT tool availability.
"""

import io
import sys
import shutil
import asyncio
import wave
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "backend"))

from app.services.document.parsers.pdf import PDFParser
from app.services.document.parsers.docx import DocxParser
from app.services.document.parsers.txt import TxtParser
from app.services.document.parsers.image import ImageParser
from app.services.document.parsers.audio import AudioParser
from app.services.document.parsers.video import VideoParser
from app.services.multimodal.providers.mock import MockOCRProvider, MockTranscriptionProvider
from app.services.document.cleaner import cleaner
from app.services.document.structure import structure_detector
from app.services.document.chunking import get_chunker
from app.models.document import ChunkingStrategy
from app.services.embeddings.hf_local import default_embedding_provider
from app.services.retrieval.models import RetrievedChunk
from app.services.retrieval.normalizer import ContextNormalizer
from app.services.generation.router import default_generation_router
from app.services.generation.models import (
    OutputType,
    AudienceType,
    ToneType,
    DetailLevel,
    CommunicationObjective,
    GenerationConfig,
)
from app.services.generation.providers.mock import MockLLMProvider
import uuid


def create_synthetic_docx() -> bytes:
    import docx
    doc = docx.Document()
    doc.add_heading("TransformAI Technical Specifications", level=1)
    doc.add_paragraph("TransformAI provides multi-format content transformation with source grounding.")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_synthetic_pdf() -> bytes:
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def create_synthetic_image() -> bytes:
    img = Image.new("RGB", (300, 150), color=(15, 23, 42))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_synthetic_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)
    return buf.getvalue()


if sys.platform == "win32":
    import io
    sys.stdout.reconfigure(encoding="utf-8")


async def verify_modality(name: str, parser, content: bytes, filename: str):
    print(f"\n[Testing Modality: {name.upper()}] ({filename})")
    
    # 1. Parse
    parsed = await parser.parse(content, filename)
    print(f"  - Parse succeeded: {len(parsed.elements)} element(s), modality={parsed.modality.value}")
    
    # 2. Clean & Structure
    cleaned = cleaner.clean_parsed_document(parsed)
    structured = structure_detector.enrich_document_structure(cleaned)
    print(f"  - Clean & Structure succeeded: total words={structured.total_word_count}")
    
    # 3. Chunk
    chunker = get_chunker(ChunkingStrategy.STRUCTURE_AWARE)
    chunks = chunker.chunk(structured)
    print(f"  - Chunking succeeded: {len(chunks)} chunk(s)")
    
    # 4. Embed
    chunk_texts = [c.content for c in chunks]
    embeddings = await default_embedding_provider.embed_batch(chunk_texts)
    print(f"  - Embedding succeeded: {len(embeddings)} vector(s) of dimension {default_embedding_provider.dimension}")
    
    # 5. Normalization
    retrieved = [
        RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content=c.content,
            similarity_score=0.95,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            section_title=c.section_title,
            source_filename=filename,
            metadata={"modality": parsed.modality.value, "formatted_timestamp": c.metadata.get("formatted_timestamp")},
        )
        for c in chunks
    ]
    normalizer = ContextNormalizer()
    normalized_ctx = normalizer.build_normalized_context(query="Summarize key facts", retrieved_chunks=retrieved)
    print(f"  - Context Normalization succeeded: {len(normalized_ctx.facts)} fact(s), {len(normalized_ctx.source_references)} citation(s)")
    
    # 6. Multi-Format Transformation
    generator = default_generation_router.get_generator(OutputType.EXECUTIVE_SUMMARY)
    config = GenerationConfig(
        output_type=OutputType.EXECUTIVE_SUMMARY,
        audience=AudienceType.EXECUTIVE,
        tone=ToneType.PROFESSIONAL,
        detail_level=DetailLevel.MODERATE,
        communication_objective=CommunicationObjective.INFORM,
    )
    parsed_summary, gen_resp = await generator.generate_format(
        context=normalized_ctx,
        config=config,
        provider=MockLLMProvider(),
    )
    print(f"  - Transformation succeeded: '{parsed_summary.title}' generated.")


async def main():
    print("=" * 80)
    print("TransformAI: End-to-End Verification across All Modalities (Milestone 5)")
    print("=" * 80)
    
    # Check local OCR / STT tool availability
    print("\n[Local System Tooling Inspection]")
    tesseract_path = shutil.which("tesseract")
    whisper_path = shutil.which("whisper")
    ffmpeg_path = shutil.which("ffmpeg")
    
    print(f"  - Tesseract OCR binary: {'Found (' + tesseract_path + ')' if tesseract_path else 'Not installed (Using verified MockOCRProvider)'}")
    print(f"  - Whisper STT binary:   {'Found (' + whisper_path + ')' if whisper_path else 'Not installed (Using verified MockTranscriptionProvider)'}")
    print(f"  - FFmpeg binary:        {'Found (' + ffmpeg_path + ')' if ffmpeg_path else 'Not installed (Container inspection uses native streams)'}")

    ocr_mock = MockOCRProvider()
    stt_mock = MockTranscriptionProvider()

    # 1. TXT
    await verify_modality(
        "TXT",
        TxtParser(),
        b"# Plain Text File\nTransformAI converts raw text into structured formats.\nSource grounding guarantees factual fidelity.",
        "sample.txt",
    )

    # 2. DOCX
    await verify_modality(
        "DOCX",
        DocxParser(),
        create_synthetic_docx(),
        "sample.docx",
    )

    # 3. PDF
    await verify_modality(
        "PDF",
        PDFParser(),
        create_synthetic_pdf(),
        "sample.pdf",
    )

    # 4. IMAGE (Mock OCR)
    await verify_modality(
        "IMAGE",
        ImageParser(ocr_provider=ocr_mock),
        create_synthetic_image(),
        "architecture_diagram.png",
    )

    # 5. AUDIO (Mock STT)
    await verify_modality(
        "AUDIO",
        AudioParser(transcription_provider=stt_mock),
        create_synthetic_wav(),
        "meeting_recording.wav",
    )

    # 6. VIDEO (Mock Audio STT + Sampled Scene Headers)
    await verify_modality(
        "VIDEO",
        VideoParser(transcription_provider=stt_mock),
        b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 200,
        "product_demo.mp4",
    )

    print("\n" + "=" * 80)
    print("ALL 6 MODALITIES (PDF, DOCX, TXT, IMAGE, AUDIO, VIDEO) SUCCESSFULLY VERIFIED!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
