from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, median, pstdev


@dataclass(frozen=True)
class Stats:
    n: int
    min: float
    max: float
    avg: float
    median: float
    stddev: float


def summarize(samples: list[float]) -> Stats:
    if not samples:
        raise ValueError("summarize requires at least one sample")
    return Stats(
        n=len(samples),
        min=min(samples),
        max=max(samples),
        avg=fmean(samples),
        median=median(samples),
        stddev=pstdev(samples) if len(samples) > 1 else 0.0,
    )


def delta_pct(baseline: float, value: float) -> float:
    if baseline == 0:
        raise ValueError("baseline must be non-zero")
    return (value - baseline) / baseline * 100.0
