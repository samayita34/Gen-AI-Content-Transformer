from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ExtractionUnavailableError(RuntimeError):
    """
    Raised when an OCR or Speech-to-Text extraction provider is not configured
    or cannot perform extraction.
    """
    pass


# ---------------------------------------------------------------------------
# OCR Data Models & Base Provider
# ---------------------------------------------------------------------------

class OCRTextBlock(BaseModel):
    """
    Represents a discrete recognized text region from an image.
    Confidence and spatial bounding box are recorded only if provided by provider.
    """
    text: str
    confidence: Optional[float] = None  # Stored only if provider explicitly supplies it
    bounding_box: Optional[Dict[str, float]] = None  # e.g., {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.1}
    block_type: Optional[str] = "paragraph"  # "heading", "paragraph", "caption", "table_cell"


class OCROutput(BaseModel):
    """Normalized OCR output from an image source."""
    blocks: List[OCRTextBlock] = Field(default_factory=list)
    raw_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseOCRProvider(ABC):
    """
    Abstract interface for Optical Character Recognition (OCR) engines.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the OCR provider."""
        pass

    @abstractmethod
    async def extract_text(self, image_bytes: bytes, filename: str) -> OCROutput:
        """
        Extracts recognized text blocks from raw image bytes.
        Raises ExtractionUnavailableError if provider cannot perform extraction.
        """
        pass


# ---------------------------------------------------------------------------
# Speech-to-Text Data Models & Base Provider
# ---------------------------------------------------------------------------

class TranscriptSegment(BaseModel):
    """
    Represents a timestamped speech segment from an audio/video source.
    Timestamps represent provider-returned start and end offsets in seconds.
    """
    start_time_sec: float
    end_time_sec: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None  # Stored only if provider explicitly supplies it

    @property
    def formatted_timestamp(self) -> str:
        """Returns provider-returned timestamp in [MM:SS - MM:SS] format."""
        def _fmt(sec: float) -> str:
            m = int(sec // 60)
            s = int(sec % 60)
            return f"{m:02d}:{s:02d}"
        return f"{_fmt(self.start_time_sec)} - {_fmt(self.end_time_sec)}"


class TranscriptionOutput(BaseModel):
    """Normalized speech-to-text transcript output from an audio/video source."""
    segments: List[TranscriptSegment] = Field(default_factory=list)
    full_transcript: str = ""
    duration_seconds: Optional[float] = None
    language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTranscriptionProvider(ABC):
    """
    Abstract interface for Speech-to-Text (STT) transcription engines.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the transcription provider."""
        pass

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionOutput:
        """
        Transcribes raw audio bytes into timestamped transcript segments.
        Raises ExtractionUnavailableError if provider cannot perform transcription.
        """
        pass
