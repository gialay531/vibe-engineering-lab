from collections import Counter

REQUIRED_RESPONSE_FIELDS = (
    "prompt_version",
    "schema_version",
    "analysis_method",
    "analyzed_items",
    "excluded_items",
    "warnings",
)

REQUIRED_ANALYSIS_FIELDS = (
    "brief_section",
    "urgency",
    "impact",
    "confidence",
    "priority_score",
    "rationale",
    "analysis_method",
    "analyzed_at",
)

ALLOWED_BRIEF_SECTIONS = (
    "accomplished",
    "before_next_brief",
    "roadblock_risk_or_bottleneck",
    "unclassified",
)

SUPPORTED_PROMPT_VERSIONS = ("1.0",)
SUPPORTED_ANALYSIS_METHODS = ("ai_assisted_v1",)
ALLOWED_EXCLUSION_FIELDS = {"id", "reason"}


def collect_entry_ids(entries: list, collection_name: str) -> list[str]:
    """Return validated identifiers from one response collection."""
    identifiers = []

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{collection_name} entry at position {index} " "must be a JSON object."
            )

        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(
                f"{collection_name} entry at position {index} "
                "must contain a non-empty string id."
            )

        identifiers.append(identifier)

    return identifiers


def validate_analysis_response(source_data: dict, response: dict) -> None:
    """Validate response structure and complete source-ID coverage."""
    if not isinstance(response, dict):
        raise ValueError("Analysis response must be a JSON object.")

    missing_fields = [
        field for field in REQUIRED_RESPONSE_FIELDS if field not in response
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"Analysis response is missing required field(s): {missing}")

    for collection_name in ("analyzed_items", "excluded_items", "warnings"):
        if not isinstance(response[collection_name], list):
            raise ValueError(f"{collection_name} must be a JSON array.")

    analyzed_ids = collect_entry_ids(
        response["analyzed_items"],
        "analyzed_items",
    )
    excluded_ids = collect_entry_ids(
        response["excluded_items"],
        "excluded_items",
    )
    for index, entry in enumerate(response["analyzed_items"]):
        analysis = entry.get("analysis")

        if not isinstance(analysis, dict):
            raise ValueError(
                f"Analyzed item at position {index} "
                "must contain an analysis JSON object."
            )

        missing_fields = [
            field for field in REQUIRED_ANALYSIS_FIELDS if field not in analysis
        ]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(
                f"Analyzed item at position {index} "
                f"is missing required field(s): {missing}"
            )

        brief_section = analysis["brief_section"]
        if brief_section not in ALLOWED_BRIEF_SECTIONS:
            raise ValueError(f"Unsupported brief section: {brief_section}")

        for score_name in ("urgency", "impact"):
            score = analysis[score_name]

            if brief_section == "unclassified":
                if score is not None:
                    raise ValueError(
                        f"{score_name} must be null for unclassified items."
                    )
            elif (
                not isinstance(score, int)
                or isinstance(score, bool)
                or not 1 <= score <= 5
            ):
                raise ValueError(f"{score_name} must be an integer from 1 through 5.")

        confidence = analysis["confidence"]
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0.0 <= confidence <= 1.0
        ):
            raise ValueError("confidence must be a number from 0.0 through 1.0.")

        priority_score = analysis["priority_score"]
        if not isinstance(priority_score, (int, float)) or isinstance(
            priority_score, bool
        ):
            raise ValueError("priority score must be a number.")

        if brief_section == "unclassified":
            expected_priority_score = 0.0
        else:
            expected_priority_score = round(
                analysis["urgency"] * analysis["impact"] * confidence,
                2,
            )

        if priority_score != expected_priority_score:
            raise ValueError(
                "priority score does not match " "urgency × impact × confidence."
            )
        rationale = analysis["rationale"]
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("rationale must be a non-empty string.")

        if analysis["analysis_method"] != response["analysis_method"]:
            raise ValueError("item analysis method does not match response.")

        if analysis["analyzed_at"] is not None:
            raise ValueError("analyzed_at must be null.")

    result_ids = analyzed_ids + excluded_ids
    counts = Counter(result_ids)
    duplicate_ids = sorted(
        identifier for identifier, count in counts.items() if count > 1
    )
    if duplicate_ids:
        duplicates = ", ".join(duplicate_ids)
        raise ValueError(
            f"Analysis response contains duplicate item id(s): {duplicates}"
        )
    if response["prompt_version"] not in SUPPORTED_PROMPT_VERSIONS:
        raise ValueError(f"Unsupported prompt version: {response['prompt_version']}")

    if response["schema_version"] != source_data["schema_version"]:
        raise ValueError("Analysis response schema version does not match source data.")

    if response["analysis_method"] not in SUPPORTED_ANALYSIS_METHODS:
        raise ValueError(f"Unsupported analysis method: {response['analysis_method']}")

    if not all(isinstance(warning, str) for warning in response["warnings"]):
        raise ValueError("Every warning must be a string.")

    for index, entry in enumerate(response["excluded_items"]):
        extra_fields = set(entry) - ALLOWED_EXCLUSION_FIELDS
        if extra_fields:
            extras = ", ".join(sorted(extra_fields))
            raise ValueError(
                f"Excluded item at position {index} "
                f"contains prohibited field(s): {extras}"
            )

        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"Excluded item at position {index} " "must contain a non-empty reason."
            )

    source_ids = {item["id"] for item in source_data["items"]}
    response_ids = set(result_ids)

    unknown_ids = sorted(response_ids - source_ids)
    if unknown_ids:
        unknown = ", ".join(unknown_ids)
        raise ValueError(f"Analysis response contains unknown item id(s): {unknown}")

    missing_ids = sorted(source_ids - response_ids)
    if missing_ids:
        missing = ", ".join(missing_ids)
        raise ValueError(f"Analysis response is missing source item id(s): {missing}")

    source_items_by_id = {item["id"]: item for item in source_data["items"]}

    for entry in response["analyzed_items"]:
        source_item = source_items_by_id[entry["id"]]
        authorized_for_ai = source_item["governance"]["authorized_for_ai"]

        if authorized_for_ai is not True:
            raise ValueError(
                f"Item {entry['id']} is not authorized " "for AI processing."
            )
