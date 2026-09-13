import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("transformai.research")


class ResearchLogger:
    """
    Structured logger for document processing experiments and benchmarking telemetry.
    Saves metrics to research/results/pipeline_telemetry.jsonl.
    """

    def __init__(self, log_dir: str = "../research/results"):
        self.log_dir = Path(log_dir)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "pipeline_telemetry.jsonl"
        except Exception:
            # Fallback relative to current working directory
            self.log_dir = Path("research/results")
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "pipeline_telemetry.jsonl"

    def log_document_pipeline_run(
        self,
        document_id: str,
        filename: str,
        parser_used: str,
        chunking_strategy: str,
        total_chunks: int,
        chunk_sizes: list[int],
        processing_duration_sec: float,
        embedding_model: str,
        embedding_dimension: int,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records telemetry payload and appends to JSONL file."""
        avg_chunk_size = (
            round(sum(chunk_sizes) / len(chunk_sizes), 2) if chunk_sizes else 0
        )
        min_chunk_size = min(chunk_sizes) if chunk_sizes else 0
        max_chunk_size = max(chunk_sizes) if chunk_sizes else 0

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "document_id": document_id,
            "filename": filename,
            "parser_used": parser_used,
            "chunking_strategy": chunking_strategy,
            "number_of_chunks": total_chunks,
            "average_chunk_size_chars": avg_chunk_size,
            "min_chunk_size_chars": min_chunk_size,
            "max_chunk_size_chars": max_chunk_size,
            "processing_duration_sec": round(processing_duration_sec, 3),
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension,
            "success": error is None,
            "error": error,
        }

        logger.info("Pipeline Telemetry Recorded: %s", json.dumps(record))

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning("Could not write to research telemetry file: %s", e)

        return record


research_logger = ResearchLogger()
