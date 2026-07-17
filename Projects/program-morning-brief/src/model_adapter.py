from copy import deepcopy
from datetime import datetime
from typing import Protocol

from analysis_interface import analyze_program_data


class ModelAdapter(Protocol):
    """Provider-neutral contract for structured AI analysis."""

    def analyze(
        self,
        prompt: str,
        source_data: dict,
    ) -> dict:
        """Return one structured analysis response."""
        ...


def analyze_with_model(
    source_data: dict,
    adapter: ModelAdapter,
    prompt: str,
    trusted_time: datetime,
) -> dict:
    """Run one model adapter and safely apply its response."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Model analysis requires a non-empty prompt.")

    model_input = deepcopy(source_data)
    authorized_items = []
    system_exclusions = []

    for item in model_input["items"]:
        governance = item.get("governance")
        authorized_for_ai = (
            isinstance(governance, dict) and governance.get("authorized_for_ai") is True
        )

        if authorized_for_ai:
            authorized_items.append(item)
        else:
            system_exclusions.append(
                {
                    "id": item["id"],
                    "reason": (
                        "Item was excluded by the system governance "
                        "gate before model processing."
                    ),
                }
            )

    model_input["items"] = authorized_items
    response = deepcopy(adapter.analyze(prompt, model_input))

    if isinstance(response, dict) and isinstance(response.get("excluded_items"), list):
        response["excluded_items"].extend(system_exclusions)

    return analyze_program_data(
        source_data,
        analysis_method="ai_assisted_v1",
        ai_response=response,
        trusted_time=trusted_time,
    )
