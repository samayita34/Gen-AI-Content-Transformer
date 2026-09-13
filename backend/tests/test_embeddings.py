import pytest
from app.core.config import settings
from app.services.embeddings.hf_local import SentenceTransformerEmbeddingProvider


@pytest.mark.asyncio
async def test_embedding_provider_interface():
    provider = SentenceTransformerEmbeddingProvider()
    assert provider.dimension == settings.EMBEDDING_DIMENSION

    # Test single embed
    sample_text = "Dense vector indexing for content transformation."
    emb = await provider.embed_text(sample_text)
    assert isinstance(emb, list)
    assert len(emb) == provider.dimension
    assert all(isinstance(x, float) for x in emb)

    # Test batch embed
    texts = [
        "First document chunk for indexing.",
        "Second document chunk regarding evaluation.",
    ]
    batch_emb = await provider.embed_batch(texts)
    assert len(batch_emb) == 2
    assert len(batch_emb[0]) == provider.dimension
    assert len(batch_emb[1]) == provider.dimension


@pytest.mark.asyncio
async def test_embedding_empty_batch():
    provider = SentenceTransformerEmbeddingProvider()
    result = await provider.embed_batch([])
    assert result == []
