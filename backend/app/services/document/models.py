import enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ElementType(str, enum.Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    UNKNOWN = "unknown"


class DocumentElement(BaseModel):
    """
    Represents a discrete structural unit (paragraph, heading, list item)
    extracted during parsing.
    """
    element_type: ElementType = ElementType.PARAGRAPH
    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    heading_level: Optional[int] = None  # 1 for H1, 2 for H2, etc.
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
    Normalized intermediate representation of an ingested document.
    Preserves document structure, page numbering, sections, and metadata.
    """
    elements: List[DocumentElement] = Field(default_factory=list)
    raw_text: str = ""
    page_count: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def total_character_count(self) -> int:
        return sum(e.character_count for e in self.elements) or len(self.raw_text)

    @property
    def total_word_count(self) -> int:
        if self.elements:
            return sum(len(e.text.split()) for e in self.elements)
        return len(self.raw_text.split())
