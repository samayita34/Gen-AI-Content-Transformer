from typing import Dict, Any, List
from app.services.generation.generators.base import BaseFormatGenerator
from app.services.generation.models import OutputType, VideoScriptContent, SceneItem
from app.services.retrieval.models import NormalizedContext


class VideoScriptGenerator(BaseFormatGenerator):
    """
    Generator for Video Script and Storyboard transformations.
    """

    @property
    def output_type(self) -> OutputType:
        return OutputType.VIDEO_SCRIPT

    def get_json_schema_description(self) -> str:
        return """{
  "title": "String — Compelling video script title",
  "target_duration": "String — Estimated runtime (e.g. '60 seconds', '2 minutes')",
  "scenes": [
    {
      "scene_number": 1,
      "visual_description": "String — Visual direction describing animations, charts, or visual framing of source facts",
      "narration": "String — Spoken voiceover script communicating source facts clearly",
      "on_screen_text": "String — Key takeaways, metrics, or title cards displayed on screen"
    }
  ]
}"""

    def parse_and_validate(
        self,
        raw_json: Dict[str, Any],
        context: NormalizedContext,
    ) -> VideoScriptContent:
        title = str(raw_json.get("title") or "Video Script & Storyboard")
        target_duration = str(raw_json.get("target_duration") or "60 seconds")
        raw_scenes = raw_json.get("scenes", [])

        scenes: List[SceneItem] = []
        for idx, sc in enumerate(raw_scenes, 1):
            scene_num = int(sc.get("scene_number") or idx)
            visual_desc = str(sc.get("visual_description") or "")
            narration = str(sc.get("narration") or "")
            on_screen_text = str(sc.get("on_screen_text") or "")

            scenes.append(
                SceneItem(
                    scene_number=scene_num,
                    visual_description=visual_desc,
                    narration=narration,
                    on_screen_text=on_screen_text,
                    source_references=context.source_references,
                )
            )

        if not scenes:
            scenes.append(
                SceneItem(
                    scene_number=1,
                    visual_description="Opening title card displaying document overview.",
                    narration="Welcome to this summary briefing.",
                    on_screen_text=title,
                    source_references=context.source_references,
                )
            )

        return VideoScriptContent(
            title=title,
            target_duration=target_duration,
            scenes=scenes,
        )
