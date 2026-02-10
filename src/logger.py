"""Centralised logging configuration for the resume parser."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

_LOG_DIR = Path("logs")
_CONFIGURED = False


def _make_log_path() -> Path:
    """Generate a timestamped log file path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return _LOG_DIR / f"resume_parser_{timestamp}.log"


def setup_logging(
    *,
    level: int = logging.DEBUG,
    log_to_file: bool = True,
    log_to_console: bool = False,
) -> None:
    """Initialise the root logger with Rich console + optional file output.

    Args:
        level: Minimum log level (default ``DEBUG``).
        log_to_file: If ``True``, write logs to a timestamped file under ``logs/``.
        log_to_console: If ``True``, show log messages in the terminal via
            a Rich handler.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return
    _CONFIGURED = True

    root = logging.getLogger()
    root.setLevel(level)

    # ── Rich console handler ────────────────────────────────────────
    if log_to_console:
        console = Console(stderr=True)
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
        )
        rich_handler.setLevel(level)
        rich_fmt = logging.Formatter("%(message)s", datefmt="[%Y-%m-%d %H:%M:%S]")
        rich_handler.setFormatter(rich_fmt)
        root.addHandler(rich_handler)

    # ── Timestamped file handler ────────────────────────────────────
    if log_to_file:
        _LOG_DIR.mkdir(exist_ok=True)
        log_file = _make_log_path()
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s │ %(levelname)-8s │ %(name)-30s │ %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_fmt)
        root.addHandler(file_handler)

    # Quieten noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root.debug(
        "Logging initialised (level=%s, file=%s, console=%s)",
        logging.getLevelName(level),
        log_to_file,
        log_to_console,
    )
