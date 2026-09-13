from pathlib import Path
from typing import Optional, Dict
from app.services.document.parsers.base import BaseDocumentParser
from app.services.document.parsers.pdf import PDFParser
from app.services.document.parsers.docx import DocxParser
from app.services.document.parsers.txt import TxtParser

_PARSERS: Dict[str, BaseDocumentParser] = {
    ".pdf": PDFParser(),
    ".docx": DocxParser(),
    ".txt": TxtParser(),
    ".text": TxtParser(),
    ".md": TxtParser(),
}


def get_parser_for_filename(filename: str) -> Optional[BaseDocumentParser]:
    """Returns matching parser for a given filename extension."""
    ext = Path(filename).suffix.lower()
    return _PARSERS.get(ext)


__all__ = [
    "BaseDocumentParser",
    "PDFParser",
    "DocxParser",
    "TxtParser",
    "get_parser_for_filename",
]
