"""Notion CLI - Command-line interface for Notion API."""

import json
import sys
from typing import Optional

import click
from notion_client import Client

from cli_anything.notion.utils.auth import get_token, save_token, remove_token
from cli_anything.notion.core import pages, blocks, databases, search, users, comments


def make_client(token: Optional[str] = None) -> Client:
    """Create a Notion client with resolved token."""
    return Client(auth=get_token(token))


@click.group(invoke_without_command=True)
@click.option("--token", envvar="NOTION_API_KEY", help="Notion API token")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx: click.Context, token: Optional[str], as_json: bool) -> None:
    """CLI interface for Notion API.

    Manage pages, databases, blocks, and more from the command line.
    """
    ctx.ensure_object(dict)
    ctx.obj["token"] = token
    ctx.obj["json"] = as_json
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ── Config commands ──────────────────────────────────────────────────────


@cli.group()
def config() -> None:
    """Manage CLI configuration."""
    pass


@config.command("set-token")
@click.argument("token")
def config_set_token(token: str) -> None:
    """Save Notion API token to config file."""
    save_token(token)
    click.echo("Token saved to ~/.notion-cli/config.json")


@config.command("remove-token")
def config_remove_token() -> None:
    """Remove saved token."""
    remove_token()
    click.echo("Token removed.")


# ── Pages commands ───────────────────────────────────────────────────────


@cli.group(name="pages")
def pages_group() -> None:
    """Manage Notion pages."""
    pass


@pages_group.command("get")
@click.argument("page_id")
@click.pass_context
def pages_get(ctx: click.Context, page_id: str) -> None:
    """Retrieve a page by ID."""
    client = make_client(ctx.obj["token"])
    pages.page_retrieve(client, page_id, ctx.obj["json"])


@pages_group.command("create")
@click.argument("title")
@click.option("--parent", required=True, help="Parent page or database ID")
@click.option("--parent-type", default="page_id", type=click.Choice(["page_id", "database_id"]))
@click.option("--content", help="Initial page content (paragraph text)")
@click.pass_context
def pages_create(
    ctx: click.Context,
    title: str,
    parent: str,
    parent_type: str,
    content: Optional[str],
) -> None:
    """Create a new page."""
    client = make_client(ctx.obj["token"])
    pages.page_create(client, parent, title, parent_type, content, ctx.obj["json"])


@pages_group.command("update")
@click.argument("page_id")
@click.option("--icon", help="Emoji icon")
@click.option("--archive/--no-archive", default=None, help="Archive or unarchive")
@click.option("--title", help="New page title")
@click.option("--property", "properties_json", help="Properties as JSON string")
@click.option("--cover", "cover_url", help="Cover image URL")
@click.pass_context
def pages_update(
    ctx: click.Context,
    page_id: str,
    icon: Optional[str],
    archive: Optional[bool],
    title: Optional[str],
    properties_json: Optional[str],
    cover_url: Optional[str],
) -> None:
    """Update a page (title, icon, properties, cover, archive)."""
    client = make_client(ctx.obj["token"])
    pages.page_update(
        client, page_id, archive, icon, title, properties_json, cover_url, ctx.obj["json"]
    )


@pages_group.command("archive")
@click.argument("page_id")
@click.pass_context
def pages_archive(ctx: click.Context, page_id: str) -> None:
    """Archive a page."""
    client = make_client(ctx.obj["token"])
    pages.page_archive(client, page_id, ctx.obj["json"])


@pages_group.command("markdown")
@click.argument("page_id")
@click.pass_context
def pages_markdown(ctx: click.Context, page_id: str) -> None:
    """Get page content as markdown."""
    client = make_client(ctx.obj["token"])
    pages.page_retrieve_markdown(client, page_id, ctx.obj["json"])


@pages_group.command("update-markdown")
@click.argument("page_id")
@click.argument("markdown")
@click.option("--allow-deleting-content", is_flag=True, help="Allow deleting child pages/databases")
@click.pass_context
def pages_update_md(
    ctx: click.Context, page_id: str, markdown: str, allow_deleting_content: bool
) -> None:
    """Replace entire page content with markdown."""
    client = make_client(ctx.obj["token"])
    pages.page_update_markdown(
        client, page_id, markdown, allow_deleting_content, ctx.obj["json"]
    )


@pages_group.command("edit-markdown")
@click.argument("page_id")
@click.option("--old", "old_str", required=True, help="Text to find in page markdown")
@click.option("--new", "new_str", required=True, help="Replacement text")
@click.option("--replace-all", is_flag=True, help="Replace all matches (default: single match)")
@click.option("--allow-deleting-content", is_flag=True, help="Allow deleting child pages/databases")
@click.pass_context
def pages_edit_md(
    ctx: click.Context,
    page_id: str,
    old_str: str,
    new_str: str,
    replace_all: bool,
    allow_deleting_content: bool,
) -> None:
    """Surgical find-and-replace on page markdown content."""
    client = make_client(ctx.obj["token"])
    pages.page_edit_markdown(
        client, page_id, old_str, new_str, replace_all, allow_deleting_content, ctx.obj["json"]
    )


@pages_group.command("edit-markdown-batch")
@click.argument("page_id")
@click.argument("updates_json")
@click.option("--allow-deleting-content", is_flag=True, help="Allow deleting child pages/databases")
@click.pass_context
def pages_edit_md_batch(
    ctx: click.Context, page_id: str, updates_json: str, allow_deleting_content: bool
) -> None:
    """Batch find-and-replace on page markdown.

    UPDATES_JSON: JSON array of {old_str, new_str, replace_all_matches?} objects (max 100).
    """
    client = make_client(ctx.obj["token"])
    pages.page_edit_markdown_batch(
        client, page_id, updates_json, allow_deleting_content, ctx.obj["json"]
    )


@pages_group.command("move")
@click.argument("page_id")
@click.option("--to", "new_parent", required=True, help="New parent ID")
@click.option("--parent-type", default="page_id", type=click.Choice(["page_id", "database_id"]))
@click.pass_context
def pages_move(
    ctx: click.Context, page_id: str, new_parent: str, parent_type: str
) -> None:
    """Move a page to a new parent."""
    client = make_client(ctx.obj["token"])
    pages.page_move(client, page_id, new_parent, parent_type, ctx.obj["json"])


# ── Blocks commands ──────────────────────────────────────────────────────


@cli.group(name="blocks")
def blocks_group() -> None:
    """Manage Notion blocks."""
    pass


@blocks_group.command("get")
@click.argument("block_id")
@click.pass_context
def blocks_get(ctx: click.Context, block_id: str) -> None:
    """Retrieve a block by ID."""
    client = make_client(ctx.obj["token"])
    blocks.block_retrieve(client, block_id, ctx.obj["json"])


@blocks_group.command("children")
@click.argument("block_id")
@click.option("--all", "all_pages", is_flag=True, help="Auto-paginate all results")
@click.pass_context
def blocks_children(ctx: click.Context, block_id: str, all_pages: bool) -> None:
    """List child blocks."""
    client = make_client(ctx.obj["token"])
    blocks.block_children_list(client, block_id, all_pages, ctx.obj["json"])


@blocks_group.command("append")
@click.argument("block_id")
@click.argument("text")
@click.option(
    "--type",
    "block_type",
    default="paragraph",
    type=click.Choice([
        "paragraph", "heading_1", "heading_2", "heading_3",
        "bulleted_list_item", "numbered_list_item", "to_do", "quote", "callout",
        "code", "divider", "toggle",
    ]),
)
@click.option("--language", help="Language for code blocks (e.g., python, javascript)")
@click.pass_context
def blocks_append(
    ctx: click.Context, block_id: str, text: str, block_type: str, language: Optional[str]
) -> None:
    """Append a block (text, code, divider, etc.)."""
    client = make_client(ctx.obj["token"])
    blocks.block_append_text(client, block_id, text, block_type, language, ctx.obj["json"])


@blocks_group.command("update")
@click.argument("block_id")
@click.argument("text")
@click.option("--type", "block_type", default=None, help="Block type (auto-detected if omitted)")
@click.option("--language", help="Language for code blocks")
@click.pass_context
def blocks_update(
    ctx: click.Context, block_id: str, text: str, block_type: Optional[str], language: Optional[str]
) -> None:
    """Update a block's text content."""
    client = make_client(ctx.obj["token"])
    blocks.block_update_text(client, block_id, text, block_type, language, ctx.obj["json"])


@blocks_group.command("delete")
@click.argument("block_id")
@click.pass_context
def blocks_delete(ctx: click.Context, block_id: str) -> None:
    """Delete a block."""
    client = make_client(ctx.obj["token"])
    blocks.block_delete(client, block_id, ctx.obj["json"])


# ── Databases commands ───────────────────────────────────────────────────


@cli.group(name="databases")
def databases_group() -> None:
    """Manage Notion databases."""
    pass


@databases_group.command("get")
@click.argument("database_id")
@click.pass_context
def databases_get(ctx: click.Context, database_id: str) -> None:
    """Retrieve a database by ID."""
    client = make_client(ctx.obj["token"])
    databases.database_retrieve(client, database_id, ctx.obj["json"])


@databases_group.command("create")
@click.argument("title")
@click.option("--parent", required=True, help="Parent page ID")
@click.pass_context
def databases_create(ctx: click.Context, title: str, parent: str) -> None:
    """Create a new database."""
    client = make_client(ctx.obj["token"])
    databases.database_create(client, parent, title, as_json=ctx.obj["json"])


@databases_group.command("update")
@click.argument("database_id")
@click.option("--title", help="New title")
@click.pass_context
def databases_update(
    ctx: click.Context, database_id: str, title: Optional[str]
) -> None:
    """Update a database."""
    client = make_client(ctx.obj["token"])
    databases.database_update(client, database_id, title, ctx.obj["json"])


@databases_group.command("query")
@click.argument("data_source_id")
@click.option("--filter", "filter_obj", help="Filter as JSON string")
@click.option("--sorts", help="Sorts as JSON string")
@click.option("--all", "all_pages", is_flag=True, help="Auto-paginate all results")
@click.pass_context
def databases_query(
    ctx: click.Context,
    data_source_id: str,
    filter_obj: Optional[str],
    sorts: Optional[str],
    all_pages: bool,
) -> None:
    """Query a data source."""
    client = make_client(ctx.obj["token"])
    databases.data_source_query(
        client, data_source_id, filter_obj, sorts, all_pages, ctx.obj["json"]
    )


# ── Search command ───────────────────────────────────────────────────────


@cli.command()
@click.argument("query", default="")
@click.option("--type", "filter_type", type=click.Choice(["page", "database"]))
@click.option("--all", "all_pages", is_flag=True, help="Auto-paginate all results")
@click.pass_context
def search_cmd(
    ctx: click.Context,
    query: str,
    filter_type: Optional[str],
    all_pages: bool,
) -> None:
    """Search pages and databases."""
    client = make_client(ctx.obj["token"])
    search.search(client, query, filter_type, all_pages, ctx.obj["json"])


# Alias: `notion search` instead of `notion search-cmd`
cli.add_command(search_cmd, "search")


# ── Users commands ───────────────────────────────────────────────────────


@cli.group(name="users")
def users_group() -> None:
    """Manage Notion users."""
    pass


@users_group.command("list")
@click.pass_context
def users_list_cmd(ctx: click.Context) -> None:
    """List workspace users."""
    client = make_client(ctx.obj["token"])
    users.users_list(client, ctx.obj["json"])


@users_group.command("me")
@click.pass_context
def users_me_cmd(ctx: click.Context) -> None:
    """Get current bot user info."""
    client = make_client(ctx.obj["token"])
    users.users_me(client, ctx.obj["json"])


@users_group.command("get")
@click.argument("user_id")
@click.pass_context
def users_get(ctx: click.Context, user_id: str) -> None:
    """Retrieve a user by ID."""
    client = make_client(ctx.obj["token"])
    users.users_retrieve(client, user_id, ctx.obj["json"])


# ── Comments commands ────────────────────────────────────────────────────


@cli.group(name="comments")
def comments_group() -> None:
    """Manage Notion comments."""
    pass


@comments_group.command("list")
@click.argument("block_id")
@click.pass_context
def comments_list_cmd(ctx: click.Context, block_id: str) -> None:
    """List comments on a block/page."""
    client = make_client(ctx.obj["token"])
    comments.comments_list(client, block_id, ctx.obj["json"])


@comments_group.command("create")
@click.argument("parent_id")
@click.argument("text")
@click.option("--discussion", help="Reply to a discussion thread")
@click.pass_context
def comments_create_cmd(
    ctx: click.Context,
    parent_id: str,
    text: str,
    discussion: Optional[str],
) -> None:
    """Create a comment on a page."""
    client = make_client(ctx.obj["token"])
    comments.comments_create(client, parent_id, text, discussion, ctx.obj["json"])


# ── Entry point ──────────────────────────────────────────────────────────


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
