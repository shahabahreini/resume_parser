from __future__ import annotations

import logging

from src.field_extractor import CombinedExtractor, FieldExtractor
from src.resume_data import ResumeData

logger = logging.getLogger(__name__)


class ResumeExtractor:
    """Coordinate a set of field extractors to build a :class:`ResumeData`.

    Args:
        field_extractors: Mapping of ``ResumeData`` field names
            (``"name"``, ``"email"``, ``"skills"``) to their corresponding
            :class:`FieldExtractor` instances.
        combined_extractor: Optional :class:`CombinedExtractor` that
            retrieves all fields in a single API call (recommended to
            stay within free-tier rate limits).
    """

    def __init__(
        self,
        field_extractors: dict[str, FieldExtractor] | None = None,
        combined_extractor: CombinedExtractor | None = None,
    ) -> None:
        if not field_extractors and not combined_extractor:
            raise ValueError("Provide either field_extractors or combined_extractor")
        self._extractors = field_extractors
        self._combined = combined_extractor

    def extract(self, resume_text: str) -> ResumeData:
        """Run every registered extractor and assemble a :class:`ResumeData`.

        Args:
            resume_text: Plain-text content of a parsed resume.

        Returns:
            A populated ``ResumeData`` instance.

        Raises:
            ValueError: If extraction or data assembly fails.
            ConnectionError: If the AI service is unreachable.
        """
        if self._combined:
            logger.info("Using combined extractor (single API call)")
            data = self._combined.extract(resume_text)
            logger.debug("Combined extraction returned keys: %s", list(data.keys()))
            try:
                return ResumeData(**data)
            except TypeError as exc:
                logger.error(
                    "Failed to build ResumeData from keys %s: %s",
                    list(data.keys()),
                    exc,
                )
                raise ValueError(
                    f"AI extraction returned unexpected data structure: {exc}"
                ) from exc

        logger.info("Using per-field extractors (%d fields)", len(self._extractors))
        results: dict[str, object] = {}
        errors: list[str] = []
        for field_name, extractor in self._extractors.items():
            logger.debug("Extracting field '%s'", field_name)
            try:
                results[field_name] = extractor.extract(resume_text)
            except Exception as exc:
                logger.error("Failed to extract field '%s': %s", field_name, exc)
                errors.append(f"{field_name}: {exc}")

        if errors:
            raise ValueError(
                f"Failed to extract {len(errors)} field(s):\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

        try:
            return ResumeData(**results)  # type: ignore[arg-type]
        except TypeError as exc:
            logger.error("Failed to build ResumeData: %s", exc)
            raise ValueError(
                f"Extracted data doesn't match expected resume structure: {exc}"
            ) from exc
