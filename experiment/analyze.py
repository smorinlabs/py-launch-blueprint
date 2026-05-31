#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Analyze CI timing runs and emit report + charts.

Two modes:
  --fixture PATH   read pre-tagged runs from a JSON array (no gh calls)
  --live --repo O/R --branch B   collect via `gh api` (see experiment/README.md)
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiment.bench.aggregate import (  # noqa: E402
    Cell,
    TaggedRun,
    aggregate_jobs,
    aggregate_totals,
)
from experiment.bench.charts import grouped_total_bars  # noqa: E402
from experiment.bench.collect import JobTiming, RunTiming, parse_run  # noqa: E402
from experiment.bench.report import render_totals_table  # noqa: E402


def _tagged_from_fixture(path: Path) -> list[TaggedRun]:
    raw = json.loads(path.read_text())
    out: list[TaggedRun] = []
    for item in raw:
        jobs = [
            JobTiming(
                name=j["name"],
                seconds=j["seconds"],
                setup_seconds=j["setup_seconds"],
                work_seconds=j["seconds"] - j["setup_seconds"],
            )
            for j in item["jobs"]
        ]
        run = RunTiming(item["run_id"], item["total_seconds"], jobs)
        out.append(TaggedRun(Cell(item["side"], item["os"], item["cache"]), run))
    return out


def _gh_json(args: list[str]) -> dict:
    res = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def _tagged_from_live(repo: str, run_ids: dict[str, list[int]]) -> list[TaggedRun]:
    # run_ids maps "side|os|cache" -> [run_id, ...] (produced by the driver)
    out: list[TaggedRun] = []
    for tag, ids in run_ids.items():
        side, os_, cache = tag.split("|")
        for rid in ids:
            timing = _gh_json(["api", f"repos/{repo}/actions/runs/{rid}/timing"])
            jobs = _gh_json(["api", f"repos/{repo}/actions/runs/{rid}/jobs"])
            out.append(TaggedRun(Cell(side, os_, cache), parse_run(rid, timing, jobs)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--repo")
    ap.add_argument("--run-ids", type=Path, help="JSON: {'side|os|cache': [ids]}")
    ap.add_argument("--out", type=Path, default=Path("experiment/results"))
    args = ap.parse_args()

    if args.fixture:
        tagged = _tagged_from_fixture(args.fixture)
    elif args.live:
        run_ids = json.loads(args.run_ids.read_text())
        tagged = _tagged_from_live(args.repo, run_ids)
    else:
        ap.error("one of --fixture or --live is required")

    totals = aggregate_totals(tagged)
    jobs = aggregate_jobs(tagged)
    args.out.mkdir(parents=True, exist_ok=True)

    # raw json
    (args.out / "results.json").write_text(
        json.dumps(
            {f"{c.side}|{c.os}|{c.cache}": asdict(s) for c, s in totals.items()},
            indent=2,
        )
    )
    # csv
    with (args.out / "results.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["side", "os", "cache", "n", "min", "max", "avg", "median", "stddev"])
        for c, s in sorted(totals.items(), key=lambda kv: (kv[0].os, kv[0].cache, kv[0].side)):
            w.writerow([c.side, c.os, c.cache, s.n, s.min, s.max, s.avg, s.median, s.stddev])
    # per-job table (markdown)
    job_lines = ["| job | side | os | cache | avg | stddev |", "| --- | --- | --- | --- | ---: | ---: |"]
    for (c, name), s in sorted(jobs.items(), key=lambda kv: (kv[0][0].os, kv[0][0].side, kv[0][1])):
        job_lines.append(f"| {name} | {c.side} | {c.os} | {c.cache} | {s.avg:.1f} | {s.stddev:.1f} |")

    report = (
        "# Flox vs Traditional CI — timing results\n\n"
        "## Total run time (per side × os × cache)\n\n"
        + render_totals_table(totals, baseline_side="traditional")
        + "\n## Per-job breakdown\n\n"
        + "\n".join(job_lines)
        + "\n\n## Charts\n\n![total time](total_time.png)\n"
    )
    (args.out / "REPORT.md").write_text(report)
    grouped_total_bars(totals, args.out / "total_time.png")
    print(f"wrote report + charts to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
