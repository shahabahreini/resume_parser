from pathlib import Path

import pymupdf

from src.file_parser import FileParser


class PDFParser(FileParser, extensions=(".pdf",)):
    """Extracts text from PDF resume files."""

    def parse(self, file_path: Path) -> str:
        """Extract text from a PDF file using PyMuPDF."""
        text_parts: list[str] = []
        with pymupdf.open(file_path) as doc:
            for page in doc:
                text_parts.append(str(page.get_text("text")))
        return "\n".join(text_parts).strip()
