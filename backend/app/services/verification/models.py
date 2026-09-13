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
    """
    claim_id: uuid.UUID
    statement: str
    claim_type: ClaimType = ClaimType.FACTUAL
    context_source_field: str = ""  # e.g., "overview", "key_points[0]", "slides[1].bullets[0]"
    normalized_statement: str = ""   # Clean search-optimized claim statement


@dataclass
class EvidenceMatch:
    """
    Represents an independently retrieved source chunk evaluated as evidence for a claim.
    Preserves first-class source provenance without fabricating missing metadata.
    """
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_content: str
    similarity_score: float  # Cosine similarity [0.0, 1.0] from independent vector search
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    modality: Optional[str] = "text"
    timestamp_start_sec: Optional[float] = None
    timestamp_end_sec: Optional[float] = None
    formatted_timestamp: Optional[str] = None
    spatial_bounds: Optional[Dict[str, float]] = None
    relevance_snippet: str = ""


@dataclass
class ClaimVerificationResult:
    """
    Verification evaluation result for an individual atomic claim.
    """
    claim: AtomicClaim
    verdict: VerificationVerdict
    confidence: float  # Operational confidence score [0.0, 1.0]
    explanation: str
    evidence: List[EvidenceMatch] = field(default_factory=list)


@dataclass
class VerificationReport:
    """
    Comprehensive verification report aggregating independent claim-level verdicts.
    Exposes raw operational counts only; does NOT compute or claim percentage benchmark scores.
    """
    document_id: uuid.UUID
    output_type: str
    total_claims: int
    supported_claims: int
    contradicted_claims: int
    partially_supported_claims: int
    insufficient_evidence_claims: int
    claim_results: List[ClaimVerificationResult] = field(default_factory=list)
    summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
