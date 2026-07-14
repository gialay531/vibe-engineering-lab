import sys
import unittest
from copy import deepcopy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"

sys.path.insert(0, str(SRC_DIR))

from generate_brief import load_program_data
from validate_analysis_response import validate_analysis_response


class TestValidateAnalysisResponse(unittest.TestCase):
    """Verify structural validation of analysis responses."""

    def setUp(self) -> None:
        """Create a valid response that safely excludes all source items."""
        self.data = load_program_data(DATA_FILE)
        self.valid_response = {
            "prompt_version": "1.0",
            "schema_version": "1.0",
            "analysis_method": "ai_assisted_v1",
            "analyzed_items": [],
            "excluded_items": [
                {
                    "id": item["id"],
                    "reason": "Item is not authorized for AI processing.",
                }
                for item in self.data["items"]
            ],
            "warnings": [],
        }

    def make_response_with_analyzed_item(self) -> dict:
        """Return a valid response containing one authorized analyzed item."""
        response = deepcopy(self.valid_response)
        excluded_item = response["excluded_items"].pop(0)

        self.data["items"][0]["governance"]["authorized_for_ai"] = True

        response["analyzed_items"].append(
            {
                "id": excluded_item["id"],
                "analysis": {
                    "brief_section": "accomplished",
                    "urgency": 2,
                    "impact": 4,
                    "confidence": 0.9,
                    "priority_score": 7.2,
                    "rationale": (
                        "The source explicitly states that the API "
                        "contract was approved."
                    ),
                    "analysis_method": "ai_assisted_v1",
                    "analyzed_at": None,
                },
            }
        )

        return response

    def test_missing_analysis_field_is_rejected(self) -> None:
        """Every analyzed item must contain all required analysis fields."""
        invalid_response = self.make_response_with_analyzed_item()
        del invalid_response["analyzed_items"][0]["analysis"]["rationale"]

        with self.assertRaisesRegex(
            ValueError,
            "missing required field.*rationale",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_complete_response_is_accepted(self) -> None:
        """Every source ID appearing exactly once should pass."""
        validate_analysis_response(self.data, self.valid_response)

    def test_missing_source_id_is_rejected(self) -> None:
        """Every source item must appear in the response."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["excluded_items"].pop()

        with self.assertRaisesRegex(
            ValueError,
            "missing source item id",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_duplicate_id_is_rejected(self) -> None:
        """One source ID cannot appear more than once."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["excluded_items"].append(
            deepcopy(invalid_response["excluded_items"][0])
        )

        with self.assertRaisesRegex(
            ValueError,
            "duplicate item id",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_unknown_id_is_rejected(self) -> None:
        """The response cannot introduce an unknown source ID."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["excluded_items"][0]["id"] = "UNKNOWN-001"

        with self.assertRaisesRegex(
            ValueError,
            "unknown item id",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_missing_response_field_is_rejected(self) -> None:
        """All required top-level response fields must be present."""
        invalid_response = deepcopy(self.valid_response)
        del invalid_response["warnings"]

        with self.assertRaisesRegex(
            ValueError,
            "missing required field.*warnings",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_unsupported_prompt_version_is_rejected(self) -> None:
        """The response must use a supported prompt contract version."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["prompt_version"] = "99.0"

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported prompt version: 99.0",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_schema_version_mismatch_is_rejected(self) -> None:
        """The response schema must match the source-data schema."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["schema_version"] = "99.0"

        with self.assertRaisesRegex(
            ValueError,
            "schema version does not match",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_excluded_item_cannot_repeat_source_content(self) -> None:
        """Excluded items must not reproduce protected source content."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["excluded_items"][0]["content"] = "Sensitive source content"

        with self.assertRaisesRegex(
            ValueError,
            "contains prohibited field.*content",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_unsupported_analysis_method_is_rejected(self) -> None:
        """The response must identify a supported analysis method."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["analysis_method"] = "unknown_method"

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported analysis method: unknown_method",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_warning_must_be_a_string(self) -> None:
        """Every warning must be represented as text."""
        invalid_response = deepcopy(self.valid_response)
        invalid_response["warnings"] = [{"message": "Review required"}]

        with self.assertRaisesRegex(
            ValueError,
            "Every warning must be a string",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_unsupported_brief_section_is_rejected(self) -> None:
        """An analyzed item must use an allowed brief section."""
        invalid_response = self.make_response_with_analyzed_item()
        invalid_response["analyzed_items"][0]["analysis"][
            "brief_section"
        ] = "something_else"

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported brief section: something_else",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_urgency_outside_allowed_range_is_rejected(self) -> None:
        """Urgency must be an integer from 1 through 5."""
        invalid_response = self.make_response_with_analyzed_item()
        invalid_response["analyzed_items"][0]["analysis"]["urgency"] = 6

        with self.assertRaisesRegex(
            ValueError,
            "urgency must be an integer from 1 through 5",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_confidence_outside_allowed_range_is_rejected(self) -> None:
        """Confidence must be a number from 0.0 through 1.0."""
        invalid_response = self.make_response_with_analyzed_item()
        invalid_response["analyzed_items"][0]["analysis"]["confidence"] = 1.1

        with self.assertRaisesRegex(
            ValueError,
            "confidence must be a number from 0.0 through 1.0",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_incorrect_priority_score_is_rejected(self) -> None:
        """Priority score must equal urgency times impact times confidence."""
        invalid_response = self.make_response_with_analyzed_item()
        invalid_response["analyzed_items"][0]["analysis"]["priority_score"] = 99.0

        with self.assertRaisesRegex(
            ValueError,
            "priority score does not match",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_blank_rationale_is_rejected(self) -> None:
        """An analyzed item must include a meaningful rationale."""
        invalid_response = self.make_response_with_analyzed_item()
        invalid_response["analyzed_items"][0]["analysis"]["rationale"] = "   "

        with self.assertRaisesRegex(
            ValueError,
            "rationale must be a non-empty string",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_item_analysis_method_must_match_response(self) -> None:
        """Item provenance must match the response analysis method."""
        invalid_response = self.make_response_with_analyzed_item()
        invalid_response["analyzed_items"][0]["analysis"][
            "analysis_method"
        ] = "different_method"

        with self.assertRaisesRegex(
            ValueError,
            "item analysis method does not match response",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_ai_supplied_timestamp_is_rejected(self) -> None:
        """The calling system, not the AI, must add the trusted timestamp."""
        invalid_response = self.make_response_with_analyzed_item()
        invalid_response["analyzed_items"][0]["analysis"][
            "analyzed_at"
        ] = "2026-07-14T07:30:00-06:00"

        with self.assertRaisesRegex(
            ValueError,
            "analyzed_at must be null",
        ):
            validate_analysis_response(self.data, invalid_response)

    def test_unauthorized_item_cannot_be_analyzed(self) -> None:
        """Governance must prevent unauthorized AI analysis."""
        invalid_response = self.make_response_with_analyzed_item()
        self.data["items"][0]["governance"]["authorized_for_ai"] = False

        with self.assertRaisesRegex(
            ValueError,
            "not authorized for AI processing",
        ):
            validate_analysis_response(self.data, invalid_response)


if __name__ == "__main__":
    unittest.main()
