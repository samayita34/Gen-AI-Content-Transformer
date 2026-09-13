import json
import re
import logging
from typing import List, Tuple, Optional

from app.core.config import settings
from app.services.generation.base import BaseLLMProvider, GenerationRequest
from app.services.generation.providers.factory import get_llm_provider
from app.services.verification.base import BaseClaimVerifier, VerificationUnavailableError
from app.services.verification.models import (
    AtomicClaim,
    EvidenceMatch,
    ClaimVerificationResult,
    VerificationVerdict,
)

logger = logging.getLogger("transformai.verification.llm")


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class LLMClaimVerifier(BaseClaimVerifier):
    """
    LLM-based claim–evidence verifier.
    Performs entailment-style classification into:
    - SUPPORTED
    - CONTRADICTED
    - PARTIALLY_SUPPORTED
    - INSUFFICIENT_EVIDENCE
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self._llm_provider = llm_provider

    @property
    def verifier_name(self) -> str:
        return f"llm_verifier_{settings.VERIFICATION_MODEL}"

    @property
    def llm_provider(self) -> BaseLLMProvider:
        return self._llm_provider or get_llm_provider()

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
                explanation="No relevant source evidence was retrieved for this claim from the source document.",
                evidence=[],
                confidence=None,
            )

        evidence_text = "\n\n".join(
            f"[Evidence Passage {idx + 1} | Section: {e.section_title or 'General'} | Page: {e.page_number or 'N/A'}]\n{e.chunk_content}"
            for idx, e in enumerate(evidence_matches)
        )

        system_instruction = """You are a rigorous Claim-Level Source-Grounded Verification Judge.
Your job is to independently evaluate whether an extracted generated claim is supported by the provided source evidence.

VERDICT DEFINITIONS:
1. SUPPORTED: The provided source evidence completely entails and corroborates the entire claim.
2. CONTRADICTED: The provided source evidence directly conflicts with or refutes the claim.
3. PARTIALLY_SUPPORTED: The claim contains multiple assertions and only some are supported by the evidence, or the evidence supports only a subset of the claim.
4. INSUFFICIENT_EVIDENCE: The provided source evidence does not contain enough information to prove or disprove the claim. Lack of evidence is NEVER a contradiction.

DO NOT USE VAGUE VERDICTS such as 'probably true', 'seems correct', or 'likely factual'.
Use ONLY the four exact verdict strings above.

RULES:
- Do NOT use outside world knowledge; rely ONLY on the provided <SOURCE_EVIDENCE>.
- Provide a clear, factual explanation explaining why the verdict was chosen.
- If confidence can be assessed, provide a float between 0.0 and 1.0; otherwise provide null."""

        prompt = f"""EVALUATE THE FOLLOWING CLAIM AGAINST THE RETRIEVED SOURCE EVIDENCE:

<CLAIM>
{claim_stmt}
</CLAIM>

<SOURCE_EVIDENCE>
{evidence_text}
</SOURCE_EVIDENCE>

Respond ONLY with valid JSON following this schema:
{{
  "verdict": "SUPPORTED" | "CONTRADICTED" | "PARTIALLY_SUPPORTED" | "INSUFFICIENT_EVIDENCE",
  "confidence": 0.95,
  "explanation": "Detailed rationale referencing the source evidence passage."
}}"""

        req = GenerationRequest(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=settings.VERIFICATION_TEMPERATURE,
            response_format_json=True,
            timeout_seconds=settings.VERIFICATION_TIMEOUT_SECONDS,
        )

        try:
            resp = await self.llm_provider.generate(req)
            clean_content = _clean_json(resp.content if hasattr(resp, "content") else getattr(resp, "text", str(resp)))
            data = json.loads(clean_content)

            verdict_str = str(data.get("verdict", "")).strip().lower()
            if verdict_str == "supported":
                verdict = VerificationVerdict.SUPPORTED
            elif verdict_str == "contradicted":
                verdict = VerificationVerdict.CONTRADICTED
            elif verdict_str == "partially_supported":
                verdict = VerificationVerdict.PARTIALLY_SUPPORTED
            else:
                verdict = VerificationVerdict.INSUFFICIENT_EVIDENCE

            # Preserve provider confidence if returned, else None
            conf_val = data.get("confidence")
            confidence = None
            if conf_val is not None:
                try:
                    confidence = float(conf_val)
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    confidence = None

            explanation = str(data.get("explanation", "Verification completed."))

            return ClaimVerificationResult(
                claim=claim,
                claim_id=claim.claim_id,
                verdict=verdict,
                explanation=explanation,
                evidence=evidence_matches,
                confidence=confidence,
            )

        except Exception as exc:
            logger.error("LLM verification evaluation failed: %s", exc)
            raise VerificationUnavailableError(f"LLM verification evaluation failed: {str(exc)}") from exc


# Backward compatibility alias
LLMVerificationJudge = LLMClaimVerifier
