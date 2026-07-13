import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

sys.path.insert(0, str(SRC_DIR))

from generate_brief import generate_brief, load_program_data


class TestGenerateBrief(unittest.TestCase):
    """Verify the required behavior of the morning brief generator."""

    def setUp(self) -> None:
        """Load the sample data and generate a fresh brief before each test."""
        self.data = load_program_data(DATA_FILE)
        self.brief = generate_brief(self.data)

    def test_required_sections_are_present(self) -> None:
        """The brief should contain the BLUF and all three required sections."""
        required_headings = (
            "## BLUF",
            "## 1. Accomplished Since the Previous Brief",
            "## 2. Before the Next Brief",
            "## 3. Roadblocks, Risks, and Bottlenecks",
        )

        for heading in required_headings:
            self.assertIn(heading, self.brief)

    def test_brief_contains_exactly_nine_bullets(self) -> None:
        """The three sections should contain three bullets each."""
        self.assertEqual(self.brief.count("\n- "), 9)

    def test_every_source_item_is_cited(self) -> None:
        """Every sample source item should have a citation in the brief."""
        for item in self.data["items"]:
            citation = f"**[{item['id']}]**"
            self.assertIn(citation, self.brief)


if __name__ == "__main__":
    unittest.main()