import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"


def load_program_data(file_path: Path) -> dict:
    """Load and return program data from a JSON file."""
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    """Load the sample data and display a simple inventory."""
    data = load_program_data(DATA_FILE)

    print(f"Program: {data['program']['name']}")
    print(f"Brief date: {data['brief_date']}")
    print(f"Source items: {len(data['items'])}")
    print()

    for item in data["items"]:
        print(f"- {item['id']}: {item['title']} ({item['source_system']})")


if __name__ == "__main__":
    main()