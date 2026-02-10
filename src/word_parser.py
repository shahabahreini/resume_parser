from pathlib import Path

from docx import Document

from src.file_parser import FileParser


class WordParser(FileParser, extensions=(".docx",)):
    """Extracts text from Word (.docx) resume files."""

    def parse(self, file_path: Path) -> str:
        doc = Document(str(file_path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
