"""Databases endpoint commands."""

import json
from typing import Any, Dict, List, Optional

from notion_client import Client

from cli_anything.notion.utils.output import (
    extract_title,
    format_rich_text,
    print_json,
    print_table,
    truncate,
)
from cli_anything.notion.utils.pagination import collect_all


def database_retrieve(
    client: Client, database_id: str, as_json: bool = False
) -> Dict[str, Any]:
    """Retrieve a database by ID."""
    result = client.databases.retrieve(database_id=database_id)
    if as_json:
        print_json(result)
    else:
        title_arr = result.get("title", [])
        title = format_rich_text(title_arr) if title_arr else "(untitled)"
        print(f"ID:         {result.get('id')}")
        print(f"Title:      {title}")
        print(f"URL:        {result.get('url', '')}")
        print(f"Properties: {len(result.get('properties', {}))}")
        for name, prop in result.get("properties", {}).items():
            print(f"  - {name}: {prop.get('type', '?')}")
    return result


def database_create(
    client: Client,
    parent_id: str,
    title: str,
    parent_type: str = "page_id",
    as_json: bool = False,
) -> Dict[str, Any]:
    """Create a new database."""
    result = client.databases.create(
        parent={"type": parent_type, parent_type: parent_id},
        title=[{"type": "text", "text": {"content": title}}],
    )
    if as_json:
        print_json(result)
    else:
        print(f"Created database: {result.get('id')}")
        print(f"URL: {result.get('url', '')}")
    return result


def database_update(
    client: Client,
    database_id: str,
    title: Optional[str] = None,
    as_json: bool = False,
) -> Dict[str, Any]:
    """Update a database."""
    kwargs: Dict[str, Any] = {}
    if title:
        kwargs["title"] = [{"type": "text", "text": {"content": title}}]

    result = client.databases.update(database_id=database_id, **kwargs)
    if as_json:
        print_json(result)
    else:
        print(f"Updated database: {result.get('id')}")
    return result


def data_source_query(
    client: Client,
    data_source_id: str,
    filter_obj: Optional[str] = None,
    sorts: Optional[str] = None,
    all_pages: bool = False,
    as_json: bool = False,
) -> List[Dict[str, Any]]:
    """Query a data source. Falls back to databases.query if data_sources fails."""
    filter_parsed = json.loads(filter_obj) if filter_obj else None
    sorts_parsed = json.loads(sorts) if sorts else None

    def _do_query(ds_id: str) -> List[Dict[str, Any]]:
        qkw: Dict[str, Any] = {"data_source_id": ds_id}
        if filter_parsed:
            qkw["filter"] = filter_parsed
        if sorts_parsed:
            qkw["sorts"] = sorts_parsed
        if all_pages:
            return collect_all(client.data_sources.query, **qkw)
        resp = client.data_sources.query(**qkw)
        return resp.get("results", [])

    try:
        results = _do_query(data_source_id)
    except Exception:
        # data_source_id might be a database_id; resolve actual data_source id
        db_info = client.databases.retrieve(database_id=data_source_id)
        ds_list = db_info.get("data_sources", [])
        if ds_list:
            resolved_id = ds_list[0].get("id") if isinstance(ds_list[0], dict) else ds_list[0]
            results = _do_query(resolved_id)
        else:
            raise

    if as_json:
        print_json(results)
    else:
        rows = []
        for item in results:
            item_id = item.get("id", "")[:8]
            title = extract_title(item)
            updated = item.get("last_edited_time", "")[:10]
            rows.append([item_id, truncate(title, 40), updated])
        print_table(["ID", "Title", "Updated"], rows)
    return results
