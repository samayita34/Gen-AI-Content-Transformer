import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.document import Document
from app.schemas.retrieval import (
    RetrievalSearchRequest,
    RetrievalChunkItem,
    RetrievalSearchResponse,
    NormalizedContextResponse,
    SourceDocumentSummarySchema,
    NormalizedFactSchema,
    NormalizedEntitySchema,
    NormalizedClaimSchema,
    SourceReferenceSchema,
)
from app.services.retrieval.pgvector_retriever import PgVectorRetriever
from app.services.retrieval.normalizer import default_context_normalizer

logger = logging.getLogger("transformai.api.retrieval")

router = APIRouter()


@router.post(
    "/search",
    response_model=RetrievalSearchResponse,
    summary="Semantic Vector Retrieval",
    description=(
        "Executes dense semantic vector search over document chunks via pgvector. "
        "Returns provenance-tracked chunks ordered by cosine similarity descending (0.0 to 1.0)."
    ),
)
async def search_retrieval(
    request: RetrievalSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> RetrievalSearchResponse:
    # 1. If document_id is supplied, verify it exists
    if request.document_id is not None:
        doc_stmt = select(Document).where(Document.id == request.document_id)
        doc_result = await db.execute(doc_stmt)
        if not doc_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {request.document_id} does not exist.",
            )

    # 2. Execute retrieval via PgVectorRetriever
    retriever = PgVectorRetriever(session=db)
    chunks = await retriever.search(
        query=request.query,
        document_id=request.document_id,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )

    results = [
        RetrievalChunkItem(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            content=c.content,
            similarity_score=c.similarity_score,
            page_number=c.page_number,
            section_title=c.section_title,
            chunk_index=c.chunk_index,
            chunking_strategy=c.chunking_strategy,
            source_filename=c.source_filename,
            metadata=c.metadata,
        )
        for c in chunks
    ]

    return RetrievalSearchResponse(
        query=request.query,
        results=results,
        total_retrieved=len(results),
    )


@router.post(
    "/context",
    response_model=NormalizedContextResponse,
    summary="Normalized Context Retrieval",
    description=(
        "Retrieves relevant source chunks and performs deterministic, 100% source-grounded context normalization "
        "without generative hallucination or rewriting."
    ),
)
async def get_normalized_context(
    request: RetrievalSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> NormalizedContextResponse:
    if request.document_id is not None:
        doc_stmt = select(Document).where(Document.id == request.document_id)
        doc_result = await db.execute(doc_stmt)
        if not doc_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {request.document_id} does not exist.",
            )

    retriever = PgVectorRetriever(session=db)
    chunks = await retriever.search(
        query=request.query,
        document_id=request.document_id,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )

    norm_context = default_context_normalizer.build_normalized_context(
        query=request.query,
        retrieved_chunks=chunks,
    )

    return NormalizedContextResponse(
        query=norm_context.query,
        source_documents=[
            SourceDocumentSummarySchema(
                document_id=doc["document_id"],
                source_filename=doc["source_filename"],
                retrieved_chunk_count=doc["retrieved_chunk_count"],
                pages=doc["pages"],
                sections=doc["sections"],
            )
            for doc in norm_context.source_documents
        ],
        retrieved_chunks=[
            RetrievalChunkItem(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                content=c.content,
                similarity_score=c.similarity_score,
                page_number=c.page_number,
                section_title=c.section_title,
                chunk_index=c.chunk_index,
                chunking_strategy=c.chunking_strategy,
                source_filename=c.source_filename,
                metadata=c.metadata,
            )
            for c in norm_context.retrieved_chunks
        ],
        facts=[
            NormalizedFactSchema(
                fact_text=f.fact_text,
                source_reference=SourceReferenceSchema(
                    document_id=f.source_reference.document_id,
                    source_filename=f.source_reference.source_filename,
                    chunk_id=f.source_reference.chunk_id,
                    chunk_index=f.source_reference.chunk_index,
                    page_number=f.source_reference.page_number,
                    section_title=f.source_reference.section_title,
                ),
            )
            for f in norm_context.facts
        ],
        key_points=norm_context.key_points,
        entities=[
            NormalizedEntitySchema(
                entity_name=e.entity_name,
                entity_type=e.entity_type,
                source_references=[
                    SourceReferenceSchema(
                        document_id=r.document_id,
                        source_filename=r.source_filename,
                        chunk_id=r.chunk_id,
                        chunk_index=r.chunk_index,
                        page_number=r.page_number,
                        section_title=r.section_title,
                    )
                    for r in e.source_references
                ],
            )
            for e in norm_context.entities
        ],
        claims=[
            NormalizedClaimSchema(
                statement=cl.statement,
                source_reference=SourceReferenceSchema(
                    document_id=cl.source_reference.document_id,
                    source_filename=cl.source_reference.source_filename,
                    chunk_id=cl.source_reference.chunk_id,
                    chunk_index=cl.source_reference.chunk_index,
                    page_number=cl.source_reference.page_number,
                    section_title=cl.source_reference.section_title,
                ),
            )
            for cl in norm_context.claims
        ],
        source_references=[
            SourceReferenceSchema(
                document_id=r.document_id,
                source_filename=r.source_filename,
                chunk_id=r.chunk_id,
                chunk_index=r.chunk_index,
                page_number=r.page_number,
                section_title=r.section_title,
            )
            for r in norm_context.source_references
        ],
    )
