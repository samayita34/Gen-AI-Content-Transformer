import json
import pytest
from app.services.document.parsers.json import JSONDocumentParser
from app.services.document.parsers import get_parser_for_filename
from app.services.document.pipeline import document_pipeline
from app.services.document.structure import structure_detector
from app.services.document.chunking import get_chunker
from app.services.embeddings.hf_local import SentenceTransformerEmbeddingProvider
from app.services.retrieval.pgvector_retriever import PgVectorRetriever
from app.models.document import ChunkingStrategy, Document, DocumentChunk


@pytest.mark.asyncio
async def test_1_simple_json_object():
    parser = JSONDocumentParser()
    payload = {
        "title": "TransformAI",
        "version": "1.0",
        "domain": "GenAI Content Transformation",
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    parsed = await parser.parse(raw_bytes, "simple.json")

    assert parsed.page_count == 1
    assert len(parsed.elements) >= 1
    assert "TransformAI" in parsed.elements[0].text
    assert "GenAI Content Transformation" in parsed.elements[0].text
    assert parsed.elements[0].metadata.get("json_path") == "root"


@pytest.mark.asyncio
async def test_2_nested_json_object():
    parser = JSONDocumentParser()
    payload = {
        "project": "TransformAI",
        "metadata": {
            "author": "Google Deepmind",
            "year": 2026,
            "architecture": {
                "vector_db": "pgvector",
                "embedding_dim": 384,
            },
        },
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    parsed = await parser.parse(raw_bytes, "nested.json")

    assert len(parsed.elements) >= 2
    paths = [e.metadata.get("json_path") for e in parsed.elements]
    assert any("metadata" in p for p in paths if p)
    full_text = " ".join(e.text for e in parsed.elements)
    assert "pgvector" in full_text
    assert "384" in full_text


@pytest.mark.asyncio
async def test_3_json_array():
    parser = JSONDocumentParser()
    payload = [
        "Executive Summary",
        "Presentation Slides",
        "Video Script",
        "Technical Advisory",
    ]
    raw_bytes = json.dumps(payload).encode("utf-8")
    parsed = await parser.parse(raw_bytes, "array.json")

    assert len(parsed.elements) >= 1
    full_text = " ".join(e.text for e in parsed.elements)
    assert "Executive Summary" in full_text
    assert "Video Script" in full_text


@pytest.mark.asyncio
async def test_4_nested_arrays_and_objects():
    parser = JSONDocumentParser()
    payload = {
        "title": "SIH Evaluation",
        "benchmarks": [
            {"id": "BM-01", "metric": "factual_consistency", "target": 0.95},
            {"id": "BM-02", "metric": "semantic_preservation", "target": 0.90},
        ],
        "tags": ["AI", "RAG", "SIH26154"],
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    parsed = await parser.parse(raw_bytes, "nested_complex.json")

    assert len(parsed.elements) >= 2
    full_text = " ".join(e.text for e in parsed.elements)
    assert "factual_consistency" in full_text
    assert "SIH26154" in full_text


@pytest.mark.asyncio
async def test_5_invalid_json():
    parser = JSONDocumentParser()
    invalid_bytes = b'{"title": "Unterminated JSON, '

    with pytest.raises(ValueError, match="Invalid JSON"):
        await parser.parse(invalid_bytes, "broken.json")

    empty_bytes = b"   "
    with pytest.raises(ValueError, match="empty"):
        await parser.parse(empty_bytes, "empty.json")


@pytest.mark.asyncio
async def test_6_json_parser_registration():
    parser = get_parser_for_filename("dataset.json")
    assert parser is not None
    assert isinstance(parser, JSONDocumentParser)
    assert ".json" in parser.supported_extensions


@pytest.mark.asyncio
async def test_7_json_accepted_by_pipeline_validation(db_session):
    valid, err = document_pipeline.validate_file("metrics.json", 1024)
    assert valid is True
    assert err is None

    sample_json = json.dumps({"status": "healthy", "service": "TransformAI"}).encode("utf-8")
    doc = await document_pipeline.ingest_document(
        file_bytes=sample_json,
        original_filename="metrics.json",
        file_size=len(sample_json),
        db=db_session,
        chunking_strategy=ChunkingStrategy.STRUCTURE_AWARE,
    )
    assert doc.id is not None
    assert doc.file_type == "json"


@pytest.mark.asyncio
async def test_8_json_content_reaches_chunking():
    parser = JSONDocumentParser()
    payload = {
        "section_1": {"topic": "Document Intelligence", "body": "TransformAI parses text, pdf, and json."},
        "section_2": {"topic": "Vector Search", "body": "PostgreSQL pgvector indexes 384-dimensional embeddings."},
    }
    parsed = await parser.parse(json.dumps(payload).encode("utf-8"), "data.json")
    structured = structure_detector.enrich_document_structure(parsed)

    chunker = get_chunker(ChunkingStrategy.STRUCTURE_AWARE)
    chunks = chunker.chunk(structured)

    assert len(chunks) >= 1
    assert all(c.content for c in chunks)
    assert any("Document Intelligence" in c.content for c in chunks)


@pytest.mark.asyncio
async def test_9_json_chunks_embedded_384_dim():
    provider = SentenceTransformerEmbeddingProvider()
    assert provider.dimension == 384

    texts = ["title: TransformAI", "topic: RAG pgvector embeddings"]
    embeddings = await provider.embed_batch(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384


@pytest.mark.asyncio
async def test_10_json_embeddings_stored_and_retrieved_via_pgvector(db_session):
    sample_json = {
        "title": "Quantum RAG Research",
        "description": "High-density vector embeddings with PostgreSQL pgvector for content transformation.",
        "author": "TransformAI Team",
    }
    raw_bytes = json.dumps(sample_json).encode("utf-8")

    # Ingest and process JSON document through full pipeline
    doc = await document_pipeline.ingest_document(
        file_bytes=raw_bytes,
        original_filename="quantum_rag.json",
        file_size=len(raw_bytes),
        db=db_session,
        chunking_strategy=ChunkingStrategy.STRUCTURE_AWARE,
    )

    processed_doc = await document_pipeline.process_document(doc.id, db_session)
    assert processed_doc.processing_status.value == "completed"

    # Verify retrieval over pgvector retriever
    retriever = PgVectorRetriever(session=db_session)
    retrieved = await retriever.search(
        query="vector embeddings with pgvector",
        document_id=processed_doc.id,
        top_k=3,
    )

    assert len(retrieved) >= 1
    assert "pgvector" in retrieved[0].content or "TransformAI" in retrieved[0].content
    assert retrieved[0].similarity_score > 0.0


@pytest.mark.asyncio
async def test_11_manual_verification_sample(db_session):
    from sqlalchemy import select
    payload = {
        "title": "TransformAI Test",
        "organization": "NTRO",
        "topics": ["AI", "RAG", "content transformation"],
        "year": 2026,
    }
    raw_bytes = json.dumps(payload, indent=2).encode("utf-8")

    # Ingest
    doc = await document_pipeline.ingest_document(
        file_bytes=raw_bytes,
        original_filename="manual_sample.json",
        file_size=len(raw_bytes),
        db=db_session,
        chunking_strategy=ChunkingStrategy.STRUCTURE_AWARE,
    )
    assert doc.id is not None
    assert doc.file_type == "json"

    # Process through pipeline
    processed_doc = await document_pipeline.process_document(doc.id, db_session)
    assert processed_doc.processing_status.value == "completed"

    # Explicitly query chunks to avoid async lazy loading
    chunk_res = await db_session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    chunks = chunk_res.scalars().all()
    assert len(chunks) >= 1

    # Embedding vector validation (384 dimensions)
    for c in chunks:
        assert c.embedding is not None
        assert len(c.embedding) == 384

    # Semantic similarity search
    retriever = PgVectorRetriever(session=db_session)
    results = await retriever.search(
        query="NTRO AI content transformation",
        document_id=doc.id,
        top_k=3,
    )
    assert len(results) >= 1
    assert results[0].similarity_score > 0.0
    matched_text = " ".join(r.content for r in results)
    assert "NTRO" in matched_text or "TransformAI" in matched_text or "content transformation" in matched_text

