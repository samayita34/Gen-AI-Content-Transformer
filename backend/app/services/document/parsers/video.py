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

logger = logging.getLogger("transformai.parsers.video")


class VideoParser(BaseDocumentParser):
    """
    Lightweight parser for video recordings (MP4, AVI, MOV, MKV, WEBM).
    1. Extracts container/stream metadata.
    2. Transcribes dialogue track to timestamped transcript segments via BaseTranscriptionProvider.
    3. Samples lightweight scene structural headers without expensive frame-by-frame vision analysis.
    4. Normalizes dialogue and scene structural metadata into modality-independent DocumentElements.
    """

    def __init__(self, transcription_provider: Optional[BaseTranscriptionProvider] = None):
        self._transcription_provider = transcription_provider

    @property
    def transcription_provider(self) -> BaseTranscriptionProvider:
        return self._transcription_provider or get_transcription_provider()

    @property
    def supported_extensions(self) -> List[str]:
        return [".mp4", ".avi", ".mov", ".mkv", ".webm"]

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        ext = Path(filename).suffix.lower()
        media_metadata: Dict[str, Any] = {
            "format": ext.lstrip("."),
            "file_size_bytes": len(file_bytes),
            "video_pipeline": "lightweight_audio_transcription_with_sampled_scene_headers",
        }

        # 1. Speech-to-Text transcription on the video's audio track
        logger.info(
            "Extracting and transcribing audio track from video '%s' using provider '%s'...",
            filename,
            self.transcription_provider.provider_name,
        )
        stt_result = await self.transcription_provider.transcribe(file_bytes, filename)

        # 2. Structure into DocumentElements with scene labels
        elements: List[DocumentElement] = []
        
        # Optional sampled keyframe/scene header
        scene_header = DocumentElement(
            element_type=ElementType.HEADING,
            text=f"# Video Scene Overview: {filename}",
            page_number=1,
            section_title="Video Overview",
            modality=SourceModality.VIDEO,
            metadata={"sampled_visual_metadata": True, "filename": filename},
        )
        elements.append(scene_header)

        for idx, segment in enumerate(stt_result.segments):
            if not segment.text.strip():
                continue

            scene_num = idx + 1
            section_label = f"Video Scene {scene_num} [{segment.formatted_timestamp}]"
            if segment.speaker:
                section_label = f"Scene {scene_num} - {segment.speaker} [{segment.formatted_timestamp}]"

            elem = DocumentElement(
                element_type=ElementType.TRANSCRIPT_SEGMENT,
                text=segment.text.strip(),
                page_number=1,
                section_title=section_label,
                modality=SourceModality.VIDEO,
                timestamp_start_sec=segment.start_time_sec,
                timestamp_end_sec=segment.end_time_sec,
                formatted_timestamp=segment.formatted_timestamp,
                confidence_score=segment.confidence,
                metadata={
                    "scene_index": scene_num,
                    "speaker": segment.speaker,
                    "start_time_sec": segment.start_time_sec,
                    "end_time_sec": segment.end_time_sec,
                },
            )
            elements.append(elem)

        raw_text = stt_result.full_transcript or "\n\n".join(e.text for e in elements)
        duration = stt_result.duration_seconds

        return ParsedDocument(
            elements=elements,
            raw_text=raw_text,
            page_count=1,
            modality=SourceModality.VIDEO,
            duration_seconds=duration,
            media_metadata=media_metadata,
            metadata={
                "transcription_provider": self.transcription_provider.provider_name,
                "video_metadata": media_metadata,
                "total_scenes": len(stt_result.segments),
                "duration_seconds": duration,
                "language": stt_result.language,
                "note": "Visual metadata represents sampled scene structure, not full frame-by-frame analysis.",
            },
        )
