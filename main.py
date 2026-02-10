import sys

from src.field_extractor import CombinedExtractor
from src.resume_extractor import ResumeExtractor
from src.resume_parser_framework import ResumeParserFramework


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <resume_file>")
        sys.exit(1)

    # Single API call extracts all fields — 3× fewer requests, avoids rate limits
    extractor = ResumeExtractor(combined_extractor=CombinedExtractor())
    framework = ResumeParserFramework(extractor)

    result = framework.parse_resume(sys.argv[1])
    print(result)


if __name__ == "__main__":
    main()
