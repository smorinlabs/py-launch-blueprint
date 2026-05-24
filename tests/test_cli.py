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

"""Tests for CLI functionality."""

import json
import re
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from py_launch_blueprint import __version__
from py_launch_blueprint.projects import Config, PyClient, main


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_client():
    """Create a mock Py client."""
    with patch("py_launch_blueprint.projects.PyClient") as mock:
        client = Mock(spec=PyClient)
        mock.return_value = client
        yield client


def test_cli_help(runner):
    """Test CLI help output."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Search and select Py projects." in result.output


def test_cli_version(runner):
    """Test CLI version output."""
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output.lower()


def test_cli_no_token(runner):
    """Test CLI behavior with no token."""
    with patch("py_launch_blueprint.projects.get_config", return_value=Config()):
        result = runner.invoke(main)
        assert result.exit_code == 1
        assert "No Py token provided" in result.output


def test_cli_with_token(runner, mock_client):
    """Test CLI with token provided."""
    # Mock project data
    mock_client.get_projects.return_value = [
        {"id": "1", "name": "Test Project", "workspace": {"name": "Test Workspace"}}
    ]

    # Run with token
    with patch(
        "py_launch_blueprint.projects.get_config", return_value=Config(token="test")
    ):
        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.ask.return_value = []  # No selection
            result = runner.invoke(main, ["--token", "test"])
            assert result.exit_code == 0


def test_cli_workspace_filter(runner, mock_client):
    """Test CLI with workspace filter."""
    project_data = {
        "id": "1",
        "name": "Test Project",
        "workspace": {"name": "Test Workspace"},
    }
    mock_client.get_projects.return_value = [project_data]

    with patch(
        "py_launch_blueprint.projects.get_config", return_value=Config(token="test")
    ):
        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.ask.return_value = []
            result = runner.invoke(main, ["--workspace", "Test"])
            assert result.exit_code == 0
            mock_client.get_projects.assert_called_with(
                workspace_name="Test", limit=200
            )


def test_cli_output_formats(runner, mock_client):
    """Test different output formats."""
    project_data = {
        "id": "1",
        "name": "Test Project",
        "workspace": {"name": "Test Workspace"},
    }
    mock_client.get_projects.return_value = [project_data]

    with patch(
        "py_launch_blueprint.projects.get_config", return_value=Config(token="test")
    ):
        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = [project_data]

            # Test JSON format
            result = runner.invoke(main, ["--format", "json"])
            cleaned_output = re.sub(r"Fetching projects.*\n", "", result.output).strip()
            assert result.exit_code == 0
            json.loads(cleaned_output)
            # Should be valid JSON

            # Test CSV format
            result = runner.invoke(main, ["--format", "csv"])
            assert result.exit_code == 0
            assert "id,name" in result.output

            # Test text format
            result = runner.invoke(main, ["--format", "text"])
            assert result.exit_code == 0
            assert "1" in result.output


def test_cli_output_file(runner, mock_client, tmp_path):
    """Test writing output to file."""
    project_data = {
        "id": "1",
        "name": "Test Project",
        "workspace": {"name": "Test Workspace"},
    }

    output_file = tmp_path / "output.txt"

    with patch(
        "py_launch_blueprint.projects.get_config", return_value=Config(token="test")
    ):
        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.ask.return_value = [project_data]
            mock_client.get_projects.return_value = [project_data]

            with patch("py_launch_blueprint.projects.format_output", return_value="1"):
                result = runner.invoke(
                    main, ["--output", str(output_file), "--format", "text"]
                )

                assert result.exit_code == 0
                assert output_file.exists()
                assert output_file.read_text().strip() == "1"


@patch("pyperclip.copy")
def test_cli_copy_to_clipboard(mock_copy, runner, mock_client):
    """Test copying output to clipboard."""
    project_data = {
        "id": "1",
        "name": "Test Project",
        "workspace": {"name": "Test Workspace"},
    }
    mock_client.get_projects.return_value = [project_data]

    with patch(
        "py_launch_blueprint.projects.get_config", return_value=Config(token="test")
    ):
        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = [project_data]
            result = runner.invoke(main, ["--copy"])
            assert result.exit_code == 0
            mock_copy.assert_called_with("1")
