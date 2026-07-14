import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

sys.path.insert(0, str(SRC_DIR))

from evaluate_brief import evaluate_brief, extract_bluf
from generate_brief import generate_brief, load_program_data


class TestEvaluateBrief(unittest.TestCase):
    """Verify objective evaluation checks for morning briefs."""

    def setUp(self) -> None:
        """Load the sample data and generate a valid brief."""
        self.data = load_program_data(DATA_FILE)
        self.brief = generate_brief(self.data)

    def test_valid_brief_passes(self) -> None:
        """The generated sample brief should pass objective checks."""
        result = evaluate_brief(self.data, self.brief)

        self.assertTrue(result["passed"])
        self.assertTrue(all(result["checks"].values()))

    def test_unknown_citation_is_rejected(self) -> None:
        """A citation absent from the dataset should fail evaluation."""
        invalid_brief = self.brief.replace(
            "**[JIRA-003]**",
            "**[UNKNOWN-001]**",
        )

        result = evaluate_brief(self.data, invalid_brief)

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["citations_exist_in_dataset"])

    def test_missing_citation_is_rejected(self) -> None:
        """A substantive bullet without a citation should fail evaluation."""
        invalid_brief = self.brief.replace(
            " **[TEAMS-001]**",
            "",
        )

        result = evaluate_brief(self.data, invalid_brief)

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["substantive_bullets_are_cited"])

    def test_duplicate_citation_is_rejected(self) -> None:
        """Reusing one citation for multiple bullets should fail evaluation."""
        invalid_brief = self.brief.replace(
            "**[EMAIL-001]**",
            "**[JIRA-003]**",
        )

        result = evaluate_brief(self.data, invalid_brief)

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["citations_are_unique"])

    def test_empty_bluf_is_rejected(self) -> None:
        """A blank BLUF should fail evaluation."""
        bluf = extract_bluf(self.brief)
        invalid_brief = self.brief.replace(bluf, "", 1)

        result = evaluate_brief(self.data, invalid_brief)

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["bluf_is_not_empty"])


if __name__ == "__main__":
    unittest.main()
