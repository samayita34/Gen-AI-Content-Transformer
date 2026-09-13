import time
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.document import Document, DocumentChunk, ProcessingStatus, ChunkingStrategy
from app.services.document.storage import BaseDocumentStorage, default_storage
from app.services.document.parsers import get_parser_for_filename
from app.services.document.cleaner import cleaner
from app.services.document.structure import structure_detector
from app.services.document.chunking import get_chunker
from app.services.embeddings.base import BaseEmbeddingProvider
from app.services.embeddings.hf_local import default_embedding_provider
from app.services.document.research_logger import research_logger

logger = logging.getLogger("transformai.pipeline")

# Modality Extensions
TEXT_EXTENSIONS = {".pdf", ".docx", ".txt", ".text", ".md"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


def get_max_size_for_extension(ext: str) -> int:
    """Returns the centralized configured maximum file size for a given extension."""
    if ext in IMAGE_EXTENSIONS:
        return settings.MAX_IMAGE_FILE_SIZE_BYTES
    elif ext in AUDIO_EXTENSIONS:
        return settings.MAX_AUDIO_FILE_SIZE_BYTES
    elif ext in VIDEO_EXTENSIONS:
        return settings.MAX_VIDEO_FILE_SIZE_BYTES
    return settings.MAX_TEXT_FILE_SIZE_BYTES


class DocumentPipelineService:
    """
    End-to-end Document Ingestion and Intelligence Pipeline Orchestrator.
    Handles Validation -> Storage -> Parsing -> Cleaning -> Structure Detection
    -> Chunking -> Batch Embedding -> PostgreSQL/pgvector Persistence -> Telemetry Logging.
    """

    def __init__(
        self,
        storage: BaseDocumentStorage = default_storage,
        embedding_provider: BaseEmbeddingProvider = default_embedding_provider,
    ):
        self.storage = storage
        self.embedding_provider = embedding_provider

    @staticmethod
    def validate_file(filename: str, file_size: int, content_type: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Validates file extension, emptiness, and modality-specific size limit."""
        if not filename or not filename.strip():
            return False, "Filename cannot be empty."

        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return (
                False,
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            )

        if file_size <= 0:
            return False, "Uploaded file is empty (0 bytes)."

        max_allowed_bytes = get_max_size_for_extension(ext)
        if file_size > max_allowed_bytes:
            max_mb = max_allowed_bytes // (1024 * 1024)
            return False, f"File size ({round(file_size / (1024 * 1024), 2)} MB) exceeds maximum allowed limit of {max_mb} MB for format '{ext}'."

        return True, None

    async def ingest_document(
        self,
        file_bytes: bytes,
        original_filename: str,
        file_size: int,
        db: AsyncSession,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.STRUCTURE_AWARE,
    ) -> Document:
        """
        Validates file, persists raw content to secure storage, and creates initial Document record.
        """
        valid, err_msg = self.validate_file(original_filename, file_size)
        if not valid:
            raise ValueError(err_msg)

        ext = Path(original_filename).suffix.lower()
        storage_key = await self.storage.save_file(file_bytes, original_filename)

        # Detect high-level modality
        modality_str = "text"
        if ext in IMAGE_EXTENSIONS:
            modality_str = "image"
        elif ext in AUDIO_EXTENSIONS:
            modality_str = "audio"
        elif ext in VIDEO_EXTENSIONS:
            modality_str = "video"

        doc = Document(
            original_filename=original_filename,
            storage_key=storage_key,
            file_type=ext.lstrip("."),
            file_size_bytes=file_size,
            processing_status=ProcessingStatus.UPLOADED,
            chunking_strategy=chunking_strategy,
            doc_metadata={
                "original_size": file_size,
                "extension": ext,
                "modality": modality_str,
            },
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    async def process_document(
        self,
        document_id: uuid.UUID,
        db: AsyncSession,
    ) -> Document:
        """
        Executes the full parsing, cleaning, structuring, chunking, embedding,
        and database storage pipeline for an ingested document.
        """
        start_time = time.perf_counter()
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        doc = result.scalar_one_or_none()

        if not doc:
            raise ValueError(f"Document with ID {document_id} not found.")

        # Update status to PROCESSING
        doc.processing_status = ProcessingStatus.PROCESSING
        doc.error_message = None
        await db.commit()

        try:
            # 1. Retrieve raw bytes
            file_bytes = await self.storage.get_file_bytes(doc.storage_key)

            # 2. Select appropriate parser
            parser = get_parser_for_filename(doc.original_filename)
            if not parser:
                raise ValueError(f"No registered parser for file '{doc.original_filename}'.")

            # 3. Document / Media Parsing
            logger.info("Parsing document %s (%s)...", doc.id, doc.original_filename)
            parsed_doc = await parser.parse(file_bytes, doc.original_filename)

            # 4. Deterministic Text Cleaning
            logger.info("Cleaning extracted text for document %s...", doc.id)
            cleaned_doc = cleaner.clean_parsed_document(parsed_doc)

            # 5. Deterministic Structure Detection
            logger.info("Detecting document structure for %s...", doc.id)
            structured_doc = structure_detector.enrich_document_structure(cleaned_doc)

            # Update document stats
            doc.page_count = structured_doc.page_count
            doc.character_count = structured_doc.total_character_count
            doc.word_count = structured_doc.total_word_count
            doc.doc_metadata.update(structured_doc.metadata)
            doc.doc_metadata["modality"] = structured_doc.modality.value
            if structured_doc.duration_seconds is not None:
                doc.doc_metadata["duration_seconds"] = structured_doc.duration_seconds
            if structured_doc.media_metadata:
                doc.doc_metadata["media_metadata"] = structured_doc.media_metadata

            # 6. Chunking
            chunker = get_chunker(doc.chunking_strategy)
            logger.info("Chunking document %s using %s...", doc.id, doc.chunking_strategy.value)
            raw_chunks = chunker.chunk(structured_doc)

            if not raw_chunks:
                logger.warning("No chunks generated for document %s.", doc.id)

            # 7. Dense Batch Embeddings Generation
            chunk_texts = [c.content for c in raw_chunks]
            embeddings: List[List[float]] = []
            if chunk_texts:
                logger.info("Generating %d batch embeddings for document %s...", len(chunk_texts), doc.id)
                embeddings = await self.embedding_provider.embed_batch(chunk_texts)

            # 8. Persist Chunks with Embeddings in PostgreSQL (pgvector)
            chunk_models: List[DocumentChunk] = []
            chunk_sizes: List[int] = []

            for idx, c in enumerate(raw_chunks):
                emb = embeddings[idx] if idx < len(embeddings) else None
                chunk_sizes.append(c.character_count)
                chunk_model = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    page_number=c.page_number,
                    section_title=c.section_title,
                    character_count=c.character_count,
                    token_count=c.token_count,
                    chunking_strategy=c.chunking_strategy,
                    chunk_metadata=c.metadata,
                    embedding=emb,
                )
                chunk_models.append(chunk_model)

            db.add_all(chunk_models)

            # 9. Mark Status as COMPLETED
            doc.processing_status = ProcessingStatus.COMPLETED
            await db.commit()
            await db.refresh(doc)

            duration = time.perf_counter() - start_time
            logger.info(
                "Document %s processed successfully in %.3fs (%d chunks).",
                doc.id,
                duration,
                len(chunk_models),
            )

            # 10. Research Telemetry Logging
            research_logger.log_document_pipeline_run(
                document_id=str(doc.id),
                filename=doc.original_filename,
                parser_used=parser.__class__.__name__,
                chunking_strategy=doc.chunking_strategy.value,
                total_chunks=len(chunk_models),
                chunk_sizes=chunk_sizes,
                processing_duration_sec=duration,
                embedding_model=getattr(self.embedding_provider, "model_name", "SentenceTransformer"),
                embedding_dimension=self.embedding_provider.dimension,
            )

            return doc

        except Exception as exc:
            duration = time.perf_counter() - start_time
            logger.error("Processing failed for document %s: %s", doc.id, exc, exc_info=True)
            doc.processing_status = ProcessingStatus.FAILED
            doc.error_message = str(exc)
            await db.commit()
            await db.refresh(doc)

            research_logger.log_document_pipeline_run(
                document_id=str(doc.id),
                filename=doc.original_filename,
                parser_used="Unknown",
                chunking_strategy=doc.chunking_strategy.value,
                total_chunks=0,
                chunk_sizes=[],
                processing_duration_sec=duration,
                embedding_model="None",
                embedding_dimension=0,
                error=str(exc),
            )
            return doc


document_pipeline = DocumentPipelineService()
