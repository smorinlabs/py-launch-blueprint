#!/usr/bin/env python3
"""Analyze a flox-provisioning phases.json into a phase table + report skeleton.

Stdlib-only so it runs as `python3 -m experiment.profiling.analyze <phases.json>`
with no dependencies, and is unit-testable.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Phase:
    name: str
    seconds: float
    max_rss_mb: float
    io_read_mb: float
    io_write_mb: float


@dataclass(frozen=True)
class Profile:
    os: str
    arch: str
    cache: str
    flox_version: str
    phases: list[Phase]
    flamegraphs: list[str]


def load_profile(path: Path) -> Profile:
    raw = json.loads(Path(path).read_text())
    meta = raw["meta"]
    phases = [
        Phase(
            p["name"],
            float(p["seconds"]),
            float(p["max_rss_mb"]),
            float(p["io_read_mb"]),
            float(p["io_write_mb"]),
        )
        for p in raw["phases"]
    ]
    fgs = raw.get("artifacts", {}).get("flamegraphs", [])
    return Profile(
        os=meta["os"],
        arch=meta.get("arch", ""),
        cache=meta["cache"],
        flox_version=meta.get("flox_version", ""),
        phases=phases,
        flamegraphs=fgs,
    )


def total_seconds(p: Profile) -> float:
    return sum(ph.seconds for ph in p.phases)


def dominant_phase(p: Profile) -> Phase:
    if not p.phases:
        raise ValueError("profile has no phases")
    return max(p.phases, key=lambda ph: ph.seconds)


def phase_table(p: Profile) -> str:
    total = total_seconds(p) or 1.0
    header = (
        "| phase | seconds | % | max RSS (MB) | IO read (MB) | IO write (MB) |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: |"
    )
    rows = [
        f"| {ph.name} | {ph.seconds:.1f} | {100 * ph.seconds / total:.1f}% "
        f"| {ph.max_rss_mb:.0f} | {ph.io_read_mb:.0f} | {ph.io_write_mb:.0f} |"
        for ph in p.phases
    ]
    return header + "\n" + "\n".join(rows) + "\n"


def render_report(p: Profile) -> str:
    dom = dominant_phase(p)
    fg_lines = "\n".join(f"- `{f}`" for f in p.flamegraphs) or "- (none captured yet)"
    return (
        "# Flox provisioning — root-cause report\n\n"
        f"- env: {p.os}/{p.arch} · cache: {p.cache} · flox {p.flox_version}\n"
        f"- total provisioning: {total_seconds(p):.1f}s · "
        f"Dominant phase: **{dom.name}** ({dom.seconds:.1f}s)\n\n"
        "## Phase breakdown\n\n" + phase_table(p) + "\n"
        "## Resource attribution\n\n"
        f"Dominant phase `{dom.name}` — classify via the flame graphs / IO below:\n"
        "- CPU-bound?  on-CPU flame graph hot stacks → (fill)\n"
        "- Off-CPU (blocked)?  off-CPU flame graph (Linux) → (fill: read/write/futex)\n"
        "- Disk?  IO write/read MB + biolatency → (fill)\n"
        "- Network?  bytes downloaded / time → (fill)\n\n"
        "## Flame graphs\n\n" + fg_lines + "\n\n"
        "## Ranked optimization candidates\n\n"
        "1. (fill: what · evidence · est. impact · where in flox/nix · upstream-fixable?)\n"
    )


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: analyze.py <phases.json> [out_report.md]", file=sys.stderr)
        return 2
    profile = load_profile(Path(argv[1]))
    report = render_report(profile)
    if len(argv) >= 3:
        Path(argv[2]).write_text(report)
        print(f"wrote {argv[2]}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
