import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

ACCOMPLISHMENT_KEYWORDS = ("approved", "completed", "resolved")
NEXT_PERIOD_KEYWORDS = ("scheduled", "will", "expects", "due")
RISK_KEYWORDS = ("delay", "late", "blocked", "risk")


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


def main() -> None:
    """Load, classify, and display the sample source items."""
    data = load_program_data(DATA_FILE)

    print(f"Program: {data['program']['name']}")
    print(f"Brief date: {data['brief_date']}")
    print(f"Source items: {len(data['items'])}")
    print()

    for item in data["items"]:
        classification = classify_item(item)
        print(f"- {item['id']}: {classification}")


if __name__ == "__main__":
    main()