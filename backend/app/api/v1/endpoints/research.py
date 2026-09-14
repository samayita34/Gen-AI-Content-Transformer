import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("transformai.api.research")
router = APIRouter()

# Path to processed evaluation summary
RESEARCH_SUMMARY_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "research" / "results" / "processed" / "m7_evaluation_summary.json"


class ResearchSummaryResponse(BaseModel):
    is_available: bool
    is_development_fixture: bool
    fixture_disclaimer: Optional[str] = None
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None


@router.get(
    "/summary",
    response_model=ResearchSummaryResponse,
    summary="Get M7 Research Evaluation Summary",
    description=(
        "Returns the processed quantitative research benchmark summary. "
        "Explicitly marks development fixtures with 'DEVELOPMENT FIXTURE — NOT RESEARCH RESULT'. "
        "If no results exist, returns 'No evaluation results available yet.'"
    ),
)
async def get_research_summary() -> ResearchSummaryResponse:
    if not RESEARCH_SUMMARY_PATH.exists():
        return ResearchSummaryResponse(
            is_available=False,
            is_development_fixture=False,
            fixture_disclaimer=None,
            message="No evaluation results available yet.",
            summary=None,
        )

    try:
        with open(RESEARCH_SUMMARY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("benchmark_metadata", {})
        is_fixture = bool(meta.get("is_development_fixture", False))
        disclaimer = meta.get(
            "fixture_disclaimer",
            "DEVELOPMENT FIXTURE — NOT RESEARCH RESULT. Used solely for validating M7 pipeline logic, schemas, and metric calculations."
        ) if is_fixture else None

        return ResearchSummaryResponse(
            is_available=True,
            is_development_fixture=is_fixture,
            fixture_disclaimer=disclaimer,
            message=None,
            summary=data,
        )
    except Exception as exc:
        logger.error("Failed to read research summary from %s: %s", RESEARCH_SUMMARY_PATH, exc)
        return ResearchSummaryResponse(
            is_available=False,
            is_development_fixture=False,
            fixture_disclaimer=None,
            message=f"Error reading evaluation results: {str(exc)}",
            summary=None,
        )
