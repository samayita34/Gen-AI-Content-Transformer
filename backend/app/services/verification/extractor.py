import re
import uuid
from typing import List, Dict, Any, Union
from app.services.verification.models import AtomicClaim, ClaimType


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


class ClaimExtractor:
    """
    Deconstructs multi-format generated outputs into discrete atomic factual claims.
    """

    @classmethod
    def extract_from_text(cls, text: str, source_field: str = "text") -> List[AtomicClaim]:
        """Extracts atomic claims from a block of prose text."""
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
                    statement=clean_s,
                    claim_type=_classify_claim_type(clean_s),
                    context_source_field=source_field,
                    normalized_statement=clean_s,
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
            return cls.extract_from_text(str(content), "raw_content")

        if output_type == "executive_summary":
            if "overview" in data and isinstance(data["overview"], str):
                claims.extend(cls.extract_from_text(data["overview"], "overview"))

            for idx, kp in enumerate(data.get("key_points", [])):
                claims.extend(cls.extract_from_text(str(kp), f"key_points[{idx}]"))

            for idx, fact in enumerate(data.get("important_facts", [])):
                claims.extend(cls.extract_from_text(str(fact), f"important_facts[{idx}]"))

            for idx, imp in enumerate(data.get("implications", [])):
                claims.extend(cls.extract_from_text(str(imp), f"implications[{idx}]"))

            if "conclusion" in data and isinstance(data["conclusion"], str):
                claims.extend(cls.extract_from_text(data["conclusion"], "conclusion"))

        elif output_type == "advisory":
            if "situation" in data and isinstance(data["situation"], str):
                claims.extend(cls.extract_from_text(data["situation"], "situation"))

            for idx, info in enumerate(data.get("key_information", [])):
                claims.extend(cls.extract_from_text(str(info), f"key_information[{idx}]"))

            for idx, risk in enumerate(data.get("risks_or_considerations", [])):
                claims.extend(cls.extract_from_text(str(risk), f"risks_or_considerations[{idx}]"))

            for idx, action in enumerate(data.get("recommended_actions", [])):
                claims.extend(cls.extract_from_text(str(action), f"recommended_actions[{idx}]"))

            for idx, note in enumerate(data.get("important_notes", [])):
                claims.extend(cls.extract_from_text(str(note), f"important_notes[{idx}]"))

            if "conclusion" in data and isinstance(data["conclusion"], str):
                claims.extend(cls.extract_from_text(data["conclusion"], "conclusion"))

        elif output_type == "presentation":
            slides = data.get("slides", [])
            for s_idx, slide in enumerate(slides):
                s_data = slide.__dict__ if hasattr(slide, "__dict__") else slide
                bullets = s_data.get("bullets", [])
                for b_idx, bullet in enumerate(bullets):
                    claims.extend(cls.extract_from_text(str(bullet), f"slides[{s_idx}].bullets[{b_idx}]"))

                notes = s_data.get("speaker_notes", "")
                if notes:
                    claims.extend(cls.extract_from_text(str(notes), f"slides[{s_idx}].speaker_notes"))

        elif output_type == "video_script":
            scenes = data.get("scenes", [])
            for sc_idx, scene in enumerate(scenes):
                sc_data = scene.__dict__ if hasattr(scene, "__dict__") else scene
                vo = sc_data.get("voiceover", "")
                if vo:
                    claims.extend(cls.extract_from_text(str(vo), f"scenes[{sc_idx}].voiceover"))

                ost = sc_data.get("on_screen_text", "")
                if ost:
                    claims.extend(cls.extract_from_text(str(ost), f"scenes[{sc_idx}].on_screen_text"))

                vd = sc_data.get("visual_description", "")
                if vd:
                    claims.extend(cls.extract_from_text(str(vd), f"scenes[{sc_idx}].visual_description"))

        else:
            # Fallback recursive sweep of string fields
            for k, v in data.items():
                if isinstance(v, str) and len(v.strip()) > 10:
                    claims.extend(cls.extract_from_text(v, k))
                elif isinstance(v, list):
                    for idx, item in enumerate(v):
                        if isinstance(item, str):
                            claims.extend(cls.extract_from_text(item, f"{k}[{idx}]"))

        return claims
