#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Regenerate experiment/results/LAST_RUN_TOTALS.md from the run-id artifact.

A point-in-time appendix: for each `side|os|cache` cell, take the LAST recorded
(successful) run and report GitHub's literal workflow wall-clock
(`run_duration_ms`), plus job count and the longest job. This is the apples-to-
apples total for `flox-baked` (whose container image pull/start is included in the
run wall clock). NOT a replacement for the aggregate medians in REPORT.md — each
row is n=1.

Usage (run-ids default points at the cleaned Stage-3 artifact):
  experiment/last_run_totals.py [run-ids.json] [out.md]
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = "smorinlabs/py-launch-blueprint"
ORDER = [  # display order: ubuntu cold, ubuntu warm, macos cold, macos warm
    ("ubuntu-latest", "cold"),
    ("ubuntu-latest", "warm"),
    ("macos-latest", "cold"),
    ("macos-latest", "warm"),
]
SIDE_ORDER = [
    "traditional",
    "mise-mirror",
    "mise-consolidated",
    "flox-mirror",
    "flox-consolidated",
    "flox-nocache-mirror",
    "flox-nocache-consolidated",
    "flox-noaction-mirror",
    "flox-noaction-consolidated",
    "flox-baked",
]


def _gh(args: list[str], retries: int = 4) -> dict:
    for attempt in range(retries):
        res = subprocess.run(["gh", *args], capture_output=True, text=True)
        if res.returncode == 0:
            return json.loads(res.stdout)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"gh {' '.join(args)} failed: {res.stderr.strip()}")


def _dur(s: str, e: str) -> int:
    from datetime import datetime

    def p(v: str) -> datetime:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))

    return round((p(e) - p(s)).total_seconds())


def main() -> int:
    src = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("experiment/results/run-ids-stage3-all.json")
    )
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else Path("experiment/results/LAST_RUN_TOTALS.md")
    )
    cells = json.loads(src.read_text())

    # last-run total + job info per cell
    info: dict[tuple[str, str, str], dict] = {}
    missing: list[str] = []
    n_runs = 0
    n_jobs = 0
    for cell, ids in cells.items():
        side, os_, cache = cell.split("|")
        if not ids:
            missing.append(cell)
            continue
        rid = ids[-1]
        timing = _gh(["api", f"repos/{REPO}/actions/runs/{rid}/timing"])
        jobsj = _gh(["api", f"repos/{REPO}/actions/runs/{rid}/jobs"])
        total = round(timing["run_duration_ms"] / 1000)
        jobs = jobsj["jobs"]
        n_runs += 1
        n_jobs += len(jobs)
        longest = max(jobs, key=lambda j: _dur(j["started_at"], j["completed_at"]))
        info[(side, os_, cache)] = {
            "run": rid,
            "total": total,
            "jobs": len(jobs),
            "longest": f"{longest['name']} {_dur(longest['started_at'], longest['completed_at'])}s",
        }

    def base(os_: str, cache: str) -> int | None:
        b = info.get(("traditional", os_, cache))
        return b["total"] if b else None

    def vs(total: int, b: int | None) -> str:
        if not b:
            return "—"
        return f"{total / b:.1f}x / {round(100 * (total - b) / b):+d}%"

    md = ["# Last-run workflow wall-clock totals", ""]
    md += [
        "This appendix records a single-run remeasurement of the Stage 3 experiment",
        "cells using literal GitHub Actions workflow wall time. It is the apples-to-",
        "apples check for `flox-baked` because the total includes container image",
        "pull/start, setup, checks, post steps, and all overhead GitHub counts in",
        "`run_duration_ms`. Each row is n=1 (the last successful run per cell in the",
        "cleaned `run-ids-stage3-all.json`); the aggregate medians in `REPORT.md`",
        "remain the primary evidence.",
        "",
        "## Measurement",
        "",
        f"- Source run-id artifact: `{src.as_posix()}` (cross-OS-cleaned)",
        "- Timing: GitHub REST `actions/runs/{id}/timing` -> `run_duration_ms / 1000`",
        f"- Rows fetched: {n_runs} workflow runs, covering {n_jobs} GitHub jobs",
        "- Branch: `experiment/flox-ci-timing-perf-analysis`",
        "",
        "## Flox baked vs consolidated variants",
        "",
        "`flox-baked` is Linux-only. On ubuntu, the last-run totals land on the same",
        "floor as the other consolidated flox variants.",
        "",
        "| side | ubuntu cold | cold vs flox-consolidated | ubuntu warm | warm vs flox-consolidated |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    fc_c = info.get(("flox-consolidated", "ubuntu-latest", "cold"))
    fc_w = info.get(("flox-consolidated", "ubuntu-latest", "warm"))
    for side in [
        "flox-consolidated",
        "flox-nocache-consolidated",
        "flox-noaction-consolidated",
        "flox-baked",
    ]:
        c = info.get((side, "ubuntu-latest", "cold"))
        w = info.get((side, "ubuntu-latest", "warm"))
        cv = (
            "baseline"
            if side == "flox-consolidated"
            else (f"{c['total'] - fc_c['total']:+d}s" if c and fc_c else "n/a")
        )
        wv = (
            "baseline"
            if side == "flox-consolidated"
            else (f"{w['total'] - fc_w['total']:+d}s" if w and fc_w else "n/a")
        )
        md.append(
            f"| {side} | {c['total'] if c else 'n/a'}s | {cv} "
            f"| {w['total'] if w else 'n/a'}s | {wv} |"
        )
    md += [
        "",
        "Interpretation: pre-baking relocates the flox cost into container image",
        "pull/start, but the total workflow time is still effectively the same as",
        "normal flox consolidated execution.",
        "",
        "## Last successful run per cell",
        "",
        "| side | os | cache | run | total | vs traditional same os/cache | jobs | longest job |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for os_, cache in ORDER:
        for side in SIDE_ORDER:
            d = info.get((side, os_, cache))
            if not d:
                continue
            ratio = (
                "baseline"
                if side == "traditional"
                else vs(d["total"], base(os_, cache))
            )
            md.append(
                f"| {side} | {os_} | {cache} | {d['run']} | {d['total']}s "
                f"| {ratio} | {d['jobs']} | {d['longest']} |"
            )
    if missing:
        md += [
            "",
            "## Missing cells",
            "",
            "These cells had no successful run IDs, so they are absent above:",
            "",
        ]
        md += [f"- `{c}`" for c in sorted(missing)]
    md += [
        "",
        "## Reading notes",
        "",
        "- Point-in-time appendix; the aggregate table in `REPORT.md` is the primary evidence.",
        "- macOS traditional baselines carry high runner-queue variance, so same-cell",
        "  macOS ratios against them are noisy.",
        "- The workflow total is the right metric for `flox-baked` vs normal flox because",
        "  GitHub includes container initialization in the run wall clock.",
    ]
    out.write_text("\n".join(md) + "\n")
    print(f"wrote {out} ({n_runs} runs, {len(missing)} missing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
