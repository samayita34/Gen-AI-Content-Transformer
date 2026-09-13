import hashlib
from typing import Dict, Any, List
from app.services.multimodal.base import (
    BaseOCRProvider,
    BaseTranscriptionProvider,
    OCROutput,
    OCRTextBlock,
    TranscriptionOutput,
    TranscriptSegment,
    ExtractionUnavailableError,
)


class MockOCRProvider(BaseOCRProvider):
    """
    Deterministic schema-compliant mock OCR provider for CI and offline execution.
    Generates structured OCR text blocks without requiring external cloud/native OCR binaries.
    """

    @property
    def provider_name(self) -> str:
        return "mock_ocr"

    async def extract_text(self, image_bytes: bytes, filename: str) -> OCROutput:
        file_hash = hashlib.md5(image_bytes).hexdigest()[:8]
        
        blocks = [
            OCRTextBlock(
                text=f"# Visual Document Header: {filename}",
                confidence=0.98,
                bounding_box={"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.12},
                block_type="heading",
            ),
            OCRTextBlock(
                text=f"TransformAI multimodal intelligence extracted text from image {filename} (hash: {file_hash}). The visual diagram illustrates the end-to-end data pipeline from document ingestion to vector embedding storage.",
                confidence=0.95,
                bounding_box={"x": 0.05, "y": 0.20, "w": 0.90, "h": 0.40},
                block_type="paragraph",
            ),
            OCRTextBlock(
                text="Figure 1.1: Schematic representation of source-grounded multimodal content transformation architecture.",
                confidence=0.92,
                bounding_box={"x": 0.10, "y": 0.65, "w": 0.80, "h": 0.15},
                block_type="caption",
            ),
        ]
        
        raw_text = "\n\n".join(b.text for b in blocks)
        return OCROutput(
            blocks=blocks,
            raw_text=raw_text,
            metadata={
                "provider": self.provider_name,
                "filename": filename,
                "extracted_blocks_count": len(blocks),
                "checksum": file_hash,
            },
        )


class MockTranscriptionProvider(BaseTranscriptionProvider):
    """
    Deterministic schema-compliant mock speech-to-text provider for CI and offline execution.
    Generates structured timestamped transcript segments without external audio services.
    """

    @property
    def provider_name(self) -> str:
        return "mock_stt"

    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionOutput:
        file_hash = hashlib.md5(audio_bytes).hexdigest()[:8]
        
        segments = [
            TranscriptSegment(
                start_time_sec=0.0,
                end_time_sec=18.5,
                text=f"Welcome to the TransformAI multimodal session regarding {filename}. In this segment we discuss system architecture and vector normalization.",
                speaker="Speaker 1",
                confidence=0.96,
            ),
            TranscriptSegment(
                start_time_sec=18.5,
                end_time_sec=45.0,
                text="The speech transcription pipeline parses input waveforms, segments audio intervals, and aligns textual dialogue with provider-returned timestamps.",
                speaker="Speaker 2",
                confidence=0.94,
            ),
            TranscriptSegment(
                start_time_sec=45.0,
                end_time_sec=72.0,
                text="All extracted transcript segments are normalized into DocumentElements for downstream chunking and pgvector similarity retrieval.",
                speaker="Speaker 1",
                confidence=0.97,
            ),
        ]
        
        full_transcript = " ".join(s.text for s in segments)
        return TranscriptionOutput(
            segments=segments,
            full_transcript=full_transcript,
            duration_seconds=72.0,
            language="en",
            metadata={
                "provider": self.provider_name,
                "filename": filename,
                "segment_count": len(segments),
                "checksum": file_hash,
            },
        )


class UnavailableOCRProvider(BaseOCRProvider):
    """
    Explicitly simulates an unconfigured or unavailable OCR engine.
    Always raises ExtractionUnavailableError.
    """

    @property
    def provider_name(self) -> str:
        return "unavailable_ocr"

    async def extract_text(self, image_bytes: bytes, filename: str) -> OCROutput:
        raise ExtractionUnavailableError(
            f"OCR extraction is unavailable for '{filename}'. No OCR engine is configured or active."
        )


class UnavailableTranscriptionProvider(BaseTranscriptionProvider):
    """
    Explicitly simulates an unconfigured or unavailable Transcription engine.
    Always raises ExtractionUnavailableError.
    """

    @property
    def provider_name(self) -> str:
        return "unavailable_stt"

    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionOutput:
        raise ExtractionUnavailableError(
            f"Speech-to-text transcription is unavailable for '{filename}'. No transcription engine is configured or active."
        )
