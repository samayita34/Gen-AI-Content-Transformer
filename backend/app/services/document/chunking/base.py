from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models.document import ChunkingStrategy
from app.services.document.models import ParsedDocument


class ChunkData(BaseModel):
    """
    Normalized chunk representation retaining full provenance to source document.
    """
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    character_count: int
    token_count: int
    chunking_strategy: ChunkingStrategy
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseChunker(ABC):
    """
    Abstract interface for deterministic chunking strategies.
    """

    @property
    @abstractmethod
    def strategy_name(self) -> ChunkingStrategy:
        """Returns the chunking strategy enum."""
        pass

    @abstractmethod
    def chunk(self, doc: ParsedDocument) -> List[ChunkData]:
        """Transforms a parsed document into a list of provenance-tracked chunks."""
        pass
