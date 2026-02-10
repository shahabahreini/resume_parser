import argparse
import sys
from pathlib import Path

from src.field_extractor import CombinedExtractor
from src.logger import setup_logging
from src.resume_extractor import ResumeExtractor
from src.resume_parser_framework import ResumeParserFramework
from src.terminal_styler import (
    console,
    make_spinner,
    print_banner,
    print_divider,
    print_error,
    print_error_panel,
    print_file_info,
    print_hint,
    print_info,
    print_resume_result,
    print_success,
    print_usage,
    print_warning,
)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="resume-parser",
        description="Parse resumes and extract structured data using Gemini AI.",
        add_help=False,
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to a resume file (.pdf or .docx)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Show detailed log messages in the terminal.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    setup_logging(log_to_console=args.verbose)
    print_banner()
    console.print()

    if not args.file:
        print_error_panel(
            "No file provided",
            "Please specify a resume file to parse.",
            hints=[
                "Run: python3 main.py <resume.pdf>",
                "Supported formats: .pdf, .docx",
            ],
        )
        print_usage()
        sys.exit(1)

    file_path = args.file
    path = Path(file_path)

    if not path.exists():
        print_error_panel(
            "File not found",
            f"'{file_path}' does not exist.",
            hints=[
                "Check the file path for typos.",
                "Use a relative or absolute path to the resume file.",
            ],
        )
        sys.exit(1)

    if not path.is_file():
        print_error_panel(
            "Not a file",
            f"'{file_path}' is a directory, not a file.",
        )
        sys.exit(1)

    suffix = path.suffix.lower()
    if suffix not in (".pdf", ".docx"):
        print_error_panel(
            "Unsupported format",
            f"'{suffix}' files are not supported.",
            hints=["Supported formats: .pdf, .docx"],
        )
        sys.exit(1)

    print_info(f"Processing resume")
    print_file_info(path)
    print_divider()

    try:
        extractor = ResumeExtractor(combined_extractor=CombinedExtractor())
    except EnvironmentError as exc:
        print_error_panel(
            "Missing API Key",
            str(exc),
            hints=[
                "Create a .env file in the project root.",
                "Add: GEMINI_API_KEY=your_key_here",
                "Get a key at https://aistudio.google.com/apikey",
            ],
        )
        sys.exit(1)
    except ConnectionError as exc:
        print_error_panel(
            "Connection Failed",
            str(exc),
            hints=["Check your internet connection and try again."],
        )
        sys.exit(1)

    framework = ResumeParserFramework(extractor)

    try:
        with make_spinner("Parsing resume and extracting fields..."):
            result = framework.parse_resume(file_path)
        console.print()
        print_success("Resume parsed successfully!")
        print_resume_result(result)

    except FileNotFoundError as exc:
        print_error_panel("File Not Found", str(exc))
        sys.exit(1)

    except PermissionError as exc:
        print_error_panel(
            "Access Denied",
            str(exc),
            hints=[
                "If the PDF is password-protected, unlock it first.",
                "Check file permissions with: ls -la <file>",
            ],
        )
        sys.exit(1)

    except RuntimeError as exc:
        print_error_panel(
            "Parse Error",
            str(exc),
            hints=[
                "The file may be corrupt — try re-exporting it.",
                "For PDFs: re-save with a tool like Preview or Adobe.",
                "For .docx: re-save from Word or Google Docs.",
            ],
        )
        sys.exit(1)

    except ValueError as exc:
        msg = str(exc)
        hints = []
        if "verification" in msg.lower() or "empty" in msg.lower():
            hints = [
                "The file may be a scanned image (not machine-readable text).",
                "Try re-exporting the resume as a text-based PDF.",
                "Password-protected or image-only PDFs cannot be parsed.",
            ]
        elif "json" in msg.lower():
            hints = ["The AI returned an unexpected format. Try again."]
        elif "unsupported" in msg.lower():
            hints = ["Supported file types: .pdf, .docx"]
        print_error_panel("Extraction Failed", msg, hints=hints)
        sys.exit(1)

    except ConnectionError as exc:
        print_error_panel(
            "AI Service Error",
            str(exc),
            hints=[
                "Check your internet connection.",
                "The Gemini API may be temporarily down — retry shortly.",
                "Verify your GEMINI_API_KEY is valid.",
            ],
        )
        sys.exit(1)

    except KeyboardInterrupt:
        console.print()
        print_warning("Interrupted by user.")
        sys.exit(130)

    except Exception as exc:
        print_error_panel(
            "Unexpected Error",
            f"{type(exc).__name__}: {exc}",
            hints=["Check the latest log file in logs/ for details."],
        )
        console.print_exception(show_locals=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
