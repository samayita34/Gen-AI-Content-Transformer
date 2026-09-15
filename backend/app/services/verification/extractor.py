import re
import json
import uuid
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.services.generation.base import BaseLLMProvider, GenerationRequest
from app.services.generation.providers.factory import get_llm_provider
from app.services.verification.models import AtomicClaim, ClaimType

logger = logging.getLogger("transformai.verification.extractor")

# Regex patterns for splitting compound sentences & identifying claim types
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+|\n+")
STATISTICAL_PATTERN = re.compile(r"\b\d+(?:\.\d+)?(?:\s*(?:%|percent|ms|s|seconds|MB|GB|TB|users|dimensions|dim|kg|km|m))\b", re.IGNORECASE)
ATTRIBUTION_PATTERN = re.compile(r"\b(?:according to|stated by|authored by|reported by|by)\b", re.IGNORECASE)


def _clean_statement(text: str) -> str:
    """Strips bullet markers, markdown formatting, and extra whitespace."""
    text = re.sub(r"^[\s*\-•\d.]+", "", text)
    text = re.sub(r"[*_`#]", "", text)
    return text.strip()


def _classify_claim_type(statement: str) -> ClaimType:
    """Classifies atomic claim based on lexical features."""
    if STATISTICAL_PATTERN.search(statement):
        return ClaimType.STATISTICAL
    if ATTRIBUTION_PATTERN.search(statement):
        return ClaimType.ATTRIBUTIONAL
    if any(w in statement.lower() for w in ["implies", "suggests", "consequently", "therefore", "indicates"]):
        return ClaimType.IMPLICATION
    return ClaimType.FACTUAL


def _clean_json(text: str) -> str:
    """Extracts clean JSON substring from LLM response fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class LLMExtractedClaimItem(BaseModel):
    """Pydantic validation schema for individual LLM extracted claims."""
    text: str
    normalized_text: Optional[str] = None
    claim_type: Optional[str] = "factual"
    source_output_reference: Optional[str] = None
    extraction_confidence: Optional[float] = None


class LLMExtractionResponse(BaseModel):
    """Pydantic validation schema for the LLM extraction payload."""
    claims: List[LLMExtractedClaimItem] = Field(default_factory=list)


class BaseClaimExtractor(ABC):
    """
    Abstract Base Class for claim extraction providers.
    Deconstructs multi-format generated outputs into discrete atomic factual claims.
    """

    @property
    @abstractmethod
    def extractor_name(self) -> str:
        """Identifier for the extractor provider."""
        pass

    @abstractmethod
    async def extract_claims(self, content: Any, output_type: str) -> List[AtomicClaim]:
        """
        Extracts structured atomic claims from generated content.
        
        Args:
            content: Generated transformation output (dict, Pydantic model, or raw text).
            output_type: Format ('executive_summary', 'advisory', 'presentation', 'video_script').
            
        Returns:
            List[AtomicClaim]
        """
        pass


class MockClaimExtractor(BaseClaimExtractor):
    """
    Deterministic rule-based claim extractor for testing and offline execution.
    Deconstructs text and structured multi-format transformations deterministically.
    """

    @property
    def extractor_name(self) -> str:
        return "mock_rule_based_extractor"

    @classmethod
    def extract_from_text(cls, text: str, source_field: str = "text", output_type: str = "text") -> List[AtomicClaim]:
        """Extracts atomic claims deterministically from a block of prose text."""
        claims: List[AtomicClaim] = []
        if not text or not text.strip():
            return claims

        raw_sentences = SENTENCE_SPLIT_REGEX.split(text.strip())
        for s in raw_sentences:
            clean_s = _clean_statement(s)
            if len(clean_s) < 8:
                continue

            claims.append(
                AtomicClaim(
                    claim_id=uuid.uuid4(),
                    text=clean_s,
                    normalized_text=clean_s,
                    output_format=output_type,
                    source_output_reference=source_field,
                    claim_type=_classify_claim_type(clean_s),
                    extraction_confidence=None,  # Do not invent confidence values
                )
            )
        return claims

    @classmethod
    def extract_from_transformation(cls, content: Any, output_type: str) -> List[AtomicClaim]:
        """
        Deconstructs any generated transformation object or dict into atomic claims.
        """
        claims: List[AtomicClaim] = []

        # Convert dict or object to accessible mapping
        if hasattr(content, "__dict__"):
            data = content.__dict__
        elif isinstance(content, dict):
            data = content
        else:
            return cls.extract_from_text(str(content), "raw_content", output_type)

        if output_type == "executive_summary":
            if "overview" in data and isinstance(data["overview"], str):
                claims.extend(cls.extract_from_text(data["overview"], "overview", output_type))

            for idx, kp in enumerate(data.get("key_points", [])):
                claims.extend(cls.extract_from_text(str(kp), f"key_points[{idx}]", output_type))

            for idx, fact in enumerate(data.get("important_facts", [])):
                claims.extend(cls.extract_from_text(str(fact), f"important_facts[{idx}]", output_type))

            for idx, imp in enumerate(data.get("implications", [])):
                claims.extend(cls.extract_from_text(str(imp), f"implications[{idx}]", output_type))

            if "conclusion" in data and isinstance(data["conclusion"], str):
                claims.extend(cls.extract_from_text(data["conclusion"], "conclusion", output_type))

        elif output_type == "advisory":
            if "situation" in data and isinstance(data["situation"], str):
                claims.extend(cls.extract_from_text(data["situation"], "situation", output_type))

            for idx, info in enumerate(data.get("key_information", [])):
                claims.extend(cls.extract_from_text(str(info), f"key_information[{idx}]", output_type))

            for idx, risk in enumerate(data.get("risks_or_considerations", [])):
                claims.extend(cls.extract_from_text(str(risk), f"risks_or_considerations[{idx}]", output_type))

            for idx, action in enumerate(data.get("recommended_actions", [])):
                claims.extend(cls.extract_from_text(str(action), f"recommended_actions[{idx}]", output_type))

            for idx, note in enumerate(data.get("important_notes", [])):
                claims.extend(cls.extract_from_text(str(note), f"important_notes[{idx}]", output_type))

            if "conclusion" in data and isinstance(data["conclusion"], str):
                claims.extend(cls.extract_from_text(data["conclusion"], "conclusion", output_type))

        elif output_type == "presentation":
            slides = data.get("slides", [])
            for s_idx, slide in enumerate(slides):
                s_data = slide.__dict__ if hasattr(slide, "__dict__") else slide
                bullets = s_data.get("bullets", [])
                for b_idx, bullet in enumerate(bullets):
                    claims.extend(cls.extract_from_text(str(bullet), f"slides[{s_idx}].bullets[{b_idx}]", output_type))

                notes = s_data.get("speaker_notes", "")
                if notes:
                    claims.extend(cls.extract_from_text(str(notes), f"slides[{s_idx}].speaker_notes", output_type))

        elif output_type == "video_script":
            scenes = data.get("scenes", [])
            for sc_idx, scene in enumerate(scenes):
                sc_data = scene.__dict__ if hasattr(scene, "__dict__") else scene
                vo = sc_data.get("voiceover", "")
                if vo:
                    claims.extend(cls.extract_from_text(str(vo), f"scenes[{sc_idx}].voiceover", output_type))

                ost = sc_data.get("on_screen_text", "")
                if ost:
                    claims.extend(cls.extract_from_text(str(ost), f"scenes[{sc_idx}].on_screen_text", output_type))

                vd = sc_data.get("visual_description", "")
                if vd:
                    claims.extend(cls.extract_from_text(str(vd), f"scenes[{sc_idx}].visual_description", output_type))

        else:
            # Fallback recursive sweep of string fields
            for k, v in data.items():
                if isinstance(v, str) and len(v.strip()) > 10:
                    claims.extend(cls.extract_from_text(v, k, output_type))
                elif isinstance(v, list):
                    for idx, item in enumerate(v):
                        if isinstance(item, str):
                            claims.extend(cls.extract_from_text(item, f"{k}[{idx}]", output_type))

        return claims

    async def extract_claims(self, content: Any, output_type: str) -> List[AtomicClaim]:
        """Asynchronously extracts claims using deterministic rule-based logic."""
        return self.extract_from_transformation(content, output_type)


class LLMClaimExtractor(BaseClaimExtractor):
    """
    LLM-powered atomic claim extractor.
    Prompts an LLM to deconstruct complex prose into atomic testable propositions,
    validating output strictly with Pydantic.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self._llm_provider = llm_provider

    @property
    def extractor_name(self) -> str:
        return f"llm_claim_extractor_{settings.VERIFICATION_MODEL}"

    @property
    def llm_provider(self) -> BaseLLMProvider:
        return self._llm_provider or get_llm_provider()

    async def extract_claims(self, content: Any, output_type: str) -> List[AtomicClaim]:
        """
        Extracts claims using LLM with structured JSON output and Pydantic validation.
        """
        # Format payload as readable string for prompt
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, indent=2)
        elif hasattr(content, "__dict__"):
            content_str = json.dumps(content.__dict__, indent=2, default=str)
        else:
            content_str = str(content)

        system_instruction = """You are a rigorous Fact Extraction Assistant.
Your task is to decompose the provided generated content into discrete, testable atomic claims.

RULES:
1. Break down compound statements into single factual assertions.
2. Preserve numbers, dates, named entities, and explicit claims verbatim.
3. For each claim, provide:
   - "text": The exact or atomic claim statement.
   - "normalized_text": A clean, self-contained search query statement.
   - "claim_type": "factual" | "statistical" | "attributional" | "implication".
   - "source_output_reference": Where in the content this claim came from (e.g., "overview", "slide 1", "key_points[0]").
   - "extraction_confidence": A float between 0.0 and 1.0 representing extraction confidence, or null if unavailable.
4. Do NOT invent or add external facts that are not present in the generated content.
5. Return ONLY a valid JSON object matching the requested schema."""

        prompt = f"""DECONSTRUCT THE FOLLOWING '{output_type.upper()}' GENERATED OUTPUT INTO ATOMIC CLAIMS:

<GENERATED_CONTENT>
{content_str}
</GENERATED_CONTENT>

Respond ONLY with valid JSON in this exact structure:
{{
  "claims": [
    {{
      "text": "The platform uses pgvector for similarity search.",
      "normalized_text": "TransformAI uses pgvector for vector similarity search",
      "claim_type": "factual",
      "source_output_reference": "overview",
      "extraction_confidence": 0.95
    }}
  ]
}}"""

        req = GenerationRequest(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.0,
            response_format_json=True,
            timeout_seconds=settings.VERIFICATION_TIMEOUT_SECONDS,
        )

        try:
            resp = await self.llm_provider.generate(req)
            raw_payload = resp.content if hasattr(resp, "content") else getattr(resp, "text", str(resp))
            clean_text = _clean_json(raw_payload)
            parsed_data = json.loads(clean_text)
            validated = LLMExtractionResponse.model_validate(parsed_data)

            extracted_claims: List[AtomicClaim] = []
            for item in validated.claims:
                claim_type_enum = ClaimType.FACTUAL
                if item.claim_type:
                    try:
                        claim_type_enum = ClaimType(item.claim_type.lower())
                    except ValueError:
                        claim_type_enum = ClaimType.FACTUAL

                # Only include extraction_confidence if actually supplied and within [0, 1]
                conf = None
                if item.extraction_confidence is not None and 0.0 <= item.extraction_confidence <= 1.0:
                    conf = item.extraction_confidence

                extracted_claims.append(
                    AtomicClaim(
                        claim_id=uuid.uuid4(),
                        text=item.text,
                        normalized_text=item.normalized_text or item.text,
                        output_format=output_type,
                        source_output_reference=item.source_output_reference,
                        claim_type=claim_type_enum,
                        extraction_confidence=conf,
                    )
                )

            return extracted_claims

        except (json.JSONDecodeError, ValidationError) as ve:
            logger.error("Failed to parse/validate LLM claim extraction response: %s", ve)
            logger.warning("Falling back to deterministic rule-based extractor.")
            return MockClaimExtractor.extract_from_transformation(content, output_type)
        except Exception as e:
            logger.error("LLM claim extraction encountered an error: %s", e)
            logger.warning("Falling back to deterministic rule-based extractor.")
            return MockClaimExtractor.extract_from_transformation(content, output_type)


# Backward-compatible alias for existing codebase and tests
ClaimExtractor = MockClaimExtractor


def get_claim_extractor(provider_type: Optional[str] = None) -> BaseClaimExtractor:
    """
    Factory function for obtaining a claim extractor instance.
    """
    provider = provider_type or settings.VERIFICATION_PROVIDER
    if provider.lower() in ("llm", "gemini", "openai", "openai_compatible", "ollama", "cloud") and not getattr(settings, "TESTING", False):
        return LLMClaimExtractor()
    return MockClaimExtractor()
