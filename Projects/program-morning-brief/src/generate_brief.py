import json
from pathlib import Path
from copy import deepcopy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"
OUTPUT_DIR = PROJECT_ROOT / "generated-output"
SUPPORTED_SCHEMA_VERSIONS = ("1.0",)

ACCOMPLISHMENT_KEYWORDS = ("approved", "completed", "resolved")
NEXT_PERIOD_KEYWORDS = ("scheduled", "will", "expects", "due")
RISK_KEYWORDS = ("delay", "late", "blocked", "risk")
REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "brief_date",
    "program",
    "items",
)

REQUIRED_PROGRAM_FIELDS = (
    "name",
    "description",
)

REQUIRED_ITEM_FIELDS = (
    "id",
    "source_system",
    "source_type",
    "timestamp",
    "author",
    "title",
    "content",
    "source_reference",
    "source_url",
    "owner",
    "due_date",
    "status",
    "source_priority",
    "thread_id",
    "retrieved_at",
)
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
NORMALIZED_ITEM_DEFAULTS = {
    "source_url": None,
    "owner": None,
    "due_date": None,
    "status": None,
    "source_priority": None,
    "thread_id": None,
    "retrieved_at": None,
}


def normalize_program_data(data: dict) -> dict:
    """Return a normalized copy with explicit defaults for optional metadata."""
    normalized_data = deepcopy(data)

    if not isinstance(normalized_data, dict):
        return normalized_data

    items = normalized_data.get("items")
    if not isinstance(items, list):
        return normalized_data

    for item in items:
        if not isinstance(item, dict):
            continue

        for field, default_value in NORMALIZED_ITEM_DEFAULTS.items():
            item.setdefault(field, default_value)

    return normalized_data


def load_program_data(file_path: Path) -> dict:
    """Load, normalize, validate, and return program data from a JSON file."""
    with file_path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    data = normalize_program_data(raw_data)
    validate_program_data(data)
    return data


def validate_program_data(data: dict) -> None:
    """Raise a clear error when required program data is missing or invalid."""
    if not isinstance(data, dict):
        raise ValueError("Program data must be a JSON object.")

    missing_top_level = [
        field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in data
    ]
    if missing_top_level:
        missing = ", ".join(missing_top_level)
        raise ValueError(f"Program data is missing required field(s): {missing}")

    if data["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported schema version: {data['schema_version']}")

    if not isinstance(data["program"], dict):
        raise ValueError("The program field must be a JSON object.")

    missing_program_fields = [
        field for field in REQUIRED_PROGRAM_FIELDS if field not in data["program"]
    ]
    if missing_program_fields:
        missing = ", ".join(missing_program_fields)
        raise ValueError(f"Program is missing required field(s): {missing}")

    if not isinstance(data["items"], list):
        raise ValueError("The items field must be a JSON array.")

    for index, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            raise ValueError(f"Item at position {index} must be a JSON object.")

        missing_item_fields = [
            field for field in REQUIRED_ITEM_FIELDS if field not in item
        ]
        if missing_item_fields:
            missing = ", ".join(missing_item_fields)
            raise ValueError(
                f"Item at position {index} is missing required field(s): {missing}"
            )


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
    return f"- {item['title']}: {item['content']} " f"**[{item['id']}]**"


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


def generate_bluf(groups: dict[str, list[dict]]) -> str:
    """Generate a concise BLUF from the highest-priority grouped items."""
    sentences = []

    if groups["accomplished"]:
        title = groups["accomplished"][0]["title"].lower()
        sentences.append(f"Progress is confirmed on {title}.")

    if groups["before_next_brief"]:
        title = groups["before_next_brief"][0]["title"].lower()
        sentences.append(f"Before the next brief, attention should focus on {title}.")

    if groups["roadblock_risk_or_bottleneck"]:
        title = groups["roadblock_risk_or_bottleneck"][0]["title"].lower()
        sentences.append(f"The primary risk is {title}.")

    if not sentences:
        return "No supported items were identified in the available source data."

    return " ".join(sentences)


def generate_brief(data: dict) -> str:
    """Generate a complete BLUF 3x3 morning brief as Markdown."""
    groups = group_items(data["items"])

    lines = [
        f"# Morning Brief — {data['brief_date']}",
        "",
        "## BLUF",
        "",
        generate_bluf(groups),
        "",
    ]

    for title, group_name, empty_message in SECTION_CONFIG:
        section = format_section(
            title,
            groups[group_name],
            empty_message,
        )
        lines.append(section)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def save_brief(
    brief: str,
    brief_date: str,
    output_dir: Path = OUTPUT_DIR,
) -> Path:
    """Save a generated brief and return the output file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"morning-brief-{brief_date}.md"
    output_file.write_text(brief, encoding="utf-8")
    return output_file


def main() -> None:
    """Load the source data, generate the brief, and save it."""
    data = load_program_data(DATA_FILE)
    brief = generate_brief(data)
    output_file = save_brief(brief, data["brief_date"])
    print(f"Morning brief saved to: {output_file}")


if __name__ == "__main__":
    main()
