import uuid
import time
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.services.generation.base import BaseLLMProvider
from app.services.generation.models import GenerationConfig, TransformationResult
from app.services.generation.providers.factory import get_llm_provider
from app.services.generation.router import default_generation_router, GenerationRouter
from app.services.retrieval.pgvector_retriever import PgVectorRetriever
from app.services.retrieval.normalizer import default_context_normalizer, ContextNormalizer

logger = logging.getLogger("transformai.generation.service")


class GenerationService:
    """
    Core orchestrator for Multi-Format Source-Grounded Content Transformation.
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        router: Optional[GenerationRouter] = None,
        normalizer: Optional[ContextNormalizer] = None,
    ):
        self.provider = provider
        self.router = router or default_generation_router
        self.normalizer = normalizer or default_context_normalizer

    async def transform_document(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        config: GenerationConfig,
        query: Optional[str] = None,
        custom_intent: Optional[str] = None,
    ) -> TransformationResult:
        """
        Executes end-to-end multi-format transformation for a given source document.
        """
        # 1. Verify document existence
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_res = await db.execute(doc_stmt)
        document = doc_res.scalar_one_or_none()
        if not document:
            raise ValueError(f"Document with ID {document_id} does not exist.")

        # 2. Retrieve relevant chunks via PgVectorRetriever
        retrieval_query = (query or "").strip()
        if not retrieval_query:
            # If no query specified, use general document synthesis prompt
            retrieval_query = f"Key findings, operational context, and core topics in {document.original_filename}"

        retriever = PgVectorRetriever(session=db)
        retrieved_chunks = await retriever.search(
            query=retrieval_query,
            document_id=document_id,
            top_k=config.top_k,
            similarity_threshold=config.similarity_threshold,
        )

        if not retrieved_chunks:
            # Fallback to general retrieval without strict similarity threshold
            retrieved_chunks = await retriever.search(
                query=retrieval_query,
                document_id=document_id,
                top_k=config.top_k,
                similarity_threshold=0.0,
            )

        if not retrieved_chunks:
            raise ValueError(f"No indexed chunks found for document {document_id} ({document.original_filename}).")

        # 3. Build deterministic NormalizedContext
        normalized_context = self.normalizer.build_normalized_context(
            query=retrieval_query,
            retrieved_chunks=retrieved_chunks,
        )

        # 4. Resolve generator & provider
        generator = self.router.get_generator(config.output_type)
        llm_provider = self.provider or get_llm_provider()

        # 5. Execute generation
        t0 = time.perf_counter()
        parsed_content, gen_response = await generator.generate_format(
            context=normalized_context,
            config=config,
            provider=llm_provider,
            custom_intent=custom_intent,
        )
        total_latency_ms = (time.perf_counter() - t0) * 1000

        # 6. Assemble rich TransformationResult metadata for research evaluation
        transformation_id = uuid.uuid4()
        config_dict = {
            "output_type": config.output_type.value,
            "audience": config.audience.value,
            "tone": config.tone.value,
            "detail_level": config.detail_level.value,
            "communication_objective": config.communication_objective.value,
            "language": config.language,
            "length_constraint": config.length_constraint,
            "temperature": config.temperature,
            "top_k": config.top_k,
            "similarity_threshold": config.similarity_threshold,
            "query": retrieval_query,
            "custom_intent": custom_intent,
        }

        result_obj = TransformationResult(
            transformation_id=transformation_id,
            document_id=document_id,
            output_type=config.output_type,
            configuration=config_dict,
            content=parsed_content,
            source_references=normalized_context.source_references,
            retrieved_chunk_ids=[str(c.chunk_id) for c in retrieved_chunks],
            retrieval_similarity_scores=[c.similarity_score for c in retrieved_chunks],
            retrieval_ranks=list(range(1, len(retrieved_chunks) + 1)),
            number_of_retrieved_chunks=len(retrieved_chunks),
            provider=gen_response.provider_name,
            model=gen_response.model_name,
            generation_latency_ms=round(total_latency_ms, 2),
            token_usage=gen_response.usage,
        )

        from app.services.generation.store import default_result_store
        default_result_store.save_result(result_obj)

        return result_obj


default_generation_service = GenerationService()
