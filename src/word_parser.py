import re
import zipfile
from pathlib import Path

from docx import Document

from src.file_parser import FileParser


class WordParser(FileParser, extensions=(".docx",)):
    """Extracts text from Word (.docx) resume files."""

    def parse(self, file_path: Path) -> str:
        # Try the standard python-docx approach first (paragraphs + tables)
        doc = Document(str(file_path))
        parts: list[str] = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                parts.append(text)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        text = paragraph.text.strip()
                        if text:
                            parts.append(text)

        if parts:
            return "\n".join(parts)

        # Fallback: some templates use structured document tags (w:sdt)
        # that python-docx doesn't expose.  Extract all <w:t> text from
        # the raw XML inside the .docx zip.
        return self._extract_from_xml(file_path)

    @staticmethod
    def _extract_from_xml(file_path: Path) -> str:
        """Extract text directly from the document.xml inside the .docx zip."""
        with zipfile.ZipFile(file_path) as zf:
            xml_bytes = zf.read("word/document.xml")
        xml_text = xml_bytes.decode("utf-8")
        fragments = re.findall(r"<w:t[^>]*>([^<]+)</w:t>", xml_text)
        return " ".join(fragments)
