from typing import Dict, Any
from app.services.generation.generators.base import BaseFormatGenerator
from app.services.generation.models import OutputType, AdvisoryContent
from app.services.retrieval.models import NormalizedContext


class AdvisoryGenerator(BaseFormatGenerator):
    """
    Generator for Advisory & Briefing transformations with explicit anti-fabrication constraints.
    """

    @property
    def output_type(self) -> OutputType:
        return OutputType.ADVISORY

    def get_json_schema_description(self) -> str:
        return """{
  "title": "String — Clear title for the advisory notice or briefing",
  "situation": "String — Objective statement of the current situation / context",
  "key_information": ["String — Vital factual details and context points from source"],
  "risks_or_considerations": ["String — Specific risks, challenges, or constraints identified in source"],
  "recommended_actions": ["String — Grounded actions explicitly mentioned in source. NOTE: If source contains no recommendations, return ['No specific recommendations are stated in the source document.']"],
  "important_notes": ["String — Operational caveats, dates, or technical boundaries"],
  "conclusion": "String — Final guidance or closing statement supported by source"
}"""

    def parse_and_validate(
        self,
        raw_json: Dict[str, Any],
        context: NormalizedContext,
    ) -> AdvisoryContent:
        title = str(raw_json.get("title") or "Advisory Briefing")
        situation = str(raw_json.get("situation") or "")
        key_info = [str(k) for k in raw_json.get("key_information", []) if k]
        risks = [str(r) for r in raw_json.get("risks_or_considerations", []) if r]
        recommended_actions = [str(a) for a in raw_json.get("recommended_actions", []) if a]
        if not recommended_actions:
            recommended_actions = ["No explicit recommendations are present in the source document."]
        important_notes = [str(n) for n in raw_json.get("important_notes", []) if n]
        conclusion = str(raw_json.get("conclusion") or "")

        return AdvisoryContent(
            title=title,
            situation=situation,
            key_information=key_info,
            risks_or_considerations=risks,
            recommended_actions=recommended_actions,
            important_notes=important_notes,
            conclusion=conclusion,
            source_references=context.source_references,
        )
