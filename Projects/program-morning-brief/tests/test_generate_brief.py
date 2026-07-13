import sys
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

sys.path.insert(0, str(SRC_DIR))

from generate_brief import (
    generate_brief,
    group_items,
    load_program_data,
    save_brief,
    validate_program_data,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

sys.path.insert(0, str(SRC_DIR))

from generate_brief import (
    generate_brief,
    load_program_data,
    save_brief,
    validate_program_data,
)


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

    def test_brief_can_be_saved(self) -> None:
        """The saved file should contain the complete generated brief."""
        with TemporaryDirectory() as temporary_directory:
            output_file = save_brief(
                self.brief,
                self.data["brief_date"],
                Path(temporary_directory),
            )

            self.assertTrue(output_file.exists())
            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                self.brief,
            )

    def test_missing_top_level_field_is_rejected(self) -> None:
        """Missing briefing metadata should produce a clear error."""
        invalid_data = deepcopy(self.data)
        del invalid_data["brief_date"]

        with self.assertRaisesRegex(ValueError, "brief_date"):
            validate_program_data(invalid_data)

    def test_missing_item_field_is_rejected(self) -> None:
        """An incomplete source item should identify its position and field."""
        invalid_data = deepcopy(self.data)
        del invalid_data["items"][0]["title"]

        with self.assertRaisesRegex(
            ValueError,
            "Item at position 0.*title",
        ):
            validate_program_data(invalid_data)

    def test_sample_data_fills_all_three_sections(self) -> None:
        """The expanded dataset should supply three items per brief section."""
        groups = group_items(self.data["items"])

        self.assertEqual(len(groups["accomplished"]), 3)
        self.assertEqual(len(groups["before_next_brief"]), 3)
        self.assertEqual(len(groups["roadblock_risk_or_bottleneck"]), 3)
        self.assertEqual(len(groups["unclassified"]), 0)

    def test_unsupported_schema_version_is_rejected(self) -> None:
        """An unknown schema version should produce a clear error."""
        invalid_data = deepcopy(self.data)
        invalid_data["schema_version"] = "99.0"

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported schema version: 99.0",
        ):
            validate_program_data(invalid_data)


if __name__ == "__main__":
    unittest.main()
