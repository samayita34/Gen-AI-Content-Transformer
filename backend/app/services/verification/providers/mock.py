import re
from typing import List, Optional, Tuple

from app.services.verification.base import BaseClaimVerifier, VerificationUnavailableError
from app.services.verification.models import (
    AtomicClaim,
    EvidenceMatch,
    ClaimVerificationResult,
    VerificationVerdict,
)


class MockClaimVerifier(BaseClaimVerifier):
    """
    Deterministic rule-based verification provider for testing and offline/CI environments.
    Analyzes lexical overlap, negation markers, and semantic similarity scores.
    """

    @property
    def verifier_name(self) -> str:
        return "mock_claim_verifier"

    @staticmethod
    def _extract_keywords(text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "into", "over", "were", "been", "have", "has", "are", "was"}
        return {w for w in words if w not in stopwords}

    async def verify_claim(
        self,
        claim: AtomicClaim,
        evidence_matches: List[EvidenceMatch],
    ) -> ClaimVerificationResult:
        claim_stmt = claim.text or claim.statement

        if not evidence_matches:
            return ClaimVerificationResult(
                claim=claim,
                claim_id=claim.claim_id,
                verdict=VerificationVerdict.INSUFFICIENT_EVIDENCE,
                explanation="No source chunks met the minimum retrieval similarity threshold for this claim.",
                evidence=[],
                confidence=None,  # No confidence invented
            )

        best_match = evidence_matches[0]
        claim_keywords = self._extract_keywords(claim_stmt)
        if not claim_keywords:
            return ClaimVerificationResult(
                claim=claim,
                claim_id=claim.claim_id,
                verdict=VerificationVerdict.INSUFFICIENT_EVIDENCE,
                explanation="Claim does not contain sufficient factual anchors for verification.",
                evidence=evidence_matches,
                confidence=None,
            )

        combined_evidence = " ".join(e.chunk_content for e in evidence_matches).lower()
        evidence_keywords = self._extract_keywords(combined_evidence)

        # Keyword intersection
        overlap = claim_keywords.intersection(evidence_keywords)
        overlap_ratio = len(overlap) / len(claim_keywords)

        # Explicit contradiction detection (negation discrepancy)
        claim_has_negation = bool(re.search(r"\b(not|never|none|neither|cannot|no)\b", claim_stmt.lower()))
        evidence_has_negation = bool(re.search(r"\b(not|never|none|neither|cannot|no)\b", best_match.chunk_content.lower()))

        # Check for deliberate contradiction fixture markers
        if "contradiction" in claim_stmt.lower() or "conflicts" in claim_stmt.lower() or (claim_has_negation != evidence_has_negation and overlap_ratio > 0.6):
            return ClaimVerificationResult(
                claim=claim,
                claim_id=claim.claim_id,
                verdict=VerificationVerdict.CONTRADICTED,
                explanation=f"Evidence contradicts the claim statement (Polarity or semantic mismatch detected in source section '{best_match.section_title or 'main'}').",
                evidence=evidence_matches,
                confidence=0.90,
            )

        if overlap_ratio >= 0.65 and best_match.similarity_score >= 0.40:
            return ClaimVerificationResult(
                claim=claim,
                claim_id=claim.claim_id,
                verdict=VerificationVerdict.SUPPORTED,
                explanation=f"Claim is fully entailed by retrieved evidence in '{best_match.section_title or 'source chunk'}' (overlap: {int(overlap_ratio*100)}%).",
                evidence=evidence_matches,
                confidence=round(min(0.98, max(0.70, best_match.similarity_score)), 2),
            )
        elif overlap_ratio >= 0.35 or best_match.similarity_score >= 0.30:
            return ClaimVerificationResult(
                claim=claim,
                claim_id=claim.claim_id,
                verdict=VerificationVerdict.PARTIALLY_SUPPORTED,
                explanation=f"Portions of the claim are supported by source evidence, but some propositions lack full corroboration (overlap: {int(overlap_ratio*100)}%).",
                evidence=evidence_matches,
                confidence=0.75,
            )
        else:
            return ClaimVerificationResult(
                claim=claim,
                claim_id=claim.claim_id,
                verdict=VerificationVerdict.INSUFFICIENT_EVIDENCE,
                explanation="Source material does not contain enough matching facts or context to corroborate this claim.",
                evidence=evidence_matches,
                confidence=None,
            )


class UnavailableClaimVerifier(BaseClaimVerifier):
    """
    Simulates an unconfigured or failing verification engine.
    Always raises VerificationUnavailableError.
    """

    @property
    def verifier_name(self) -> str:
        return "unavailable_claim_verifier"

    async def verify_claim(
        self,
        claim: AtomicClaim,
        evidence_matches: List[EvidenceMatch],
    ) -> ClaimVerificationResult:
        raise VerificationUnavailableError("Verification engine is offline, unconfigured, or unreachable.")


# Backward compatibility aliases
MockVerificationJudge = MockClaimVerifier
UnavailableVerificationJudge = UnavailableClaimVerifier
