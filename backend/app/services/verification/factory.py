import os
from typing import Optional
from app.core.config import settings
from app.services.verification.base import BaseClaimVerifier, BaseVerificationJudge
from app.services.verification.providers.mock import (
    MockClaimVerifier,
    UnavailableClaimVerifier,
    MockVerificationJudge,
    UnavailableVerificationJudge,
)
from app.services.verification.providers.llm import LLMClaimVerifier, LLMVerificationJudge


def get_claim_verifier(provider_override: Optional[str] = None) -> BaseClaimVerifier:
    """
    Factory resolving active Claim Verifier based on configuration.
    Defaults to 'mock' for deterministic offline/CI execution.
    """
    # Force mock during testing
    if os.getenv("TRANSFORMAI_TESTING") == "1":
        return MockClaimVerifier()

    provider = (provider_override or settings.VERIFICATION_PROVIDER).lower().strip()

    if provider in ("llm", "gemini", "openai"):
        return LLMClaimVerifier()
    elif provider == "mock":
        return MockClaimVerifier()
    elif provider == "unavailable":
        return UnavailableClaimVerifier()
    else:
        # Unknown provider defaults to mock with fallback
        return MockClaimVerifier()


# Backward compatibility alias
get_verification_judge = get_claim_verifier
