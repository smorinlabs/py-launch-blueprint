from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from experiment.bench.collect import RunTiming
from experiment.bench.stats import Stats, summarize


@dataclass(frozen=True)
class Cell:
    side: str
    os: str
    cache: str


@dataclass(frozen=True)
class TaggedRun:
    cell: Cell
    run: RunTiming


def aggregate_totals(runs: list[TaggedRun]) -> dict[Cell, Stats]:
    buckets: dict[Cell, list[float]] = defaultdict(list)
    for tr in runs:
        buckets[tr.cell].append(tr.run.total_seconds)
    return {cell: summarize(values) for cell, values in buckets.items()}


def aggregate_jobs(runs: list[TaggedRun]) -> dict[tuple[Cell, str], Stats]:
    buckets: dict[tuple[Cell, str], list[float]] = defaultdict(list)
    for tr in runs:
        for job in tr.run.jobs:
            buckets[(tr.cell, job.name)].append(job.seconds)
    return {key: summarize(values) for key, values in buckets.items()}
