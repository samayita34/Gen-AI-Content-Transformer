import re
from typing import List, Optional
from app.services.document.models import ParsedDocument, DocumentElement, ElementType


class StructureDetector:
    """
    Deterministic document structure detector.
    Analyzes typography, numbering patterns, and line layout to identify
    headings, section hierarchies, lists, and paragraphs.
    """

    # Common heading patterns:
    # 1. Markdown headings: '# Heading'
    # 2. Numbered headings: '1. Introduction', '1.1 Background', 'Section 2:'
    # 3. All caps short lines: 'EXECUTIVE SUMMARY'
    MARKDOWN_HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.+)$")
    NUMBERED_HEADING_REGEX = re.compile(
        r"^(?:(?:Section|Chapter|Part)\s+\d+[:.]?|\d+(?:\.\d+)*\.?)\s+([A-Z][\w\s,–—\-:]{2,100})$"
    )
    ALL_CAPS_HEADING_REGEX = re.compile(r"^[A-Z0-9\s\-–—:]{4,60}$")
    LIST_ITEM_REGEX = re.compile(r"^(?:[-*•–—]|\d+[.)])\s+(.+)$")

    @classmethod
    def detect_heading(cls, text: str) -> Optional[tuple[int, str]]:
        """
        Returns (heading_level, title_text) if the line matches a heading pattern, else None.
        """
        text_clean = text.strip()
        if not text_clean or len(text_clean) > 150:
            return None

        # Check Markdown
        md_match = cls.MARKDOWN_HEADING_REGEX.match(text_clean)
        if md_match:
            level = len(md_match.group(1))
            return level, md_match.group(2).strip()

        # Check Numbered Heading
        num_match = cls.NUMBERED_HEADING_REGEX.match(text_clean)
        if num_match:
            # Count segment parts (e.g., '1' -> 1, '1.2' -> 2, '1.2.3' -> 3)
            prefix = text_clean.split()[0].rstrip(".:")
            parts = [p for p in prefix.split(".") if p.isdigit()]
            level = min(4, max(1, len(parts))) if parts else 1
            return level, text_clean

        # Check Short ALL-CAPS (e.g. "EXECUTIVE SUMMARY", "ABSTRACT")
        if cls.ALL_CAPS_HEADING_REGEX.match(text_clean) and not text_clean.endswith("."):
            words = text_clean.split()
            if 1 <= len(words) <= 7:
                return 1, text_clean

        return None

    @classmethod
    def enrich_document_structure(cls, doc: ParsedDocument) -> ParsedDocument:
        """
        Processes all elements of a document to detect headings, sections, and lists,
        assigning hierarchical section context to subsequent paragraphs.
        """
        enriched_elements: List[DocumentElement] = []
        current_section_title: Optional[str] = None
        current_heading_level: Optional[int] = None

        for elem in doc.elements:
            # If element is already typed as heading from DOCX parser, keep and track section
            if elem.element_type == ElementType.HEADING:
                current_section_title = elem.text
                current_heading_level = elem.heading_level or 1
                elem.section_title = current_section_title
                enriched_elements.append(elem)
                continue

            # Check if text is a heading
            heading_info = cls.detect_heading(elem.text)
            if heading_info:
                level, title = heading_info
                current_section_title = elem.text
                current_heading_level = level

                elem.element_type = ElementType.HEADING
                elem.heading_level = level
                elem.section_title = current_section_title
                enriched_elements.append(elem)
                continue

            # Check if text is a list item
            list_match = cls.LIST_ITEM_REGEX.match(elem.text)
            if list_match:
                elem.element_type = ElementType.LIST_ITEM
                elem.section_title = current_section_title
                enriched_elements.append(elem)
                continue

            # Standard paragraph with inherited section context
            elem.element_type = ElementType.PARAGRAPH
            elem.section_title = current_section_title
            enriched_elements.append(elem)

        return ParsedDocument(
            elements=enriched_elements,
            raw_text=doc.raw_text,
            page_count=doc.page_count,
            metadata=doc.metadata,
        )


structure_detector = StructureDetector()
