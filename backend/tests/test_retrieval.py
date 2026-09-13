import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk, ProcessingStatus, ChunkingStrategy
from app.services.embeddings.hf_local import SentenceTransformerEmbeddingProvider
from app.services.retrieval.pgvector_retriever import PgVectorRetriever


@pytest.mark.asyncio
async def test_pgvector_retriever_search(async_client: AsyncClient):
    # In SQLite test environment, verify retriever search logic with mock embeddings
    provider = SentenceTransformerEmbeddingProvider()
    doc_id = uuid.uuid4()
    
    # 1. Create a dummy document and chunks in DB via async_client dependency session
    # We can perform this by calling document upload API or directly inserting into DB
    # Let's test the search API endpoint with an uploaded document
    file_content = b"""# SIH Project Overview
TransformAI is an automated content transformation platform.
It converts technical documents into multiple communication formats.

# Architecture
The architecture comprises FastAPI backend, PostgreSQL with pgvector, and Next.js frontend.
Embeddings are generated locally using SentenceTransformers.
"""
    files = {"file": ("test_retrieval_doc.txt", file_content, "text/plain")}
    data = {"chunking_strategy": "structure_aware"}
    
    upload_res = await async_client.post("/api/v1/documents/upload", files=files, data=data)
    assert upload_res.status_code == 202
    uploaded_doc = upload_res.json()
    document_id = uploaded_doc["document_id"]

    # 2. Test valid retrieval search across all documents
    search_payload = {
        "query": "What is the architecture and embedding model?",
        "top_k": 3,
        "similarity_threshold": 0.0,
    }
    search_res = await async_client.post("/api/v1/retrieval/search", json=search_payload)
    assert search_res.status_code == 200
    res_json = search_res.json()
    assert res_json["query"] == search_payload["query"]
    assert "results" in res_json
    assert len(res_json["results"]) > 0

    first_chunk = res_json["results"][0]
    assert "chunk_id" in first_chunk
    assert "similarity_score" in first_chunk
    assert 0.0 <= first_chunk["similarity_score"] <= 1.0
    assert "source_filename" in first_chunk
    assert first_chunk["source_filename"] == "test_retrieval_doc.txt"
    assert "chunk_index" in first_chunk

    # 3. Test document_id filtering
    scoped_payload = {
        "query": "content transformation platform",
        "document_id": document_id,
        "top_k": 2,
        "similarity_threshold": 0.0,
    }
    scoped_res = await async_client.post("/api/v1/retrieval/search", json=scoped_payload)
    assert scoped_res.status_code == 200
    scoped_json = scoped_res.json()
    for chunk in scoped_json["results"]:
        assert chunk["document_id"] == document_id

    # 4. Test similarity ordering (results must be ordered by similarity descending)
    if len(scoped_json["results"]) >= 2:
        scores = [c["similarity_score"] for c in scoped_json["results"]]
        assert scores == sorted(scores, reverse=True)

    # 5. Test nonexistent document_id returns 404
    nonexistent_doc_id = str(uuid.uuid4())
    bad_doc_res = await async_client.post(
        "/api/v1/retrieval/search",
        json={"query": "test query", "document_id": nonexistent_doc_id},
    )
    assert bad_doc_res.status_code == 404

    # 6. Test invalid similarity threshold (e.g. negative or > 1.0)
    neg_thresh_res = await async_client.post(
        "/api/v1/retrieval/search",
        json={"query": "test", "similarity_threshold": -0.5},
    )
    assert neg_thresh_res.status_code == 422

    high_thresh_res = await async_client.post(
        "/api/v1/retrieval/search",
        json={"query": "test", "similarity_threshold": 1.5},
    )
    assert high_thresh_res.status_code == 422

    # 7. Test invalid top_k (e.g. 0 or > 50)
    zero_k_res = await async_client.post(
        "/api/v1/retrieval/search",
        json={"query": "test", "top_k": 0},
    )
    assert zero_k_res.status_code == 422

    over_k_res = await async_client.post(
        "/api/v1/retrieval/search",
        json={"query": "test", "top_k": 100},
    )
    assert over_k_res.status_code == 422

    # 8. Test empty query
    empty_query_res = await async_client.post(
        "/api/v1/retrieval/search",
        json={"query": "", "top_k": 5},
    )
    assert empty_query_res.status_code == 422
