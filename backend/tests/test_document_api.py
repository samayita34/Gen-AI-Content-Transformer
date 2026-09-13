import pytest
import io
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_invalid_extension(async_client: AsyncClient):
    """Verifies that unsupported file extensions are rejected with HTTP 400."""
    files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    response = await async_client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_file(async_client: AsyncClient):
    """Verifies that empty files (0 bytes) are rejected with HTTP 400."""
    files = {"file": ("empty.txt", b"", "text/plain")}
    response = await async_client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_and_pipeline_flow(async_client: AsyncClient):
    """
    Verifies valid upload of a TXT document, status retrieval, and chunks retrieval.
    """
    sample_content = (
        "# 1. Introduction\n"
        "Distributed generative AI platforms enable automated multi-format transformation.\n\n"
        "# 2. System Architecture\n"
        "The architecture contains document ingestion, parsing, and vector indexing tiers."
    )
    files = {"file": ("research_paper.txt", sample_content.encode("utf-8"), "text/plain")}
    data = {"chunking_strategy": "structure_aware"}

    # 1. Upload
    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data,
    )
    assert response.status_code == 202
    upload_res = response.json()
    assert "document_id" in upload_res
    assert upload_res["original_filename"] == "research_paper.txt"
    assert upload_res["processing_status"] in ("uploaded", "processing", "completed")

    doc_id = upload_res["document_id"]

    # 2. Get Document by ID
    get_res = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    doc_detail = get_res.json()
    assert doc_detail["id"] == doc_id
    assert doc_detail["original_filename"] == "research_paper.txt"

    # 3. Get Chunks for Document
    chunk_res = await async_client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunk_res.status_code == 200
    chunk_list = chunk_res.json()
    assert "chunks" in chunk_list
    assert chunk_list["document_id"] == doc_id

    # 4. List Documents
    list_res = await async_client.get("/api/v1/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert "documents" in docs
    assert any(d["id"] == doc_id for d in docs["documents"])


@pytest.mark.asyncio
async def test_get_nonexistent_document(async_client: AsyncClient):
    """Verifies that non-existent document ID returns HTTP 404."""
    fake_id = uuid.uuid4()
    response = await async_client.get(f"/api/v1/documents/{fake_id}")
    assert response.status_code == 404
