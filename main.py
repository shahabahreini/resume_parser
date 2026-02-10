import sys
from pathlib import Path

from src.file_parser import FileParser


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <resume_file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    text = FileParser.parse_resume(file_path)
    print(text)


if __name__ == "__main__":
    main()
