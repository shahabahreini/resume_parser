from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)


class FieldExtractor(ABC):
    """Abstract interface for extracting a single field from resume text."""

    @abstractmethod
    def extract(self, resume_text: str) -> Any:
        """Extract a field value from the given resume text.

        Args:
            resume_text: Plain-text content of a parsed resume.

        Returns:
            The extracted value (type depends on the concrete extractor).
        """
        ...


class GeminiFieldExtractor(FieldExtractor):
    """Gemini-powered extractor for a single resume field.

    Subclasses set ``_PROMPT`` and ``_FIELD_KEY`` to customise what is
    extracted and how the JSON response is decoded.
    """

    _PROMPT: str = ""
    _FIELD_KEY: str = ""

    def __init__(self, model: str = "gemini-flash-latest") -> None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY is not set")
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Create a .env file based on .env.example and add your key."
            )
        try:
            self._client = genai.Client(api_key=api_key)
        except Exception as exc:
            logger.error("Failed to initialise Gemini client: %s", exc)
            raise ConnectionError(
                f"Failed to initialise the Gemini AI client: {exc}"
            ) from exc
        self._model = model
        logger.debug("Initialised Gemini client (model=%s)", model)

    def extract(self, resume_text: str) -> Any:
        """Send resume text to Gemini and return the extracted field value."""
        if not resume_text or not resume_text.strip():
            raise ValueError("Cannot extract fields from empty resume text.")

        logger.info("Extracting field '%s' via Gemini", self._FIELD_KEY)
        prompt = self._PROMPT.format(resume_text=resume_text)

        response = self._call_with_retry(prompt)

        if not response or not response.text:
            logger.error(
                "Gemini returned empty response for field '%s'", self._FIELD_KEY
            )
            raise ValueError(
                f"Gemini returned an empty response when extracting '{self._FIELD_KEY}'. "
                f"The resume text may be too short or unreadable."
            )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

        try:
            data: dict = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse Gemini JSON for '%s': %s", self._FIELD_KEY, raw[:200]
            )
            raise ValueError(
                f"Gemini returned invalid JSON when extracting '{self._FIELD_KEY}'.\n"
                f"Raw response: {raw[:300]}"
            ) from exc

        if self._FIELD_KEY not in data:
            logger.error(
                "Key '%s' missing from Gemini response: %s",
                self._FIELD_KEY,
                list(data.keys()),
            )
            raise ValueError(
                f"Gemini response is missing the expected '{self._FIELD_KEY}' key. "
                f"Got keys: {list(data.keys())}"
            )

        logger.debug(
            "Extracted '%s' = %s", self._FIELD_KEY, str(data[self._FIELD_KEY])[:100]
        )
        return data[self._FIELD_KEY]

    def _call_with_retry(
        self, prompt: str, *, max_retries: int = 5, initial_delay: float = 5.0
    ):
        """Call Gemini with exponential backoff on rate-limit (429) errors."""
        delay = initial_delay
        for attempt in range(max_retries + 1):
            try:
                logger.debug("Sending request to Gemini (attempt %d)", attempt + 1)
                return self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
            except genai_errors.ClientError as exc:
                if exc.code == 429 and attempt < max_retries:
                    logger.warning(
                        "Rate limited (429). Retrying in %.0fs (attempt %d/%d)",
                        delay,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error("Gemini API error (code=%s): %s", exc.code, exc)
                    raise ConnectionError(
                        f"Gemini API request failed (code {exc.code}): {exc}"
                    ) from exc
            except genai_errors.ServerError as exc:
                if attempt < max_retries:
                    logger.warning(
                        "Gemini server error (%s). Retrying in %.0fs (attempt %d/%d)",
                        exc,
                        delay,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error("Gemini server error after retries: %s", exc)
                    raise ConnectionError(
                        f"Gemini AI service is temporarily unavailable: {exc}"
                    ) from exc
            except OSError as exc:
                logger.error("Network error contacting Gemini: %s", exc)
                raise ConnectionError(
                    f"Network error: could not reach the Gemini API. "
                    f"Check your internet connection. ({exc})"
                ) from exc


class NameExtractor(GeminiFieldExtractor):
    """Extract the candidate's full name from resume text."""

    _FIELD_KEY = "name"
    _PROMPT = (
        "You are a resume parsing assistant. "
        "Extract the candidate's full name from the following resume text.\n\n"
        "Resume text:\n---\n{resume_text}\n---\n\n"
        "Respond ONLY with valid JSON in this exact format "
        "(no markdown, no extra text):\n"
        '{{"name": "..."}}'
    )


class EmailExtractor(GeminiFieldExtractor):
    """Extract the candidate's email address from resume text."""

    _FIELD_KEY = "email"
    _PROMPT = (
        "You are a resume parsing assistant. "
        "Extract the candidate's email address from the following resume text.\n\n"
        "Resume text:\n---\n{resume_text}\n---\n\n"
        "Respond ONLY with valid JSON in this exact format "
        "(no markdown, no extra text):\n"
        '{{"email": "..."}}'
    )


class SkillsExtractor(GeminiFieldExtractor):
    """Extract the candidate's technical/professional skills from resume text."""

    _FIELD_KEY = "skills"
    _PROMPT = (
        "You are a resume parsing assistant. "
        "Extract a list of the candidate's technical and professional skills "
        "from the following resume text.\n\n"
        "Resume text:\n---\n{resume_text}\n---\n\n"
        "Respond ONLY with valid JSON in this exact format "
        "(no markdown, no extra text):\n"
        '{{"skills": ["...", "..."]}}'
    )


class CombinedExtractor(GeminiFieldExtractor):
    """Extract name, email, and skills in a single Gemini API call.

    This reduces API usage by 3× compared to separate extractors and
    avoids hitting per-minute rate limits on the free tier.
    """

    _FIELD_KEY = ""
    _PROMPT = (
        "You are a resume parsing assistant. "
        "Extract the candidate's full name, email address, and a list of "
        "technical/professional skills from the following resume text.\n\n"
        "Resume text:\n---\n{resume_text}\n---\n\n"
        "Respond ONLY with valid JSON in this exact format "
        "(no markdown, no extra text):\n"
        '{{"name": "...", "email": "...", "skills": ["...", "..."]}}'
    )

    def extract(self, resume_text: str) -> dict[str, Any]:
        """Return a dict with ``name``, ``email``, and ``skills`` keys."""
        if not resume_text or not resume_text.strip():
            raise ValueError("Cannot extract fields from empty resume text.")

        logger.info("Extracting all fields via combined Gemini call")
        prompt = self._PROMPT.format(resume_text=resume_text)
        response = self._call_with_retry(prompt)

        if not response or not response.text:
            logger.error("Gemini returned empty response for combined extraction")
            raise ValueError(
                "Gemini returned an empty response for the combined extraction. "
                "The resume text may be too short or unreadable."
            )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

        try:
            data: dict = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse Gemini JSON for combined extraction: %s", raw[:200]
            )
            raise ValueError(
                f"Gemini returned invalid JSON for combined extraction.\n"
                f"Raw response: {raw[:300]}"
            ) from exc

        expected_keys = {"name", "email", "skills"}
        missing = expected_keys - set(data.keys())
        if missing:
            logger.error(
                "Combined extraction missing keys %s; got %s",
                missing,
                list(data.keys()),
            )
            raise ValueError(
                f"Gemini response is missing expected fields: {', '.join(sorted(missing))}. "
                f"Got: {list(data.keys())}"
            )

        return data
