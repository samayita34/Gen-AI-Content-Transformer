import io
import asyncio
import pypdf
from typing import List
from app.services.document.parsers.base import BaseDocumentParser
from app.services.document.models import ParsedDocument, DocumentElement, ElementType


class PDFParser(BaseDocumentParser):
    """
    Parser for PDF documents using pypdf.
    Preserves page boundaries, document metadata, and extracted text blocks.
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        def _parse_sync() -> ParsedDocument:
            stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(stream)
            num_pages = len(reader.pages)

            metadata = {}
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.title,
                    "author": reader.metadata.author,
                    "creator": reader.metadata.creator,
                    "producer": reader.metadata.producer,
                }
                # Clean None values
                metadata = {k: v for k, v in metadata.items() if v is not None}

            elements: List[DocumentElement] = []
            full_text_blocks: List[str] = []

            for page_idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    continue

                full_text_blocks.append(page_text)

                # Split page text into paragraph blocks
                raw_paragraphs = page_text.split("\n\n")
                for p in raw_paragraphs:
                    p_clean = p.strip()
                    if p_clean:
                        elements.append(
                            DocumentElement(
                                element_type=ElementType.PARAGRAPH,
                                text=p_clean,
                                page_number=page_idx,
                                metadata={"page": page_idx, "filename": filename},
                            )
                        )

            raw_text = "\n\n".join(full_text_blocks)

            return ParsedDocument(
                elements=elements,
                raw_text=raw_text,
                page_count=num_pages,
                metadata=metadata,
            )

        return await asyncio.to_thread(_parse_sync)
