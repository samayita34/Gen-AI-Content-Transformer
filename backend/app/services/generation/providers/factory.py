import os
from typing import Optional
from app.core.config import settings
from app.services.generation.base import BaseLLMProvider
from app.services.generation.providers.gemini import GeminiProvider
from app.services.generation.providers.openai_compatible import OpenAICompatibleProvider
from app.services.generation.providers.mock import MockLLMProvider


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory resolving the active LLM provider instance based on settings or explicit override.
    """
    name = (provider_name or settings.LLM_PROVIDER).lower()

    # If in automated testing mode or mock requested, always return mock provider
    if os.getenv("TRANSFORMAI_TESTING", "0") == "1" or name == "mock":
        return MockLLMProvider()

    if name == "gemini":
        if not settings.GEMINI_API_KEY:
            # Fall back to mock if no API key is set
            return MockLLMProvider()
        return GeminiProvider()

    elif name in ["openai", "openai_compatible", "ollama", "groq", "vllm"]:
        if name in ["ollama", "vllm", "openai_compatible"]:
            # Local endpoints don't require an API key as long as base_url is configured or defaults
            return OpenAICompatibleProvider()
        if not settings.OPENAI_API_KEY and not settings.OPENAI_API_BASE:
            return MockLLMProvider()
        return OpenAICompatibleProvider()

    return MockLLMProvider()
