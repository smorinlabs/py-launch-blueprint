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

"""Composition root (HEX-04).

The single place that binds the abstract ``ProjectsRepository`` port to a
concrete adapter and returns a wired :class:`ProjectsService`. Only the
front-ends (``cli``, ``web``) import this module; nothing in ``core`` may
(enforced by import-linter), which is what keeps a top-level composition root
free of the circular-import risk it would otherwise carry.
"""

from py_launch_blueprint.core.adapters.py_api import (
    DEFAULT_TIMEOUT,
    PyApiProjectsRepository,
)
from py_launch_blueprint.core.services.projects import ProjectsService


def build_projects_service(
    token: str, timeout: int = DEFAULT_TIMEOUT
) -> ProjectsService:
    """Wire a :class:`ProjectsService` over the live Py API adapter."""
    return ProjectsService(PyApiProjectsRepository(token, timeout=timeout))
