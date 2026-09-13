import io
import logging
from typing import Optional, List
from PIL import Image

from app.services.document.parsers.base import BaseDocumentParser
from app.services.document.models import (
    ParsedDocument,
    DocumentElement,
    ElementType,
    SourceModality,
)
from app.services.multimodal.base import BaseOCRProvider, ExtractionUnavailableError
from app.services.multimodal.factory import get_ocr_provider

logger = logging.getLogger("transformai.parsers.image")


class ImageParser(BaseDocumentParser):
    """
    Parser for visual image documents (PNG, JPG, JPEG, WEBP, BMP, TIFF).
    1. Uses Pillow exclusively for image decoding, dimension verification, and container metadata.
    2. Delegates text recognition to an explicit BaseOCRProvider.
    3. Normalizes recognized text blocks into modality-independent DocumentElements.
    """

    def __init__(self, ocr_provider: Optional[BaseOCRProvider] = None):
        self._ocr_provider = ocr_provider

    @property
    def ocr_provider(self) -> BaseOCRProvider:
        return self._ocr_provider or get_ocr_provider()

    @property
    def supported_extensions(self) -> List[str]:
        return [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        # 1. Image validation and metadata inspection with Pillow
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                width, height = img.size
                img_format = img.format or "UNKNOWN"
                img_mode = img.mode
        except Exception as exc:
            logger.error("Failed to decode image file '%s': %s", filename, exc)
            raise ValueError(f"Invalid or corrupted image file '{filename}': {str(exc)}") from exc

        media_metadata = {
            "width": width,
            "height": height,
            "format": img_format,
            "color_mode": img_mode,
            "aspect_ratio": round(width / max(1, height), 2),
        }

        # 2. Text recognition via explicit OCR Provider
        logger.info(
            "Extracting OCR text from '%s' (%dx%d) using provider '%s'...",
            filename,
            width,
            height,
            self.ocr_provider.provider_name,
        )
        ocr_result = await self.ocr_provider.extract_text(file_bytes, filename)

        # 3. Structure into DocumentElements
        elements: List[DocumentElement] = []
        for idx, block in enumerate(ocr_result.blocks):
            if not block.text.strip():
                continue

            # Determine structural element type
            elem_type = ElementType.OCR_BLOCK
            if block.block_type == "heading" or block.text.startswith("#"):
                elem_type = ElementType.HEADING

            elem = DocumentElement(
                element_type=elem_type,
                text=block.text.strip(),
                page_number=1,
                section_title=f"Image Section {idx + 1}" if elem_type == ElementType.OCR_BLOCK else block.text.lstrip("# ").strip(),
                modality=SourceModality.IMAGE,
                confidence_score=block.confidence,  # Stored only if provider supplied it
                spatial_bounds=block.bounding_box,
                metadata={
                    "block_index": idx,
                    "block_type": block.block_type,
                    "image_dimensions": f"{width}x{height}",
                },
            )
            elements.append(elem)

        raw_text = ocr_result.raw_text or "\n\n".join(e.text for e in elements)

        return ParsedDocument(
            elements=elements,
            raw_text=raw_text,
            page_count=1,
            modality=SourceModality.IMAGE,
            media_metadata=media_metadata,
            metadata={
                "ocr_provider": self.ocr_provider.provider_name,
                "image_metadata": media_metadata,
                "extracted_blocks": len(elements),
            },
        )
