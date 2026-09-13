import pytest
from app.models.document import ChunkingStrategy
from app.services.document.models import ParsedDocument, DocumentElement, ElementType
from app.services.document.chunking.fixed import FixedSizeChunker
from app.services.document.chunking.structure_aware import StructureAwareChunker
from app.services.document.chunking import get_chunker


def create_mock_parsed_document() -> ParsedDocument:
    elements = [
        DocumentElement(
            element_type=ElementType.HEADING,
            text="1. Background",
            section_title="1. Background",
            page_number=1,
            heading_level=1,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            text="Generative AI systems require factual consistency and grounding. This paragraph explores the key mechanisms.",
            section_title="1. Background",
            page_number=1,
        ),
        DocumentElement(
            element_type=ElementType.HEADING,
            text="2. Implementation",
            section_title="2. Implementation",
            page_number=2,
            heading_level=1,
        ),
        DocumentElement(
            element_type=ElementType.PARAGRAPH,
            text="The pipeline is structured with modular services. Each service handles a specific stage cleanly.",
            section_title="2. Implementation",
            page_number=2,
        ),
    ]
    raw_text = "\n\n".join(e.text for e in elements)
    return ParsedDocument(elements=elements, raw_text=raw_text, page_count=2)


def test_fixed_size_chunker():
    doc = create_mock_parsed_document()
    chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk(doc)

    assert len(chunks) > 1
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert c.chunking_strategy == ChunkingStrategy.FIXED_SIZE
        assert c.character_count <= 100
        assert c.token_count > 0
        assert "start_char" in c.metadata


def test_structure_aware_chunker():
    doc = create_mock_parsed_document()
    chunker = StructureAwareChunker(target_chunk_size=300, max_chunk_size=500)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 2
    # Check that section boundary was respected
    first_chunk = chunks[0]
    assert first_chunk.section_title == "1. Background"
    assert "1. Background" in first_chunk.content

    second_chunk = chunks[1]
    assert second_chunk.section_title == "2. Implementation"
    assert "2. Implementation" in second_chunk.content

    for c in chunks:
        assert c.chunking_strategy == ChunkingStrategy.STRUCTURE_AWARE
        assert c.page_number in (1, 2)


def test_chunker_factory():
    fixed = get_chunker(ChunkingStrategy.FIXED_SIZE)
    assert isinstance(fixed, FixedSizeChunker)

    struct = get_chunker(ChunkingStrategy.STRUCTURE_AWARE)
    assert isinstance(struct, StructureAwareChunker)
