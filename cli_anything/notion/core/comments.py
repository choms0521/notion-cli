"""Comments endpoint commands."""

from typing import Any, Dict, List, Optional

from notion_client import Client

from cli_anything.notion.utils.output import format_rich_text, print_json, print_table, truncate


def comments_list(
    client: Client,
    block_id: str,
    as_json: bool = False,
) -> List[Dict[str, Any]]:
    """List comments on a block/page."""
    response = client.comments.list(block_id=block_id)
    results = response.get("results", [])

    if as_json:
        print_json(results)
    else:
        rows = []
        for c in results:
            text = format_rich_text(c.get("rich_text", []))
            rows.append([
                c.get("id", "")[:8],
                truncate(text, 50),
                c.get("created_time", "")[:10],
            ])
        print_table(["ID", "Text", "Created"], rows)
    return results


def comments_create(
    client: Client,
    parent_id: str,
    text: str,
    discussion_id: Optional[str] = None,
    as_json: bool = False,
) -> Dict[str, Any]:
    """Create a comment."""
    kwargs: Dict[str, Any] = {
        "rich_text": [{"type": "text", "text": {"content": text}}],
    }
    if discussion_id:
        kwargs["discussion_id"] = discussion_id
    else:
        kwargs["parent"] = {"page_id": parent_id}

    result = client.comments.create(**kwargs)
    if as_json:
        print_json(result)
    else:
        print(f"Created comment: {result.get('id')}")
    return result
