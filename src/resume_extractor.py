from __future__ import annotations

from src.field_extractor import CombinedExtractor, FieldExtractor
from src.resume_data import ResumeData


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
        """
        if self._combined:
            data = self._combined.extract(resume_text)
            return ResumeData(**data)

        results: dict[str, object] = {}
        for field_name, extractor in self._extractors.items():
            results[field_name] = extractor.extract(resume_text)
        return ResumeData(**results)  # type: ignore[arg-type]
