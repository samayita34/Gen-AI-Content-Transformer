import json
import time
import asyncio
from typing import Optional, Dict, Any

from app.services.generation.base import BaseLLMProvider, GenerationRequest, GenerationResponse


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider for automated testing and offline development.
    Produces valid schema-compliant JSON transformations without external API dependencies.
    """

    def __init__(self, model_name: str = "mock-transformer-v1"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        t0 = time.perf_counter()
        await asyncio.sleep(0.01)  # Simulate brief generation latency

        prompt_lower = request.prompt.lower()
        sys_lower = (request.system_instruction or "").lower()

        # Determine target output format
        if "advisory" in prompt_lower or "advisory" in sys_lower:
            payload = {
                "title": "Automated Advisory Briefing",
                "situation": "The organization requires a scalable, source-grounded approach to document transformation.",
                "key_information": [
                    "Document ingestion handles PDF, DOCX, and TXT formats with structural heading extraction.",
                    "Dense vector retrieval uses pgvector for database-side cosine distance ordering.",
                ],
                "risks_or_considerations": [
                    "Unnormalized source text can degrade retrieval precision.",
                    "LLM generation requires strict anti-fabrication prompt boundaries.",
                ],
                "recommended_actions": [
                    "Verify that vector dimensions match embedding model configurations across all deployments.",
                    "Ensure source provenance citations are attached to extracted factual units.",
                ],
                "important_notes": [
                    "Recommendations are derived strictly from documented operational constraints.",
                ],
                "conclusion": "Adopting structure-aware chunking and deterministic context normalization ensures consistent factual alignment.",
                "source_references": [],
            }

        elif "presentation" in prompt_lower or "slides" in prompt_lower or "presentation" in sys_lower:
            payload = {
                "presentation_title": "Source-Grounded Content Transformation",
                "slides": [
                    {
                        "slide_number": 1,
                        "title": "Platform Overview & Problem Statement",
                        "bullets": [
                            "Automates multi-format transformation from common source documents",
                            "Preserves factual consistency and semantic fidelity",
                            "Eliminates manual re-authoring overhead across communication tiers",
                        ],
                        "speaker_notes": "Welcome everyone. Today we are presenting the architecture of TransformAI, focusing on grounded content generation.",
                        "source_references": [],
                    },
                    {
                        "slide_number": 2,
                        "title": "System Architecture & Retrieval Tier",
                        "bullets": [
                            "Decoupled parsing for PDF, DOCX, and TXT materials",
                            "Local dense embeddings with pgvector indexing",
                            "Deterministic context normalization without generative hallucination",
                        ],
                        "speaker_notes": "The ingestion and retrieval tiers guarantee that all downstream generation is anchored in verified source passages.",
                        "source_references": [],
                    },
                    {
                        "slide_number": 3,
                        "title": "Summary & Strategic Roadmap",
                        "bullets": [
                            "Milestones 1-3 established infrastructure and retrieval grounding",
                            "Milestone 4 introduces multi-format generative synthesis",
                            "Future milestones will implement automated verification and empirical benchmarks",
                        ],
                        "speaker_notes": "In conclusion, our research provides a modular foundation for trustworthy generative AI.",
                        "source_references": [],
                    },
                ],
            }

        elif "video" in prompt_lower or "storyboard" in prompt_lower or "video_script" in sys_lower:
            payload = {
                "title": "TransformAI System Walkthrough",
                "target_duration": "90 seconds",
                "scenes": [
                    {
                        "scene_number": 1,
                        "visual_description": "Wide shot of a clean technical dashboard showing live PostgreSQL and Redis telemetry indicators.",
                        "narration": "In an era of information overload, transforming complex technical documents into clear executive summaries is critical.",
                        "on_screen_text": "TransformAI: Automated Content Transformation",
                        "source_references": [],
                    },
                    {
                        "scene_number": 2,
                        "visual_description": "Animated diagram illustrating document ingestion flowing through structure-aware chunking and pgvector search.",
                        "narration": "Our platform preserves heading hierarchies, extracts dense embeddings, and queries vector similarity directly in PostgreSQL.",
                        "on_screen_text": "Dense Vector Retrieval (pgvector)",
                        "source_references": [],
                    },
                    {
                        "scene_number": 3,
                        "visual_description": "Split screen demonstrating simultaneous synthesis of Executive Summaries, Advisories, Presentations, and Video Scripts.",
                        "narration": "Every output is strictly anchored in source evidence, ensuring transparent provenance from source to screen.",
                        "on_screen_text": "100% Source-Grounded Synthesis",
                        "source_references": [],
                    },
                ],
            }

        else:
            # Default: Executive Summary
            payload = {
                "title": "Executive Summary: Content Transformation Platform",
                "overview": "The TransformAI platform provides an automated architecture for converting technical source documents into structured communication formats.",
                "key_points": [
                    "Supports native document ingestion across PDF, DOCX, and TXT formats.",
                    "Employs structure-aware semantic chunking and 384-dimensional dense vector retrieval.",
                    "Provides deterministic context normalization to ensure high-fidelity source grounding.",
                ],
                "important_facts": [
                    "Vector similarity search uses cosine distance in pgvector.",
                    "All generation pipelines preserve document, page, and chunk provenance citations.",
                ],
                "implications": [
                    "Significantly reduces manual authoring effort for executive briefings and presentations.",
                    "Enables scalable multi-format content distribution without compromising factual integrity.",
                ],
                "conclusion": "TransformAI establishes a modular, research-driven foundation for reliable generative document transformation.",
                "source_references": [],
            }

        latency_ms = (time.perf_counter() - t0) * 1000
        content_str = json.dumps(payload, indent=2)

        return GenerationResponse(
            content=content_str,
            model_name=self._model_name,
            provider_name=self.provider_name,
            finish_reason="stop",
            usage={
                "prompt_tokens": len(request.prompt.split()) * 2,
                "completion_tokens": len(content_str.split()) * 2,
                "total_tokens": len(request.prompt.split()) * 2 + len(content_str.split()) * 2,
            },
            latency_ms=round(latency_ms, 2),
        )
