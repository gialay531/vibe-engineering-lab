from copy import deepcopy
from datetime import datetime

from validate_analysis_response import validate_analysis_response


def apply_analysis_response(
    source_data: dict,
    response: dict,
    trusted_time: datetime,
) -> dict:
    """Apply validated analysis to a separate copy of source data."""
    validate_analysis_response(source_data, response)

    if not isinstance(trusted_time, datetime):
        raise TypeError("trusted_time must be a datetime.")

    if trusted_time.tzinfo is None or trusted_time.utcoffset() is None:
        raise ValueError("trusted_time must include timezone information.")

    result = deepcopy(source_data)
    trusted_timestamp = trusted_time.isoformat()

    analysis_by_id = {
        entry["id"]: entry["analysis"] for entry in response["analyzed_items"]
    }

    for item in result["items"]:
        analysis = analysis_by_id.get(item["id"])

        if analysis is not None:
            item["analysis"] = deepcopy(analysis)
            item["analysis"]["analyzed_at"] = trusted_timestamp

    return result
