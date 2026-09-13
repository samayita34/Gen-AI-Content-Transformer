import uuid
import pytest
from httpx import AsyncClient

from app.services.retrieval.models import RetrievedChunk
from app.services.retrieval.normalizer import ContextNormalizer


def test_context_normalizer_deterministic():
    normalizer = ContextNormalizer()
    doc_id = uuid.uuid4()
    chunk_1_id = uuid.uuid4()
    chunk_2_id = uuid.uuid4()

    chunks = [
        RetrievedChunk(
            chunk_id=chunk_1_id,
            document_id=doc_id,
            content="The platform supports PDF, DOCX, and TXT document ingestion. Latency is under 50ms.",
            similarity_score=0.92,
            chunk_index=0,
            page_number=1,
            section_title="Ingestion Overview",
            chunking_strategy="structure_aware",
            source_filename="spec.txt",
        ),
        RetrievedChunk(
            chunk_id=chunk_2_id,
            document_id=doc_id,
            content="pgvector performs 384-dimensional dense cosine similarity search with 100% precision.",
            similarity_score=0.85,
            chunk_index=1,
            page_number=2,
            section_title="Vector Retrieval",
            chunking_strategy="structure_aware",
            source_filename="spec.txt",
        ),
    ]

    context_a = normalizer.build_normalized_context(query="supported formats", retrieved_chunks=chunks)
    context_b = normalizer.build_normalized_context(query="supported formats", retrieved_chunks=chunks)

    # 1. Deterministic verification: Context A and Context B must be identical
    assert len(context_a.facts) == len(context_b.facts)
    assert len(context_a.entities) == len(context_b.entities)
    assert len(context_a.key_points) == len(context_b.key_points)
    assert [f.fact_text for f in context_a.facts] == [f.fact_text for f in context_b.facts]

    # 2. Ranking preservation: Top chunk is first
    assert context_a.retrieved_chunks[0].chunk_id == chunk_1_id
    assert context_a.retrieved_chunks[1].chunk_id == chunk_2_id

    # 3. Provenance traceability: Every fact must have accurate source reference
    for fact in context_a.facts:
        assert fact.source_reference.document_id == doc_id
        assert fact.source_reference.source_filename == "spec.txt"
        assert fact.source_reference.page_number in [1, 2]

    # 4. Entity extraction: acronyms like PDF, DOCX, TXT or metrics like 50ms should be recognized
    entity_names = [e.entity_name for e in context_a.entities]
    assert any("PDF" in name or "DOCX" in name or "TXT" in name or "50ms" in name for name in entity_names)

    # 5. Document grouping
    assert len(context_a.source_documents) == 1
    assert context_a.source_documents[0]["document_id"] == str(doc_id)
    assert context_a.source_documents[0]["source_filename"] == "spec.txt"
    assert context_a.source_documents[0]["retrieved_chunk_count"] == 2


def test_context_normalizer_deduplication():
    normalizer = ContextNormalizer()
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    duplicate_chunks = [
        RetrievedChunk(
            chunk_id=chunk_id,
            document_id=doc_id,
            content="Identical content for deduplication test.",
            similarity_score=0.90,
            chunk_index=0,
            page_number=1,
            section_title="Intro",
            chunking_strategy="structure_aware",
            source_filename="test.txt",
        ),
        RetrievedChunk(
            chunk_id=chunk_id,
            document_id=doc_id,
            content="Identical content for deduplication test.",
            similarity_score=0.90,
            chunk_index=0,
            page_number=1,
            section_title="Intro",
            chunking_strategy="structure_aware",
            source_filename="test.txt",
        ),
    ]

    context = normalizer.build_normalized_context(query="dedup", retrieved_chunks=duplicate_chunks)
    assert len(context.retrieved_chunks) == 1


def test_context_normalizer_empty():
    normalizer = ContextNormalizer()
    context = normalizer.build_normalized_context(query="empty", retrieved_chunks=[])
    assert context.retrieved_chunks == []
    assert context.facts == []
    assert context.key_points == []
    assert context.entities == []
    assert context.claims == []
    assert context.source_documents == []


@pytest.mark.asyncio
async def test_context_normalization_api(async_client: AsyncClient):
    file_content = b"""# SIH Research Statement
The goal is automated content transformation with 100% factual accuracy.
No hallucinated facts are permitted during normalization.
"""
    files = {"file": ("research_spec.txt", file_content, "text/plain")}
    data = {"chunking_strategy": "structure_aware"}
    
    upload_res = await async_client.post("/api/v1/documents/upload", files=files, data=data)
    assert upload_res.status_code == 202
    doc_id = upload_res.json()["document_id"]

    context_req = {
        "query": "What is the goal and accuracy requirement?",
        "document_id": doc_id,
        "top_k": 3,
        "similarity_threshold": 0.0,
    }
    context_res = await async_client.post("/api/v1/retrieval/context", json=context_req)
    assert context_res.status_code == 200
    res_json = context_res.json()

    assert res_json["query"] == context_req["query"]
    assert "source_documents" in res_json
    assert len(res_json["source_documents"]) > 0
    assert "facts" in res_json
    assert len(res_json["facts"]) > 0
    assert "key_points" in res_json
    assert "entities" in res_json
    assert "claims" in res_json
    assert "source_references" in res_json
