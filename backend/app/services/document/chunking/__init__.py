from app.models.document import ChunkingStrategy
from app.services.document.chunking.base import BaseChunker, ChunkData
from app.services.document.chunking.fixed import FixedSizeChunker
from app.services.document.chunking.structure_aware import StructureAwareChunker


def get_chunker(
    strategy: ChunkingStrategy = ChunkingStrategy.STRUCTURE_AWARE,
    chunk_size: int = 600,
    chunk_overlap: int = 60,
) -> BaseChunker:
    """Factory function for instantiating selected chunking algorithm."""
    if strategy == ChunkingStrategy.FIXED_SIZE:
        return FixedSizeChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return StructureAwareChunker(target_chunk_size=chunk_size)


__all__ = [
    "BaseChunker",
    "ChunkData",
    "FixedSizeChunker",
    "StructureAwareChunker",
    "get_chunker",
]
