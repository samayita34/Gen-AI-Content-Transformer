import enum
import uuid
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from app.services.retrieval.models import SourceReference


class OutputType(str, enum.Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    ADVISORY = "advisory"
    PRESENTATION = "presentation"
    VIDEO_SCRIPT = "video_script"


class AudienceType(str, enum.Enum):
    GENERAL_PUBLIC = "general_public"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    ACADEMIC = "academic"
    OPERATIONAL = "operational"


class ToneType(str, enum.Enum):
    NEUTRAL = "neutral"
    PROFESSIONAL = "professional"
    CONCISE = "concise"
    FORMAL = "formal"
    EXPLANATORY = "explanatory"


class DetailLevel(str, enum.Enum):
    BRIEF = "brief"
    MODERATE = "moderate"
    DETAILED = "detailed"


class CommunicationObjective(str, enum.Enum):
    INFORM = "inform"
    BRIEF = "brief"
    EXPLAIN = "explain"
    PERSUADE = "persuade"
    PREPARE_ACTION = "prepare_action"


@dataclass
class GenerationConfig:
    output_type: OutputType
    audience: AudienceType = AudienceType.EXECUTIVE
    tone: ToneType = ToneType.PROFESSIONAL
    detail_level: DetailLevel = DetailLevel.MODERATE
    communication_objective: CommunicationObjective = CommunicationObjective.INFORM
    language: str = "English"
    length_constraint: Optional[str] = None
    temperature: float = 0.2
    top_k: int = 5
    similarity_threshold: float = 0.0


@dataclass
class ExecutiveSummaryContent:
    title: str
    overview: str
    key_points: List[str]
    important_facts: List[str]
    implications: List[str]
    conclusion: str
    source_references: List[SourceReference] = field(default_factory=list)


@dataclass
class AdvisoryContent:
    title: str
    situation: str
    key_information: List[str]
    risks_or_considerations: List[str]
    recommended_actions: List[str]
    important_notes: List[str]
    conclusion: str
    source_references: List[SourceReference] = field(default_factory=list)


@dataclass
class SlideItem:
    slide_number: int
    title: str
    bullets: List[str]
    speaker_notes: str
    source_references: List[SourceReference] = field(default_factory=list)


@dataclass
class PresentationContent:
    presentation_title: str
    slides: List[SlideItem]


@dataclass
class SceneItem:
    scene_number: int
    visual_description: str
    narration: str
    on_screen_text: str
    source_references: List[SourceReference] = field(default_factory=list)


@dataclass
class VideoScriptContent:
    title: str
    target_duration: str
    scenes: List[SceneItem]


@dataclass
class TransformationResult:
    transformation_id: uuid.UUID
    document_id: uuid.UUID
    output_type: OutputType
    configuration: Dict[str, Any]
    content: Union[ExecutiveSummaryContent, AdvisoryContent, PresentationContent, VideoScriptContent, Dict[str, Any]]
    source_references: List[SourceReference]
    retrieved_chunk_ids: List[str]
    retrieval_similarity_scores: List[float]
    retrieval_ranks: List[int]
    number_of_retrieved_chunks: int
    provider: str
    model: str
    generation_latency_ms: float
    token_usage: Optional[Dict[str, int]] = None
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
