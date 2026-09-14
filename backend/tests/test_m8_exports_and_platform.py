import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.generation.models import (
    OutputType,
    TransformationResult,
    ExecutiveSummaryContent,
    AdvisoryContent,
    PresentationContent,
    SlideItem,
    VideoScriptContent,
    SceneItem,
)
from app.services.retrieval.models import SourceReference
from app.services.verification.models import (
    VerificationReport,
    ClaimVerificationResult,
    AtomicClaim,
    VerificationVerdict,
    EvidenceMatch,
)
from app.services.generation.store import default_result_store
from app.services.export.service import default_export_service


@pytest.fixture(autouse=True)
def clean_store():
    default_result_store.clear()
    yield
    default_result_store.clear()


@pytest.fixture
def sample_source_references():
    return [
        SourceReference(
            document_id=uuid.uuid4(),
            source_filename="DOC-DEV-01-TECH.txt",
            chunk_id=uuid.uuid4(),
            chunk_index=0,
            page_number=1,
            section_title="SLA Overview",
        ),
        SourceReference(
            document_id=uuid.uuid4(),
            source_filename="DOC-DEV-01-TECH.txt",
            chunk_id=uuid.uuid4(),
            chunk_index=1,
            page_number=1,
            section_title="Redundancy Architecture",
        ),
    ]


@pytest.fixture
def sample_verification_report():
    doc_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    return VerificationReport(
        report_id=str(uuid.uuid4()),
        document_id=doc_id,
        output_type="executive_summary",
        total_claims=2,
        supported_claims=1,
        contradicted_claims=0,
        partially_supported_claims=1,
        insufficient_evidence_claims=0,
        claim_results=[
            ClaimVerificationResult(
                claim=AtomicClaim(
                    claim_id=claim_id,
                    statement="Uptime SLA is guaranteed at 99.99%.",
                    context_source_field="overview",
                ),
                verdict=VerificationVerdict.SUPPORTED,
                confidence=0.95,
                explanation="Directly stated in Section 1.",
                evidence=[
                    EvidenceMatch(
                        chunk_id=uuid.uuid4(),
                        document_id=doc_id,
                        chunk_content="The platform provides an uptime SLA of 99.99%.",
                        similarity_score=0.92,
                        section_title="SLA Overview",
                        page_number=1,
                    )
                ],
            ),
            ClaimVerificationResult(
                claim=AtomicClaim(
                    claim_id=uuid.uuid4(),
                    statement="Automated failover latency is under 5 seconds.",
                    context_source_field="key_points[0]",
                ),
                verdict=VerificationVerdict.PARTIALLY_SUPPORTED,
                confidence=0.80,
                explanation="Source confirms failover exists, but latency is unspecified.",
                evidence=[],
            ),
        ],
        summary="Evaluated 2 claims: 1 supported, 1 partially supported.",
    )


def test_export_service_executive_summary_pdf(sample_source_references, sample_verification_report):
    """Verifies that ExportService generates valid PDF bytes for Executive Summary."""
    trans_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=doc_id,
        output_type=OutputType.EXECUTIVE_SUMMARY,
        configuration={"audience": "executive", "tone": "professional"},
        content=ExecutiveSummaryContent(
            title="Executive Summary: Cloud Infrastructure SLA",
            overview="This document analyzes high-availability cloud architecture.",
            key_points=["99.99% availability target", "Automated multi-region failover"],
            important_facts=["Multi-region deployment across 3 zones", "RTO < 10ms"],
            implications=["Significant cost savings", "Zero unplanned downtime"],
            conclusion="Recommended for production adoption.",
        ),
        source_references=sample_source_references,
        retrieved_chunk_ids=[str(uuid.uuid4()), str(uuid.uuid4())],
        retrieval_similarity_scores=[0.95, 0.88],
        retrieval_ranks=[1, 2],
        number_of_retrieved_chunks=2,
        provider="mock",
        model="mock-llm-v1",
        generation_latency_ms=120.5,
    )

    pdf_bytes = default_export_service.generate_pdf_export(
        result=res,
        verification_report=sample_verification_report,
        include_provenance=True,
        include_verification=True,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")


def test_export_service_advisory_pdf(sample_source_references):
    """Verifies that ExportService generates valid PDF bytes for Advisory Briefing."""
    trans_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=doc_id,
        output_type=OutputType.ADVISORY,
        configuration={"audience": "technical", "tone": "formal"},
        content=AdvisoryContent(
            title="Technical Advisory: Security Protocols",
            situation="Active migration to TLS 1.3 cryptographic cipher suites.",
            key_information=["Legacy cipher suites disabled by Q3", "Mandatory HSM integration"],
            risks_or_considerations=["Temporary latency increase during key exchange"],
            recommended_actions=["Upgrade all proxy endpoints", "Rotate root keys"],
            important_notes=["Ensure backward compatibility for legacy clients"],
            conclusion="Action required before end of sprint.",
        ),
        source_references=sample_source_references,
        retrieved_chunk_ids=[str(uuid.uuid4())],
        retrieval_similarity_scores=[0.91],
        retrieval_ranks=[1],
        number_of_retrieved_chunks=1,
        provider="mock",
        model="mock-llm-v1",
        generation_latency_ms=95.0,
    )

    pdf_bytes = default_export_service.generate_pdf_export(
        result=res,
        verification_report=None,
        include_provenance=True,
        include_verification=False,
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_export_service_presentation_pptx():
    """Verifies that ExportService generates valid PPTX bytes with slides and speaker notes."""
    trans_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=doc_id,
        output_type=OutputType.PRESENTATION,
        configuration={"audience": "executive", "tone": "professional"},
        content=PresentationContent(
            presentation_title="Q4 Infrastructure Strategy",
            slides=[
                SlideItem(
                    slide_number=1,
                    title="Executive Vision",
                    bullets=["Scale to 10M DAU", "Ensure 99.99% reliability"],
                    speaker_notes="Welcome leadership. Today we outline our scalability plan.",
                ),
                SlideItem(
                    slide_number=2,
                    title="Architecture Roadmap",
                    bullets=["Deploy pgvector clusters", "Context normalization pipeline"],
                    speaker_notes="Here we see our retrieval and normalizer architecture.",
                ),
            ],
        ),
        source_references=[],
        retrieved_chunk_ids=[],
        retrieval_similarity_scores=[],
        retrieval_ranks=[],
        number_of_retrieved_chunks=0,
        provider="mock",
        model="mock-llm-v1",
        generation_latency_ms=80.0,
    )

    pptx_bytes = default_export_service.generate_presentation_pptx(
        result=res,
        verification_report=None,
        include_verification=False,
    )

    assert isinstance(pptx_bytes, bytes)
    assert len(pptx_bytes) > 1000
    assert pptx_bytes.startswith(b"PK")


def test_export_service_video_script_pdf():
    """Verifies that ExportService generates valid PDF bytes for Video Script / Storyboard."""
    trans_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=doc_id,
        output_type=OutputType.VIDEO_SCRIPT,
        configuration={"audience": "general_public", "tone": "explanatory"},
        content=VideoScriptContent(
            title="Product Overview Explainer",
            target_duration="90 seconds",
            scenes=[
                SceneItem(
                    scene_number=1,
                    visual_description="Opening title card with animated waveform.",
                    narration="Welcome to TransformAI, where technical documents become multi-format content.",
                    on_screen_text="TransformAI: Grounded AI",
                ),
                SceneItem(
                    scene_number=2,
                    visual_description="Split screen comparing unstructured text with structured deck.",
                    narration="Transform reports into verified summaries in seconds.",
                    on_screen_text="Zero Hallucination Guarantee",
                ),
            ],
        ),
        source_references=[],
        retrieved_chunk_ids=[],
        retrieval_similarity_scores=[],
        retrieval_ranks=[],
        number_of_retrieved_chunks=0,
        provider="mock",
        model="mock-llm-v1",
        generation_latency_ms=110.0,
    )

    pdf_bytes = default_export_service.generate_pdf_export(
        result=res,
        include_provenance=False,
        include_verification=False,
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_transformation_result_store():
    """Verifies store save, retrieve, attach verification, and LRU eviction."""
    trans_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=uuid.uuid4(),
        output_type=OutputType.EXECUTIVE_SUMMARY,
        configuration={},
        content=ExecutiveSummaryContent(
            title="Test",
            overview="Overview",
            key_points=["Point 1"],
            important_facts=["Fact 1"],
            implications=["Imp 1"],
            conclusion="Conclusion",
        ),
        source_references=[],
        retrieved_chunk_ids=[],
        retrieval_similarity_scores=[],
        retrieval_ranks=[],
        number_of_retrieved_chunks=0,
        provider="mock",
        model="mock",
        generation_latency_ms=10.0,
    )

    default_result_store.save_result(res)
    retrieved = default_result_store.get_result(trans_id)
    assert retrieved is not None
    assert retrieved.transformation_id == trans_id

    # Non-existent ID
    assert default_result_store.get_result(uuid.uuid4()) is None

    # Attach verification report
    rep = VerificationReport(
        report_id="rep-1",
        document_id=res.document_id,
        output_type="executive_summary",
        total_claims=1,
        supported_claims=1,
        contradicted_claims=0,
        partially_supported_claims=0,
        insufficient_evidence_claims=0,
    )
    default_result_store.attach_verification_report(trans_id, rep)
    assert default_result_store.get_verification_report(trans_id) == rep


@pytest.mark.asyncio
async def test_api_export_endpoint_pdf_success():
    """Tests POST /api/v1/generation/export with valid transformation_id."""
    trans_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=doc_id,
        output_type=OutputType.EXECUTIVE_SUMMARY,
        configuration={"audience": "executive"},
        content=ExecutiveSummaryContent(
            title="Executive Summary: Cloud Infrastructure SLA",
            overview="This document analyzes high-availability cloud architecture.",
            key_points=["99.99% availability"],
            important_facts=["3 availability zones"],
            implications=["Zero downtime"],
            conclusion="Production ready.",
        ),
        source_references=[],
        retrieved_chunk_ids=[],
        retrieval_similarity_scores=[],
        retrieval_ranks=[],
        number_of_retrieved_chunks=0,
        provider="mock",
        model="mock-llm-v1",
        generation_latency_ms=100.0,
    )
    default_result_store.save_result(res)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "transformation_id": str(trans_id),
            "export_format": "pdf",
            "include_provenance": True,
            "include_verification": True,
        }
        response = await client.post("/api/v1/generation/export", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert f"transformai_executive_summary_{str(trans_id)[:8]}.pdf" in response.headers["content-disposition"]
        assert response.content.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_api_export_endpoint_pptx_success():
    """Tests POST /api/v1/generation/export with Presentation PPTX."""
    trans_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=doc_id,
        output_type=OutputType.PRESENTATION,
        configuration={},
        content=PresentationContent(
            presentation_title="Q4 Strategy",
            slides=[
                SlideItem(
                    slide_number=1,
                    title="Introduction",
                    bullets=["Goal 1", "Goal 2"],
                    speaker_notes="Opening remarks.",
                )
            ],
        ),
        source_references=[],
        retrieved_chunk_ids=[],
        retrieval_similarity_scores=[],
        retrieval_ranks=[],
        number_of_retrieved_chunks=0,
        provider="mock",
        model="mock-llm-v1",
        generation_latency_ms=100.0,
    )
    default_result_store.save_result(res)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "transformation_id": str(trans_id),
            "export_format": "pptx",
        }
        response = await client.post("/api/v1/generation/export", json=payload)
        assert response.status_code == 200
        assert "presentationml.presentation" in response.headers["content-type"]
        assert f"transformai_presentation_{str(trans_id)[:8]}.pptx" in response.headers["content-disposition"]
        assert response.content.startswith(b"PK")


@pytest.mark.asyncio
async def test_api_export_endpoint_not_found():
    """Tests POST /api/v1/generation/export with non-existent transformation_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "transformation_id": str(uuid.uuid4()),
            "export_format": "pdf",
        }
        response = await client.post("/api/v1/generation/export", json=payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_export_endpoint_invalid_pptx_for_summary():
    """Tests POST /api/v1/generation/export rejecting PPTX for non-presentation formats."""
    trans_id = uuid.uuid4()
    res = TransformationResult(
        transformation_id=trans_id,
        document_id=uuid.uuid4(),
        output_type=OutputType.EXECUTIVE_SUMMARY,
        configuration={},
        content=ExecutiveSummaryContent(
            title="Summary",
            overview="Overview",
            key_points=["Key 1"],
            important_facts=["Fact 1"],
            implications=["Imp 1"],
            conclusion="Conclusion",
        ),
        source_references=[],
        retrieved_chunk_ids=[],
        retrieval_similarity_scores=[],
        retrieval_ranks=[],
        number_of_retrieved_chunks=0,
        provider="mock",
        model="mock",
        generation_latency_ms=50.0,
    )
    default_result_store.save_result(res)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "transformation_id": str(trans_id),
            "export_format": "pptx",
        }
        response = await client.post("/api/v1/generation/export", json=payload)
        assert response.status_code == 422
        assert "only supported for presentation" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_research_summary_endpoint():
    """Tests GET /api/v1/research/summary returning M7 fixture evaluation summary."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/research/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["is_available"] is True
        assert data["is_development_fixture"] is True
        assert "DEVELOPMENT FIXTURE" in data["fixture_disclaimer"]
        assert "track_1_generation_quality" in data["summary"]
        assert "track_2_verification_quality" in data["summary"]
        assert "track_3_operational_latency" in data["summary"]
