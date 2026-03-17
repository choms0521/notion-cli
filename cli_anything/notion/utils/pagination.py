"""Pagination utilities for Notion CLI."""

from typing import Any, Callable, Dict, List


def collect_all(
    api_call: Callable[..., Dict[str, Any]],
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Auto-paginate a Notion API list endpoint, collecting all results."""
    results: List[Dict[str, Any]] = []
    has_more = True
    start_cursor = kwargs.pop("start_cursor", None)

    while has_more:
        call_kwargs = {**kwargs}
        if start_cursor:
            call_kwargs["start_cursor"] = start_cursor

        response = api_call(**call_kwargs)
        results.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")

    return results
