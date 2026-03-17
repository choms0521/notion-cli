from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-notion",
    version="1.0.0",
    description="CLI interface for Notion API - built with cli-anything methodology",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0.0",
        "notion-client>=3.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-notion=cli_anything.notion.notion_cli:main",
            "notion-cli=cli_anything.notion.notion_cli:main",
        ],
    },
    python_requires=">=3.10",
)
