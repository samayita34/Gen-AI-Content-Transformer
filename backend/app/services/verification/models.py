import enum
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class VerificationVerdict(str, enum.Enum):
    """
    Four-verdict taxonomy for claim-level verification:
    - SUPPORTED: The retrieved source evidence sufficiently entails the complete claim.
    - CONTRADICTED: The retrieved source evidence clearly conflicts with the claim.
    - PARTIALLY_SUPPORTED: Compound claim containing multiple propositions where only some are supported.
    - INSUFFICIENT_EVIDENCE: Source material does not contain enough evidence to establish or contradict.
    """
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    PARTIALLY_SUPPORTED = "partially_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ClaimType(str, enum.Enum):
    """Classification of extracted factual propositions."""
    FACTUAL = "factual"
    STATISTICAL = "statistical"
    ATTRIBUTIONAL = "attributional"
    IMPLICATION = "implication"


@dataclass
class AtomicClaim:
    """
    Represents a discrete, testable factual proposition deconstructed from generated output.
    Contains minimum required fields:
    - claim_id
    - text (aliased to statement)
    - normalized_text (aliased to normalized_statement)
    - output_format
    - source_output_reference (aliased to context_source_field)
    - claim_type
    - extraction_confidence (only when actually supplied by provider, never invented)
    """
    claim_id: uuid.UUID
    text: str = ""
    normalized_text: str = ""
    output_format: str = ""
    source_output_reference: Optional[str] = None
    claim_type: ClaimType = ClaimType.FACTUAL
    extraction_confidence: Optional[float] = None
    # Backwards-compatibility fields
    statement: str = ""
    context_source_field: str = ""
    normalized_statement: str = ""

    def __post_init__(self):
        # Synchronize statement and text
        if not self.text and self.statement:
            self.text = self.statement
        elif not self.statement and self.text:
            self.statement = self.text

        # Synchronize normalized_text and normalized_statement
        if not self.normalized_text and self.normalized_statement:
            self.normalized_text = self.normalized_statement
        elif not self.normalized_statement and self.normalized_text:
            self.normalized_statement = self.normalized_text
        elif not self.normalized_text and not self.normalized_statement:
            self.normalized_text = self.text
            self.normalized_statement = self.statement

        # Synchronize source_output_reference and context_source_field
        if not self.source_output_reference and self.context_source_field:
            self.source_output_reference = self.context_source_field
        elif not self.context_source_field and self.source_output_reference:
            self.context_source_field = self.source_output_reference


@dataclass
class EvidenceMatch:
    """
    Represents an independently retrieved source chunk evaluated as evidence for a claim.
    Preserves first-class source provenance without fabricating missing metadata.
    """
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_content: str = ""
    similarity_score: float = 0.0  # Cosine similarity [0.0, 1.0] from independent vector search
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    modality: Optional[str] = "text"
    timestamp_start_sec: Optional[float] = None
    timestamp_end_sec: Optional[float] = None
    formatted_timestamp: Optional[str] = None
    spatial_bounds: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_snippet: str = ""
    # Standardized aliases
    text: str = ""
    similarity: float = 0.0
    source_reference: Optional[str] = None

    def __post_init__(self):
        # Synchronize chunk_content and text
        if not self.text and self.chunk_content:
            self.text = self.chunk_content
        elif not self.chunk_content and self.text:
            self.chunk_content = self.text

        # Synchronize similarity and similarity_score
        if self.similarity == 0.0 and self.similarity_score != 0.0:
            self.similarity = self.similarity_score
        elif self.similarity_score == 0.0 and self.similarity != 0.0:
            self.similarity_score = self.similarity

        # Build human-readable source_reference if not supplied
        if not self.source_reference:
            ref_parts = []
            if self.section_title:
                ref_parts.append(f"Section: {self.section_title}")
            if self.page_number is not None:
                ref_parts.append(f"Page {self.page_number}")
            if self.formatted_timestamp:
                ref_parts.append(f"Time {self.formatted_timestamp}")
            elif self.timestamp_start_sec is not None:
                ref_parts.append(f"t={self.timestamp_start_sec:.1f}s")
            self.source_reference = " | ".join(ref_parts) if ref_parts else (f"Chunk {str(self.chunk_id)[:8]}")


@dataclass
class ClaimVerificationResult:
    """
    Verification evaluation result for an individual atomic claim.
    Returns structured data: claim_id, text, normalized_text, verdict, explanation, confidence, evidence.
    """
    claim: AtomicClaim
    verdict: VerificationVerdict
    explanation: str
    evidence: List[EvidenceMatch] = field(default_factory=list)
    confidence: Optional[float] = None  # Preserved from provider output; None if not supplied
    claim_id: Optional[uuid.UUID] = None
    text: str = ""
    normalized_text: str = ""

    def __post_init__(self):
        if self.claim_id is None and self.claim is not None:
            self.claim_id = self.claim.claim_id
        if not self.text and self.claim is not None:
            self.text = self.claim.text or self.claim.statement
        if not self.normalized_text and self.claim is not None:
            self.normalized_text = self.claim.normalized_text or self.claim.normalized_statement


@dataclass
class VerificationReport:
    """
    Comprehensive verification report aggregating independent claim-level verdicts.
    Exposes raw operational counts only; does NOT compute or claim percentage benchmark scores.
    """
    document_id: uuid.UUID
    output_type: str = ""
    total_claims: int = 0
    supported_claims: int = 0
    contradicted_claims: int = 0
    partially_supported_claims: int = 0
    insufficient_evidence_claims: int = 0
    claim_results: List[ClaimVerificationResult] = field(default_factory=list)
    summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    report_id: uuid.UUID = field(default_factory=uuid.uuid4)
    generated_output_id: Optional[uuid.UUID] = None
    format: str = ""
    claims: List[ClaimVerificationResult] = field(default_factory=list)

    def __post_init__(self):
        # Synchronize output_type and format
        if not self.format and self.output_type:
            self.format = self.output_type
        elif not self.output_type and self.format:
            self.output_type = self.format

        # Synchronize claim_results and claims
        if not self.claims and self.claim_results:
            self.claims = self.claim_results
        elif not self.claim_results and self.claims:
            self.claim_results = self.claims
