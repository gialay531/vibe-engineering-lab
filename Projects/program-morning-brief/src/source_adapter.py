from datetime import datetime
from typing import Protocol


class SourceAdapter(Protocol):
    """Provider-neutral contract for retrieving canonical source items."""

    source_system: str

    def fetch_items(
        self,
        lookback_start: datetime,
        lookback_end: datetime,
    ) -> list[dict]:
        """Return canonical items found within the requested time window."""
        ...


def collect_source_items(
    adapters: list[SourceAdapter],
    lookback_start: datetime,
    lookback_end: datetime,
) -> list[dict]:
    """Collect independent canonical items from each source adapter."""
    if lookback_start.tzinfo is None or lookback_end.tzinfo is None:
        raise ValueError("Source lookback times must include timezone information.")
    if lookback_start >= lookback_end:
        raise ValueError("Source lookback start must be before lookback end.")

    collected_items = []

    for adapter in adapters:
        source_items = adapter.fetch_items(
            lookback_start,
            lookback_end,
        )

        if not isinstance(source_items, list):
            raise ValueError(f"{adapter.source_system} adapter must return a list.")

        collected_items.extend(source_items)

    return collected_items
