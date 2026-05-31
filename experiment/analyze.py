#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Analyze CI timing runs and emit report + charts.

Two modes:
  --fixture PATH   read pre-tagged runs from a JSON array (no gh calls)
  --live --repo O/R --run-ids run-ids.json   collect via `gh api` (see experiment/README.md)
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

from experiment.bench.aggregate import (
    Cell,
    TaggedRun,
    aggregate_jobs,
    aggregate_totals,
)
from experiment.bench.charts import grouped_total_bars
from experiment.bench.collect import JobTiming, RunTiming, parse_run
from experiment.bench.report import render_totals_table


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
        if not args.repo or not args.run_ids:
            ap.error("--live requires --repo and --run-ids")
        run_ids = json.loads(args.run_ids.read_text())
        tagged = _tagged_from_live(args.repo, run_ids)
    else:
        ap.error("one of --fixture or --live is required")

    totals = aggregate_totals(tagged)
    jobs = aggregate_jobs(tagged)
    args.out.mkdir(parents=True, exist_ok=True)

    # raw json (trailing newline so generated files satisfy editorconfig)
    (args.out / "results.json").write_text(
        json.dumps(
            {f"{c.side}|{c.os}|{c.cache}": asdict(s) for c, s in totals.items()},
            indent=2,
        )
        + "\n"
    )
    # csv (force LF line endings; csv.writer defaults to CRLF)
    with (args.out / "results.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(
            ["side", "os", "cache", "n", "min", "max", "avg", "median", "stddev"]
        )
        for c, s in sorted(
            totals.items(), key=lambda kv: (kv[0].os, kv[0].cache, kv[0].side)
        ):
            w.writerow(
                [c.side, c.os, c.cache, s.n, s.min, s.max, s.avg, s.median, s.stddev]
            )
    # per-job table (markdown)
    job_lines = [
        "| job | side | os | cache | avg | stddev |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for (c, name), s in sorted(
        jobs.items(), key=lambda kv: (kv[0][0].os, kv[0][0].side, kv[0][1])
    ):
        job_lines.append(
            f"| {name} | {c.side} | {c.os} | {c.cache} | {s.avg:.1f} | {s.stddev:.1f} |"
        )

    # provisioning (setup) vs work, averaged over all jobs and reps per cell.
    # setup = the `provision (flox|traditional)` step; work = rest of the job.
    setup_acc: dict[Cell, list[float]] = {}
    work_acc: dict[Cell, list[float]] = {}
    jobtot_acc: dict[Cell, list[float]] = {}
    prov_per_run: dict[Cell, list[float]] = {}
    jobs_per_run: dict[Cell, list[int]] = {}
    for tr in tagged:
        run_setup = 0.0
        for j in tr.run.jobs:
            setup_acc.setdefault(tr.cell, []).append(j.setup_seconds)
            work_acc.setdefault(tr.cell, []).append(j.work_seconds)
            jobtot_acc.setdefault(tr.cell, []).append(j.seconds)
            run_setup += j.setup_seconds
        prov_per_run.setdefault(tr.cell, []).append(run_setup)
        jobs_per_run.setdefault(tr.cell, []).append(len(tr.run.jobs))

    def _mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    setup_lines = [
        "| side | os | cache | jobs | avg setup/job | avg work/job "
        "| setup % | total provisioning/run |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cell in sorted(setup_acc, key=lambda c: (c.os, c.cache, c.side)):
        s = _mean(setup_acc[cell])
        t = _mean(jobtot_acc[cell])
        pct = (100 * s / t) if t else 0.0
        setup_lines.append(
            f"| {cell.side} | {cell.os} | {cell.cache} "
            f"| {_mean([float(n) for n in jobs_per_run[cell]]):.0f} "
            f"| {s:.1f}s | {_mean(work_acc[cell]):.1f}s | {pct:.0f}% "
            f"| {_mean(prov_per_run[cell]):.0f}s |"
        )

    report = (
        "# Flox vs Traditional CI — timing results\n\n"
        "## Total run time (per side × os × cache)\n\n"
        + render_totals_table(totals, baseline_side="traditional")
        + "\n## Provisioning (setup) vs work — per job\n\n"
        "setup = the `provision` step (flox install/activate, or setup-uv/just/"
        "bun); work = the rest of the job. `total provisioning/run` = setup summed "
        "across all jobs in a run (the cumulative billable provisioning cost).\n\n"
        + "\n".join(setup_lines)
        + "\n\n## Per-job breakdown (total job seconds)\n\n"
        + "\n".join(job_lines)
        + "\n\n## Charts\n\n![total time](total_time.png)\n"
    )
    (args.out / "REPORT.md").write_text(report)
    grouped_total_bars(totals, args.out / "total_time.png")
    print(f"wrote report + charts to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
