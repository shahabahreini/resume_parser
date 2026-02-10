import sys

from src.field_extractor import EmailExtractor, NameExtractor, SkillsExtractor
from src.resume_extractor import ResumeExtractor
from src.resume_parser_framework import ResumeParserFramework


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <resume_file>")
        sys.exit(1)

    field_extractors = {
        "name": NameExtractor(),
        "email": EmailExtractor(),
        "skills": SkillsExtractor(),
    }
    extractor = ResumeExtractor(field_extractors)
    framework = ResumeParserFramework(extractor)

    result = framework.parse_resume(sys.argv[1])
    print(result)


if __name__ == "__main__":
    main()
