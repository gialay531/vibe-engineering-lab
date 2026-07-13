import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

ACCOMPLISHMENT_KEYWORDS = ("approved", "completed", "resolved")
NEXT_PERIOD_KEYWORDS = ("scheduled", "will", "expects", "due")
RISK_KEYWORDS = ("delay", "late", "blocked", "risk")
SECTION_CONFIG = (
    (
        "1. Accomplished Since the Previous Brief",
        "accomplished",
        "No additional supported accomplishment was identified.",
    ),
    (
        "2. Before the Next Brief",
        "before_next_brief",
        "No additional supported planned outcome was identified.",
    ),
    (
        "3. Roadblocks, Risks, and Bottlenecks",
        "roadblock_risk_or_bottleneck",
        "No additional supported roadblock, risk, or bottleneck was identified.",
    ),
)


def load_program_data(file_path: Path) -> dict:
    """Load and return program data from a JSON file."""
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def classify_item(item: dict) -> str:
    """Classify one source item using simple keyword rules."""
    text = f"{item['title']} {item['content']}".lower()

    if any(keyword in text for keyword in ACCOMPLISHMENT_KEYWORDS):
        return "accomplished"

    if any(keyword in text for keyword in RISK_KEYWORDS):
        return "roadblock_risk_or_bottleneck"

    if any(keyword in text for keyword in NEXT_PERIOD_KEYWORDS):
        return "before_next_brief"

    return "unclassified"
def group_items(items: list[dict]) -> dict[str, list[dict]]:
    """Group source items by their morning-brief classification."""
    groups = {
        "accomplished": [],
        "before_next_brief": [],
        "roadblock_risk_or_bottleneck": [],
        "unclassified": [],
    }

    for item in items:
        classification = classify_item(item)
        groups[classification].append(item)

    return groups
def format_item(item: dict) -> str:
    """Format one source item as a cited Markdown bullet."""
    return (
        f"- {item['title']}: {item['content']} "
        f"**[{item['id']}]**"
    )


def format_section(
    title: str,
    items: list[dict],
    empty_message: str,
) -> str:
    """Format one BLUF 3x3 section with exactly three bullets."""
    bullets = [format_item(item) for item in items[:3]]

    while len(bullets) < 3:
        bullets.append(f"- {empty_message}")

    return "\n".join([f"## {title}", "", *bullets])

def main() -> None:
    """Load the source data and print the three brief sections."""
    data = load_program_data(DATA_FILE)
    groups = group_items(data["items"])

    print(f"# Morning Brief — {data['brief_date']}")
    print()

    for title, group_name, empty_message in SECTION_CONFIG:
        section = format_section(
            title,
            groups[group_name],
            empty_message,
        )
        print(section)
        print()


if __name__ == "__main__":
    main()