from __future__ import annotations

import logging
import string
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_RESUME_KEYWORDS: list[str] = [
    "experience",
    "education",
    "skills",
    "summary",
    "projects",
]

_MIN_TEXT_LENGTH = 200
_MIN_PRINTABLE_RATIO = 0.8


@dataclass
class VerificationResult:
    """Outcome of a text-quality verification check."""

    is_empty: bool = False
    too_short: bool = False
    missing_keywords: bool = False
    garbage_ratio_low: bool = False

    @property
    def passed(self) -> bool:
        """Return ``True`` when none of the failure flags are set."""
        return not (
            self.is_empty
            or self.too_short
            or self.missing_keywords
            or self.garbage_ratio_low
        )

    @property
    def issues(self) -> list[str]:
        """Human-readable list of detected issues."""
        msgs: list[str] = []
        if self.is_empty:
            msgs.append("Extracted text is empty")
        if self.too_short:
            msgs.append(
                f"Extracted text is too short (< {_MIN_TEXT_LENGTH} characters)"
            )
        if self.missing_keywords:
            msgs.append(
                "None of the expected resume keywords found "
                f"({', '.join(_RESUME_KEYWORDS)})"
            )
        if self.garbage_ratio_low:
            msgs.append(
                f"Printable-character ratio is below {_MIN_PRINTABLE_RATIO:.0%}"
            )
        return msgs


class TextVerifier:
    """Validates that text extracted from a resume file looks reasonable."""

    def verify(self, text: str) -> VerificationResult:
        """Run all quality checks on *text* and return a ``VerificationResult``.

        Checks performed:
        1. **Empty** – the text is blank or whitespace-only.
        2. **Too short** – fewer than ``_MIN_TEXT_LENGTH`` characters.
        3. **Missing keywords** – none of the common resume section headings
           appear in the text.
        4. **Garbage ratio** – the proportion of printable characters is below
           ``_MIN_PRINTABLE_RATIO``.
        """
        result = VerificationResult()

        # 1. Empty check
        if not text.strip():
            result.is_empty = True
            logger.warning("Verification failed: extracted text is empty.")
            return result  # no point running further checks

        # 2. Length check
        if len(text) < _MIN_TEXT_LENGTH:
            result.too_short = True
            logger.warning(
                "Verification warning: text length (%d) < %d.",
                len(text),
                _MIN_TEXT_LENGTH,
            )

        # 3. Keyword check
        lower_text = text.lower()
        if not any(kw in lower_text for kw in _RESUME_KEYWORDS):
            result.missing_keywords = True
            logger.warning("Verification warning: no expected resume keywords found.")

        # 4. Garbage / non-printable character check
        printable_count = sum(c in string.printable for c in text)
        ratio = printable_count / max(len(text), 1)
        if ratio < _MIN_PRINTABLE_RATIO:
            result.garbage_ratio_low = True
            logger.warning(
                "Verification warning: printable-char ratio %.2f < %.2f.",
                ratio,
                _MIN_PRINTABLE_RATIO,
            )

        if result.passed:
            logger.info("Text verification passed.")
        else:
            logger.warning("Text verification failed: %s", "; ".join(result.issues))

        return result
