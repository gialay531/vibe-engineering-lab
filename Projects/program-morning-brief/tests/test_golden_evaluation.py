import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"
AI_RESPONSE_FILE = PROJECT_ROOT / "sample-data" / "ai-analysis-response.json"
GOLDEN_BRIEF_FILE = PROJECT_ROOT / "expected-output" / "morning-brief-2026-07-13.md"

sys.path.insert(0, str(SRC_DIR))

from analysis_interface import analyze_program_data
from evaluate_brief import CITATION_PATTERN, evaluate_brief
from generate_brief import generate_brief, load_program_data


class TestGoldenEvaluation(unittest.TestCase):
    """Verify the AI-assisted pipeline against approved sample data."""

    def setUp(self) -> None:
        """Load the approved synthetic dataset."""
        self.data = load_program_data(DATA_FILE)
        self.trusted_time = datetime.fromisoformat("2026-07-17T09:00:00-06:00")

    def test_complete_ai_response_fixture_is_accepted(self) -> None:
        """All nine approved items should receive validated AI analysis."""
        response = json.loads(AI_RESPONSE_FILE.read_text(encoding="utf-8"))

        result = analyze_program_data(
            self.data,
            analysis_method="ai_assisted_v1",
            ai_response=response,
            trusted_time=self.trusted_time,
        )

        analyzed_items = [item for item in result["items"] if "analysis" in item]

        self.assertEqual(len(analyzed_items), 9)
        self.assertTrue(
            all(
                item["analysis"]["analysis_method"] == "ai_assisted_v1"
                for item in analyzed_items
            )
        )
        self.assertTrue(
            all(
                item["analysis"]["analyzed_at"] == "2026-07-17T09:00:00-06:00"
                for item in analyzed_items
            )
        )

    def test_ai_assisted_brief_matches_golden_structure(self) -> None:
        """AI analysis should produce the approved sections and priorities."""
        response = json.loads(AI_RESPONSE_FILE.read_text(encoding="utf-8"))

        analyzed_data = analyze_program_data(
            self.data,
            analysis_method="ai_assisted_v1",
            ai_response=response,
            trusted_time=self.trusted_time,
        )
        brief = generate_brief(analyzed_data)
        evaluation = evaluate_brief(analyzed_data, brief)

        golden_brief = GOLDEN_BRIEF_FILE.read_text(encoding="utf-8")
        actual_citation_order = CITATION_PATTERN.findall(brief)
        golden_citation_order = CITATION_PATTERN.findall(golden_brief)

        self.assertTrue(evaluation["passed"])
        self.assertEqual(
            actual_citation_order,
            golden_citation_order,
        )


if __name__ == "__main__":
    unittest.main()
