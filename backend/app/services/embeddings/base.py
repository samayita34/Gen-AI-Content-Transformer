from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """
    Abstract Base Class for Dense Embedding Models.
    Ensures provider-independent embedding generation across HuggingFace, OpenAI, etc.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns vector dimensionality produced by this model."""
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single text string."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text strings."""
        pass
