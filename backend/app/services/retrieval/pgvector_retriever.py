import math
import uuid
import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.services.embeddings.base import BaseEmbeddingProvider
from app.services.embeddings.hf_local import default_embedding_provider
from app.services.retrieval.base import BaseRetriever
from app.services.retrieval.models import RetrievedChunk

logger = logging.getLogger("transformai.retrieval.pgvector")


def _compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two unit/dense vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    sim = dot_product / (norm_a * norm_b)
    return max(0.0, min(1.0, float(sim)))


class PgVectorRetriever(BaseRetriever):
    """
    Production-grade semantic retriever backed by PostgreSQL and the pgvector extension.
    Converts queries into dense embeddings and executes database-side vector similarity search.
    """

    def __init__(
        self,
        session: AsyncSession,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.session = session
        self.embedding_provider = embedding_provider or default_embedding_provider

    async def search(
        self,
        query: str,
        document_id: Optional[uuid.UUID] = None,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """
        Performs semantic vector search against indexed document chunks.
        Cosine similarity: similarity = 1 - cosine_distance. Higher score represents greater similarity.
        """
        if not query or not query.strip():
            return []

        # Bound top_k
        top_k = max(1, min(top_k, settings.MAX_RETRIEVAL_TOP_K))
        threshold = similarity_threshold if similarity_threshold is not None else settings.DEFAULT_SIMILARITY_THRESHOLD
        threshold = max(0.0, min(1.0, threshold))

        # 1. Generate query embedding
        query_embedding = await self.embedding_provider.embed_text(query.strip())
        if not query_embedding:
            logger.warning("Failed to generate embedding for query: '%s'", query)
            return []

        # Check database dialect (native pgvector vs test environment)
        bind = self.session.bind
        dialect_name = bind.dialect.name if bind else ""

        if dialect_name == "postgresql":
            # Database-side vector distance search via pgvector
            distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
            similarity_expr = (1.0 - distance_expr).label("similarity_score")

            stmt = (
                select(
                    DocumentChunk,
                    Document.original_filename,
                    similarity_expr,
                )
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.embedding.is_not(None))
            )

            if document_id is not None:
                stmt = stmt.where(DocumentChunk.document_id == document_id)

            if threshold > 0.0:
                stmt = stmt.where(similarity_expr >= threshold)

            stmt = stmt.order_by(distance_expr.asc()).limit(top_k)

            result = await self.session.execute(stmt)
            rows = result.all()

            results: List[RetrievedChunk] = []
            for chunk, original_filename, raw_sim in rows:
                sim_score = max(0.0, min(1.0, float(raw_sim) if raw_sim is not None else 0.0))
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        content=chunk.content,
                        similarity_score=round(sim_score, 4),
                        chunk_index=chunk.chunk_index,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        chunking_strategy=chunk.chunking_strategy.value if hasattr(chunk.chunking_strategy, "value") else str(chunk.chunking_strategy),
                        source_filename=original_filename or "",
                        metadata=chunk.chunk_metadata or {},
                    )
                )
            return results

        else:
            # Dialect fallback for SQLite / test environments
            stmt = (
                select(DocumentChunk, Document.original_filename)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.embedding.is_not(None))
            )
            if document_id is not None:
                stmt = stmt.where(DocumentChunk.document_id == document_id)

            result = await self.session.execute(stmt)
            rows = result.all()

            scored_chunks = []
            for chunk, original_filename in rows:
                emb = chunk.embedding
                if isinstance(emb, list) and len(emb) > 0:
                    sim = _compute_cosine_similarity(query_embedding, emb)
                    if sim >= threshold:
                        scored_chunks.append((sim, chunk, original_filename))

            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_scored = scored_chunks[:top_k]

            results = []
            for sim, chunk, original_filename in top_scored:
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        content=chunk.content,
                        similarity_score=round(sim, 4),
                        chunk_index=chunk.chunk_index,
                        page_number=chunk.page_number,
                        section_title=chunk.section_title,
                        chunking_strategy=chunk.chunking_strategy.value if hasattr(chunk.chunking_strategy, "value") else str(chunk.chunking_strategy),
                        source_filename=original_filename or "",
                        metadata=chunk.chunk_metadata or {},
                    )
                )
            return results
