import asyncio
import hashlib
import logging
import math
import os
from typing import List, Optional
from app.core.config import settings
from app.services.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger("transformai.embeddings")


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Local dense embedding provider using SentenceTransformers.
    Features deterministic local fallback to prevent hangs during network timeouts or offline test runs.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None
        self._dim = settings.EMBEDDING_DIMENSION
        self._load_attempted = False
        # If in test mode, immediately use deterministic offline generator
        self._use_fallback = os.getenv("TRANSFORMAI_TESTING", "0") == "1"

    def _load_model(self):
        """Lazy loads SentenceTransformer model in memory."""
        if not self._load_attempted:
            self._load_attempted = True
            if self._use_fallback:
                return

            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading local embedding model '%s'...", self.model_name)
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)

                if hasattr(self._model, "get_embedding_dimension"):
                    self._dim = self._model.get_embedding_dimension() or settings.EMBEDDING_DIMENSION
                elif hasattr(self._model, "get_sentence_embedding_dimension"):
                    self._dim = self._model.get_sentence_embedding_dimension() or settings.EMBEDDING_DIMENSION
                else:
                    self._dim = settings.EMBEDDING_DIMENSION
                logger.info("SentenceTransformer model loaded successfully (dimension: %d).", self._dim)
            except Exception as e:
                logger.warning(
                    "SentenceTransformer '%s' not cached locally (%s). Using deterministic %d-dim semantic projection.",
                    self.model_name,
                    e,
                    self._dim,
                )
                self._use_fallback = True

    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """
        Generates a normalized dense vector of dimension `self._dim` based on deterministic
        multi-hash projections (unit L2-norm).
        """
        dim = self._dim
        vec = [0.0] * dim
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            h1 = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            h2 = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            for i in range(4):
                idx = (h1 + i * 31) % dim
                weight = ((h2 >> (i * 8)) & 0xFF) / 255.0 - 0.5
                vec[idx] += weight

        # Normalize to unit length (L2 norm)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_text(self, text: str) -> List[float]:
        """Embeds a single string."""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a batch of texts asynchronously.
        """
        if not texts:
            return []

        def _encode_sync() -> List[List[float]]:
            self._load_model()
            if self._model is not None and not self._use_fallback:
                try:
                    embeddings = self._model.encode(
                        texts,
                        batch_size=32,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                    )
                    return embeddings.tolist()
                except Exception as exc:
                    logger.warning("Model encode error, falling back: %s", exc)

            return [self._generate_deterministic_embedding(t) for t in texts]

        return await asyncio.to_thread(_encode_sync)


# Global default embedding provider instance
default_embedding_provider = SentenceTransformerEmbeddingProvider()
