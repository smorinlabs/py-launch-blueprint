"""Guard-wiring check — shared between init_doctor and CI workflow.

Verifies:
  1. The Tier-1 `_blueprint_notice := shell('bash init/guard.sh warn')` variable
     exists in the Justfile (with sufficient flexibility for quoting variants).
  2. Every recipe in TIER_2_RECIPES declares `_guard` as a dependency.

Importable + runnable. As CLI:
    python init/ci/check_guard_wiring.py [--justfile PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

TIER_2_RECIPES = ("build", "pr-to-testrepo", "clean-pr-to-testrepo")

_TIER1_PATTERN = re.compile(
    r"^_blueprint_notice\s*:=\s*shell\(\s*['\"]bash\s+init/guard\.sh\s+warn['\"]\s*\)",
    re.MULTILINE,
)


@dataclass
class CheckResult:
    ok: bool
    messages: list[str]

    def render(self) -> str:
        prefix = "OK" if self.ok else "FAIL"
        return f"[{prefix}] guard-wiring:\n" + "\n".join(
            f"  - {m}" for m in self.messages
        )


def _recipe_line_re(name: str) -> re.Pattern[str]:
    safe = re.escape(name)
    return re.compile(rf"^@?\s*{safe}(?:\s+[^:]*)?\s*:\s*(.*?)$", re.MULTILINE)


def check(justfile: Path) -> CheckResult:
    text = justfile.read_text(encoding="utf-8")
    messages: list[str] = []
    ok = True

    if _TIER1_PATTERN.search(text):
        messages.append("Tier-1 `_blueprint_notice` variable present")
    else:
        ok = False
        messages.append(
            "Tier-1 `_blueprint_notice := shell('bash init/guard.sh warn')` MISSING"
        )

    for recipe in TIER_2_RECIPES:
        m = _recipe_line_re(recipe).search(text)
        if m is None:
            messages.append(f"recipe `{recipe}` not found in Justfile (skipping)")
            continue
        deps = m.group(1).strip()
        if re.search(r"\b_guard\b", deps):
            messages.append(f"Tier-2 recipe `{recipe}` declares `_guard` dependency")
        else:
            ok = False
            messages.append(
                f"Tier-2 recipe `{recipe}` MISSING `_guard` dependency (current deps: {deps!r})"
            )

    return CheckResult(ok=ok, messages=messages)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--justfile",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "Justfile",
    )
    args = parser.parse_args(argv)
    result = check(args.justfile)
    print(result.render())
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
