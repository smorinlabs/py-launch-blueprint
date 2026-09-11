"""Remove an inherited release cutoff from a freshly generated repository."""

import json
from pathlib import Path


def main() -> None:
    """Preserve release settings while dropping the source repository's cutoff."""
    path = Path("release-please-config.json")
    config = json.loads(path.read_text(encoding="utf-8"))
    config.pop("bootstrap-sha", None)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
