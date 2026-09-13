import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.document import ProcessingStatus, ChunkingStrategy


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    original_filename: str
    file_type: str
    file_size_bytes: int
    processing_status: ProcessingStatus
    chunking_strategy: ChunkingStrategy
    message: str = "Document uploaded successfully and queued for processing."

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    character_count: int
    token_count: int
    chunking_strategy: ChunkingStrategy
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkListResponse(BaseModel):
    document_id: uuid.UUID
    total_chunks: int
    chunks: List[DocumentChunkResponse]


class DocumentDetailResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_type: str
    file_size_bytes: int
    processing_status: ProcessingStatus
    page_count: Optional[int] = None
    character_count: Optional[int] = None
    word_count: Optional[int] = None
    chunking_strategy: ChunkingStrategy
    total_chunks: int = 0
    error_message: Optional[str] = None
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentDetailResponse]
