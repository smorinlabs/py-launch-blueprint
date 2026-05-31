from __future__ import annotations

from experiment.bench.aggregate import Cell, TaggedRun, aggregate_jobs, aggregate_totals
from experiment.bench.collect import JobTiming, RunTiming


def _run(run_id: int, total: float, ruff: float) -> RunTiming:
    return RunTiming(
        run_id=run_id,
        total_seconds=total,
        jobs=[JobTiming("ruff-check", ruff, 0.0, ruff)],
    )


def test_aggregate_totals_groups_by_cell():
    cell = Cell("traditional", "ubuntu-latest", "cold")
    runs = [
        TaggedRun(cell, _run(1, 100.0, 10.0)),
        TaggedRun(cell, _run(2, 120.0, 12.0)),
    ]
    totals = aggregate_totals(runs)
    assert totals[cell].avg == 110.0


def test_aggregate_jobs_keys_by_cell_and_job():
    cell = Cell("flox-mirror", "ubuntu-latest", "warm")
    runs = [
        TaggedRun(cell, _run(1, 100.0, 10.0)),
        TaggedRun(cell, _run(2, 100.0, 14.0)),
    ]
    jobs = aggregate_jobs(runs)
    assert jobs[(cell, "ruff-check")].avg == 12.0
