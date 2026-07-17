import json
import sys
import unittest
from copy import deepcopy
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_FILE = PROJECT_ROOT / "sample-data" / "program-items.json"
AI_RESPONSE_FILE = PROJECT_ROOT / "sample-data" / "ai-analysis-response.json"
PROMPT_FILE = PROJECT_ROOT / "prompts" / "analyze-program-items.md"

sys.path.insert(0, str(SRC_DIR))

from generate_brief import load_program_data
from model_adapter import analyze_with_model


class RecordingAdapter:
    """Return a fixed response while recording model inputs."""

    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls = []

    def analyze(self, prompt: str, source_data: dict) -> dict:
        """Record one call and return an independent response copy."""
        self.calls.append(
            {
                "prompt": prompt,
                "source_data": deepcopy(source_data),
            }
        )
        return deepcopy(self.response)


class TestModelAdapter(unittest.TestCase):
    """Verify the provider-neutral model boundary."""

    def setUp(self) -> None:
        """Load approved synthetic inputs and a fixed model response."""
        self.data = load_program_data(DATA_FILE)
        self.response = json.loads(AI_RESPONSE_FILE.read_text(encoding="utf-8"))
        self.prompt = PROMPT_FILE.read_text(encoding="utf-8")
        self.trusted_time = datetime.fromisoformat("2026-07-17T09:00:00-06:00")

    def test_adapter_response_runs_through_analysis_pipeline(self) -> None:
        """A provider response should be validated and safely applied."""
        adapter = RecordingAdapter(self.response)

        result = analyze_with_model(
            self.data,
            adapter,
            self.prompt,
            self.trusted_time,
        )

        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(adapter.calls[0]["prompt"], self.prompt)
        self.assertIsNot(
            adapter.calls[0]["source_data"],
            self.data,
        )
        self.assertNotIn("analysis", self.data["items"][0])
        self.assertEqual(
            result["items"][0]["analysis"]["analysis_method"],
            "ai_assisted_v1",
        )

    def test_unauthorized_items_are_filtered_before_adapter_call(
        self,
    ) -> None:
        """Unauthorized source content must not reach a model provider."""
        unauthorized_id = self.data["items"][0]["id"]
        self.data["items"][0]["governance"]["authorized_for_ai"] = False

        response = deepcopy(self.response)
        response["analyzed_items"] = [
            entry
            for entry in response["analyzed_items"]
            if entry["id"] != unauthorized_id
        ]

        adapter = RecordingAdapter(response)

        result = analyze_with_model(
            self.data,
            adapter,
            self.prompt,
            self.trusted_time,
        )

        sent_ids = {item["id"] for item in adapter.calls[0]["source_data"]["items"]}

        self.assertNotIn(unauthorized_id, sent_ids)
        self.assertNotIn("analysis", result["items"][0])

    def test_empty_prompt_is_rejected_before_adapter_call(self) -> None:
        """A provider must not be called without versioned instructions."""
        adapter = RecordingAdapter(self.response)

        with self.assertRaisesRegex(
            ValueError,
            "requires a non-empty prompt",
        ):
            analyze_with_model(
                self.data,
                adapter,
                "   ",
                self.trusted_time,
            )

        self.assertEqual(adapter.calls, [])

    def test_invalid_provider_response_is_rejected(self) -> None:
        """Provider output must not bypass response validation."""
        invalid_response = deepcopy(self.response)
        invalid_response["analyzed_items"][0]["analysis"]["priority_score"] = 99.0
        adapter = RecordingAdapter(invalid_response)

        with self.assertRaisesRegex(
            ValueError,
            "priority score does not match",
        ):
            analyze_with_model(
                self.data,
                adapter,
                self.prompt,
                self.trusted_time,
            )


if __name__ == "__main__":
    unittest.main()
