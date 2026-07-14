import re
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
    "governance",
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

GOVERNANCE_DEFAULTS = {
    "sensitivity": "restricted",
    "authorized_for_ai": False,
    "retention_policy": None,
    "contains_personal_data": None,
}

REQUIRED_GOVERNANCE_FIELDS = (
    "sensitivity",
    "authorized_for_ai",
    "retention_policy",
    "contains_personal_data",
)

ALLOWED_SENSITIVITY_VALUES = (
    "public",
    "internal",
    "confidential",
    "restricted",
)

SECTION_DEFAULT_SCORES = {
    "accomplished": (1, 3),
    "before_next_brief": (3, 3),
    "roadblock_risk_or_bottleneck": (4, 4),
    "unclassified": (None, None),
}

URGENCY_SIGNALS = (
    (5, ("today", "blocked", "critical")),
    (4, ("late", "delay", "risk")),
    (3, ("scheduled", "due", "will")),
)

IMPACT_SIGNALS = (
    (5, ("critical", "authentication", "end-to-end")),
    (4, ("executive", "api", "migration")),
)


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

        if "governance" not in item:
            item["governance"] = deepcopy(GOVERNANCE_DEFAULTS)
        elif isinstance(item["governance"], dict):
            for field, default_value in GOVERNANCE_DEFAULTS.items():
                item["governance"].setdefault(field, default_value)

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
        governance = item["governance"]

        if not isinstance(governance, dict):
            raise ValueError(
                f"Governance for item at position {index} must be a JSON object."
            )

        missing_governance_fields = [
            field for field in REQUIRED_GOVERNANCE_FIELDS if field not in governance
        ]
        if missing_governance_fields:
            missing = ", ".join(missing_governance_fields)
            raise ValueError(
                f"Governance for item at position {index} "
                f"is missing required field(s): {missing}"
            )

        if governance["sensitivity"] not in ALLOWED_SENSITIVITY_VALUES:
            raise ValueError(
                f"Item at position {index} has unsupported sensitivity: "
                f"{governance['sensitivity']}"
            )

        if not isinstance(governance["authorized_for_ai"], bool):
            raise ValueError(
                f"authorized_for_ai for item at position {index} " "must be a boolean."
            )

        retention_policy = governance["retention_policy"]
        if retention_policy is not None and not isinstance(retention_policy, str):
            raise ValueError(
                f"retention_policy for item at position {index} "
                "must be a string or null."
            )

        contains_personal_data = governance["contains_personal_data"]
        if contains_personal_data is not None and not isinstance(
            contains_personal_data,
            bool,
        ):
            raise ValueError(
                f"contains_personal_data for item at position {index} "
                "must be a boolean or null."
            )


def contains_signal(text: str, signal: str) -> bool:
    """Return whether text contains a complete signal word or phrase."""
    pattern = rf"(?<!\w){re.escape(signal)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def classify_item(item: dict) -> str:
    """Classify one source item using simple keyword rules."""
    text = f"{item['title']} {item['content']}".lower()

    if any(contains_signal(text, keyword) for keyword in ACCOMPLISHMENT_KEYWORDS):
        return "accomplished"

    if any(contains_signal(text, keyword) for keyword in RISK_KEYWORDS):
        return "roadblock_risk_or_bottleneck"

    if any(contains_signal(text, keyword) for keyword in NEXT_PERIOD_KEYWORDS):
        return "before_next_brief"

    return "unclassified"


def calculate_priority_attributes(
    item: dict,
    brief_section: str,
) -> tuple[int | None, int | None]:
    """Calculate transparent urgency and impact scores."""
    urgency, impact = SECTION_DEFAULT_SCORES[brief_section]

    if urgency is None or impact is None:
        return None, None

    text = f"{item['title']} {item['content']}".lower()

    for score, keywords in URGENCY_SIGNALS:
        if any(contains_signal(text, keyword) for keyword in keywords):
            urgency = max(urgency, score)

    for score, keywords in IMPACT_SIGNALS:
        if any(contains_signal(text, keyword) for keyword in keywords):
            impact = max(impact, score)

    return urgency, impact


def calculate_priority_score(
    urgency: int | None,
    impact: int | None,
    confidence: float,
) -> float:
    """Calculate a deterministic priority score."""
    if urgency is None or impact is None:
        return 0.0

    return round(urgency * impact * confidence, 2)


def analyze_item(item: dict) -> dict:
    """Return an analyzed copy without modifying source facts."""
    analyzed_item = deepcopy(item)
    brief_section = classify_item(item)

    urgency, impact = calculate_priority_attributes(
        item,
        brief_section,
    )
    confidence = 0.6 if brief_section != "unclassified" else 0.0
    priority_score = calculate_priority_score(
        urgency,
        impact,
        confidence,
    )

    analyzed_item["analysis"] = {
        "brief_section": brief_section,
        "urgency": urgency,
        "impact": impact,
        "confidence": confidence,
        "priority_score": priority_score,
        "rationale": (
            f"Classified as {brief_section} with urgency {urgency} "
            f"and impact {impact} using transparent keyword rules."
        ),
        "analysis_method": "keyword_rules_v1",
        "analyzed_at": None,
    }

    return analyzed_item


def group_items(items: list[dict]) -> dict[str, list[dict]]:
    """Group source items by their morning-brief classification."""
    groups = {
        "accomplished": [],
        "before_next_brief": [],
        "roadblock_risk_or_bottleneck": [],
        "unclassified": [],
    }

    for item in items:
        analyzed_item = analyze_item(item)
        brief_section = analyzed_item["analysis"]["brief_section"]
        groups[brief_section].append(analyzed_item)

    for grouped_items in groups.values():
        grouped_items.sort(
            key=lambda item: item["analysis"]["priority_score"],
            reverse=True,
        )

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
