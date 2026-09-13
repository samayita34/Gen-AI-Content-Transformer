import os
from typing import Optional
from app.core.config import settings
from app.services.verification.base import BaseVerificationJudge
from app.services.verification.providers.mock import MockVerificationJudge, UnavailableVerificationJudge
from app.services.verification.providers.llm import LLMVerificationJudge


def get_verification_judge(provider_override: Optional[str] = None) -> BaseVerificationJudge:
    """
    Factory resolving active Verification Judge based on configuration.
    Defaults to 'mock' for deterministic offline/CI execution.
    """
    # Force mock during testing
    if os.getenv("TRANSFORMAI_TESTING") == "1":
        return MockVerificationJudge()

    provider = (provider_override or settings.VERIFICATION_PROVIDER).lower().strip()

    if provider in ("llm", "gemini", "openai"):
        return LLMVerificationJudge()
    elif provider == "mock":
        return MockVerificationJudge()
    elif provider == "unavailable":
        return UnavailableVerificationJudge()
    else:
        # Unknown provider defaults to mock with fallback
        return MockVerificationJudge()
