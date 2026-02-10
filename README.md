# Resume Parser

Extract **name**, **email**, and **skills** from `.pdf` / `.docx` resumes using Google Gemini AI.

## Table of Contents

- [Quick Start](#quick-start)
- [Usage](#usage)
- [CLI Arguments](#cli-arguments)
- [Logging](#logging)
- [Troubleshooting](#troubleshooting)

## Quick Start

```bash
git clone <repo-url> && cd resume_parser
uv sync
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

> Get a free key at [Google AI Studio](https://aistudio.google.com/apikey).

## Usage

```bash
uv run main.py <resume_file>
```

```bash
uv run main.py resumes/john_doe.pdf
uv run main.py resumes/jane_smith.docx
uv run main.py resumes/resume.pdf -v
```

## CLI Arguments

| Argument    | Short | Required | Default | Description                                |
| ----------- | ----- | -------- | ------- | ------------------------------------------ |
| `file`      | —     | Yes      | —       | Path to a resume file (`.pdf` or `.docx`)  |
| `--verbose` | `-v`  | No       | `False` | Show detailed log messages in the terminal |

## Output

On success, a styled panel displays the extracted **Name**, **Email**, and **Skills** directly in the terminal.

## Logging

Each run writes a timestamped log to `logs/` (e.g. `resume_parser_2026-02-10_14-30-45.log`). Use `-v` to also print logs to the terminal.

## Troubleshooting

| Error                              | Fix                                          |
| ---------------------------------- | -------------------------------------------- |
| **Missing API Key**                | Create `.env` with `GEMINI_API_KEY=your_key` |
| **ModuleNotFoundError**            | Run `uv sync`                                |
| **Connection Failed**              | Check internet; retry later                  |
| **Unsupported format**             | Convert to `.pdf` or `.docx`                 |
| **Access Denied**                  | Unlock the PDF before parsing                |
| **Extraction Failed** (empty text) | Re-export as a text-based PDF                |
| **Parse Error**                    | Re-save from the source application          |
