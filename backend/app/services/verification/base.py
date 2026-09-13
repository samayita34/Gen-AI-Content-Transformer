import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.services.verification.models import (
    AtomicClaim,
    EvidenceMatch,
    ClaimVerificationResult,
    VerificationVerdict,
)


class VerificationUnavailableError(RuntimeError):
    """
    Raised when the verification engine is not configured, unavailable,
    or fails to perform claim verification.
    """
    pass


class BaseClaimVerifier(ABC):
    """
    Abstract Base Class for provider-agnostic claim verifiers.
    Evaluates the entailment relationship between an extracted claim
    and independently retrieved source evidence passages.
    """

    @property
    @abstractmethod
    def verifier_name(self) -> str:
        """Identifier of the claim verifier."""
        pass

    @property
    def judge_name(self) -> str:
        """Backwards compatibility alias for verifier_name."""
        return self.verifier_name

    @abstractmethod
    async def verify_claim(
        self,
        claim: AtomicClaim,
        evidence_matches: List[EvidenceMatch],
    ) -> ClaimVerificationResult:
        """
        Verifies a single atomic claim against retrieved source evidence.
        Returns a structured ClaimVerificationResult containing:
        - claim_id
        - verdict (SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, INSUFFICIENT_EVIDENCE)
        - explanation
        - evidence
        - confidence (provider output if available, else None)
        """
        pass

    async def evaluate_claim(
        self,
        claim: AtomicClaim,
        evidence_matches: List[EvidenceMatch],
    ) -> Tuple[VerificationVerdict, Optional[float], str]:
        """
        Convenience backward-compatible evaluator returning (verdict, confidence, explanation).
        """
        result = await self.verify_claim(claim, evidence_matches)
        return result.verdict, result.confidence, result.explanation


# Backward compatibility alias
BaseVerificationJudge = BaseClaimVerifier
