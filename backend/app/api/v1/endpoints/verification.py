import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.verification import (
    VerificationRequestSchema,
    VerificationReportResponseSchema,
    VerificationOptionsResponseSchema,
    ClaimVerificationResultSchema,
    AtomicClaimSchema,
    EvidenceMatchSchema,
)
from app.services.verification.service import default_verification_service
from app.services.verification.base import VerificationUnavailableError

logger = logging.getLogger("transformai.api.verification")
router = APIRouter()


@router.get(
    "/options",
    response_model=VerificationOptionsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Supported Verification Options & Configuration",
    description="Returns metadata about available verification engines, supported output formats, allowed verdict taxonomy, and default retrieval parameters.",
)
async def get_verification_options() -> VerificationOptionsResponseSchema:
    return VerificationOptionsResponseSchema(
        allowed_verdicts=["supported", "contradicted", "partially_supported", "insufficient_evidence"],
        supported_output_formats=["executive_summary", "advisory", "presentation", "video_script"],
        supported_extractors=["mock", "gemini", "openai", "claude", "local"],
        supported_verifiers=["mock", "gemini", "openai", "claude", "local"],
        active_verifier=default_verification_service.verifier.verifier_name,
        default_top_k=settings.VERIFICATION_TOP_K,
        default_similarity_threshold=settings.VERIFICATION_SIMILARITY_THRESHOLD,
    )


@router.post(
    "/verify",
    response_model=VerificationReportResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Claim-Level Source-Grounded Verification",
    description="Deconstructs generated transformation content into atomic factual claims, independently retrieves evidence chunks from the original source document using PgVectorRetriever, and evaluates support/contradiction with detailed provenance.",
)
async def verify_generated_content(
    request: VerificationRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> VerificationReportResponseSchema:
    try:
        report = await default_verification_service.verify_transformation(
            document_id=request.document_id,
            output_type=request.output_type,
            transformation_content=request.transformation_content,
            db=db,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )

        claims_list = [
            ClaimVerificationResultSchema(
                claim=AtomicClaimSchema(
                    claim_id=cr.claim.claim_id,
                    text=cr.claim.text,
                    normalized_text=cr.claim.normalized_text,
                    output_format=cr.claim.output_format,
                    source_output_reference=cr.claim.source_output_reference,
                    claim_type=cr.claim.claim_type,
                    extraction_confidence=cr.claim.extraction_confidence,
                    statement=cr.claim.statement,
                    context_source_field=cr.claim.context_source_field,
                    normalized_statement=cr.claim.normalized_statement,
                ),
                verdict=cr.verdict,
                confidence=cr.confidence,
                explanation=cr.explanation,
                claim_id=cr.claim_id,
                text=cr.text,
                normalized_text=cr.normalized_text,
                evidence=[
                    EvidenceMatchSchema(
                        chunk_id=ev.chunk_id,
                        document_id=ev.document_id,
                        chunk_content=ev.chunk_content,
                        similarity_score=ev.similarity_score,
                        page_number=ev.page_number,
                        section_title=ev.section_title,
                        modality=ev.modality,
                        timestamp_start_sec=ev.timestamp_start_sec,
                        timestamp_end_sec=ev.timestamp_end_sec,
                        formatted_timestamp=ev.formatted_timestamp,
                        spatial_bounds=ev.spatial_bounds,
                        metadata=ev.metadata or {},
                        relevance_snippet=ev.relevance_snippet,
                        text=ev.text,
                        similarity=ev.similarity,
                        source_reference=ev.source_reference,
                    )
                    for ev in cr.evidence
                ],
            )
            for cr in report.claim_results
        ]

        return VerificationReportResponseSchema(
            report_id=report.report_id,
            generated_output_id=report.generated_output_id,
            document_id=report.document_id,
            output_type=report.output_type,
            format=report.format or report.output_type,
            total_claims=report.total_claims,
            supported_claims=report.supported_claims,
            contradicted_claims=report.contradicted_claims,
            partially_supported_claims=report.partially_supported_claims,
            insufficient_evidence_claims=report.insufficient_evidence_claims,
            claim_results=claims_list,
            claims=claims_list,
            summary=report.summary,
            created_at=report.created_at,
        )

    except ValueError as val_err:
        logger.warning("Invalid verification request: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(val_err).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except VerificationUnavailableError as unavail_err:
        logger.error("Verification engine unavailable: %s", unavail_err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(unavail_err),
        )
    except Exception as exc:
        logger.error("Unexpected error during claim verification: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(exc)}",
        )
