"""Skip web-layer tests when the ``web`` extra isn't installed.

The base dev environment (`uv sync --group dev`) has no FastAPI; CI and
`just test-web` install the extra so these tests actually run there.
"""

import importlib.util

collect_ignore_glob: list[str] = []
if importlib.util.find_spec("fastapi") is None:
    collect_ignore_glob = ["test_*.py"]
