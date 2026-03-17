"""Users endpoint commands."""

from typing import Any, Dict, List

from notion_client import Client

from cli_anything.notion.utils.output import print_json, print_table


def users_list(client: Client, as_json: bool = False) -> List[Dict[str, Any]]:
    """List all users."""
    response = client.users.list()
    results = response.get("results", [])

    if as_json:
        print_json(results)
    else:
        rows = []
        for u in results:
            rows.append([
                u.get("id", "")[:8],
                u.get("type", ""),
                u.get("name", ""),
            ])
        print_table(["ID", "Type", "Name"], rows)
    return results


def users_me(client: Client, as_json: bool = False) -> Dict[str, Any]:
    """Get the current bot user."""
    result = client.users.me()
    if as_json:
        print_json(result)
    else:
        print(f"ID:   {result.get('id')}")
        print(f"Name: {result.get('name')}")
        print(f"Type: {result.get('type')}")
        bot = result.get("bot", {})
        owner = bot.get("owner", {})
        print(f"Owner: {owner.get('type', '')} - {owner.get('user', {}).get('name', '')}")
    return result


def users_retrieve(client: Client, user_id: str, as_json: bool = False) -> Dict[str, Any]:
    """Retrieve a user by ID."""
    result = client.users.retrieve(user_id=user_id)
    if as_json:
        print_json(result)
    else:
        print(f"ID:   {result.get('id')}")
        print(f"Name: {result.get('name')}")
        print(f"Type: {result.get('type')}")
    return result
