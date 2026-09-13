import io
import pytest
from PIL import Image

from app.services.document.parsers import get_parser_for_filename
from app.services.document.parsers.image import ImageParser
from app.services.document.parsers.audio import AudioParser
from app.services.document.parsers.video import VideoParser
from app.services.document.models import SourceModality, ElementType
from app.services.multimodal.providers.mock import (
    MockOCRProvider,
    MockTranscriptionProvider,
    UnavailableOCRProvider,
    UnavailableTranscriptionProvider,
)
from app.services.multimodal.base import ExtractionUnavailableError


def _generate_test_image_bytes() -> bytes:
    img = Image.new("RGB", (320, 240), color=(15, 23, 42))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_test_wav_bytes() -> bytes:
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_image_parser_success():
    parser = ImageParser(ocr_provider=MockOCRProvider())
    img_bytes = _generate_test_image_bytes()

    parsed = await parser.parse(img_bytes, "system_arch.png")
    assert parsed.modality == SourceModality.IMAGE
    assert parsed.media_metadata["width"] == 320
    assert parsed.media_metadata["height"] == 240
    assert len(parsed.elements) > 0
    assert parsed.elements[0].modality == SourceModality.IMAGE
    assert parsed.elements[0].confidence_score is not None


@pytest.mark.asyncio
async def test_image_parser_corrupted_bytes():
    parser = ImageParser(ocr_provider=MockOCRProvider())
    with pytest.raises(ValueError, match="Invalid or corrupted image"):
        await parser.parse(b"not_an_image", "bad.png")


@pytest.mark.asyncio
async def test_image_parser_unavailable_provider():
    parser = ImageParser(ocr_provider=UnavailableOCRProvider())
    img_bytes = _generate_test_image_bytes()
    with pytest.raises(ExtractionUnavailableError):
        await parser.parse(img_bytes, "system_arch.png")


@pytest.mark.asyncio
async def test_audio_parser_success():
    parser = AudioParser(transcription_provider=MockTranscriptionProvider())
    wav_bytes = _generate_test_wav_bytes()

    parsed = await parser.parse(wav_bytes, "interview.wav")
    assert parsed.modality == SourceModality.AUDIO
    assert parsed.duration_seconds is not None
    assert len(parsed.elements) > 0
    assert parsed.elements[0].element_type == ElementType.TRANSCRIPT_SEGMENT
    assert parsed.elements[0].timestamp_start_sec is not None
    assert parsed.elements[0].formatted_timestamp is not None


@pytest.mark.asyncio
async def test_audio_parser_unavailable_provider():
    parser = AudioParser(transcription_provider=UnavailableTranscriptionProvider())
    wav_bytes = _generate_test_wav_bytes()
    with pytest.raises(ExtractionUnavailableError):
        await parser.parse(wav_bytes, "interview.wav")


@pytest.mark.asyncio
async def test_video_parser_success():
    parser = VideoParser(transcription_provider=MockTranscriptionProvider())
    video_bytes = b"fake_mp4_stream_data"

    parsed = await parser.parse(video_bytes, "demo.mp4")
    assert parsed.modality == SourceModality.VIDEO
    assert len(parsed.elements) > 1
    # Check scene header and transcript segments
    assert any(e.element_type == ElementType.HEADING for e in parsed.elements)
    assert any(e.element_type == ElementType.TRANSCRIPT_SEGMENT for e in parsed.elements)


def test_multimodal_parser_factory_registration():
    for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
        p = get_parser_for_filename(f"file{ext}")
        assert isinstance(p, ImageParser)

    for ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]:
        p = get_parser_for_filename(f"file{ext}")
        assert isinstance(p, AudioParser)

    for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
        p = get_parser_for_filename(f"file{ext}")
        assert isinstance(p, VideoParser)
