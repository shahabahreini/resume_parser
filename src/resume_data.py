from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResumeData:
    """Structured data extracted from a parsed resume."""

    name: str
    email: str
    skills: list[str]

    def __str__(self) -> str:
        skills_str = ", ".join(self.skills) if self.skills else "N/A"
        return (
            f"Name:   {self.name}\n" f"Email:  {self.email}\n" f"Skills: {skills_str}"
        )
