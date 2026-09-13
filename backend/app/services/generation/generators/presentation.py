from typing import Dict, Any, List
from app.services.generation.generators.base import BaseFormatGenerator
from app.services.generation.models import OutputType, PresentationContent, SlideItem
from app.services.retrieval.models import NormalizedContext, SourceReference


class PresentationGenerator(BaseFormatGenerator):
    """
    Generator for Presentation Deck and Speaker Notes transformations.
    """

    @property
    def output_type(self) -> OutputType:
        return OutputType.PRESENTATION

    def get_json_schema_description(self) -> str:
        return """{
  "presentation_title": "String — Overarching presentation deck title",
  "slides": [
    {
      "slide_number": 1,
      "title": "String — Slide title",
      "bullets": ["String — 3 to 5 clear, source-grounded bullet points"],
      "speaker_notes": "String — Comprehensive spoken narrative script for the presenter grounded in source facts"
    }
  ]
}"""

    def parse_and_validate(
        self,
        raw_json: Dict[str, Any],
        context: NormalizedContext,
    ) -> PresentationContent:
        pres_title = str(raw_json.get("presentation_title") or "Source Presentation")
        raw_slides = raw_json.get("slides", [])

        slides: List[SlideItem] = []
        for idx, s in enumerate(raw_slides, 1):
            slide_num = int(s.get("slide_number") or idx)
            title = str(s.get("title") or f"Slide {slide_num}")
            bullets = [str(b) for b in s.get("bullets", []) if b]
            speaker_notes = str(s.get("speaker_notes") or "")

            # Attach appropriate source reference (fallback to global context refs)
            slide_refs = context.source_references

            slides.append(
                SlideItem(
                    slide_number=slide_num,
                    title=title,
                    bullets=bullets,
                    speaker_notes=speaker_notes,
                    source_references=slide_refs,
                )
            )

        if not slides:
            # Fallback single slide if model returned empty array
            slides.append(
                SlideItem(
                    slide_number=1,
                    title="Source Overview",
                    bullets=["Source content synthesized into presentation format."],
                    speaker_notes="Overview slide generated from retrieved source material.",
                    source_references=context.source_references,
                )
            )

        return PresentationContent(
            presentation_title=pres_title,
            slides=slides,
        )
