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

"""Tests for Py API client."""

from unittest.mock import Mock, patch

import pytest
import requests

from py_launch_blueprint.projects import PyClient, PyError


@pytest.fixture
def client():
    """Create a test client."""
    return PyClient("test_token")


def test_client_initialization(client):
    """Test client initialization."""
    assert client.session.headers["Authorization"] == "Bearer test_token"
    assert client.session.headers["Accept"] == "application/json"


@patch("requests.Session.request")
def test_successful_request(mock_request, client):
    """Test successful API request."""
    mock_response = Mock()
    mock_response.json.return_value = {"data": {"id": "123", "name": "Test"}}
    mock_request.return_value = mock_response

    result = client._request("GET", "/test")
    assert result == {"data": {"id": "123", "name": "Test"}}


@patch("requests.Session.request")
def test_failed_request(mock_request, client):
    """Test failed API request."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_response.json.return_value = {"errors": [{"message": "Test error"}]}
    mock_request.return_value = mock_response

    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "Test error"
    )
    with pytest.raises(PyError, match="Test error"):
        client._request("GET", "/test")


@patch("requests.Session.request")
def test_get_workspaces(mock_request, client):
    """Test getting workspaces."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {"gid": "1", "name": "Workspace 1"},
            {"gid": "2", "name": "Workspace 2"},
        ]
    }
    mock_request.return_value = mock_response

    workspaces = client.get_workspaces()
    assert len(workspaces) == 2
    assert workspaces[0]["name"] == "Workspace 1"


@patch("requests.Session.request")
def test_get_projects(mock_request, client):
    """Test getting projects."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {"gid": "1", "name": "Project 1", "workspace": {"name": "Workspace 1"}}
        ]
    }
    mock_request.return_value = mock_response

    projects = client.get_projects(limit=1)
    assert len(projects) == 1
    assert projects[0]["name"] == "Project 1"


@patch.object(PyClient, "get_workspaces")
@patch("requests.Session.request")
def test_get_projects_with_workspace(mock_request, mock_get_workspaces, client):
    """Test getting projects filtered by workspace."""
    # Mock workspace response
    mock_get_workspaces.return_value = [{"gid": "ws1", "name": "Test Workspace"}]

    # Mock projects response
    mock_response = Mock()
    mock_response.json.return_value = {"data": []}
    mock_request.return_value = mock_response

    projects = client.get_projects(workspace_name="Test Workspace")  # noqa F841

    # Verify workspace parameter was included
    called_params = mock_request.call_args[1]["params"]
    assert called_params["workspace"] == "ws1"


@patch.object(PyClient, "get_workspaces")
def test_get_projects_invalid_workspace(mock_get_workspaces, client):
    """Test getting projects with invalid workspace name."""
    mock_get_workspaces.return_value = []

    with pytest.raises(PyError, match="Workspace not found"):
        client.get_projects(workspace_name="Invalid Workspace")
