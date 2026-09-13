import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.generation import (
    TransformationRequestSchema,
    TransformationResultResponseSchema,
    AvailableFormatsResponseSchema,
    FormatOptionSchema,
    ExecutiveSummaryResponseContentSchema,
    AdvisoryResponseContentSchema,
    PresentationResponseContentSchema,
    SlideItemSchema,
    VideoScriptResponseContentSchema,
    SceneItemSchema,
)
from app.schemas.retrieval import SourceReferenceSchema
from app.services.generation.models import (
    GenerationConfig,
    OutputType,
    ExecutiveSummaryContent,
    AdvisoryContent,
    PresentationContent,
    VideoScriptContent,
)
from app.services.generation.service import default_generation_service

logger = logging.getLogger("transformai.api.generation")

router = APIRouter()


@router.post(
    "/transform",
    response_model=TransformationResultResponseSchema,
    summary="Multi-Format Source-Grounded Content Transformation",
    description=(
        "Transforms source document content into one of four structured formats "
        "(Executive Summary, Advisory, Presentation + Speaker Notes, Video Script + Storyboard) "
        "using pgvector dense retrieval and source-grounded generation with anti-fabrication constraints."
    ),
)
async def transform_document(
    request: TransformationRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> TransformationResultResponseSchema:
    config = GenerationConfig(
        output_type=request.output_type,
        audience=request.audience,
        tone=request.tone,
        detail_level=request.detail_level,
        communication_objective=request.communication_objective,
        language=request.language,
        length_constraint=request.length_constraint,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )

    try:
        result = await default_generation_service.transform_document(
            db=db,
            document_id=request.document_id,
            config=config,
            query=request.query,
            custom_intent=request.custom_intent,
        )
    except ValueError as val_err:
        err_msg = str(val_err)
        if "does not exist" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            )
        elif "No indexed chunks" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=err_msg,
            )
    except Exception as exc:
        logger.error("Generation transformation failure: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content transformation failed: {str(exc)}",
        )

    # Format content schema according to output type
    content = result.content
    source_refs = [
        SourceReferenceSchema(
            document_id=r.document_id,
            source_filename=r.source_filename,
            chunk_id=r.chunk_id,
            chunk_index=r.chunk_index,
            page_number=r.page_number,
            section_title=r.section_title,
        )
        for r in result.source_references
    ]

    formatted_content: Any = content
    if isinstance(content, ExecutiveSummaryContent):
        formatted_content = ExecutiveSummaryResponseContentSchema(
            title=content.title,
            overview=content.overview,
            key_points=content.key_points,
            important_facts=content.important_facts,
            implications=content.implications,
            conclusion=content.conclusion,
            source_references=source_refs,
        )
    elif isinstance(content, AdvisoryContent):
        formatted_content = AdvisoryResponseContentSchema(
            title=content.title,
            situation=content.situation,
            key_information=content.key_information,
            risks_or_considerations=content.risks_or_considerations,
            recommended_actions=content.recommended_actions,
            important_notes=content.important_notes,
            conclusion=content.conclusion,
            source_references=source_refs,
        )
    elif isinstance(content, PresentationContent):
        formatted_content = PresentationResponseContentSchema(
            presentation_title=content.presentation_title,
            slides=[
                SlideItemSchema(
                    slide_number=s.slide_number,
                    title=s.title,
                    bullets=s.bullets,
                    speaker_notes=s.speaker_notes,
                    source_references=source_refs,
                )
                for s in content.slides
            ],
        )
    elif isinstance(content, VideoScriptContent):
        formatted_content = VideoScriptResponseContentSchema(
            title=content.title,
            target_duration=content.target_duration,
            scenes=[
                SceneItemSchema(
                    scene_number=sc.scene_number,
                    visual_description=sc.visual_description,
                    narration=sc.narration,
                    on_screen_text=sc.on_screen_text,
                    source_references=source_refs,
                )
                for sc in content.scenes
            ],
        )

    return TransformationResultResponseSchema(
        transformation_id=result.transformation_id,
        document_id=result.document_id,
        output_type=result.output_type,
        configuration=result.configuration,
        content=formatted_content,
        source_references=source_refs,
        retrieved_chunk_ids=result.retrieved_chunk_ids,
        retrieval_similarity_scores=result.retrieval_similarity_scores,
        retrieval_ranks=result.retrieval_ranks,
        number_of_retrieved_chunks=result.number_of_retrieved_chunks,
        provider=result.provider,
        model=result.model,
        generation_latency_ms=result.generation_latency_ms,
        token_usage=result.token_usage,
        created_at=result.created_at,
    )


@router.get(
    "/formats",
    response_model=AvailableFormatsResponseSchema,
    summary="List Supported Transformation Formats & Parameters",
    description="Returns available output formats, target audiences, tones, and objectives.",
)
async def get_available_formats() -> AvailableFormatsResponseSchema:
    return AvailableFormatsResponseSchema(
        output_types=[
            FormatOptionSchema(
                value="executive_summary",
                label="Executive Summary",
                description="High-level decision-oriented synthesis covering overview, key findings, and implications.",
            ),
            FormatOptionSchema(
                value="advisory",
                label="Advisory & Briefing",
                description="Structured advisory covering situation, key information, risks, and grounded recommendations.",
            ),
            FormatOptionSchema(
                value="presentation",
                label="Presentation + Speaker Notes",
                description="Slide-by-slide narrative outline with bullet points and comprehensive speaker notes.",
            ),
            FormatOptionSchema(
                value="video_script",
                label="Video Script + Storyboard",
                description="Multi-scene video script with visual descriptions, voiceover narration, and on-screen text.",
            ),
        ],
        audiences=[
            FormatOptionSchema(value="executive", label="Executive Leadership", description="Focus on strategic impact and high-level decisions."),
            FormatOptionSchema(value="technical", label="Technical & Engineering", description="Focus on architecture, technical specs, and precision."),
            FormatOptionSchema(value="general_public", label="General Public", description="Clear, accessible language free of jargon."),
            FormatOptionSchema(value="academic", label="Academic & Research", description="Rigorous methodology, theoretical grounding, and formal phrasing."),
            FormatOptionSchema(value="operational", label="Operations & Implementation", description="Action-oriented procedures and workflow considerations."),
        ],
        tones=[
            FormatOptionSchema(value="professional", label="Professional", description="Balanced, polished, and workplace-appropriate."),
            FormatOptionSchema(value="concise", label="Concise", description="Direct, terse, and focused on essential points."),
            FormatOptionSchema(value="formal", label="Formal", description="Authoritative and traditional tone."),
            FormatOptionSchema(value="explanatory", label="Explanatory", description="Educational and didactic framing."),
            FormatOptionSchema(value="neutral", label="Neutral", description="Objective, dispassionate reporting."),
        ],
        detail_levels=[
            FormatOptionSchema(value="brief", label="Brief", description="Condensed overview with minimal elaboration."),
            FormatOptionSchema(value="moderate", label="Moderate", description="Standard balanced depth."),
            FormatOptionSchema(value="detailed", label="Detailed", description="In-depth coverage of nuances and data points."),
        ],
        objectives=[
            FormatOptionSchema(value="inform", label="Inform", description="Provide factual clarity on the subject matter."),
            FormatOptionSchema(value="brief", label="Brief", description="Prepare readers for imminent meetings or decisions."),
            FormatOptionSchema(value="explain", label="Explain", description="Clarify concepts and causal mechanisms."),
            FormatOptionSchema(value="persuade", label="Persuade", description="Make a compelling case based strictly on source evidence."),
            FormatOptionSchema(value="prepare_action", label="Prepare Action", description="Outline operational readiness and grounded next steps."),
        ],
    )
