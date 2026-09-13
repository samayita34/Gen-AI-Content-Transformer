from typing import Dict
from app.services.generation.models import OutputType
from app.services.generation.generators.base import BaseFormatGenerator
from app.services.generation.generators.executive_summary import ExecutiveSummaryGenerator
from app.services.generation.generators.advisory import AdvisoryGenerator
from app.services.generation.generators.presentation import PresentationGenerator
from app.services.generation.generators.video_script import VideoScriptGenerator


class GenerationRouter:
    """
    Extensible registry resolving specialized format generators.
    """

    def __init__(self):
        self._generators: Dict[OutputType, BaseFormatGenerator] = {
            OutputType.EXECUTIVE_SUMMARY: ExecutiveSummaryGenerator(),
            OutputType.ADVISORY: AdvisoryGenerator(),
            OutputType.PRESENTATION: PresentationGenerator(),
            OutputType.VIDEO_SCRIPT: VideoScriptGenerator(),
        }

    def get_generator(self, output_type: OutputType) -> BaseFormatGenerator:
        generator = self._generators.get(output_type)
        if not generator:
            raise ValueError(f"No generator registered for output format '{output_type}'.")
        return generator

    def register_generator(self, generator: BaseFormatGenerator):
        self._generators[generator.output_type] = generator


default_generation_router = GenerationRouter()
