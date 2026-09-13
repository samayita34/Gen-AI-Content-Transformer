from abc import ABC, abstractmethod
from typing import List, Tuple
from app.services.verification.models import AtomicClaim, EvidenceMatch, VerificationVerdict


class VerificationUnavailableError(RuntimeError):
    """
    Raised when the verification engine is not configured, unavailable,
    or fails to perform claim verification.
    """
    pass


class BaseVerificationJudge(ABC):
    """
    Abstract interface for claim-evidence verification judges.
    Classifies the relationship between an atomic claim and independently retrieved source evidence.
    """

    @property
    @abstractmethod
    def judge_name(self) -> str:
        """Identifier of the verification judge."""
        pass

    @abstractmethod
    async def evaluate_claim(
        self,
        claim: AtomicClaim,
        evidence_matches: List[EvidenceMatch],
    ) -> Tuple[VerificationVerdict, float, str]:
        """
        Evaluates support relationship of the claim against retrieved evidence.
        Returns (verdict, confidence, explanation).
        Raises VerificationUnavailableError if judge is unable to evaluate.
        """
        pass
