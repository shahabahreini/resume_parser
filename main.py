import sys
from pathlib import Path

from src.resume_extractor import ResumeExtractor


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <resume_file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    candidate = ResumeExtractor.from_file(file_path)
    print(candidate)


if __name__ == "__main__":
    main()
