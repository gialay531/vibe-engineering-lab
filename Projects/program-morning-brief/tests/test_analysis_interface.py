from datetime import datetime
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

sys.path.insert(0, str(SRC_DIR))

from analysis_interface import analyze_program_data
from generate_brief import load_program_data


class TestAnalysisInterface(unittest.TestCase):
    """Verify selection of configurable analysis methods."""

    def setUp(self) -> None:
        """Load normalized synthetic source data."""
        self.data = load_program_data(DATA_FILE)

    def test_deterministic_method_analyzes_a_separate_copy(self) -> None:
        """Keyword analysis should not modify the source dataset."""
        result = analyze_program_data(
            self.data,
            analysis_method="keyword_rules_v1",
        )

        self.assertIsNot(result, self.data)
        self.assertNotIn("analysis", self.data["items"][0])
        self.assertEqual(
            result["items"][0]["analysis"]["analysis_method"],
            "keyword_rules_v1",
        )
        self.assertTrue(all("analysis" in item for item in result["items"]))

    def test_ai_assisted_method_applies_validated_response(self) -> None:
        """AI-assisted analysis should use the same interface."""
        self.data["items"][0]["governance"]["authorized_for_ai"] = True

        response = {
            "prompt_version": "1.0",
            "schema_version": "1.0",
            "analysis_method": "ai_assisted_v1",
            "analyzed_items": [
                {
                    "id": self.data["items"][0]["id"],
                    "analysis": {
                        "brief_section": "accomplished",
                        "urgency": 2,
                        "impact": 4,
                        "confidence": 0.9,
                        "priority_score": 7.2,
                        "rationale": (
                            "The source explicitly states that the "
                            "API contract was approved."
                        ),
                        "analysis_method": "ai_assisted_v1",
                        "analyzed_at": None,
                    },
                }
            ],
            "excluded_items": [
                {
                    "id": item["id"],
                    "reason": ("Item is not authorized for AI processing."),
                }
                for item in self.data["items"][1:]
            ],
            "warnings": [],
        }
        trusted_time = datetime.fromisoformat("2026-07-14T07:30:00-06:00")

        result = analyze_program_data(
            self.data,
            analysis_method="ai_assisted_v1",
            ai_response=response,
            trusted_time=trusted_time,
        )

        self.assertNotIn("analysis", self.data["items"][0])
        self.assertEqual(
            result["items"][0]["analysis"]["analysis_method"],
            "ai_assisted_v1",
        )
        self.assertEqual(
            result["items"][0]["analysis"]["analyzed_at"],
            "2026-07-14T07:30:00-06:00",
        )

    def test_ai_assisted_method_requires_response(self) -> None:
        """AI-assisted analysis cannot run without model output."""
        with self.assertRaisesRegex(
            ValueError,
            "requires an AI response",
        ):
            analyze_program_data(
                self.data,
                analysis_method="ai_assisted_v1",
            )

    def test_unsupported_method_is_rejected(self) -> None:
        """Unknown analysis methods must fail clearly."""
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported analysis method: mystery_method",
        ):
            analyze_program_data(
                self.data,
                analysis_method="mystery_method",
            )

    def test_ai_assisted_method_requires_trusted_time(self) -> None:
        """AI-assisted analysis requires a system-owned timestamp."""
        with self.assertRaisesRegex(
            ValueError,
            "requires a trusted time",
        ):
            analyze_program_data(
                self.data,
                analysis_method="ai_assisted_v1",
                ai_response={},
            )


if __name__ == "__main__":
    unittest.main()
