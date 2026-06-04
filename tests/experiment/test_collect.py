from __future__ import annotations

import json
from pathlib import Path

from experiment.bench.collect import duration_seconds, parse_jobs, parse_run

FIX = Path(__file__).parent / "fixtures"


def test_duration_seconds():
    assert duration_seconds("2026-05-30T10:00:00Z", "2026-05-30T10:00:30Z") == 30.0


def test_parse_jobs_splits_setup_and_work():
    jobs = parse_jobs(json.loads((FIX / "run_jobs.json").read_text()))
    ruff = next(j for j in jobs if j.name == "ruff-check")
    assert ruff.seconds == 30.0
    assert ruff.setup_seconds == 15.0
    assert ruff.work_seconds == 15.0


def test_parse_jobs_counts_container_init_as_setup():
    # Baked (container) sides have no `provision` step; their setup is the image
    # pull, which GHA surfaces as the "Initialize containers" step. It must be
    # counted as setup so the baked row's work reflects only the actual checks.
    jobs_json = {
        "jobs": [
            {
                "name": "hygiene",
                "started_at": "2026-06-04T10:00:00Z",
                "completed_at": "2026-06-04T10:01:00Z",  # 60s total
                "steps": [
                    {
                        "name": "Initialize containers",
                        "started_at": "2026-06-04T10:00:00Z",
                        "completed_at": "2026-06-04T10:00:20Z",  # 20s pull
                    },
                    {
                        "name": "all hygiene checks under one activation (baked)",
                        "started_at": "2026-06-04T10:00:20Z",
                        "completed_at": "2026-06-04T10:01:00Z",  # 40s work
                    },
                ],
            }
        ]
    }
    job = parse_jobs(jobs_json)[0]
    assert job.setup_seconds == 20.0
    assert job.work_seconds == 40.0


def test_parse_run_uses_timing_total():
    timing = json.loads((FIX / "run_timing.json").read_text())
    jobs_json = json.loads((FIX / "run_jobs.json").read_text())
    run = parse_run(99, timing, jobs_json)
    assert run.run_id == 99
    assert run.total_seconds == 240.0
    assert len(run.jobs) == 2
