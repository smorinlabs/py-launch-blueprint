from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SETUP_STEP_NAMES = (
    "provision (flox)",
    "provision (traditional)",
    "provision (mise)",
    # Container (baked) sides have no `provision` step — their setup is the image
    # pull + container start, which GHA surfaces as the "Initialize containers"
    # step in the jobs API. Counting it as setup keeps the baked row honest
    # (the image pull is a treatment-only cost; see flox-ci-base PRD §7).
    "Initialize containers",
)


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_seconds(started_at: str, completed_at: str) -> float:
    return (_parse_ts(completed_at) - _parse_ts(started_at)).total_seconds()


@dataclass(frozen=True)
class JobTiming:
    name: str
    seconds: float
    setup_seconds: float
    work_seconds: float


@dataclass(frozen=True)
class RunTiming:
    run_id: int
    total_seconds: float
    jobs: list[JobTiming]


def parse_jobs(jobs_json: dict) -> list[JobTiming]:
    out: list[JobTiming] = []
    for job in jobs_json["jobs"]:
        secs = duration_seconds(job["started_at"], job["completed_at"])
        setup = 0.0
        for step in job.get("steps", []):
            name = step.get("name") or ""
            # Count BOTH the pre-step ("provision (flox)") and the post-step
            # ("Post provision (flox)" — the actions/cache SAVE of the Nix store)
            # as provisioning, so `work` reflects only the actual check, not the
            # cache-save overhead. Substring match catches the "Post " prefix.
            if (
                any(tag in name for tag in SETUP_STEP_NAMES)
                and step.get("started_at")
                and step.get("completed_at")
            ):
                setup += duration_seconds(step["started_at"], step["completed_at"])
        out.append(
            JobTiming(
                name=job["name"],
                seconds=secs,
                setup_seconds=setup,
                work_seconds=secs - setup,
            )
        )
    return out


def parse_run(run_id: int, timing_json: dict, jobs_json: dict) -> RunTiming:
    total = timing_json["run_duration_ms"] / 1000.0
    return RunTiming(run_id=run_id, total_seconds=total, jobs=parse_jobs(jobs_json))
