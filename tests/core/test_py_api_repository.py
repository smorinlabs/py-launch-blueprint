"""Adapter mapping tests (HEX-40, ring 4): raw API dict -> domain Project."""

from py_launch_blueprint.core.adapters.py_api import PyApiProjectsRepository


def test_to_project_maps_gid_and_workspace():
    item = {"gid": "123", "name": "Proj", "workspace": {"name": "WS"}}
    project = PyApiProjectsRepository._to_project(item)
    assert (project.id, project.name, project.workspace) == ("123", "Proj", "WS")


def test_to_project_handles_missing_workspace():
    project = PyApiProjectsRepository._to_project({"gid": "1", "name": "X"})
    assert project.workspace is None
