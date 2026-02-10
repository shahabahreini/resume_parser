from __future__ import annotations

from src.field_extractor import FieldExtractor
from src.resume_data import ResumeData


class ResumeExtractor:
    """Coordinate a set of field extractors to build a :class:`ResumeData`.

    Args:
        field_extractors: Mapping of ``ResumeData`` field names
            (``"name"``, ``"email"``, ``"skills"``) to their corresponding
            :class:`FieldExtractor` instances.
    """

    def __init__(self, field_extractors: dict[str, FieldExtractor]) -> None:
        self._extractors = field_extractors

    def extract(self, resume_text: str) -> ResumeData:
        """Run every registered extractor and assemble a :class:`ResumeData`.

        Args:
            resume_text: Plain-text content of a parsed resume.

        Returns:
            A populated ``ResumeData`` instance.
        """
        results: dict[str, object] = {}
        for field_name, extractor in self._extractors.items():
            results[field_name] = extractor.extract(resume_text)
        return ResumeData(**results)  # type: ignore[arg-type]
