from typing import Dict, Any
from app.services.generation.generators.base import BaseFormatGenerator
from app.services.generation.models import OutputType, ExecutiveSummaryContent
from app.services.retrieval.models import NormalizedContext


class ExecutiveSummaryGenerator(BaseFormatGenerator):
    """
    Generator for Executive Summary transformations.
    """

    @property
    def output_type(self) -> OutputType:
        return OutputType.EXECUTIVE_SUMMARY

    def get_json_schema_description(self) -> str:
        return """{
  "title": "String — Concise title for the executive summary",
  "overview": "String — High-level 2-3 sentence strategic overview grounded in source facts",
  "key_points": ["String — Bullet points summarizing core findings or topics"],
  "important_facts": ["String — Specific metrics, entities, and grounded factual statements"],
  "implications": ["String — Operational, strategic, or technical implications stated in the source"],
  "conclusion": "String — Concise concluding takeaway directly supported by the source"
}"""

    def parse_and_validate(
        self,
        raw_json: Dict[str, Any],
        context: NormalizedContext,
    ) -> ExecutiveSummaryContent:
        title = str(raw_json.get("title") or "Executive Summary")
        overview = str(raw_json.get("overview") or "")
        key_points = [str(p) for p in raw_json.get("key_points", []) if p]
        important_facts = [str(f) for f in raw_json.get("important_facts", []) if f]
        implications = [str(i) for i in raw_json.get("implications", []) if i]
        conclusion = str(raw_json.get("conclusion") or "")

        return ExecutiveSummaryContent(
            title=title,
            overview=overview,
            key_points=key_points,
            important_facts=important_facts,
            implications=implications,
            conclusion=conclusion,
            source_references=context.source_references,
        )
