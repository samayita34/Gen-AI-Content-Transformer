"""
M7 Research Schemas: Reproducibility & Experiment Configurations
================================================================
Defines strict parameter contracts for experiment runs to guarantee reproducibility.
Never fabricates unexposed model/pipeline parameters.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MethodType(str, Enum):
    METHOD_A = "METHOD_A"  # Direct LLM Prompting
    METHOD_B = "METHOD_B"  # Basic RAG
    METHOD_C = "METHOD_C"  # RAG + Structured Context Normalization
    METHOD_D = "METHOD_D"  # RAG + Structured Context + Claim-Level Verification


class OutputFormat(str, Enum):
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    ADVISORY = "ADVISORY"
    PRESENTATION = "PRESENTATION"
    VIDEO_SCRIPT = "VIDEO_SCRIPT"


class LatencyBreakdown(BaseModel):
    retrieval_ms: Optional[float] = None
    normalization_ms: Optional[float] = None
    generation_ms: Optional[float] = None
    verification_ms: Optional[float] = None
    total_ms: float


class TokenUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChunkingConfigRecord(BaseModel):
    strategy: str
    chunk_size: int
    chunk_overlap: int


class RetrievalConfigRecord(BaseModel):
    embedding_model: str
    top_k: int
    similarity_threshold: float


class ContextNormalizationConfigRecord(BaseModel):
    enabled: bool
    fact_extraction: bool = True
    entity_resolution: bool = True
    citation_mapping: bool = True


class VerificationConfigRecord(BaseModel):
    enabled: bool
    judge_provider: Optional[str] = None
    judge_model: Optional[str] = None
    evidence_top_k: Optional[int] = None
    evidence_threshold: Optional[float] = None


class ReproducibilityMetadata(BaseModel):
    experiment_id: str
    run_number: int
    timestamp: str
    dataset_version: str
    is_development_fixture: bool
    source_document_id: str
    source_document_hash: str
    method: MethodType
    output_format: OutputFormat
    model_provider: str
    model_identifier: str
    model_configuration: Dict[str, Any] = Field(default_factory=dict)
    temperature: Optional[float] = None
    random_seed: Optional[int] = None
    chunking_configuration: Optional[ChunkingConfigRecord] = None
    retrieval_configuration: Optional[RetrievalConfigRecord] = None
    context_normalization_configuration: Optional[ContextNormalizationConfigRecord] = None
    verification_configuration: Optional[VerificationConfigRecord] = None
    latency: LatencyBreakdown
    token_usage: Optional[TokenUsage] = None
    raw_output_artifact_path: Optional[str] = None
    evaluation_artifact_path: Optional[str] = None


class ExperimentRun(BaseModel):
    reproducibility: ReproducibilityMetadata
    generated_content: Dict[str, Any]
    retrieved_chunk_indices: List[int] = Field(default_factory=list)
