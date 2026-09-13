import pytest
from app.services.multimodal.base import (
    ExtractionUnavailableError,
    OCRTextBlock,
    OCROutput,
    TranscriptSegment,
    TranscriptionOutput,
)
from app.services.multimodal.providers.mock import (
    MockOCRProvider,
    MockTranscriptionProvider,
    UnavailableOCRProvider,
    UnavailableTranscriptionProvider,
)
from app.services.multimodal.factory import (
    get_ocr_provider,
    get_transcription_provider,
)


@pytest.mark.asyncio
async def test_mock_ocr_provider():
    provider = MockOCRProvider()
    assert provider.provider_name == "mock_ocr"

    sample_bytes = b"sample_image_binary_data"
    result: OCROutput = await provider.extract_text(sample_bytes, "test_chart.png")

    assert len(result.blocks) > 0
    assert result.raw_text != ""
    assert result.metadata["provider"] == "mock_ocr"
    assert result.blocks[0].confidence is not None
    assert result.blocks[0].bounding_box is not None


@pytest.mark.asyncio
async def test_mock_transcription_provider():
    provider = MockTranscriptionProvider()
    assert provider.provider_name == "mock_stt"

    sample_bytes = b"sample_audio_binary_data"
    result: TranscriptionOutput = await provider.transcribe(sample_bytes, "briefing.wav")

    assert len(result.segments) > 0
    assert result.duration_seconds is not None
    assert result.segments[0].formatted_timestamp != ""
    assert result.segments[0].start_time_sec < result.segments[0].end_time_sec


@pytest.mark.asyncio
async def test_unavailable_providers_raise_error():
    ocr_unavail = UnavailableOCRProvider()
    with pytest.raises(ExtractionUnavailableError, match="No OCR engine is configured"):
        await ocr_unavail.extract_text(b"data", "image.png")

    stt_unavail = UnavailableTranscriptionProvider()
    with pytest.raises(ExtractionUnavailableError, match="No transcription engine is configured"):
        await stt_unavail.transcribe(b"data", "audio.mp3")


def test_multimodal_provider_factories():
    ocr_mock = get_ocr_provider("mock")
    assert isinstance(ocr_mock, MockOCRProvider)

    ocr_none = get_ocr_provider("unavailable")
    assert isinstance(ocr_none, UnavailableOCRProvider)

    stt_mock = get_transcription_provider("mock")
    assert isinstance(stt_mock, MockTranscriptionProvider)

    stt_none = get_transcription_provider("unavailable")
    assert isinstance(stt_none, UnavailableTranscriptionProvider)
