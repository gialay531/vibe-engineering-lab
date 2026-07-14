import json
import re
from pathlib import Path

from generate_brief import DATA_FILE, generate_brief, load_program_data

REQUIRED_HEADINGS = (
    "## BLUF",
    "## 1. Accomplished Since the Previous Brief",
    "## 2. Before the Next Brief",
    "## 3. Roadblocks, Risks, and Bottlenecks",
)

CITATION_PATTERN = re.compile(r"\*\*\[([^\]]+)\]\*\*")
PLACEHOLDER_TEXT = "No additional supported"


def extract_bluf(brief: str) -> str:
    """Return the text between the BLUF and first numbered section."""
    if "## BLUF" not in brief:
        return ""

    after_heading = brief.split("## BLUF", maxsplit=1)[1]
    return after_heading.split("## 1.", maxsplit=1)[0].strip()


def evaluate_brief(data: dict, brief: str) -> dict:
    """Evaluate objective morning-brief requirements."""
    lines = brief.splitlines()
    bullet_lines = [line for line in lines if line.startswith("- ")]
    substantive_bullets = [
        line for line in bullet_lines if PLACEHOLDER_TEXT not in line
    ]

    citation_ids = CITATION_PATTERN.findall(brief)
    available_source_ids = {item["id"] for item in data["items"]}

    checks = {
        "required_headings_present": all(
            heading in brief for heading in REQUIRED_HEADINGS
        ),
        "bluf_is_not_empty": bool(extract_bluf(brief)),
        "exactly_nine_bullets": len(bullet_lines) == 9,
        "substantive_bullets_are_cited": all(
            CITATION_PATTERN.search(bullet) for bullet in substantive_bullets
        ),
        "citations_exist_in_dataset": set(citation_ids).issubset(available_source_ids),
        "citations_are_unique": len(citation_ids) == len(set(citation_ids)),
    }

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "details": {
            "bullet_count": len(bullet_lines),
            "substantive_bullet_count": len(substantive_bullets),
            "citation_count": len(citation_ids),
        },
    }


def main() -> None:
    """Generate and objectively evaluate the sample morning brief."""
    data = load_program_data(DATA_FILE)
    brief = generate_brief(data)
    result = evaluate_brief(data, brief)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
