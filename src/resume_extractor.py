from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from google import genai


@dataclass
class CandidateInfo:
    """Structured data extracted from a parsed resume."""

    name: str
    email: str
    skills: list[str]

    def __str__(self) -> str:
        skills_str = ", ".join(self.skills) if self.skills else "N/A"
        return (
            f"Name:   {self.name}\n" f"Email:  {self.email}\n" f"Skills: {skills_str}"
        )


class ResumeExtractor:
    """Use Google Gemini to extract structured candidate info from resume text."""

    _PROMPT_TEMPLATE = (
        "You are a resume parsing assistant. "
        "Given the following resume text, extract the candidate's name, "
        "email address, and a list of technical/professional skills.\n\n"
        "Resume text:\n"
        "---\n"
        "{resume_text}\n"
        "---\n\n"
        "Respond ONLY with valid JSON in this exact format (no markdown, no extra text):\n"
        '{{"name": "...", "email": "...", "skills": ["...", "..."]}}'
    )

    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Create a .env file based on .env.example and add your key."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def extract(self, resume_text: str) -> CandidateInfo:
        """Send resume text to Gemini and return structured candidate info.

        Args:
            resume_text: Plain-text content of a parsed resume.

        Returns:
            A ``CandidateInfo`` dataclass with name, email, and skills.

        Raises:
            ValueError: If the model response cannot be parsed as JSON.
        """
        prompt = self._PROMPT_TEMPLATE.format(resume_text=resume_text)

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )

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

        return CandidateInfo(
            name=data.get("name", ""),
            email=data.get("email", ""),
            skills=data.get("skills", []),
        )

    @classmethod
    def from_file(cls, file_path: Path | str, **kwargs: object) -> CandidateInfo:
        """Parse a resume file and extract candidate info in one step.

        Args:
            file_path: Path to the resume file (.pdf or .docx).
            **kwargs: Extra keyword arguments forwarded to the constructor.

        Returns:
            A ``CandidateInfo`` dataclass.
        """
        from src.file_parser import FileParser

        text = FileParser.parse_resume(Path(file_path))
        extractor = cls(**kwargs)  # type: ignore[arg-type]
        return extractor.extract(text)
