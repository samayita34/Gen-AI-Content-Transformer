import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from app.services.retrieval.models import RetrievedChunk


class BaseRetriever(ABC):
    """
    Abstract Base Class for semantic & hybrid document retrievers.
    Decouples retrieval consumers from underlying storage engines (pgvector, FAISS, OpenSearch, etc.).
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        document_id: Optional[uuid.UUID] = None,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """
        Executes semantic vector retrieval against the indexed document chunk corpus.

        Args:
            query: Natural language search query.
            document_id: Optional UUID filter for scoped search within a single document.
            top_k: Maximum number of top relevant chunks to return.
            similarity_threshold: Minimum cosine similarity score [0.0, 1.0].
                                 Chunks with lower similarity are excluded.

        Returns:
            List of RetrievedChunk domain objects ordered by similarity score descending.
        """
        pass
