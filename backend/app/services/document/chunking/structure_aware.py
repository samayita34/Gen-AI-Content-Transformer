import re
from typing import List, Optional
from app.models.document import ChunkingStrategy
from app.services.document.models import ParsedDocument, DocumentElement, ElementType
from app.services.document.chunking.base import BaseChunker, ChunkData


class StructureAwareChunker(BaseChunker):
    """
    Proposed Method 2: Structure-Aware / Semantic Boundary Chunking.
    Preserves section titles, headings, and paragraph boundaries without cutting through sentences.
    """

    def __init__(self, target_chunk_size: int = 700, max_chunk_size: int = 1000):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size

    @property
    def strategy_name(self) -> ChunkingStrategy:
        return ChunkingStrategy.STRUCTURE_AWARE

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Splits long text block into sentences cleanly."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, doc: ParsedDocument) -> List[ChunkData]:
        if not doc.elements:
            # Fallback if no parsed elements
            if doc.raw_text.strip():
                return [
                    ChunkData(
                        chunk_index=0,
                        content=doc.raw_text.strip(),
                        page_number=1,
                        section_title=None,
                        character_count=len(doc.raw_text.strip()),
                        token_count=len(doc.raw_text.strip().split()),
                        chunking_strategy=self.strategy_name,
                        metadata={"fallback": True},
                    )
                ]
            return []

        chunks: List[ChunkData] = []
        chunk_idx = 0

        current_block_texts: List[str] = []
        current_char_count = 0
        current_section: Optional[str] = None
        current_page: Optional[int] = None
        current_element_types: List[str] = []

        def _flush_current_chunk():
            nonlocal chunk_idx, current_block_texts, current_char_count, current_section, current_page, current_element_types
            if not current_block_texts:
                return

            joined_content = "\n\n".join(current_block_texts).strip()
            if joined_content:
                chunks.append(
                    ChunkData(
                        chunk_index=chunk_idx,
                        content=joined_content,
                        page_number=current_page,
                        section_title=current_section,
                        character_count=len(joined_content),
                        token_count=len(joined_content.split()),
                        chunking_strategy=self.strategy_name,
                        metadata={
                            "element_types": list(current_element_types),
                            "target_size": self.target_chunk_size,
                            "semantic_boundary": True,
                        },
                    )
                )
                chunk_idx += 1

            current_block_texts = []
            current_char_count = 0
            current_element_types = []

        for elem in doc.elements:
            elem_text = elem.text.strip()
            if not elem_text:
                continue

            elem_len = len(elem_text)

            # If section changed, flush current block to preserve section boundary
            if elem.section_title and elem.section_title != current_section and current_block_texts:
                _flush_current_chunk()
                current_section = elem.section_title

            if current_page is None or elem.page_number is not None:
                current_page = elem.page_number or current_page

            if elem.section_title:
                current_section = elem.section_title

            # If element is a Heading, include it as section header context
            if elem.element_type == ElementType.HEADING:
                if current_char_count > 0 and (current_char_count + elem_len > self.target_chunk_size):
                    _flush_current_chunk()
                current_block_texts.append(f"## {elem_text}")
                current_char_count += elem_len + 4
                current_element_types.append("heading")
                continue

            # If single paragraph exceeds max size, split by sentences
            if elem_len > self.max_chunk_size:
                if current_block_texts:
                    _flush_current_chunk()

                sentences = self._split_into_sentences(elem_text)
                sub_block: List[str] = []
                sub_char_count = 0

                for sent in sentences:
                    sent_len = len(sent)
                    if sub_char_count + sent_len > self.target_chunk_size and sub_block:
                        current_block_texts = sub_block
                        current_char_count = sub_char_count
                        current_element_types = ["paragraph_fragment"]
                        _flush_current_chunk()
                        sub_block = []
                        sub_char_count = 0

                    sub_block.append(sent)
                    sub_char_count += sent_len + 1

                if sub_block:
                    current_block_texts = sub_block
                    current_char_count = sub_char_count
                    current_element_types = ["paragraph_fragment"]
                    _flush_current_chunk()
                continue

            # Normal element packing
            if current_char_count + elem_len > self.max_chunk_size and current_block_texts:
                _flush_current_chunk()

            current_block_texts.append(elem_text)
            current_char_count += elem_len + 2
            current_element_types.append(elem.element_type.value)

            if current_char_count >= self.target_chunk_size:
                _flush_current_chunk()

        # Flush any remaining buffer
        _flush_current_chunk()

        return chunks
