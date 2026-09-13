from pathlib import Path
from typing import Optional, Dict
from app.services.document.parsers.base import BaseDocumentParser
from app.services.document.parsers.pdf import PDFParser
from app.services.document.parsers.docx import DocxParser
from app.services.document.parsers.txt import TxtParser
from app.services.document.parsers.image import ImageParser
from app.services.document.parsers.audio import AudioParser
from app.services.document.parsers.video import VideoParser

_pdf_parser = PDFParser()
_docx_parser = DocxParser()
_txt_parser = TxtParser()
_image_parser = ImageParser()
_audio_parser = AudioParser()
_video_parser = VideoParser()

_PARSERS: Dict[str, BaseDocumentParser] = {
    # Text Documents
    ".pdf": _pdf_parser,
    ".docx": _docx_parser,
    ".txt": _txt_parser,
    ".text": _txt_parser,
    ".md": _txt_parser,
    
    # Images (OCR)
    ".png": _image_parser,
    ".jpg": _image_parser,
    ".jpeg": _image_parser,
    ".webp": _image_parser,
    ".bmp": _image_parser,
    ".tiff": _image_parser,
    
    # Audio (Speech-to-Text)
    ".mp3": _audio_parser,
    ".wav": _audio_parser,
    ".m4a": _audio_parser,
    ".ogg": _audio_parser,
    ".flac": _audio_parser,
    
    # Video (Audio Transcription + Scene Metadata)
    ".mp4": _video_parser,
    ".avi": _video_parser,
    ".mov": _video_parser,
    ".mkv": _video_parser,
    ".webm": _video_parser,
}


def get_parser_for_filename(filename: str) -> Optional[BaseDocumentParser]:
    """Returns matching parser for a given filename extension across text, image, audio, and video formats."""
    ext = Path(filename).suffix.lower()
    return _PARSERS.get(ext)


__all__ = [
    "BaseDocumentParser",
    "PDFParser",
    "DocxParser",
    "TxtParser",
    "ImageParser",
    "AudioParser",
    "VideoParser",
    "get_parser_for_filename",
]
