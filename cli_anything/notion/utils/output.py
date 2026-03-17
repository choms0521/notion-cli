"""Output formatting utilities for Notion CLI."""

import json
import sys
from typing import Any, Dict, List, Optional


def print_json(data: Any) -> None:
    """Print data as formatted JSON to stdout."""
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def print_table(headers: List[str], rows: List[List[str]]) -> None:
    """Print data as a formatted table."""
    if not rows:
        print("(no results)")
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "  ".join("-" * w for w in col_widths)
    print(header_line)
    print(separator)
    for row in rows:
        line = "  ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        print(line)


def extract_title(page: Dict[str, Any]) -> str:
    """Extract title from a Notion page object."""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            if title_arr:
                return "".join(t.get("plain_text", "") for t in title_arr)
    return "(untitled)"


def extract_page_summary(page: Dict[str, Any]) -> Dict[str, str]:
    """Extract a summary dict from a page object."""
    return {
        "id": page.get("id", ""),
        "title": extract_title(page),
        "url": page.get("url", ""),
        "created": page.get("created_time", "")[:10],
        "updated": page.get("last_edited_time", "")[:10],
    }


def format_rich_text(rich_text_list: List[Dict[str, Any]]) -> str:
    """Convert Notion rich_text array to plain text."""
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def truncate(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"
