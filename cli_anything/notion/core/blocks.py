"""Blocks endpoint commands."""

from typing import Any, Dict, List, Optional

from notion_client import Client

from cli_anything.notion.utils.output import (
    format_rich_text,
    print_json,
    print_table,
    truncate,
)
from cli_anything.notion.utils.pagination import collect_all


def block_retrieve(client: Client, block_id: str, as_json: bool = False) -> Dict[str, Any]:
    """Retrieve a block by ID."""
    result = client.blocks.retrieve(block_id=block_id)
    if as_json:
        print_json(result)
    else:
        print(f"ID:   {result.get('id')}")
        print(f"Type: {result.get('type')}")
        print(f"Has children: {result.get('has_children', False)}")
        block_type = result.get("type", "")
        block_data = result.get(block_type, {})
        rt = block_data.get("rich_text", [])
        if rt:
            print(f"Text: {format_rich_text(rt)}")
    return result


def block_children_list(
    client: Client,
    block_id: str,
    all_pages: bool = False,
    as_json: bool = False,
) -> List[Dict[str, Any]]:
    """List child blocks."""
    if all_pages:
        results = collect_all(client.blocks.children.list, block_id=block_id)
    else:
        response = client.blocks.children.list(block_id=block_id)
        results = response.get("results", [])

    if as_json:
        print_json(results)
    else:
        rows = []
        for b in results:
            btype = b.get("type", "")
            bdata = b.get(btype, {})
            rt = bdata.get("rich_text", [])
            text = truncate(format_rich_text(rt), 60) if rt else ""
            rows.append([b.get("id", "")[:8], btype, text])
        print_table(["ID", "Type", "Content"], rows)
    return results


def block_children_append(
    client: Client,
    block_id: str,
    children: List[Dict[str, Any]],
    as_json: bool = False,
) -> Dict[str, Any]:
    """Append child blocks."""
    result = client.blocks.children.append(block_id=block_id, children=children)
    if as_json:
        print_json(result)
    else:
        added = result.get("results", [])
        print(f"Appended {len(added)} block(s)")
    return result


def block_append_text(
    client: Client,
    block_id: str,
    text: str,
    block_type: str = "paragraph",
    language: Optional[str] = None,
    as_json: bool = False,
) -> Dict[str, Any]:
    """Append a text block (convenience wrapper)."""
    if block_type == "code":
        block_data: Dict[str, Any] = {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "language": language or "plain text",
        }
    elif block_type == "divider":
        block_data = {}
    else:
        block_data = {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }

    children = [
        {
            "object": "block",
            "type": block_type,
            block_type: block_data,
        }
    ]
    return block_children_append(client, block_id, children, as_json)


def block_update(
    client: Client, block_id: str, updates: Dict[str, Any], as_json: bool = False
) -> Dict[str, Any]:
    """Update a block."""
    result = client.blocks.update(block_id=block_id, **updates)
    if as_json:
        print_json(result)
    else:
        print(f"Updated block: {result.get('id')}")
    return result


def block_update_text(
    client: Client,
    block_id: str,
    text: str,
    block_type: Optional[str] = None,
    language: Optional[str] = None,
    as_json: bool = False,
) -> Dict[str, Any]:
    """Update a block's text content. Auto-detects block type if not provided."""
    if not block_type:
        existing = client.blocks.retrieve(block_id=block_id)
        block_type = existing.get("type", "paragraph")

    if block_type == "code":
        updates: Dict[str, Any] = {
            block_type: {
                "rich_text": [{"type": "text", "text": {"content": text}}],
            }
        }
        if language:
            updates[block_type]["language"] = language
    else:
        updates = {
            block_type: {
                "rich_text": [{"type": "text", "text": {"content": text}}],
            }
        }

    return block_update(client, block_id, updates, as_json)


def block_delete(client: Client, block_id: str, as_json: bool = False) -> Dict[str, Any]:
    """Delete (archive) a block."""
    result = client.blocks.delete(block_id=block_id)
    if as_json:
        print_json(result)
    else:
        print(f"Deleted block: {result.get('id')}")
    return result
