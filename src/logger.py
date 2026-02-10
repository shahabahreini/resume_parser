"""Centralised logging configuration for the resume parser.

Call :func:`setup_logging` once at application startup (in ``main.py``)
to configure the root logger with both a Rich console handler and an
optional rotating file handler.

Every other module should simply use::

    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "resume_parser.log"
_CONFIGURED = False


def setup_logging(
    *,
    level: int = logging.DEBUG,
    log_to_file: bool = True,
    log_to_console: bool = False,
) -> None:
    """Initialise the root logger with Rich console + optional file output.

    Args:
        level: Minimum log level (default ``DEBUG``).
        log_to_file: If ``True``, also write logs to ``logs/resume_parser.log``.
        log_to_console: If ``True``, show log messages in the terminal via
            a Rich handler.  When ``False`` (the default) the terminal
            stays clean — only styled application output is printed.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return
    _CONFIGURED = True

    root = logging.getLogger()
    root.setLevel(level)

    # ── Rich console handler (coloured, with timestamps) ────────────
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

    # ── File handler (plain text, detailed format) ──────────────────
    if log_to_file:
        _LOG_DIR.mkdir(exist_ok=True)
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=2 * 1024 * 1024,  # 2 MB
            backupCount=3,
            encoding="utf-8",
        )
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
