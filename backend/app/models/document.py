import enum
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Text,
    Enum as SQLEnum,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.models.base import BaseDBModel


class ProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChunkingStrategy(str, enum.Enum):
    FIXED_SIZE = "fixed_size"
    STRUCTURE_AWARE = "structure_aware"


class Document(BaseDBModel):
    """
    Represents an uploaded source document (PDF, DOCX, TXT) and its ingestion state.
    """
    __tablename__ = "documents"

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus, name="processing_status_enum", native_enum=False),
        default=ProcessingStatus.UPLOADED,
        nullable=False,
        index=True,
    )

    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    character_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    chunking_strategy: Mapped[ChunkingStrategy] = mapped_column(
        SQLEnum(ChunkingStrategy, name="chunking_strategy_enum", native_enum=False),
        default=ChunkingStrategy.STRUCTURE_AWARE,
        nullable=False,
    )

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doc_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )


class DocumentChunk(BaseDBModel):
    """
    Represents a discrete semantic or fixed chunk extracted from a source document,
    annotated with provenance metadata and dense vector embedding.
    """
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    chunking_strategy: Mapped[ChunkingStrategy] = mapped_column(
        SQLEnum(ChunkingStrategy, name="chunking_strategy_chunk_enum", native_enum=False),
        nullable=False,
    )

    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Dense vector embedding (configured via settings.EMBEDDING_DIMENSION)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)

    # Relationship
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
