"""Pages endpoint commands."""

import json
from typing import Any, Dict, Optional

from notion_client import Client

from cli_anything.notion.utils.output import (
    extract_page_summary,
    extract_title,
    format_rich_text,
    print_json,
    print_table,
    truncate,
)
from cli_anything.notion.utils.pagination import collect_all


def page_retrieve(client: Client, page_id: str, as_json: bool = False) -> Dict[str, Any]:
    """Retrieve a page by ID."""
    result = client.pages.retrieve(page_id=page_id)
    if as_json:
        print_json(result)
    else:
        summary = extract_page_summary(result)
        print(f"ID:      {summary['id']}")
        print(f"Title:   {summary['title']}")
        print(f"URL:     {summary['url']}")
        print(f"Created: {summary['created']}")
        print(f"Updated: {summary['updated']}")
    return result


def page_create(
    client: Client,
    parent_id: str,
    title: str,
    parent_type: str = "page_id",
    content: Optional[str] = None,
    as_json: bool = False,
) -> Dict[str, Any]:
    """Create a new page."""
    parent = {"type": parent_type, parent_type: parent_id}
    properties: Dict[str, Any] = {
        "title": [{"text": {"content": title}}],
    }

    kwargs: Dict[str, Any] = {"parent": parent, "properties": properties}
    if content:
        kwargs["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                },
            }
        ]

    result = client.pages.create(**kwargs)
    if as_json:
        print_json(result)
    else:
        print(f"Created page: {result.get('id')}")
        print(f"URL: {result.get('url')}")
    return result


def page_update(
    client: Client,
    page_id: str,
    archived: Optional[bool] = None,
    icon_emoji: Optional[str] = None,
    title: Optional[str] = None,
    properties_json: Optional[str] = None,
    cover_url: Optional[str] = None,
    as_json: bool = False,
) -> Dict[str, Any]:
    """Update a page."""
    kwargs: Dict[str, Any] = {}
    if archived is not None:
        kwargs["archived"] = archived
    if icon_emoji:
        kwargs["icon"] = {"type": "emoji", "emoji": icon_emoji}
    if cover_url:
        kwargs["cover"] = {"type": "external", "external": {"url": cover_url}}

    properties: Dict[str, Any] = {}
    if title:
        properties["title"] = [{"text": {"content": title}}]
    if properties_json:
        extra = json.loads(properties_json)
        properties.update(extra)
    if properties:
        kwargs["properties"] = properties

    result = client.pages.update(page_id=page_id, **kwargs)
    if as_json:
        print_json(result)
    else:
        print(f"Updated page: {result.get('id')}")
    return result


def page_archive(client: Client, page_id: str, as_json: bool = False) -> Dict[str, Any]:
    """Archive (soft-delete) a page."""
    return page_update(client, page_id, archived=True, as_json=as_json)


def page_retrieve_markdown(
    client: Client, page_id: str, as_json: bool = False
) -> Dict[str, Any]:
    """Retrieve page content as markdown."""
    result = client.request(
        path=f"pages/{page_id}/markdown",
        method="GET",
    )
    if as_json:
        print_json(result)
    else:
        md = result.get("markdown", "")
        print(md)
    return result


def page_update_markdown(
    client: Client, page_id: str, markdown: str, as_json: bool = False
) -> Dict[str, Any]:
    """Update page content with markdown."""
    result = client.request(
        path=f"pages/{page_id}/markdown",
        method="PATCH",
        body={
            "type": "replace_content",
            "replace_content": {"new_str": markdown},
        },
    )
    if as_json:
        print_json(result)
    else:
        print(f"Updated page markdown: {page_id}")
    return result


def page_move(
    client: Client,
    page_id: str,
    new_parent_id: str,
    parent_type: str = "page_id",
    as_json: bool = False,
) -> Dict[str, Any]:
    """Move a page to a new parent."""
    result = client.pages.move(
        page_id=page_id,
        parent={"type": parent_type, parent_type: new_parent_id},
    )
    if as_json:
        print_json(result)
    else:
        print(f"Moved page {page_id} to {new_parent_id}")
    return result
