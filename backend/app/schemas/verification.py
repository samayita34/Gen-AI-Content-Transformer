import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.services.verification.models import VerificationVerdict, ClaimType


class VerificationRequestSchema(BaseModel):
    """
    Request model for on-demand claim-level verification of generated content.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="ID of the source document against which to verify claims.",
    )
    output_type: str = Field(
        ...,
        description="Format of the generated content ('executive_summary', 'advisory', 'presentation', 'video_script').",
    )
    transformation_content: Dict[str, Any] = Field(
        ...,
        description="JSON payload of the generated transformation output.",
    )
    top_k: Optional[int] = Field(
        3,
        ge=1,
        le=20,
        description="Number of evidence chunks to retrieve independently per atomic claim.",
    )
    similarity_threshold: Optional[float] = Field(
        0.2,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold for evidence retrieval.",
    )

    model_config = ConfigDict(from_attributes=True)


class AtomicClaimSchema(BaseModel):
    claim_id: uuid.UUID
    statement: str
    claim_type: ClaimType
    context_source_field: str
    normalized_statement: str

    model_config = ConfigDict(from_attributes=True)


class EvidenceMatchSchema(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_content: str
    similarity_score: float
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    modality: Optional[str] = "text"
    timestamp_start_sec: Optional[float] = None
    timestamp_end_sec: Optional[float] = None
    formatted_timestamp: Optional[str] = None
    spatial_bounds: Optional[Dict[str, float]] = None
    relevance_snippet: str

    model_config = ConfigDict(from_attributes=True)


class ClaimVerificationResultSchema(BaseModel):
    claim: AtomicClaimSchema
    verdict: VerificationVerdict
    confidence: float
    explanation: str
    evidence: List[EvidenceMatchSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class VerificationReportResponseSchema(BaseModel):
    """
    Verification report response exposing raw claim counts and detailed evidence matches.
    """
    document_id: uuid.UUID
    output_type: str
    total_claims: int
    supported_claims: int
    contradicted_claims: int
    partially_supported_claims: int
    insufficient_evidence_claims: int
    claim_results: List[ClaimVerificationResultSchema] = Field(default_factory=list)
    summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
