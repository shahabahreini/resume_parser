from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors


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
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Create a .env file based on .env.example and add your key."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def extract(self, resume_text: str) -> Any:
        """Send resume text to Gemini and return the extracted field value."""
        prompt = self._PROMPT.format(resume_text=resume_text)

        response = self._call_with_retry(prompt)

        if not response.text:
            raise ValueError("Gemini response returned empty or None text")

        raw = response.text.strip()
        # Strip markdown code fences if the model wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]  # remove opening fence line
            raw = raw.rsplit("```", 1)[0]  # remove closing fence
            raw = raw.strip()

        try:
            data: dict = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Failed to parse Gemini response as JSON:\n{raw}"
            ) from exc

        return data[self._FIELD_KEY]

    def _call_with_retry(
        self, prompt: str, *, max_retries: int = 5, initial_delay: float = 5.0
    ):
        """Call Gemini with exponential backoff on rate-limit (429) errors."""
        delay = initial_delay
        for attempt in range(max_retries + 1):
            try:
                return self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
            except genai_errors.ClientError as exc:
                if exc.code == 429 and attempt < max_retries:
                    print(
                        f"  ⏳ Rate limited. Retrying in {delay:.0f}s "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
                else:
                    raise


# ── Concrete extractors ──────────────────────────────────────────────


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

    _FIELD_KEY = ""  # not used — we override extract()
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
        prompt = self._PROMPT.format(resume_text=resume_text)
        response = self._call_with_retry(prompt)

        if not response.text:
            raise ValueError("Gemini response returned empty or None text")

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

        try:
            data: dict = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Failed to parse Gemini response as JSON:\n{raw}"
            ) from exc

        return data
