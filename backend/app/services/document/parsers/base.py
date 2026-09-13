from abc import ABC, abstractmethod
from typing import BinaryIO, Union
from app.services.document.models import ParsedDocument


class BaseDocumentParser(ABC):
    """
    Abstract interface for document format parsers.
    Parses raw binary/path into the normalized ParsedDocument representation.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Returns file extensions handled by this parser, e.g. ['.pdf']."""
        pass

    @abstractmethod
    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Parses raw document bytes into a normalized ParsedDocument."""
        pass
