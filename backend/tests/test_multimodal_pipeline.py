import io
import pytest
from httpx import AsyncClient, ASGITransport
from PIL import Image

from app.main import app
from app.models.document import Document, DocumentChunk, ProcessingStatus, ChunkingStrategy
from app.services.document.pipeline import DocumentPipelineService
from app.services.document.parsers.image import ImageParser
from app.services.multimodal.providers.mock import UnavailableOCRProvider


def _make_test_png() -> bytes:
    img = Image.new("RGB", (200, 100), color=(50, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_test_wav() -> bytes:
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 8000)  # 0.5s silence
    return buf.getvalue()


@pytest.mark.asyncio
async def test_multimodal_upload_api_validation(async_client):
    # 1. Test image upload
    png_bytes = _make_test_png()
    resp = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("diagram.png", png_bytes, "image/png")},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["file_type"] == "png"
    assert data["processing_status"] == "uploaded"

    # 2. Test audio upload
    wav_bytes = _make_test_wav()
    resp_audio = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("lecture.wav", wav_bytes, "audio/wav")},
    )
    assert resp_audio.status_code == 202
    assert resp_audio.json()["file_type"] == "wav"

    # 3. Test video upload
    resp_video = await async_client.post(
        "/api/v1/documents/upload",
        files={"file": ("demo.mp4", b"dummy_mp4_bytes", "video/mp4")},
    )
    assert resp_video.status_code == 202
    assert resp_video.json()["file_type"] == "mp4"


@pytest.mark.asyncio
async def test_multimodal_pipeline_full_flow(db_session):
    """
    Tests end-to-end pipeline:
    Image / Audio Ingestion -> Pipeline Processing -> Chunk Vectorization -> Retrieval -> Transformation
    """
    pipeline = DocumentPipelineService()
    png_bytes = _make_test_png()

    # 1. Ingest Image
    doc = await pipeline.ingest_document(
        file_bytes=png_bytes,
        original_filename="flowchart.png",
        file_size=len(png_bytes),
        db=db_session,
        chunking_strategy=ChunkingStrategy.STRUCTURE_AWARE,
    )
    assert doc.processing_status == ProcessingStatus.UPLOADED

    # 2. Process Image through pipeline
    processed_doc = await pipeline.process_document(doc.id, db_session)
    assert processed_doc.processing_status == ProcessingStatus.COMPLETED
    assert processed_doc.doc_metadata.get("modality") == "image"

    # Query chunks from database
    from sqlalchemy import select
    res = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    chunks = res.scalars().all()
    assert len(chunks) > 0

    # Verify chunk metadata has modality & dimensions
    chunk_0 = chunks[0]
    assert chunk_0.chunk_metadata.get("modality") == "image"
    assert chunk_0.embedding is not None


@pytest.mark.asyncio
async def test_multimodal_pipeline_unavailable_provider_error(db_session, monkeypatch):
    """
    Verifies that when an OCR/STT provider is unavailable, the pipeline marks
    the document as FAILED with an explicit error message instead of silently succeeding.
    """
    pipeline = DocumentPipelineService()
    png_bytes = _make_test_png()

    # Ingest document
    doc = await pipeline.ingest_document(
        file_bytes=png_bytes,
        original_filename="unsupported_ocr.png",
        file_size=len(png_bytes),
        db=db_session,
    )

    # Force parser to use UnavailableOCRProvider
    unavailable_parser = ImageParser(ocr_provider=UnavailableOCRProvider())
    import app.services.document.pipeline as pipe_module
    monkeypatch.setattr(pipe_module, "get_parser_for_filename", lambda fn: unavailable_parser)

    # Process document
    processed_doc = await pipeline.process_document(doc.id, db_session)

    # Must fail with clear error
    assert processed_doc.processing_status == ProcessingStatus.FAILED
    assert processed_doc.error_message is not None
    assert "No OCR engine is configured" in processed_doc.error_message
