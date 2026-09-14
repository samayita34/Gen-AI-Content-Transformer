import uuid
import threading
import logging
from typing import Optional, Dict, Any
from collections import OrderedDict

from app.services.generation.models import TransformationResult
from app.services.verification.models import VerificationReport

logger = logging.getLogger("transformai.generation.store")


class TransformationResultStore:
    """
    Thread-safe in-memory cache holding recent TransformationResult objects
    and associated VerificationReports by transformation_id.
    Ensures server-authoritative export and verification resolution without
    requiring unnecessary database migration overhead.
    """

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self._lock = threading.Lock()
        self._results: OrderedDict[str, TransformationResult] = OrderedDict()
        self._reports: Dict[str, VerificationReport] = {}

    def save_result(self, result: TransformationResult) -> None:
        """Stores a TransformationResult, maintaining LRU bounds."""
        key = str(result.transformation_id)
        with self._lock:
            if key in self._results:
                self._results.move_to_end(key)
            self._results[key] = result
            if len(self._results) > self.max_size:
                oldest_key, _ = self._results.popitem(last=False)
                self._reports.pop(oldest_key, None)
        logger.debug("Stored transformation result %s (total cached: %d)", key, len(self._results))

    def get_result(self, transformation_id: str | uuid.UUID) -> Optional[TransformationResult]:
        """Retrieves a cached TransformationResult by ID."""
        key = str(transformation_id)
        with self._lock:
            if key in self._results:
                self._results.move_to_end(key)
                return self._results[key]
        return None

    def attach_verification_report(
        self, transformation_id: str | uuid.UUID, report: VerificationReport
    ) -> None:
        """Attaches a VerificationReport to an existing transformation result."""
        key = str(transformation_id)
        with self._lock:
            self._reports[key] = report
        logger.debug("Attached verification report %s to transformation %s", report.report_id, key)

    def get_verification_report(
        self, transformation_id: str | uuid.UUID
    ) -> Optional[VerificationReport]:
        """Retrieves the VerificationReport associated with a transformation ID."""
        key = str(transformation_id)
        with self._lock:
            return self._reports.get(key)

    def clear(self) -> None:
        """Clears all cached results and reports (used in tests)."""
        with self._lock:
            self._results.clear()
            self._reports.clear()


# Global singleton instance
default_result_store = TransformationResultStore()
