import logging
from pathlib import Path

import pymupdf

from src.file_parser import FileParser

logger = logging.getLogger(__name__)


class PDFParser(FileParser, extensions=(".pdf",)):
    """Extracts text from PDF resume files."""

    def parse(self, file_path: Path) -> str:
        """Extract text from a PDF file using PyMuPDF.

        Raises:
            PermissionError: If the PDF is encrypted/password-protected.
            RuntimeError: If the PDF is corrupt or cannot be read.
        """
        try:
            doc = pymupdf.open(file_path)
        except Exception as exc:
            logger.error("Failed to open PDF '%s': %s", file_path.name, exc)
            raise RuntimeError(
                f"Cannot open '{file_path.name}': the file may be corrupt "
                f"or not a valid PDF."
            ) from exc

        try:
            if doc.is_encrypted:
                logger.error("PDF '%s' is encrypted/password-protected", file_path.name)
                raise PermissionError(
                    f"'{file_path.name}' is encrypted or password-protected. "
                    f"Please provide an unlocked PDF."
                )

            page_count = len(doc)
            logger.debug("PDF has %d page(s)", page_count)

            if page_count == 0:
                logger.warning("PDF '%s' has 0 pages", file_path.name)
                return ""

            text_parts: list[str] = []
            for page_num, page in enumerate(doc, start=1):
                try:
                    page_text = str(page.get_text("text"))
                    text_parts.append(page_text)
                except Exception as exc:
                    logger.warning(
                        "Failed to extract text from page %d of '%s': %s",
                        page_num,
                        file_path.name,
                        exc,
                    )
                    # Continue with remaining pages instead of failing entirely

            result = "\n".join(text_parts).strip()
            logger.debug("Extracted %d characters from PDF", len(result))
            return result
        finally:
            doc.close()
