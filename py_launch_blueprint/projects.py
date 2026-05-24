#!/usr/bin/env python3
# Copyright (c) 2025, Steve Morin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Py Project Search CLI Tool.

A command-line interface for searching and selecting Py projects,
with support for fuzzy matching and various output formats.
"""
# TODO: remove mypy: ignore-errors and fix all type errors
# mypy: ignore-errors

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click
import pyperclip
import questionary
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from py_launch_blueprint import __version__

# Initialize Rich console for pretty output
console = Console()
error_console = Console(stderr=True)


# Custom Exceptions
class PyError(Exception):
    """Base exception for Py-related errors."""

    pass


class ConfigError(Exception):
    """Configuration-related errors."""

    pass


# Configuration
@dataclass
class Config:
    """Configuration container."""

    token: str | None = None

    @classmethod
    def from_env(cls, env_path: str | None = None) -> "Config":
        """
        Create Config from environment variables or .env file.

        Args:
            env_path: Optional path to .env file

        Returns:
            Config object
        """
        if env_path:
            # Don't error if .env file is missing, just try to load if it exists
            load_dotenv(env_path)

        token = os.getenv("PY_TOKEN")
        if token is None:
            error_console.print(
                "\n[yellow]No PY_TOKEN found in environment or config file.[/yellow]"
            )
            error_console.print("To set your Py token, you have three options:")
            error_console.print("1. Set the PY_TOKEN environment variable:")
            error_console.print("   export PY_TOKEN=your_token_here")
            error_console.print(
                "\n2. Create a .env file in ~/.config/py-cli/.env with:"
            )
            error_console.print("   PY_TOKEN=your_token_here")
            error_console.print("\n3. Use the --token option when running the command:")
            error_console.print("   py-cli --token your_token_here")
            error_console.print(
                "\nYou can get your token from: https://app.py.com/settings/tokens\n"
            )
            raise ConfigError("No PY_TOKEN found in environment or config file")

        return cls(token=token)


def get_config_path() -> Path:
    """Get the path to the configuration directory."""
    if os.name == "nt":  # Windows
        base_path = Path(os.environ["USERPROFILE"])
    else:  # Unix-like
        base_path = Path.home()

    return base_path / ".config" / "py-cli"


def get_config(config_path: str | None = None) -> Config:
    """
    Get configuration from various sources.

    Priority (highest to lowest):
    1. Environment variables
    2. Configuration file

    Args:
        config_path: Optional path to config file

    Returns:
        Config object with merged configuration
    """
    config = Config()

    # Load from file if specified
    if config_path:
        file_config = Config.from_env(config_path)
        if file_config.token:
            config.token = file_config.token

    # Environment variables take precedence
    env_token = os.getenv("PY_TOKEN")
    if env_token:
        config.token = env_token

    return config


# API Client
class PyClient:
    """Client for interacting with the Py API."""

    BASE_URL = "https://app.py.com/api/1.0"

    def __init__(self, token: str):
        """
        Initialize the Py API client.

        Args:
            token: Py Personal Access Token
        """
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """
        Make a request to the Py API.

        Args:
            method: HTTP method
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data

        Raises:
            PyError: If the request fails
        """
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, "json"):
                try:
                    if e.response is not None:  # Check if response is not None
                        error_data = e.response.json()
                        error_msg = error_data.get("errors", [{}])[0].get(
                            "message", str(e)
                        )
                    else:
                        error_msg = str(e)
                except ValueError:
                    error_msg = str(e)
            else:
                error_msg = str(e)
            raise PyError(f"API request failed: {error_msg}") from e

    def get_workspaces(self) -> list[dict[str, Any]]:
        """
        Get all accessible workspaces.

        Returns:
            List of workspace dictionaries
        """
        return self._request("GET", "/workspaces")["data"]

    def get_projects(
        self, workspace_name: str | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        """
        Get projects, optionally filtered by workspace.

        Args:
            workspace_name: Optional workspace name filter
            limit: Maximum number of projects to return

        Returns:
            List of project dictionaries
        """
        params = {
            "limit": limit,
            "opt_fields": "name,workspace.name",
        }

        if workspace_name:
            # First get workspaces and find the matching one
            workspaces = self.get_workspaces()
            workspace = next(
                (w for w in workspaces if w["name"].lower() == workspace_name.lower()),
                None,
            )
            if not workspace:
                raise PyError(f"Workspace not found: {workspace_name}")

            params["workspace"] = workspace["gid"]

        response_data = self._request("GET", "/projects", params=params)
        return response_data.get("data", [])


# CLI Functions
def setup_config(config_path: str | None = None) -> Config:
    """
    Set up configuration from various sources.

    Args:
        config_path: Optional path to config file

    Returns:
        Config object with merged configuration
    """
    # Load from default location if not specified
    if not config_path:
        config_dir = get_config_path()
        config_path = str(config_dir / ".env")

    try:
        return get_config(config_path)
    except ConfigError as e:
        error_console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)


def format_output(projects: list[dict[str, Any]], format: str) -> str:
    """
    Format projects list according to specified format.

    Args:
        projects: List of project dictionaries
        format: Output format (text, json, or csv)

    Returns:
        Formatted string
    """
    if format == "json":
        return json.dumps({"projects": projects}, indent=2)
    elif format == "csv":
        header = "id,name\n"
        rows = [f"{p['id']},{p['name']}" for p in projects]
        return header + "\n".join(rows)
    else:  # text format
        return "\n".join(p["id"] for p in projects)


def display_projects(projects: list[dict[str, Any]], verbose: bool = False) -> None:
    """
    Display projects in a rich table format.

    Args:
        projects: List of project dictionaries
        verbose: Whether to show additional details
    """
    table = Table(show_header=True)
    table.add_column("Project Name", style="cyan")
    table.add_column("Workspace", style="green")
    if verbose:
        table.add_column("ID", style="dim")

    for project in projects:
        row = [project["name"], project["workspace"]["name"]]
        if verbose:
            row.append(project["id"])
        table.add_row(*row)

    console.print(table)


@click.command()
@click.version_option(version=__version__)
@click.option("--token", help="Py Personal Access Token")
@click.option("--config", help="Path to config file", type=click.Path(exists=True))
@click.option("--workspace", help="Filter projects by workspace name")
@click.option("--limit", default=200, help="Maximum number of projects to retrieve")
@click.option(
    "--format",
    type=click.Choice(["text", "json", "csv"]),
    default="text",
    help="Output format",
)
@click.option("--copy", is_flag=True, help="Copy results to clipboard")
@click.option("--output", type=click.Path(), help="Write results to file")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def main(
    token: str | None,
    config: str | None,
    workspace: str | None,
    limit: int,
    format: str,
    copy: bool,
    output: str | None,
    no_color: bool,
    verbose: bool,
) -> None:
    """Search and select Py projects."""
    try:
        # Setup configuration
        cfg = setup_config(config)
        if token:
            cfg.token = token

        if not cfg.token:
            error_console.print("[red]Error:[/red] No Py token provided")
            sys.exit(1)

        # Initialize API client
        client = PyClient(cfg.token)

        with Progress() as progress:
            # Fetch projects
            task = progress.add_task("Fetching projects...", total=None)
            projects = client.get_projects(workspace_name=workspace, limit=limit)
            progress.update(task, completed=True)

        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            return

        # Display projects and get selection
        if format == "text":
            display_projects(projects, verbose)

        # Allow project selection
        choices = [
            questionary.Choice(title=f"{p['name']} ({p['workspace']['name']})", value=p)
            for p in projects
        ]

        selected = questionary.checkbox(
            "Select projects:",
            choices=choices,
        ).ask()

        if not selected:
            console.print("[yellow]No projects selected[/yellow]")
            return

        # Format output
        result = format_output(selected, format)

        # Handle output
        if output:
            Path(output).write_text(result)
            console.print(f"[green]Results written to {output}[/green]")
        else:
            console.print(result)

        if copy:
            pyperclip.copy(result)
            console.print("[green]Results copied to clipboard[/green]")

    except PyError as e:
        error_console.print(f"[red]Py API error:[/red] {e}")
        sys.exit(3)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        if verbose:
            error_console.print_exception()
        sys.exit(4)


if __name__ == "__main__":
    main()
