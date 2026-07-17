import sys
import unittest
from copy import deepcopy
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from source_adapter import collect_source_items


class RecordingSourceAdapter:
    """Return fixed items while recording each requested lookback window."""

    def __init__(self, source_system: str, items: list[dict]) -> None:
        self.source_system = source_system
        self.items = items
        self.calls = []

    def fetch_items(
        self,
        lookback_start: datetime,
        lookback_end: datetime,
    ) -> list[dict]:
        """Record one source request and return an independent item copy."""
        self.calls.append(
            {
                "lookback_start": lookback_start,
                "lookback_end": lookback_end,
            }
        )
        return deepcopy(self.items)


class TestSourceAdapter(unittest.TestCase):
    """Verify the provider-neutral source boundary."""

    def test_items_are_collected_from_multiple_sources(self) -> None:
        """One coordinator should combine items from different adapters."""
        lookback_start = datetime.fromisoformat("2026-07-14T07:30:00-06:00")
        lookback_end = datetime.fromisoformat("2026-07-17T07:30:00-06:00")
        teams_items = [
            {
                "id": "TEAMS-101",
                "source_system": "Microsoft Teams",
            }
        ]
        jira_items = [
            {
                "id": "JIRA-101",
                "source_system": "Jira",
            }
        ]
        teams_adapter = RecordingSourceAdapter(
            "Microsoft Teams",
            teams_items,
        )
        jira_adapter = RecordingSourceAdapter(
            "Jira",
            jira_items,
        )

        result = collect_source_items(
            [teams_adapter, jira_adapter],
            lookback_start,
            lookback_end,
        )

        self.assertEqual(
            [item["id"] for item in result],
            ["TEAMS-101", "JIRA-101"],
        )
        self.assertEqual(
            teams_adapter.calls[0]["lookback_start"],
            lookback_start,
        )
        self.assertEqual(
            jira_adapter.calls[0]["lookback_end"],
            lookback_end,
        )

    def test_invalid_lookback_is_rejected_before_adapter_call(
        self,
    ) -> None:
        """An invalid time window must not reach a source system."""
        lookback_time = datetime.fromisoformat("2026-07-17T07:30:00-06:00")
        adapter = RecordingSourceAdapter(
            "Microsoft Teams",
            [],
        )

        with self.assertRaisesRegex(
            ValueError,
            "start must be before lookback end",
        ):
            collect_source_items(
                [adapter],
                lookback_time,
                lookback_time,
            )

        self.assertEqual(adapter.calls, [])

    def test_non_list_adapter_response_is_rejected(self) -> None:
        """Malformed source output must not enter the pipeline."""
        lookback_start = datetime.fromisoformat("2026-07-14T07:30:00-06:00")
        lookback_end = datetime.fromisoformat("2026-07-17T07:30:00-06:00")
        adapter = RecordingSourceAdapter(
            "Jira",
            [],
        )
        adapter.items = {
            "id": "JIRA-INVALID",
        }

        with self.assertRaisesRegex(
            ValueError,
            "Jira adapter must return a list",
        ):
            collect_source_items(
                [adapter],
                lookback_start,
                lookback_end,
            )

        self.assertEqual(len(adapter.calls), 1)

    def test_timezone_free_lookback_is_rejected_before_adapter_call(
        self,
    ) -> None:
        """A source request must use unambiguous timezone-aware times."""
        timezone_free_start = datetime(2026, 7, 14, 7, 30)
        lookback_end = datetime.fromisoformat("2026-07-17T07:30:00-06:00")
        adapter = RecordingSourceAdapter(
            "Microsoft Teams",
            [],
        )

        with self.assertRaisesRegex(
            ValueError,
            "must include timezone information",
        ):
            collect_source_items(
                [adapter],
                timezone_free_start,
                lookback_end,
            )

        self.assertEqual(adapter.calls, [])


if __name__ == "__main__":
    unittest.main()
