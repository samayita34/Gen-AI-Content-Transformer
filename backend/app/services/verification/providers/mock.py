import re
from typing import List, Tuple
from app.services.verification.base import BaseVerificationJudge, VerificationUnavailableError
from app.services.verification.models import AtomicClaim, EvidenceMatch, VerificationVerdict


class MockVerificationJudge(BaseVerificationJudge):
    """
    Deterministic rule-based verification judge for testing and offline/CI environments.
    Analyzes lexical overlap, negation markers, and semantic similarity scores.
    """

    @property
    def judge_name(self) -> str:
        return "mock_judge"

    @staticmethod
    def _extract_keywords(text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "into", "over", "were", "been", "have", "has", "are", "was"}
        return {w for w in words if w not in stopwords}

    async def evaluate_claim(
        self,
        claim: AtomicClaim,
        evidence_matches: List[EvidenceMatch],
    ) -> Tuple[VerificationVerdict, float, str]:
        if not evidence_matches:
            return (
                VerificationVerdict.INSUFFICIENT_EVIDENCE,
                0.85,
                "No source chunks met the minimum retrieval similarity threshold for this claim.",
            )

        best_match = evidence_matches[0]
        claim_keywords = self._extract_keywords(claim.statement)
        if not claim_keywords:
            return (
                VerificationVerdict.INSUFFICIENT_EVIDENCE,
                0.80,
                "Claim does not contain sufficient factual anchors for verification.",
            )

        combined_evidence = " ".join(e.chunk_content for e in evidence_matches).lower()
        evidence_keywords = self._extract_keywords(combined_evidence)

        # Keyword intersection
        overlap = claim_keywords.intersection(evidence_keywords)
        overlap_ratio = len(overlap) / len(claim_keywords)

        # Explicit contradiction detection (negation discrepancy)
        claim_has_negation = bool(re.search(r"\b(not|never|none|neither|cannot|no)\b", claim.statement.lower()))
        evidence_has_negation = bool(re.search(r"\b(not|never|none|neither|cannot|no)\b", best_match.chunk_content.lower()))
        
        # Check for deliberate contradiction fixture markers
        if "contradiction" in claim.statement.lower() or "conflicts" in claim.statement.lower() or (claim_has_negation != evidence_has_negation and overlap_ratio > 0.6):
            return (
                VerificationVerdict.CONTRADICTED,
                0.90,
                f"Evidence contradicts the claim statement (Polarity or semantic mismatch detected in source section '{best_match.section_title or 'main'}').",
            )

        if overlap_ratio >= 0.65 and best_match.similarity_score >= 0.40:
            return (
                VerificationVerdict.SUPPORTED,
                round(min(0.98, max(0.70, best_match.similarity_score)), 2),
                f"Claim is fully entailed by retrieved evidence in '{best_match.section_title or 'source chunk'}' (overlap: {int(overlap_ratio*100)}%).",
            )
        elif overlap_ratio >= 0.35 or best_match.similarity_score >= 0.30:
            return (
                VerificationVerdict.PARTIALLY_SUPPORTED,
                0.75,
                f"Portions of the claim are supported by source evidence, but some propositions lack full corroboration (overlap: {int(overlap_ratio*100)}%).",
            )
        else:
            return (
                VerificationVerdict.INSUFFICIENT_EVIDENCE,
                0.80,
                "Source material does not contain enough matching facts or context to corroborate this claim.",
            )


class UnavailableVerificationJudge(BaseVerificationJudge):
    """
    Simulates an unconfigured or failing verification engine.
    Always raises VerificationUnavailableError.
    """

    @property
    def judge_name(self) -> str:
        return "unavailable_judge"

    async def evaluate_claim(
        self,
        claim: AtomicClaim,
        evidence_matches: List[EvidenceMatch],
    ) -> Tuple[VerificationVerdict, float, str]:
        raise VerificationUnavailableError("Verification engine is offline, unconfigured, or unreachable.")
