from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_registry: dict[str, type[FileParser]] = {}


class FileParser(ABC):
    """Generic interface for parsing text from resume files."""

    def __init_subclass__(
        cls, *, extensions: tuple[str, ...] = (), **kwargs: object
    ) -> None:
        super().__init_subclass__(**kwargs)
        for ext in extensions:
            _registry[ext] = cls

    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Extract and return text content from the given file.

        Args:
            file_path: Path to the file to parse.

        Returns:
            Extracted text as a string.
        """
        ...

    @staticmethod
    def parse_resume(file_path: Path) -> str:
        """Select the appropriate parser based on file extension and return extracted content.

        Supported extensions are determined by the registered ``FileParser``
        subclasses (e.g. ``.pdf``, ``.docx``).

        Args:
            file_path: Path to the resume file.

        Returns:
            Extracted text as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not supported.
        """
        # Ensure subclasses are imported so they register themselves
        from src import pdf_parser, word_parser  # noqa: F401

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()
        parser_cls = _registry.get(suffix)
        if parser_cls is None:
            supported = ", ".join(sorted(_registry.keys()))
            raise ValueError(
                f"Unsupported file type: '{suffix}'. Supported types: {supported}"
            )
        return parser_cls().parse(file_path)
