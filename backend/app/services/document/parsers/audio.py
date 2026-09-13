import io
import wave
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.services.document.parsers.base import BaseDocumentParser
from app.services.document.models import (
    ParsedDocument,
    DocumentElement,
    ElementType,
    SourceModality,
)
from app.services.multimodal.base import BaseTranscriptionProvider, ExtractionUnavailableError
from app.services.multimodal.factory import get_transcription_provider

logger = logging.getLogger("transformai.parsers.audio")


class AudioParser(BaseDocumentParser):
    """
    Parser for audio recordings (MP3, WAV, M4A, OGG, FLAC).
    1. Uses standard audio inspection for container metadata (duration, sample rate, channels).
    2. Delegates speech recognition to an explicit BaseTranscriptionProvider.
    3. Normalizes timestamped transcript segments into modality-independent DocumentElements.
    """

    def __init__(self, transcription_provider: Optional[BaseTranscriptionProvider] = None):
        self._transcription_provider = transcription_provider

    @property
    def transcription_provider(self) -> BaseTranscriptionProvider:
        return self._transcription_provider or get_transcription_provider()

    @property
    def supported_extensions(self) -> List[str]:
        return [".mp3", ".wav", ".m4a", ".ogg", ".flac"]

    @staticmethod
    def _extract_container_metadata(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extracts technical container metadata using standard library tools."""
        ext = Path(filename).suffix.lower()
        meta: Dict[str, Any] = {
            "format": ext.lstrip("."),
            "file_size_bytes": len(file_bytes),
        }

        # For WAV audio, inspect header using standard library wave module
        if ext == ".wav":
            try:
                with wave.open(io.BytesIO(file_bytes), "rb") as wf:
                    channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    framerate = wf.getframerate()
                    n_frames = wf.getnframes()
                    duration_sec = round(n_frames / float(framerate), 2)
                    meta.update({
                        "channels": channels,
                        "sample_width": sample_width,
                        "sample_rate_hz": framerate,
                        "frame_count": n_frames,
                        "duration_seconds": duration_sec,
                    })
            except Exception as e:
                logger.warning("Could not read WAV container header for '%s': %s", filename, e)

        return meta

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        # 1. Container metadata inspection
        container_meta = self._extract_container_metadata(file_bytes, filename)

        # 2. Speech-to-text transcription via explicit Transcription Provider
        logger.info(
            "Transcribing audio file '%s' using provider '%s'...",
            filename,
            self.transcription_provider.provider_name,
        )
        stt_result = await self.transcription_provider.transcribe(file_bytes, filename)

        # 3. Structure timestamped segments into DocumentElements
        elements: List[DocumentElement] = []
        for idx, segment in enumerate(stt_result.segments):
            if not segment.text.strip():
                continue

            section_label = f"Audio [{segment.formatted_timestamp}]"
            if segment.speaker:
                section_label = f"{segment.speaker} [{segment.formatted_timestamp}]"

            elem = DocumentElement(
                element_type=ElementType.TRANSCRIPT_SEGMENT,
                text=segment.text.strip(),
                page_number=1,
                section_title=section_label,
                modality=SourceModality.AUDIO,
                timestamp_start_sec=segment.start_time_sec,
                timestamp_end_sec=segment.end_time_sec,
                formatted_timestamp=segment.formatted_timestamp,
                confidence_score=segment.confidence,
                metadata={
                    "segment_index": idx,
                    "speaker": segment.speaker,
                    "start_time_sec": segment.start_time_sec,
                    "end_time_sec": segment.end_time_sec,
                },
            )
            elements.append(elem)

        raw_text = stt_result.full_transcript or "\n\n".join(e.text for e in elements)
        duration = stt_result.duration_seconds or container_meta.get("duration_seconds")

        return ParsedDocument(
            elements=elements,
            raw_text=raw_text,
            page_count=1,
            modality=SourceModality.AUDIO,
            duration_seconds=duration,
            media_metadata=container_meta,
            metadata={
                "transcription_provider": self.transcription_provider.provider_name,
                "audio_metadata": container_meta,
                "total_segments": len(elements),
                "duration_seconds": duration,
                "language": stt_result.language,
            },
        )
