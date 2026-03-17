"""Search endpoint commands."""

from typing import Any, Dict, List, Optional

from notion_client import Client

from cli_anything.notion.utils.output import (
    extract_title,
    print_json,
    print_table,
    truncate,
)
from cli_anything.notion.utils.pagination import collect_all


def search(
    client: Client,
    query: str = "",
    filter_type: Optional[str] = None,
    all_pages: bool = False,
    as_json: bool = False,
) -> List[Dict[str, Any]]:
    """Search pages and databases."""
    kwargs: Dict[str, Any] = {}
    if query:
        kwargs["query"] = query
    if filter_type:
        kwargs["filter"] = {"value": filter_type, "property": "object"}

    if all_pages:
        results = collect_all(client.search, **kwargs)
    else:
        response = client.search(**kwargs)
        results = response.get("results", [])

    if as_json:
        print_json(results)
    else:
        rows = []
        for item in results:
            obj_type = item.get("object", "")
            title = extract_title(item) if obj_type == "page" else ""
            if obj_type == "database":
                title_arr = item.get("title", [])
                title = "".join(t.get("plain_text", "") for t in title_arr)
            rows.append([
                item.get("id", "")[:8],
                obj_type,
                truncate(title, 40),
                item.get("url", ""),
            ])
        print_table(["ID", "Type", "Title", "URL"], rows)
    return results
