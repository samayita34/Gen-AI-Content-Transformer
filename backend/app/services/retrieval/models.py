import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RetrievedChunk:
    """
    Internal domain model representing a single chunk retrieved via vector search,
    annotated with complete provenance metadata and cosine similarity score.
    """
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    similarity_score: float  # Cosine similarity: [0.0, 1.0], higher indicates greater semantic similarity
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunking_strategy: str = "structure_aware"
    source_filename: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceReference:
    """
    Exact source citation linking an extracted unit to its origin document, chunk, page, section,
    or temporal/multimodal timestamp.
    """
    document_id: uuid.UUID
    source_filename: str
    chunk_id: uuid.UUID
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    modality: Optional[str] = "text"
    formatted_timestamp: Optional[str] = None


@dataclass
class NormalizedFact:
    """
    Factual unit extracted strictly from source chunk sentences without generative rewriting.
    """
    fact_text: str
    source_reference: SourceReference


@dataclass
class NormalizedEntity:
    """
    Named entity or key term deterministically extracted from source passages.
    """
    entity_name: str
    entity_type: str
    source_references: List[SourceReference] = field(default_factory=list)


@dataclass
class NormalizedClaim:
    """
    Direct assertion/claim extracted strictly from source passages with source grounding.
    """
    statement: str
    source_reference: SourceReference


@dataclass
class NormalizedContext:
    """
    Standardized, deterministic context representation for downstream generation agents,
    ensuring 100% source-groundedness and strict provenance traceability.
    """
    query: str
    source_documents: List[Dict[str, Any]] = field(default_factory=list)
    retrieved_chunks: List[RetrievedChunk] = field(default_factory=list)
    facts: List[NormalizedFact] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    entities: List[NormalizedEntity] = field(default_factory=list)
    claims: List[NormalizedClaim] = field(default_factory=list)
    source_references: List[SourceReference] = field(default_factory=list)
