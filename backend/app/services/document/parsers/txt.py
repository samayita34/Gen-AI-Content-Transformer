import asyncio
from typing import List
from app.services.document.parsers.base import BaseDocumentParser
from app.services.document.models import ParsedDocument, DocumentElement, ElementType


class TxtParser(BaseDocumentParser):
    """
    Parser for plain text (.txt) and markdown/structured text files.
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".txt", ".text", ".md"]

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        def _parse_sync() -> ParsedDocument:
            # Handle encoding detection gracefully
            text = None
            for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"):
                try:
                    text = file_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if text is None:
                text = file_bytes.decode("utf-8", errors="replace")

            elements: List[DocumentElement] = []
            paragraphs = text.split("\n\n")

            for p in paragraphs:
                p_clean = p.strip()
                if p_clean:
                    elements.append(
                        DocumentElement(
                            element_type=ElementType.PARAGRAPH,
                            text=p_clean,
                            metadata={"filename": filename},
                        )
                    )

            return ParsedDocument(
                elements=elements,
                raw_text=text,
                page_count=1,
                metadata={"filename": filename},
            )

        return await asyncio.to_thread(_parse_sync)
