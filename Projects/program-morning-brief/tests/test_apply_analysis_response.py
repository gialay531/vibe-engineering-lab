import sys
import unittest
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from apply_analysis_response import apply_analysis_response


class TestApplyAnalysisResponse(unittest.TestCase):
    """Verify safe application of validated AI analysis."""

    def setUp(self) -> None:
        """Create valid source data, response data, and trusted time."""
        self.source_data = {
            "schema_version": "1.0",
            "items": [
                {
                    "id": "ITEM-001",
                    "title": "API contract approved",
                    "governance": {
                        "authorized_for_ai": True,
                    },
                }
            ],
        }
        self.response = {
            "prompt_version": "1.0",
            "schema_version": "1.0",
            "analysis_method": "ai_assisted_v1",
            "analyzed_items": [
                {
                    "id": "ITEM-001",
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
            "excluded_items": [],
            "warnings": [],
        }
        self.trusted_time = datetime.fromisoformat("2026-07-14T07:30:00-06:00")

    def test_analysis_is_applied_to_a_separate_copy(self) -> None:
        """Source facts remain unchanged and receive a trusted timestamp."""
        result = apply_analysis_response(
            self.source_data,
            self.response,
            self.trusted_time,
        )

        self.assertIsNot(result, self.source_data)
        self.assertNotIn("analysis", self.source_data["items"][0])
        self.assertEqual(
            result["items"][0]["analysis"]["brief_section"],
            "accomplished",
        )
        self.assertEqual(
            result["items"][0]["analysis"]["analyzed_at"],
            "2026-07-14T07:30:00-06:00",
        )

    def test_excluded_source_item_remains_unanalyzed(self) -> None:
        """Excluded items remain in the copy without derived analysis."""
        self.source_data["items"].append(
            {
                "id": "ITEM-002",
                "title": "Restricted program update",
                "governance": {
                    "authorized_for_ai": False,
                },
            }
        )
        self.response["excluded_items"].append(
            {
                "id": "ITEM-002",
                "reason": "Item is not authorized for AI processing.",
            }
        )

        result = apply_analysis_response(
            self.source_data,
            self.response,
            self.trusted_time,
        )

        self.assertNotIn("analysis", result["items"][1])

    def test_invalid_response_is_rejected(self) -> None:
        """Analysis must pass validation before it can be applied."""
        self.response["analyzed_items"][0]["analysis"]["priority_score"] = 99.0

        with self.assertRaisesRegex(
            ValueError,
            "priority score does not match",
        ):
            apply_analysis_response(
                self.source_data,
                self.response,
                self.trusted_time,
            )

        self.assertNotIn("analysis", self.source_data["items"][0])

    def test_trusted_time_requires_timezone(self) -> None:
        """A trusted timestamp must identify its timezone."""
        timezone_free_time = datetime(2026, 7, 14, 7, 30)

        with self.assertRaisesRegex(
            ValueError,
            "must include timezone information",
        ):
            apply_analysis_response(
                self.source_data,
                self.response,
                timezone_free_time,
            )


if __name__ == "__main__":
    unittest.main()
