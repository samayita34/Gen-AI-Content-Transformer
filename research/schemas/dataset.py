"""
M7 Research Schemas: Dataset and Ground-Truth Models
====================================================
Formal Pydantic models for ground-truth facts, documents, and dataset manifests.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FactType(str, Enum):
    FACTUAL = "FACTUAL"
    STATISTICAL = "STATISTICAL"
    ATTRIBUTIONAL = "ATTRIBUTIONAL"
    TEMPORAL = "TEMPORAL"
    NUMERICAL = "NUMERICAL"
    ENTITY_RELATION = "ENTITY_RELATION"
    IMPLICATION = "IMPLICATION"


class ImportanceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AnnotationStatus(str, Enum):
    UNANNOTATED = "UNANNOTATED"
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    FINAL = "FINAL"


class VerificationVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class SourceReferenceSpan(BaseModel):
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    paragraph_idx: Optional[int] = None
    sentence_idx: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    verbatim_text_span: Optional[str] = None


class GroundTruthFact(BaseModel):
    fact_id: str = Field(..., description="Unique fact identifier (e.g., FACT-DEV01-001 or FACT-REAL01-001)")
    statement: str = Field(..., description="Verbatim/atomic factual proposition from source")
    normalized_statement: str = Field(..., description="Normalized canonical form for matching")
    fact_type: FactType = Field(..., description="Categorical fact taxonomy type")
    source_reference: SourceReferenceSpan = Field(default_factory=SourceReferenceSpan)
    importance: ImportanceLevel = Field(default=ImportanceLevel.HIGH)
    annotation_status: AnnotationStatus = Field(default=AnnotationStatus.UNANNOTATED)
    key_entities: List[str] = Field(default_factory=list)
    numerical_values: List[str] = Field(default_factory=list)
    temporal_markers: List[str] = Field(default_factory=list)
    distractor_notes: Optional[str] = None


class GroundTruthDocument(BaseModel):
    document_id: str
    title: str
    source_hash_sha256: str
    source_modality: str = "TXT"
    word_count: int
    section_count: int
    annotation_status: AnnotationStatus = AnnotationStatus.UNANNOTATED
    facts: List[GroundTruthFact] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GroundTruthDocumentSummary(BaseModel):
    document_id: str
    title: str
    file_path: str
    source_hash_sha256: str
    source_modality: str
    length_category: str  # SHORT, MEDIUM, LONG
    word_count: int
    section_count: int
    total_facts: int
    annotation_status: str = "UNANNOTATED"


class DatasetManifest(BaseModel):
    dataset_version: str
    dataset_name: str
    is_development_fixture: bool = False
    fixture_disclaimer: Optional[str] = None
    created_at: str
    annotation_version: str
    annotation_status: str
    total_documents: int
    documents: List[GroundTruthDocumentSummary] = Field(default_factory=list)

