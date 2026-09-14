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


class ClaimOrigin(str, Enum):
    SOURCE_FACT = "SOURCE_FACT"
    CONTROLLED_PERTURBATION = "CONTROLLED_PERTURBATION"


class VerificationBenchmarkItem(BaseModel):
    benchmark_id: str = Field(..., description="Unique benchmark item ID (e.g., BENCH-REAL-001)")
    document_id: str = Field(..., description="Referenced document ID (e.g., DOC-REAL-001)")
    claim: str = Field(..., description="Atomic claim to verify against source evidence")
    expected_verdict: VerificationVerdict = Field(..., description="Gold human verification verdict")
    evidence_references: List[SourceReferenceSpan] = Field(
        default_factory=list,
        description="Source text spans establishing or contradicting the claim"
    )
    annotation_status: AnnotationStatus = Field(
        default=AnnotationStatus.UNANNOTATED,
        description="Lifecycle state (UNANNOTATED, CANDIDATE, REVIEWED, FINAL)"
    )
    claim_origin: ClaimOrigin = Field(
        default=ClaimOrigin.SOURCE_FACT,
        description="Origin of claim: SOURCE_FACT or CONTROLLED_PERTURBATION"
    )
    notes: Optional[str] = Field(default=None, description="Annotator justification notes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provenance metadata")


class VerificationBenchmarkManifest(BaseModel):
    benchmark_version: str = "1.0.0"
    benchmark_name: str = "TransformAI Track 2 Verification Benchmark"
    is_development_fixture: bool = False
    fixture_disclaimer: Optional[str] = None
    created_at: str
    annotation_status: str
    total_items: int
    verdict_distribution: Dict[str, int] = Field(default_factory=dict)
    claim_origin_distribution: Dict[str, int] = Field(default_factory=dict)
    items: List[VerificationBenchmarkItem] = Field(default_factory=list)


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


