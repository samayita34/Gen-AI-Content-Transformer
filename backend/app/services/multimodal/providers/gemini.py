import base64
import json
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings
from app.services.multimodal.base import (
    BaseOCRProvider,
    BaseTranscriptionProvider,
    OCROutput,
    OCRTextBlock,
    TranscriptionOutput,
    TranscriptSegment,
    ExtractionUnavailableError,
)

logger = logging.getLogger("transformai.multimodal.gemini")


class GeminiVisionOCRProvider(BaseOCRProvider):
    """
    Real OCR provider using Google Gemini Vision REST API.
    Sends raw image bytes with a structured JSON schema instruction for OCR block extraction.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.LLM_MODEL or "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini_vision"

    async def extract_text(self, image_bytes: bytes, filename: str) -> OCROutput:
        if not self.api_key:
            raise ExtractionUnavailableError(
                "Gemini Vision OCR extraction is unavailable: GEMINI_API_KEY is not configured."
            )

        # Detect mime type from filename
        ext = filename.lower().split(".")[-1]
        mime_type = f"image/{ext}" if ext in ["png", "jpeg", "webp", "gif"] else "image/jpeg"
        if ext == "jpg":
            mime_type = "image/jpeg"

        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        prompt = (
            "Perform Optical Character Recognition (OCR) on this image. "
            "Extract all text accurately into a structured JSON object with the following schema:\n"
            "{\n"
            '  "raw_text": "full extracted text",\n'
            '  "blocks": [\n'
            '    {\n'
            '      "text": "recognized block text",\n'
            '      "block_type": "heading" | "paragraph" | "caption" | "table_cell",\n'
            '      "confidence": 0.95 (float if estimable, else null),\n'
            '      "bounding_box": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.2} (if estimable, else null)\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Output ONLY valid JSON."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)

            blocks: List[OCRTextBlock] = []
            for b in parsed.get("blocks", []):
                blocks.append(
                    OCRTextBlock(
                        text=b.get("text", "").strip(),
                        confidence=b.get("confidence"),
                        bounding_box=b.get("bounding_box"),
                        block_type=b.get("block_type", "paragraph"),
                    )
                )

            raw_text = parsed.get("raw_text", "\n\n".join(b.text for b in blocks))
            return OCROutput(
                blocks=blocks,
                raw_text=raw_text,
                metadata={"provider": self.provider_name, "model": self.model, "filename": filename},
            )

        except Exception as exc:
            logger.error("Gemini Vision OCR extraction failed for %s: %s", filename, exc)
            raise ExtractionUnavailableError(
                f"Gemini Vision OCR extraction failed for '{filename}': {str(exc)}"
            ) from exc


class GeminiAudioTranscriptionProvider(BaseTranscriptionProvider):
    """
    Real Audio Speech-to-Text provider using Google Gemini Audio REST API.
    Sends raw audio bytes with a structured JSON schema instruction for timestamped transcription.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.LLM_MODEL or "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini_audio"

    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionOutput:
        if not self.api_key:
            raise ExtractionUnavailableError(
                "Gemini Audio Transcription is unavailable: GEMINI_API_KEY is not configured."
            )

        ext = filename.lower().split(".")[-1]
        mime_map = {
            "mp3": "audio/mp3",
            "wav": "audio/wav",
            "m4a": "audio/m4a",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
        }
        mime_type = mime_map.get(ext, "audio/mp3")

        b64_data = base64.b64encode(audio_bytes).decode("utf-8")
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        prompt = (
            "Transcribe this audio recording into timestamped dialogue segments. "
            "Output a structured JSON object with the following schema:\n"
            "{\n"
            '  "full_transcript": "entire continuous transcription text",\n'
            '  "duration_seconds": 120.5,\n'
            '  "language": "en",\n'
            '  "segments": [\n'
            '    {\n'
            '      "start_time_sec": 0.0,\n'
            '      "end_time_sec": 15.2,\n'
            '      "text": "spoken dialogue segment",\n'
            '      "speaker": "Speaker 1" (if identifiable, else null),\n'
            '      "confidence": 0.95 (if provided, else null)\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Output ONLY valid JSON."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content)

            segments: List[TranscriptSegment] = []
            for s in parsed.get("segments", []):
                segments.append(
                    TranscriptSegment(
                        start_time_sec=float(s.get("start_time_sec", 0.0)),
                        end_time_sec=float(s.get("end_time_sec", 0.0)),
                        text=s.get("text", "").strip(),
                        speaker=s.get("speaker"),
                        confidence=s.get("confidence"),
                    )
                )

            full_tx = parsed.get("full_transcript", " ".join(s.text for s in segments))
            return TranscriptionOutput(
                segments=segments,
                full_transcript=full_tx,
                duration_seconds=parsed.get("duration_seconds"),
                language=parsed.get("language", "en"),
                metadata={"provider": self.provider_name, "model": self.model, "filename": filename},
            )

        except Exception as exc:
            logger.error("Gemini Audio Transcription failed for %s: %s", filename, exc)
            raise ExtractionUnavailableError(
                f"Gemini Audio Transcription failed for '{filename}': {str(exc)}"
            ) from exc
