import json
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
    NORMALIZED_ITEM_DEFAULTS,
    GOVERNANCE_DEFAULTS,
    generate_brief,
    group_items,
    load_program_data,
    normalize_program_data,
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
    analyze_item,
)


class TestGenerateBrief(unittest.TestCase):
    """Verify the required behavior of the morning brief generator."""

    def setUp(self) -> None:
        """Load the sample data and generate a fresh brief before each test."""
        self.data = load_program_data(DATA_FILE)
        self.brief = generate_brief(self.data)

    def test_sample_items_are_explicitly_authorized_for_ai(self) -> None:
        """Approved synthetic items must declare their governance explicitly."""
        with DATA_FILE.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)

        expected_governance = {
            "sensitivity": "public",
            "authorized_for_ai": True,
            "retention_policy": None,
            "contains_personal_data": False,
        }

        noncompliant_ids = [
            item["id"]
            for item in raw_data["items"]
            if item.get("governance") != expected_governance
        ]

        self.assertEqual(
            noncompliant_ids,
            [],
            (
                "Synthetic items without explicit approved governance: "
                f"{noncompliant_ids}"
            ),
        )

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

    def test_optional_metadata_is_normalized_without_mutating_input(self) -> None:
        """Missing metadata should become null in a separate normalized copy."""
        raw_data = deepcopy(self.data)

        for field in NORMALIZED_ITEM_DEFAULTS:
            raw_data["items"][0].pop(field, None)

        normalized_data = normalize_program_data(raw_data)

        for field in NORMALIZED_ITEM_DEFAULTS:
            self.assertNotIn(field, raw_data["items"][0])
            self.assertIsNone(normalized_data["items"][0][field])

    def test_missing_governance_uses_fail_safe_defaults(self) -> None:
        """Missing governance should default to restricted and unauthorized."""
        raw_data = deepcopy(self.data)
        raw_data["items"][0].pop("governance", None)

        normalized_data = normalize_program_data(raw_data)
        governance = normalized_data["items"][0]["governance"]

        self.assertNotIn("governance", raw_data["items"][0])
        self.assertEqual(governance, GOVERNANCE_DEFAULTS)
        self.assertEqual(governance["sensitivity"], "restricted")
        self.assertFalse(governance["authorized_for_ai"])

    def test_governance_must_be_an_object(self) -> None:
        """Malformed governance data should be rejected."""
        invalid_data = deepcopy(self.data)
        invalid_data["items"][0]["governance"] = "restricted"

        with self.assertRaisesRegex(
            ValueError,
            "Governance for item at position 0 must be a JSON object",
        ):
            validate_program_data(invalid_data)

    def test_unsupported_sensitivity_is_rejected(self) -> None:
        """Sensitivity must use an allowed governance classification."""
        invalid_data = deepcopy(self.data)
        invalid_data["items"][0]["governance"]["sensitivity"] = "secret"

        with self.assertRaisesRegex(
            ValueError,
            "unsupported sensitivity: secret",
        ):
            validate_program_data(invalid_data)

    def test_analysis_is_separate_from_source_facts(self) -> None:
        """Derived analysis should be added only to an independent copy."""
        source_item = deepcopy(self.data["items"][0])
        analyzed_item = analyze_item(source_item)

        self.assertNotIn("analysis", source_item)
        self.assertIn("analysis", analyzed_item)

        self.assertEqual(analyzed_item["id"], source_item["id"])
        self.assertEqual(analyzed_item["content"], source_item["content"])
        self.assertEqual(
            analyzed_item["analysis"]["brief_section"],
            "accomplished",
        )
        self.assertEqual(
            analyzed_item["analysis"]["analysis_method"],
            "keyword_rules_v1",
        )

    def test_priority_attributes_follow_transparent_rules(self) -> None:
        """Urgency and impact should reflect documented keyword signals."""
        accomplishment = analyze_item(self.data["items"][0])

        blocked_risk_source = next(
            item for item in self.data["items"] if item["id"] == "JIRA-003"
        )
        blocked_risk = analyze_item(blocked_risk_source)

        self.assertEqual(accomplishment["analysis"]["urgency"], 1)
        self.assertEqual(accomplishment["analysis"]["impact"], 4)

        self.assertEqual(blocked_risk["analysis"]["urgency"], 5)
        self.assertEqual(blocked_risk["analysis"]["impact"], 5)

    def test_items_are_sorted_by_descending_priority_score(self) -> None:
        """Each brief section should place higher-priority items first."""
        groups = group_items(self.data["items"])
        risk_items = groups["roadblock_risk_or_bottleneck"]

        scores = [item["analysis"]["priority_score"] for item in risk_items]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(scores[0], 15.0)

    def test_late_signal_does_not_match_latest(self) -> None:
        """The word latest should not be interpreted as a late signal."""
        accessibility_source = next(
            item for item in self.data["items"] if item["id"] == "JIRA-002"
        )

        analyzed_item = analyze_item(accessibility_source)

        self.assertEqual(analyzed_item["analysis"]["urgency"], 1)

    def test_grouping_preserves_precomputed_analysis(self) -> None:
        """Validated analysis must not be replaced by keyword rules."""
        source_item = deepcopy(self.data["items"][0])
        source_item["analysis"] = {
            "brief_section": "roadblock_risk_or_bottleneck",
            "urgency": 5,
            "impact": 5,
            "confidence": 1.0,
            "priority_score": 25.0,
            "rationale": (
                "A validated AI response classified this item "
                "as a critical program risk."
            ),
            "analysis_method": "ai_assisted_v1",
            "analyzed_at": "2026-07-17T09:00:00-06:00",
        }

        groups = group_items([source_item])
        grouped_item = groups["roadblock_risk_or_bottleneck"][0]

        self.assertIsNot(grouped_item, source_item)
        self.assertEqual(
            grouped_item["analysis"],
            source_item["analysis"],
        )
        self.assertEqual(
            grouped_item["analysis"]["analysis_method"],
            "ai_assisted_v1",
        )


if __name__ == "__main__":
    unittest.main()
