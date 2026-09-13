from typing import List, Optional
from app.models.document import ChunkingStrategy
from app.services.document.models import ParsedDocument
from app.services.document.chunking.base import BaseChunker, ChunkData


class FixedSizeChunker(BaseChunker):
    """
    Baseline Method 1: Fixed-size character/token chunking with sliding window overlap.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @property
    def strategy_name(self) -> ChunkingStrategy:
        return ChunkingStrategy.FIXED_SIZE

    def chunk(self, doc: ParsedDocument) -> List[ChunkData]:
        full_text = doc.raw_text or "\n\n".join(e.text for e in doc.elements)
        if not full_text.strip():
            return []

        chunks: List[ChunkData] = []
        step = self.chunk_size - self.chunk_overlap
        start_idx = 0
        chunk_idx = 0

        # Build page map if elements have pages
        # Element character offsets
        offset_map = []
        running_char = 0
        for elem in doc.elements:
            offset_map.append({
                "start": running_char,
                "end": running_char + len(elem.text),
                "page": elem.page_number,
                "section": elem.section_title,
            })
            running_char += len(elem.text) + 2  # +2 for "\n\n"

        def _find_page_and_section(pos: int):
            for entry in offset_map:
                if entry["start"] <= pos <= entry["end"]:
                    return entry["page"], entry["section"]
            # Fallback to closest
            if offset_map:
                return offset_map[-1]["page"], offset_map[-1]["section"]
            return None, None

        while start_idx < len(full_text):
            end_idx = min(start_idx + self.chunk_size, len(full_text))
            chunk_content = full_text[start_idx:end_idx].strip()

            if chunk_content:
                page_num, section = _find_page_and_section(start_idx)
                word_count = len(chunk_content.split())
                char_count = len(chunk_content)

                chunks.append(
                    ChunkData(
                        chunk_index=chunk_idx,
                        content=chunk_content,
                        page_number=page_num,
                        section_title=section,
                        character_count=char_count,
                        token_count=word_count,
                        chunking_strategy=self.strategy_name,
                        metadata={
                            "start_char": start_idx,
                            "end_char": end_idx,
                            "chunk_size_setting": self.chunk_size,
                            "overlap_setting": self.chunk_overlap,
                        },
                    )
                )
                chunk_idx += 1

            if end_idx == len(full_text):
                break
            start_idx += step

        return chunks
