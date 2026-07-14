from copy import deepcopy
from datetime import datetime

from apply_analysis_response import apply_analysis_response
from generate_brief import analyze_item

DETERMINISTIC_ANALYSIS_METHOD = "keyword_rules_v1"
AI_ASSISTED_ANALYSIS_METHOD = "ai_assisted_v1"


def analyze_program_data(
    source_data: dict,
    analysis_method: str,
    ai_response: dict | None = None,
    trusted_time: datetime | None = None,
) -> dict:
    """Analyze a source-data copy using the selected method."""
    if analysis_method == DETERMINISTIC_ANALYSIS_METHOD:
        result = deepcopy(source_data)
        result["items"] = [analyze_item(item) for item in result["items"]]
        return result

    if analysis_method == AI_ASSISTED_ANALYSIS_METHOD:
        if ai_response is None:
            raise ValueError("AI-assisted analysis requires an AI response.")

        if trusted_time is None:
            raise ValueError("AI-assisted analysis requires a trusted time.")

        return apply_analysis_response(
            source_data,
            ai_response,
            trusted_time,
        )

    raise ValueError(f"Unsupported analysis method: {analysis_method}")
