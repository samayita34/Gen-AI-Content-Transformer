import uuid
import logging
from typing import List
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
    BackgroundTasks,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db, AsyncSessionLocal
from app.models.document import Document, DocumentChunk, ChunkingStrategy, ProcessingStatus
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentDetailResponse,
    DocumentChunkResponse,
    DocumentChunkListResponse,
    DocumentListResponse,
)
from app.services.document.pipeline import document_pipeline

logger = logging.getLogger("transformai.api.documents")
router = APIRouter()


async def _run_document_pipeline_bg(document_id: uuid.UUID):
    """Background task worker for non-blocking document intelligence processing."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Starting background processing for document %s...", document_id)
            await document_pipeline.process_document(document_id, session)
        except Exception as e:
            logger.error("Error in background pipeline processing for %s: %s", document_id, e)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and Ingest Source Document",
    description="Uploads a PDF, DOCX, or TXT document, validates format, stores raw bytes, and queues for asynchronous intelligence pipeline.",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Source document file (PDF, DOCX, TXT)"),
    chunking_strategy: ChunkingStrategy = Form(
        default=ChunkingStrategy.STRUCTURE_AWARE,
        description="Chunking algorithm: 'structure_aware' or 'fixed_size'",
    ),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    file_bytes = await file.read()
    file_size = len(file_bytes)

    valid, err_msg = document_pipeline.validate_file(
        filename=file.filename or "",
        file_size=file_size,
        content_type=file.content_type,
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )

    try:
        doc = await document_pipeline.ingest_document(
            file_bytes=file_bytes,
            original_filename=file.filename or "unknown",
            file_size=file_size,
            db=db,
            chunking_strategy=chunking_strategy,
        )

        # Enqueue background processing task
        background_tasks.add_task(_run_document_pipeline_bg, doc.id)

        return DocumentUploadResponse(
            document_id=doc.id,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            processing_status=doc.processing_status,
            chunking_strategy=doc.chunking_strategy,
            message="Document accepted and queued for intelligence processing.",
        )
    except Exception as exc:
        logger.error("Upload failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(exc)}",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List Ingested Documents",
    description="Retrieves a list of all ingested documents with metadata and processing status.",
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    # Query documents with count of chunks
    query = (
        select(Document, func.count(DocumentChunk.id).label("chunk_count"))
        .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
    )
    results = await db.execute(query)
    docs_with_counts = results.all()

    doc_responses = []
    for doc, chunk_count in docs_with_counts:
        item = DocumentDetailResponse(
            id=doc.id,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            processing_status=doc.processing_status,
            page_count=doc.page_count,
            character_count=doc.character_count,
            word_count=doc.word_count,
            chunking_strategy=doc.chunking_strategy,
            total_chunks=chunk_count or 0,
            error_message=doc.error_message,
            doc_metadata=doc.doc_metadata,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        doc_responses.append(item)

    return DocumentListResponse(total=len(doc_responses), documents=doc_responses)


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get Document Status and Metadata",
    description="Returns processing status, page count, word count, and extracted metadata for a specific document.",
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    query = (
        select(Document, func.count(DocumentChunk.id).label("chunk_count"))
        .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
        .where(Document.id == document_id)
        .group_by(Document.id)
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found.",
        )

    doc, chunk_count = row
    return DocumentDetailResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes,
        processing_status=doc.processing_status,
        page_count=doc.page_count,
        character_count=doc.character_count,
        word_count=doc.word_count,
        chunking_strategy=doc.chunking_strategy,
        total_chunks=chunk_count or 0,
        error_message=doc.error_message,
        doc_metadata=doc.doc_metadata,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get(
    "/{document_id}/chunks",
    response_model=DocumentChunkListResponse,
    summary="Get Document Chunks with Provenance",
    description="Returns the processed chunks, character/token counts, section titles, and page provenance metadata for a document.",
)
async def get_document_chunks(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentChunkListResponse:
    # Check document exists
    doc_res = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_res.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found.",
        )

    query = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    res = await db.execute(query)
    chunks = res.scalars().all()

    chunk_responses = [
        DocumentChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            content=c.content,
            page_number=c.page_number,
            section_title=c.section_title,
            character_count=c.character_count,
            token_count=c.token_count,
            chunking_strategy=c.chunking_strategy,
            chunk_metadata=c.chunk_metadata,
            created_at=c.created_at,
        )
        for c in chunks
    ]

    return DocumentChunkListResponse(
        document_id=document_id,
        total_chunks=len(chunk_responses),
        chunks=chunk_responses,
    )
