import logging
from typing import Optional
from app.core.config import settings
from app.services.multimodal.base import (
    BaseOCRProvider,
    BaseTranscriptionProvider,
    ExtractionUnavailableError,
)
from app.services.multimodal.providers.mock import (
    MockOCRProvider,
    MockTranscriptionProvider,
    UnavailableOCRProvider,
    UnavailableTranscriptionProvider,
)
from app.services.multimodal.providers.gemini import (
    GeminiVisionOCRProvider,
    GeminiAudioTranscriptionProvider,
)

logger = logging.getLogger("transformai.multimodal.factory")


def get_ocr_provider(provider_name: Optional[str] = None) -> BaseOCRProvider:
    """
    Factory to retrieve configured OCR provider instance.
    Defaults to settings.OCR_PROVIDER (defaults to 'mock').
    """
    name = (provider_name or settings.OCR_PROVIDER).lower()

    if name in ["mock", "mock_ocr"]:
        return MockOCRProvider()
    elif name in ["gemini", "gemini_vision"]:
        return GeminiVisionOCRProvider()
    elif name in ["unavailable", "none"]:
        return UnavailableOCRProvider()
    else:
        logger.warning("Unknown OCR provider '%s'. Falling back to MockOCRProvider.", name)
        return MockOCRProvider()


def get_transcription_provider(provider_name: Optional[str] = None) -> BaseTranscriptionProvider:
    """
    Factory to retrieve configured Speech-to-Text provider instance.
    Defaults to settings.TRANSCRIPTION_PROVIDER (defaults to 'mock').
    """
    name = (provider_name or settings.TRANSCRIPTION_PROVIDER).lower()

    if name in ["mock", "mock_stt", "mock_transcription"]:
        return MockTranscriptionProvider()
    elif name in ["gemini", "gemini_audio"]:
        return GeminiAudioTranscriptionProvider()
    elif name in ["unavailable", "none"]:
        return UnavailableTranscriptionProvider()
    else:
        logger.warning("Unknown transcription provider '%s'. Falling back to MockTranscriptionProvider.", name)
        return MockTranscriptionProvider()


default_ocr_provider = get_ocr_provider()
default_transcription_provider = get_transcription_provider()
