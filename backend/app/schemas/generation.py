import uuid
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

from app.services.generation.models import (
    OutputType,
    AudienceType,
    ToneType,
    DetailLevel,
    CommunicationObjective,
)
from app.schemas.retrieval import SourceReferenceSchema


class TransformationRequestSchema(BaseModel):
    """
    Request model for Multi-Format Generative Transformation.
    """
    document_id: uuid.UUID = Field(
        ...,
        description="ID of the source document to transform.",
    )
    output_type: OutputType = Field(
        OutputType.EXECUTIVE_SUMMARY,
        description="Target communication format.",
    )
    audience: AudienceType = Field(
        AudienceType.EXECUTIVE,
        description="Target audience perspective.",
    )
    tone: ToneType = Field(
        ToneType.PROFESSIONAL,
        description="Stylistic tone of communication.",
    )
    detail_level: DetailLevel = Field(
        DetailLevel.MODERATE,
        description="Granularity of information synthesis.",
    )
    communication_objective: CommunicationObjective = Field(
        CommunicationObjective.INFORM,
        description="Primary communication purpose.",
    )
    language: str = Field(
        "English",
        description="Target language for output.",
    )
    length_constraint: Optional[str] = Field(
        None,
        description="Optional length boundary (e.g. '3-5 slides', 'under 300 words', '60s script').",
    )
    query: Optional[str] = Field(
        None,
        description="Optional query to scope or focus vector retrieval on specific topics.",
    )
    custom_intent: Optional[str] = Field(
        None,
        description="Optional instructions regarding emphasis, perspective, or focus.",
    )
    top_k: int = Field(
        5,
        ge=1,
        le=50,
        description="Number of top source chunks to retrieve for grounding.",
    )
    similarity_threshold: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold (0.0 to 1.0).",
    )

    model_config = ConfigDict(from_attributes=True)


class ExecutiveSummaryResponseContentSchema(BaseModel):
    title: str
    overview: str
    key_points: List[str]
    important_facts: List[str]
    implications: List[str]
    conclusion: str
    source_references: List[SourceReferenceSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AdvisoryResponseContentSchema(BaseModel):
    title: str
    situation: str
    key_information: List[str]
    risks_or_considerations: List[str]
    recommended_actions: List[str]
    important_notes: List[str]
    conclusion: str
    source_references: List[SourceReferenceSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SlideItemSchema(BaseModel):
    slide_number: int
    title: str
    bullets: List[str]
    speaker_notes: str
    source_references: List[SourceReferenceSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PresentationResponseContentSchema(BaseModel):
    presentation_title: str
    slides: List[SlideItemSchema]

    model_config = ConfigDict(from_attributes=True)


class SceneItemSchema(BaseModel):
    scene_number: int
    visual_description: str
    narration: str
    on_screen_text: str
    source_references: List[SourceReferenceSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class VideoScriptResponseContentSchema(BaseModel):
    title: str
    target_duration: str
    scenes: List[SceneItemSchema]

    model_config = ConfigDict(from_attributes=True)


class TransformationResultResponseSchema(BaseModel):
    """
    Standardized, research-annotated response model for completed transformations.
    """
    transformation_id: uuid.UUID
    document_id: uuid.UUID
    output_type: OutputType
    configuration: Dict[str, Any]
    content: Union[
        ExecutiveSummaryResponseContentSchema,
        AdvisoryResponseContentSchema,
        PresentationResponseContentSchema,
        VideoScriptResponseContentSchema,
        Dict[str, Any],
    ]
    source_references: List[SourceReferenceSchema]
    retrieved_chunk_ids: List[str]
    retrieval_similarity_scores: List[float]
    retrieval_ranks: List[int]
    number_of_retrieved_chunks: int
    provider: str
    model: str
    generation_latency_ms: float
    token_usage: Optional[Dict[str, int]] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FormatOptionSchema(BaseModel):
    value: str
    label: str
    description: str


class AvailableFormatsResponseSchema(BaseModel):
    output_types: List[FormatOptionSchema]
    audiences: List[FormatOptionSchema]
    tones: List[FormatOptionSchema]
    detail_levels: List[FormatOptionSchema]
    objectives: List[FormatOptionSchema]
