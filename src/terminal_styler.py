"""Rich terminal output helpers for the resume parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.columns import Columns
from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

_THEME = Theme(
    {
        "info": "#5f87af",
        "success": "#87af87",
        "warning": "#d7af87",
        "error": "#d75f5f",
        "heading": "bold #af875f",
        "field_label": "#5f87af",
        "field_value": "#d7d7af",
        "muted": "#6c6c6c",
        "accent": "#87af87",
        "hint": "italic #6c6c6c",
        "filename": "bold #d7d7af",
    }
)

console = Console(theme=_THEME)


def print_heading(text: str) -> None:
    """Print a prominent section heading."""
    console.print()
    console.print(Rule(f"[heading]{text}[/heading]", style="#af875f"))


def print_info(msg: str) -> None:
    """Print an informational message."""
    console.print(f"  [info]i[/info]  {msg}")


def print_success(msg: str) -> None:
    """Print a success message."""
    console.print(f"  [success]+[/success]  {msg}")


def print_warning(msg: str) -> None:
    """Print a warning message."""
    console.print(f"  [warning]![/warning]  {msg}")


def print_error(msg: str) -> None:
    """Print an error message."""
    console.print(f"  [error]x[/error]  [error]{msg}[/error]")


def print_hint(msg: str) -> None:
    """Print a subtle hint/suggestion below an error or warning."""
    console.print(f"    [hint]> {msg}[/hint]")


def print_divider(style: str = "#3a3a3a") -> None:
    """Print a horizontal rule as a visual separator."""
    console.print(Rule(style=style))


def print_key_value(key: str, value: str) -> None:
    """Print a ``key: value`` pair with styled colours."""
    console.print(
        f"  [field_label]{key}:[/field_label] [field_value]{value}[/field_value]"
    )


def print_file_info(file_path: str | Path) -> None:
    """Print basic file metadata before processing."""
    p = Path(file_path)
    size_kb = p.stat().st_size / 1024
    suffix = p.suffix.lower()
    console.print(
        f"  [filename]{p.name}[/filename]  "
        f"[muted]({size_kb:.1f} KB | {suffix})[/muted]"
    )


def print_resume_result(data: Any) -> None:
    """Render a :class:`ResumeData` as a Rich panel with a table inside."""
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
    )
    table.add_column("Field", style="field_label", width=10, no_wrap=True)
    table.add_column("Value", style="field_value")

    table.add_row("Name", data.name or "[muted]N/A[/muted]")
    table.add_row("Email", data.email or "[muted]N/A[/muted]")

    if data.skills:
        skill_tags = "  ".join(f"[on #2e2e2e] {s} [/on #2e2e2e]" for s in data.skills)
        table.add_row("Skills", skill_tags)
    else:
        table.add_row("Skills", "[muted]N/A[/muted]")

    panel = Panel(
        table,
        title="[heading]Parsed Resume[/heading]",
        border_style="#5f6f5f",
        expand=False,
        padding=(1, 3),
    )
    console.print()
    console.print(panel)


def print_error_panel(title: str, message: str, hints: list[str] | None = None) -> None:
    """Print a prominent error panel with optional recovery hints."""
    parts: list[Any] = [Text(message, style="#d75f5f")]
    if hints:
        parts.append(Text())
        for h in hints:
            parts.append(Text(f"  > {h}", style="italic #6c6c6c"))
    panel = Panel(
        Group(*parts),
        title=f"[error]x {title}[/error]",
        border_style="#6b3a3a",
        expand=False,
        padding=(1, 3),
    )
    console.print()
    console.print(panel)


def print_usage() -> None:
    """Print a styled usage/help message."""
    usage_table = Table(show_header=False, box=None, padding=(0, 1))
    usage_table.add_column("cmd", style="accent", no_wrap=True)
    usage_table.add_column("desc", style="muted")
    usage_table.add_row(
        "python3 main.py <resume_file>",
        "Parse a single resume (.pdf or .docx)",
    )
    panel = Panel(
        usage_table,
        title="[heading]Usage[/heading]",
        border_style="#5f6f5f",
        expand=False,
        padding=(1, 2),
    )
    console.print()
    console.print(panel)


def make_spinner(description: str = "Processing..."):
    """Return a Rich Status context manager (spinner).

    Usage::

        with make_spinner("Extracting fields..."):
            do_work()
    """
    return console.status(
        f"  [info]{description}[/info]",
        spinner="dots",
        spinner_style="#5f87af",
    )


def print_banner() -> None:
    """Print an application banner at startup."""
    title = Text.assemble(
        ("Resume", "bold #87af87"),
        (" Parser", "#d7d7af"),
    )
    subtitle = Text.assemble(
        ("Powered by ", "#6c6c6c"),
        ("Gemini AI", "#6c6c6c bold"),
    )
    panel = Panel(
        Padding(title, (0, 1)),
        subtitle=subtitle,
        border_style="#5f6f5f",
        expand=False,
        padding=(0, 4),
    )
    console.print(panel)
