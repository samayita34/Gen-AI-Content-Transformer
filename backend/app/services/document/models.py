import enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceModality(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ElementType(str, enum.Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    OCR_BLOCK = "ocr_block"
    TRANSCRIPT_SEGMENT = "transcript_segment"
    VISUAL_METADATA = "visual_metadata"
    UNKNOWN = "unknown"


class DocumentElement(BaseModel):
    """
    Represents a discrete structural or multimodal unit (paragraph, heading, list item,
    OCR text block, or transcript segment) extracted during parsing.
    """
    element_type: ElementType = ElementType.PARAGRAPH
    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    heading_level: Optional[int] = None  # 1 for H1, 2 for H2, etc.

    # Multimodal annotations (modality-independent common model)
    modality: SourceModality = SourceModality.TEXT
    timestamp_start_sec: Optional[float] = None
    timestamp_end_sec: Optional[float] = None
    formatted_timestamp: Optional[str] = None  # e.g., "00:15 - 00:45"
    confidence_score: Optional[float] = None  # Provided only if underlying provider gives it
    spatial_bounds: Optional[Dict[str, float]] = None  # e.g., {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.1}

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def character_count(self) -> int:
        return len(self.text)

    @property
    def estimated_token_count(self) -> int:
        # Approximate 1 token ~= 4 characters / 0.75 words
        return max(1, len(self.text.split()))


class ParsedDocument(BaseModel):
    """
    Normalized intermediate representation of an ingested document or media file.
    Preserves document structure, page numbering, timestamps, sections, and metadata.
    """
    elements: List[DocumentElement] = Field(default_factory=list)
    raw_text: str = ""
    page_count: int = 1
    modality: SourceModality = SourceModality.TEXT
    duration_seconds: Optional[float] = None
    media_metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def total_character_count(self) -> int:
        return sum(e.character_count for e in self.elements) or len(self.raw_text)

    @property
    def total_word_count(self) -> int:
        if self.elements:
            return sum(len(e.text.split()) for e in self.elements)
        return len(self.raw_text.split())
