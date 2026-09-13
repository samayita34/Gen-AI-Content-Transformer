import time
import uuid
import logging
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.document import Document
from app.services.retrieval.pgvector_retriever import PgVectorRetriever
from app.services.verification.base import BaseVerificationJudge, VerificationUnavailableError
from app.services.verification.factory import get_verification_judge
from app.services.verification.extractor import (
    BaseClaimExtractor,
    MockClaimExtractor,
    get_claim_extractor,
    ClaimExtractor,
)
from app.services.verification.normalizer import ClaimNormalizer
from app.services.verification.models import (
    AtomicClaim,
    EvidenceMatch,
    ClaimVerificationResult,
    VerificationVerdict,
    VerificationReport,
)

logger = logging.getLogger("transformai.verification.service")


class VerificationService:
    """
    Independent Claim-Level Verification Agent Service.
    Deconstructs generated content, independently retrieves source evidence chunks,
    and evaluates factual grounding against the four-verdict taxonomy.
    """

    def __init__(
        self,
        judge: Optional[BaseVerificationJudge] = None,
        extractor: Optional[BaseClaimExtractor] = None,
    ):
        self._judge = judge
        self._extractor = extractor

    @property
    def judge(self) -> BaseVerificationJudge:
        return self._judge or get_verification_judge()

    @property
    def extractor(self) -> BaseClaimExtractor:
        return self._extractor or get_claim_extractor()

    async def verify_transformation(
        self,
        document_id: uuid.UUID,
        output_type: str,
        transformation_content: Any,
        db: AsyncSession,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> VerificationReport:
        """
        Executes claim extraction, independent evidence retrieval, and verification evaluation.
        """
        start_time = time.perf_counter()

        # 1. Verify document exists
        query = select(Document).where(Document.id == document_id)
        res = await db.execute(query)
        doc = res.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document with ID '{document_id}' not found.")

        # 2. Extract Atomic Claims from Generated Output
        logger.info("Extracting atomic claims using %s from %s output for document %s...", self.extractor.extractor_name, output_type, document_id)
        claims = await self.extractor.extract_claims(transformation_content, output_type)
        logger.info("Extracted %d atomic claims.", len(claims))

        if not claims:
            return VerificationReport(
                document_id=document_id,
                output_type=output_type,
                total_claims=0,
                supported_claims=0,
                contradicted_claims=0,
                partially_supported_claims=0,
                insufficient_evidence_claims=0,
                claim_results=[],
                summary="No factual claims were extracted from the transformation output.",
            )

        # 3. Deterministic Claim Normalization
        logger.info("Applying deterministic claim normalization on %d claims...", len(claims))
        claims = ClaimNormalizer.normalize_claims(claims)

        # 4. Independent Evidence Retrieval & Verification Evaluation
        k = top_k or settings.VERIFICATION_TOP_K
        threshold = similarity_threshold if similarity_threshold is not None else settings.VERIFICATION_SIMILARITY_THRESHOLD
        retriever = PgVectorRetriever(session=db)

        claim_results: List[ClaimVerificationResult] = []
        supported_cnt = 0
        contradicted_cnt = 0
        partially_supported_cnt = 0
        insufficient_evidence_cnt = 0

        for claim in claims:
            # Independent vector search per claim using normalized text
            search_query = claim.normalized_text or claim.normalized_statement or claim.text
            retrieved_chunks = await retriever.search(
                query=search_query,
                document_id=document_id,
                top_k=k,
                similarity_threshold=threshold,
            )

            # Map to EvidenceMatch objects preserving provenance
            evidence_matches: List[EvidenceMatch] = []
            for rc in retrieved_chunks:
                evidence_matches.append(
                    EvidenceMatch(
                        chunk_id=rc.chunk_id,
                        document_id=rc.document_id,
                        chunk_content=rc.content,
                        similarity_score=rc.similarity_score,
                        page_number=rc.page_number,
                        section_title=rc.section_title,
                        modality=rc.metadata.get("modality", "text"),
                        timestamp_start_sec=rc.metadata.get("timestamp_start_sec"),
                        timestamp_end_sec=rc.metadata.get("timestamp_end_sec"),
                        formatted_timestamp=rc.metadata.get("formatted_timestamp"),
                        spatial_bounds=rc.metadata.get("spatial_bounds"),
                        relevance_snippet=rc.content[:250] + ("..." if len(rc.content) > 250 else ""),
                    )
                )

            # Evaluate with active Verification Judge
            verdict, confidence, explanation = await self.judge.evaluate_claim(claim, evidence_matches)

            if verdict == VerificationVerdict.SUPPORTED:
                supported_cnt += 1
            elif verdict == VerificationVerdict.CONTRADICTED:
                contradicted_cnt += 1
            elif verdict == VerificationVerdict.PARTIALLY_SUPPORTED:
                partially_supported_cnt += 1
            else:
                insufficient_evidence_cnt += 1

            claim_results.append(
                ClaimVerificationResult(
                    claim=claim,
                    verdict=verdict,
                    confidence=confidence,
                    explanation=explanation,
                    evidence=evidence_matches,
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        total_claims = len(claims)
        summary = (
            f"Verification analyzed {total_claims} claim(s) in {elapsed_ms:.1f}ms: "
            f"{supported_cnt} supported, {contradicted_cnt} contradicted, "
            f"{partially_supported_cnt} partially supported, {insufficient_evidence_cnt} insufficient evidence."
        )

        return VerificationReport(
            document_id=document_id,
            output_type=output_type,
            total_claims=total_claims,
            supported_claims=supported_cnt,
            contradicted_claims=contradicted_cnt,
            partially_supported_claims=partially_supported_cnt,
            insufficient_evidence_claims=insufficient_evidence_cnt,
            claim_results=claim_results,
            summary=summary,
        )


default_verification_service = VerificationService()
