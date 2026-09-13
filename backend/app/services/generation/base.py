from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    prompt: str
    system_instruction: Optional[str] = None
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    content: str
    model_name: str
    finish_reason: Optional[str] = None
    usage: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for Generative Language Model Providers.
    Ensures decoupled, provider-independent generation across OpenAI, Anthropic, Gemini, Ollama, etc.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name/Identifier of the provider."""
        pass

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Executes generation request against the underlying provider."""
        pass
