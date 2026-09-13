import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.verification import (
    VerificationRequestSchema,
    VerificationReportResponseSchema,
)
from app.services.verification.service import default_verification_service
from app.services.verification.base import VerificationUnavailableError

logger = logging.getLogger("transformai.api.verification")
router = APIRouter()


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

        return VerificationReportResponseSchema(
            document_id=report.document_id,
            output_type=report.output_type,
            total_claims=report.total_claims,
            supported_claims=report.supported_claims,
            contradicted_claims=report.contradicted_claims,
            partially_supported_claims=report.partially_supported_claims,
            insufficient_evidence_claims=report.insufficient_evidence_claims,
            claim_results=[
                {
                    "claim": {
                        "claim_id": cr.claim.claim_id,
                        "statement": cr.claim.statement,
                        "claim_type": cr.claim.claim_type,
                        "context_source_field": cr.claim.context_source_field,
                        "normalized_statement": cr.claim.normalized_statement,
                    },
                    "verdict": cr.verdict,
                    "confidence": cr.confidence,
                    "explanation": cr.explanation,
                    "evidence": [
                        {
                            "chunk_id": ev.chunk_id,
                            "document_id": ev.document_id,
                            "chunk_content": ev.chunk_content,
                            "similarity_score": ev.similarity_score,
                            "page_number": ev.page_number,
                            "section_title": ev.section_title,
                            "modality": ev.modality,
                            "timestamp_start_sec": ev.timestamp_start_sec,
                            "timestamp_end_sec": ev.timestamp_end_sec,
                            "formatted_timestamp": ev.formatted_timestamp,
                            "spatial_bounds": ev.spatial_bounds,
                            "relevance_snippet": ev.relevance_snippet,
                        }
                        for ev in cr.evidence
                    ],
                }
                for cr in report.claim_results
            ],
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
