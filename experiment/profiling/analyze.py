#!/usr/bin/env python3
"""Analyze a flox-provisioning phases.json into a phase table + report skeleton.

Stdlib-only so it runs as `python3 -m experiment.profiling.analyze <phases.json>`
with no dependencies, and is unit-testable.
"""

from __future__ import annotations

import json
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
