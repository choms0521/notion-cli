"""Authentication utilities for Notion CLI."""

import json
import os
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".notion-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_token(token_arg: Optional[str] = None) -> str:
    """Resolve Notion API token from flag > env > config file.

    Priority:
        1. --token CLI argument
        2. NOTION_API_KEY environment variable
        3. ~/.notion-cli/config.json
    """
    if token_arg:
        return token_arg

    env_token = os.environ.get("NOTION_API_KEY")
    if env_token:
        return env_token

    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
            file_token = config.get("token")
            if file_token:
                return file_token
        except (json.JSONDecodeError, KeyError):
            pass

    raise SystemExit(
        "Notion API token not found. Provide it via:\n"
        "  1. --token flag\n"
        "  2. NOTION_API_KEY environment variable\n"
        "  3. cli-anything-notion config set-token <token>\n\n"
        "Get a token at: https://www.notion.so/my-integrations"
    )


def save_token(token: str) -> None:
    """Save token to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            pass
    config["token"] = token
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def remove_token() -> None:
    """Remove token from config file."""
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
            config.pop("token", None)
            CONFIG_FILE.write_text(json.dumps(config, indent=2))
        except json.JSONDecodeError:
            pass
