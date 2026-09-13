import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RetrievalSearchRequest(BaseModel):
    """
    Request model for semantic RAG vector retrieval.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language query string for semantic vector search.",
        examples=["What are the performance metrics of the content transformation pipeline?"],
    )
    document_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional document UUID filter to scope search to a single document.",
    )
    top_k: int = Field(
        5,
        ge=1,
        le=50,
        description="Maximum number of top semantically similar chunks to return.",
    )
    similarity_threshold: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score threshold (0.0 to 1.0). Higher values require greater semantic similarity.",
    )

    model_config = ConfigDict(from_attributes=True)


class RetrievalChunkItem(BaseModel):
    """
    Provenance-rich retrieved chunk schema.
    """
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    similarity_score: float = Field(
        ...,
        description="Cosine similarity score between 0.0 and 1.0 (higher = greater semantic match).",
    )
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_index: int
    chunking_strategy: str
    source_filename: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class RetrievalSearchResponse(BaseModel):
    """
    Response schema for vector search endpoint.
    """
    query: str
    results: List[RetrievalChunkItem]
    total_retrieved: int

    model_config = ConfigDict(from_attributes=True)


class SourceReferenceSchema(BaseModel):
    document_id: uuid.UUID
    source_filename: str
    chunk_id: uuid.UUID
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NormalizedFactSchema(BaseModel):
    fact_text: str
    source_reference: SourceReferenceSchema

    model_config = ConfigDict(from_attributes=True)


class NormalizedEntitySchema(BaseModel):
    entity_name: str
    entity_type: str
    source_references: List[SourceReferenceSchema]

    model_config = ConfigDict(from_attributes=True)


class NormalizedClaimSchema(BaseModel):
    statement: str
    source_reference: SourceReferenceSchema

    model_config = ConfigDict(from_attributes=True)


class SourceDocumentSummarySchema(BaseModel):
    document_id: str
    source_filename: str
    retrieved_chunk_count: int
    pages: List[int]
    sections: List[str]

    model_config = ConfigDict(from_attributes=True)


class NormalizedContextResponse(BaseModel):
    """
    Standardized, deterministic normalized context representation for downstream generation.
    """
    query: str
    source_documents: List[SourceDocumentSummarySchema]
    retrieved_chunks: List[RetrievalChunkItem]
    facts: List[NormalizedFactSchema]
    key_points: List[str]
    entities: List[NormalizedEntitySchema]
    claims: List[NormalizedClaimSchema]
    source_references: List[SourceReferenceSchema]

    model_config = ConfigDict(from_attributes=True)
