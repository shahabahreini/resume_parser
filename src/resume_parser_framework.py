from __future__ import annotations

from pathlib import Path

from src.file_parser import FileParser
from src.resume_data import ResumeData
from src.resume_extractor import ResumeExtractor


class ResumeParserFramework:
    """High-level facade that combines file parsing with resume extraction.

    Args:
        extractor: A :class:`ResumeExtractor` configured with the desired
            field extractors.
    """

    def __init__(self, extractor: ResumeExtractor) -> None:
        self._extractor = extractor

    def parse_resume(self, file_path: str) -> ResumeData:
        """Parse a resume file and return structured data.

        Uses :meth:`FileParser.parse_resume` to extract raw text
        (selecting the correct parser via the file extension registry),
        then delegates to the :class:`ResumeExtractor` to produce a
        :class:`ResumeData` instance.

        Args:
            file_path: Path to a resume file (``.pdf`` or ``.docx``).

        Returns:
            A populated ``ResumeData`` instance.
        """
        text = FileParser.parse_resume(Path(file_path))
        return self._extractor.extract(text)
