# Flox vs. Traditional CI Timing Experiment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained harness that measures, in GitHub Actions, how Flox-provisioned CI compares to traditional per-tool installation — across 3 sides (traditional, flox-mirror, flox-consolidated) × 2 OS (ubuntu, macOS) × 2 cache states (cold, warm) × 5 reps — and emits a markdown report plus a charts artifact.

**Architecture:** Additive Flox branch (no ADR-12 deletions). A reusable `_checks.yml` workflow defines the ~11 checks once, gated per-`provisioner` so traditional and flox-mirror run identical check semantics. A consolidated workflow shows real-world Flox usage. A driver workflow dispatches runs serially; a dependency-light Python package (`experiment/bench/`) parses `gh api` timing JSON, aggregates per cell, and renders tables + matplotlib charts. The Python harness is TDD'd against a synthetic fixture so the full output format is provable with zero Actions minutes before any live run.

**Tech Stack:** GitHub Actions (`workflow_call`, composite actions, `actions/cache`), Flox 1.12.1 (Nix), `gh` CLI 2.93, Python 3.12 stdlib + `matplotlib` (only in the PEP-723 script), `pytest`.

**Spec:** `docs/superpowers/specs/2026-05-30-flox-ci-timing-experiment-design.md`

---

## File Structure

**Flox environment (prerequisite)**
- Create: `.flox/env/manifest.toml` — declarative toolchain (ADR-12 set)
- Create: `.flox/env/manifest.lock` — generated lockfile

**Analysis harness (`experiment/bench/` — dependency-light, TDD'd)**
- Create: `experiment/bench/__init__.py`
- Create: `experiment/bench/stats.py` — `summarize()`, `delta_pct()` (pure stats)
- Create: `experiment/bench/collect.py` — parse `gh` run/job/step JSON → timings
- Create: `experiment/bench/aggregate.py` — group tagged runs into cells → `Stats`
- Create: `experiment/bench/report.py` — render markdown tables
- Create: `experiment/bench/charts.py` — matplotlib chart functions (imports matplotlib lazily)
- Create: `experiment/analyze.py` — PEP-723 uv CLI tying it together
- Create: `experiment/fixtures/synthetic_runs.json` — full synthetic dataset (all 60 cells)
- Create: `tests/experiment/test_stats.py`, `test_collect.py`, `test_aggregate.py`, `test_report.py`
- Create: `tests/experiment/fixtures/run_jobs.json`, `run_timing.json` — gh API shape fixtures

**Provisioning composite actions**
- Create: `.github/actions/provision-flox/action.yml`
- Create: `.github/actions/provision-traditional/action.yml`

**Measured workflows**
- Create: `.github/workflows/_checks.yml` — reusable, all 11 checks
- Create: `.github/workflows/trad-suite.yml` — caller (`provisioner: traditional`)
- Create: `.github/workflows/flox-mirror-suite.yml` — caller (`provisioner: flox`)
- Create: `.github/workflows/flox-consolidated.yml` — standalone consolidated
- Create: `.github/workflows/experiment-driver.yml` — orchestrator

**Runbook**
- Create: `experiment/README.md` — how to run + validation gates

---

## Conventions for this plan

- **Activate Flox before running commands (dogfooding rule).** After Task 1 locks `.flox/`, run every build/test/tool command inside the Flox environment via `flox activate -- <cmd>` (e.g. `flox activate -- uv run pytest …`). The premise of the experiment is that Flox provisions the toolchain, so the harness is built *using* it — this also continuously smoke-tests the env from Task 2 onward. **Task 1 is the only exception** (it creates the env, so it calls the local `flox` CLI directly). Each subagent is told this rule at dispatch.
- All Python uses `from __future__ import annotations` and 3.12 syntax; line length ≤ 88 (repo Ruff config).
- Tests live under `tests/experiment/` (picked up by `testpaths=["tests"]`); test files are exempt from `S101` per existing `per-file-ignores`.
- Run unit tests with: `flox activate -- uv run pytest tests/experiment/ --override-ini="addopts=" -q` (the override clears the default `-m 'not live and not slow'` so nothing is silently skipped).
- Workflows are validated with `actionlint` (already vendored as a CI tool): `bunx --bun actionlint <file>` — if `actionlint` is unavailable locally, the repo's `actionlint.yml` workflow covers it; note expected manual install in the step.
- The 11 checks and their invocations are the single source of truth — defined in Task 8's table and reused verbatim.

---

## The 11 measured checks (source of truth)

| id | traditional invocation | flox invocation | trad tools |
| --- | --- | --- | --- |
| ruff-check | `uvx ruff check .` | `ruff check .` | uv |
| ruff-format | `uvx ruff format --check .` | `ruff format --check .` | uv |
| ty | `uv sync --group dev && uv run ty check py_launch_blueprint/` | `uv sync --group dev && ty check py_launch_blueprint/` | uv |
| pytest | `uv sync --group dev && uv run pytest -m "" --cov=py_launch_blueprint --cov-report=xml` | `uv sync --group dev && pytest -m "" --cov=py_launch_blueprint --cov-report=xml` | uv |
| taplo | `taplo check '**/*.toml'` (after `just install-taplo`) | `taplo check '**/*.toml'` | just |
| codespell | `uvx codespell --toml pyproject.toml` | `codespell --toml pyproject.toml` | uv |
| yamllint | `uvx yamllint -c .yamllint .` | `yamllint -c .yamllint .` | uv |
| editorconfig | `bunx --bun editorconfig-checker --config .editorconfig-checker.json` | `editorconfig-checker --config .editorconfig-checker.json` | bun |
| bandit | `uvx bandit -r py_launch_blueprint/ -c pyproject.toml` | `bandit -r py_launch_blueprint/ -c pyproject.toml` | uv |
| gitleaks | `gitleaks detect --source . --no-banner` (after install script) | `gitleaks detect --source . --no-banner` | gitleaks |
| commitlint | `bunx --bun commitlint --from=HEAD~10 --to=HEAD` | `commitlint --from=HEAD~10 --to=HEAD` | bun |

> Note: under Flox, `ty`/`pytest` still need project deps on the Python path, so `uv sync` runs first; Flox provides the `uv` and `python` binaries, uv.lock still owns the closure (the ADR-12 boundary, exercised live).

---

## Phase 1 — Flox environment

### Task 1: Create and lock the Flox environment

**Files:**
- Create: `.flox/env/manifest.toml`
- Create: `.flox/env/manifest.lock` (generated)

- [ ] **Step 1: Write the manifest**

Create `.flox/env/manifest.toml`:

```toml
version = 1

[install]
python.pkg-path = "python312"
uv.pkg-path = "uv"
just.pkg-path = "just"
bun.pkg-path = "bun"
lefthook.pkg-path = "lefthook"
gitleaks.pkg-path = "gitleaks"
gh.pkg-path = "gh"
taplo.pkg-path = "taplo"
ruff.pkg-path = "ruff"
yamllint.pkg-path = "yamllint"
codespell.pkg-path = "codespell"
editorconfig-checker.pkg-path = "editorconfig-checker"
bandit.pkg-path = "bandit"
commitlint.pkg-path = "commitlint"
gnumake.pkg-path = "gnumake"

[vars]

[hook]
on-activate = ''

[profile]

[options]
systems = ["aarch64-darwin", "x86_64-linux", "aarch64-linux", "x86_64-darwin"]
```

- [ ] **Step 2: Lock the environment**

Run: `flox edit -f .flox/env/manifest.toml`
Then: `flox list` — confirm all 15 packages resolve.
Expected: a `.flox/env/manifest.lock` is produced; no resolution errors.

> If `flox edit -f` is not the local CLI form, use `flox install` for each pkg-path into a fresh `flox init` env, then reconcile the generated `manifest.toml` to match Step 1. The deliverable is a committed `manifest.toml` + `manifest.lock` that resolves on Linux and macOS.

- [ ] **Step 3: Validate activation runs the tools**

Run:
```bash
flox activate -- bash -c 'ruff --version && ty --version && taplo --version && \
  yamllint --version && codespell --version && bandit --version && \
  gitleaks version && commitlint --version && uv --version'
```
Expected: every tool prints a version (proves the env provides the whole toolchain).

- [ ] **Step 4: Commit**

```bash
git add .flox/env/manifest.toml .flox/env/manifest.lock
git commit -m "feat: add additive flox environment for ci timing experiment"
```

---

## Phase 2 — Analysis harness (TDD, zero Actions minutes)

### Task 2: Stats module

**Files:**
- Create: `experiment/bench/__init__.py` (empty)
- Create: `experiment/bench/stats.py`
- Test: `tests/experiment/test_stats.py`

- [ ] **Step 1: Write the failing test**

Create `tests/experiment/test_stats.py`:

```python
from __future__ import annotations

import pytest

from experiment.bench.stats import Stats, delta_pct, summarize


def test_summarize_basic():
    s = summarize([10.0, 20.0, 30.0])
    assert s == Stats(n=3, min=10.0, max=30.0, avg=20.0, median=20.0, stddev=pytest.approx(8.16496, rel=1e-4))


def test_summarize_single_sample_has_zero_stddev():
    s = summarize([42.0])
    assert s.n == 1
    assert s.stddev == 0.0


def test_summarize_empty_raises():
    with pytest.raises(ValueError):
        summarize([])


def test_delta_pct_sign():
    assert delta_pct(100.0, 80.0) == pytest.approx(-20.0)
    assert delta_pct(100.0, 130.0) == pytest.approx(30.0)


def test_delta_pct_zero_baseline_raises():
    with pytest.raises(ValueError):
        delta_pct(0.0, 5.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/experiment/test_stats.py --override-ini="addopts=" -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'experiment.bench.stats'`

- [ ] **Step 3: Write minimal implementation**

Create `experiment/__init__.py` (empty), `experiment/bench/__init__.py` (empty), and `experiment/bench/stats.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/experiment/test_stats.py --override-ini="addopts=" -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add experiment/__init__.py experiment/bench/__init__.py experiment/bench/stats.py tests/experiment/test_stats.py
git commit -m "feat: add stats summarization for ci timing harness"
```

---

### Task 3: Collect module (parse gh API timing JSON)

**Files:**
- Create: `experiment/bench/collect.py`
- Test: `tests/experiment/test_collect.py`
- Create: `tests/experiment/fixtures/run_jobs.json`, `tests/experiment/fixtures/run_timing.json`

- [ ] **Step 1: Write the gh-shape fixtures**

Create `tests/experiment/fixtures/run_timing.json` (shape of `gh api repos/{o}/{r}/actions/runs/{id}/timing`):

```json
{"run_duration_ms": 240000}
```

Create `tests/experiment/fixtures/run_jobs.json` (shape of `gh api repos/{o}/{r}/actions/runs/{id}/jobs`):

```json
{
  "jobs": [
    {
      "name": "ruff-check",
      "started_at": "2026-05-30T10:00:00Z",
      "completed_at": "2026-05-30T10:00:30Z",
      "steps": [
        {"name": "provision (flox)", "started_at": "2026-05-30T10:00:05Z", "completed_at": "2026-05-30T10:00:20Z"}
      ]
    },
    {
      "name": "pytest",
      "started_at": "2026-05-30T10:00:00Z",
      "completed_at": "2026-05-30T10:02:00Z",
      "steps": [
        {"name": "provision (flox)", "started_at": "2026-05-30T10:00:05Z", "completed_at": "2026-05-30T10:00:25Z"}
      ]
    }
  ]
}
```

- [ ] **Step 2: Write the failing test**

Create `tests/experiment/test_collect.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

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


def test_parse_run_uses_timing_total():
    timing = json.loads((FIX / "run_timing.json").read_text())
    jobs_json = json.loads((FIX / "run_jobs.json").read_text())
    run = parse_run(99, timing, jobs_json)
    assert run.run_id == 99
    assert run.total_seconds == 240.0
    assert len(run.jobs) == 2
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/experiment/test_collect.py --override-ini="addopts=" -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'experiment.bench.collect'`

- [ ] **Step 4: Write minimal implementation**

Create `experiment/bench/collect.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SETUP_STEP_NAMES = ("provision (flox)", "provision (traditional)")


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
            if (
                step.get("name") in SETUP_STEP_NAMES
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/experiment/test_collect.py --override-ini="addopts=" -q`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add experiment/bench/collect.py tests/experiment/test_collect.py tests/experiment/fixtures/
git commit -m "feat: add gh timing json parsing for ci harness"
```

---

### Task 4: Aggregate module

**Files:**
- Create: `experiment/bench/aggregate.py`
- Test: `tests/experiment/test_aggregate.py`

- [ ] **Step 1: Write the failing test**

Create `tests/experiment/test_aggregate.py`:

```python
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
    runs = [TaggedRun(cell, _run(1, 100.0, 10.0)), TaggedRun(cell, _run(2, 120.0, 12.0))]
    totals = aggregate_totals(runs)
    assert totals[cell].avg == 110.0


def test_aggregate_jobs_keys_by_cell_and_job():
    cell = Cell("flox-mirror", "ubuntu-latest", "warm")
    runs = [TaggedRun(cell, _run(1, 100.0, 10.0)), TaggedRun(cell, _run(2, 100.0, 14.0))]
    jobs = aggregate_jobs(runs)
    assert jobs[(cell, "ruff-check")].avg == 12.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/experiment/test_aggregate.py --override-ini="addopts=" -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `experiment/bench/aggregate.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/experiment/test_aggregate.py --override-ini="addopts=" -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add experiment/bench/aggregate.py tests/experiment/test_aggregate.py
git commit -m "feat: add per-cell aggregation for ci harness"
```

---

### Task 5: Report module (markdown tables)

**Files:**
- Create: `experiment/bench/report.py`
- Test: `tests/experiment/test_report.py`

- [ ] **Step 1: Write the failing test**

Create `tests/experiment/test_report.py`:

```python
from __future__ import annotations

from experiment.bench.aggregate import Cell
from experiment.bench.report import render_totals_table
from experiment.bench.stats import summarize


def test_render_totals_table_has_delta_vs_baseline():
    totals = {
        Cell("traditional", "ubuntu-latest", "cold"): summarize([100.0, 100.0]),
        Cell("flox-mirror", "ubuntu-latest", "cold"): summarize([80.0, 80.0]),
    }
    md = render_totals_table(totals, baseline_side="traditional")
    assert "| side | os | cache |" in md
    assert "flox-mirror" in md
    # flox-mirror is 20% faster than traditional baseline on the same os/cache
    assert "-20.0%" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/experiment/test_report.py --override-ini="addopts=" -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `experiment/bench/report.py`:

```python
from __future__ import annotations

from experiment.bench.aggregate import Cell
from experiment.bench.stats import Stats, delta_pct


def _baseline_for(
    totals: dict[Cell, Stats], cell: Cell, baseline_side: str
) -> Stats | None:
    key = Cell(baseline_side, cell.os, cell.cache)
    return totals.get(key)


def render_totals_table(totals: dict[Cell, Stats], baseline_side: str) -> str:
    header = (
        "| side | os | cache | n | min | max | avg | median | stddev | Δ% vs base |\n"
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    rows: list[str] = []
    for cell in sorted(totals, key=lambda c: (c.os, c.cache, c.side)):
        s = totals[cell]
        base = _baseline_for(totals, cell, baseline_side)
        if base is None or cell.side == baseline_side:
            delta = "—"
        else:
            delta = f"{delta_pct(base.avg, s.avg):+.1f}%"
        rows.append(
            f"| {cell.side} | {cell.os} | {cell.cache} | {s.n} | "
            f"{s.min:.1f} | {s.max:.1f} | {s.avg:.1f} | {s.median:.1f} | "
            f"{s.stddev:.1f} | {delta} |"
        )
    return header + "\n" + "\n".join(rows) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/experiment/test_report.py --override-ini="addopts=" -q`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add experiment/bench/report.py tests/experiment/test_report.py
git commit -m "feat: add markdown report rendering for ci harness"
```

---

### Task 6: Charts module + synthetic fixture

**Files:**
- Create: `experiment/bench/charts.py`
- Create: `experiment/fixtures/synthetic_runs.json`

- [ ] **Step 1: Write the charts module**

Create `experiment/bench/charts.py` (matplotlib imported lazily so the rest of the package stays dependency-free and unit-testable without matplotlib):

```python
from __future__ import annotations

from pathlib import Path

from experiment.bench.aggregate import Cell
from experiment.bench.stats import Stats


def grouped_total_bars(totals: dict[Cell, Stats], out: Path) -> Path:
    """Grouped bars: total time by side, grouped by OS, faceted by cache."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    caches = sorted({c.cache for c in totals})
    sides = sorted({c.side for c in totals})
    oses = sorted({c.os for c in totals})
    fig, axes = plt.subplots(1, len(caches), figsize=(6 * len(caches), 4), squeeze=False)
    for ax, cache in zip(axes[0], caches, strict=True):
        width = 0.8 / max(len(sides), 1)
        for i, side in enumerate(sides):
            ys = [
                totals[Cell(side, os, cache)].avg
                if Cell(side, os, cache) in totals
                else 0.0
                for os in oses
            ]
            errs = [
                totals[Cell(side, os, cache)].stddev
                if Cell(side, os, cache) in totals
                else 0.0
                for os in oses
            ]
            xs = [j + i * width for j in range(len(oses))]
            ax.bar(xs, ys, width=width, yerr=errs, capsize=3, label=side)
        ax.set_title(f"total time ({cache})")
        ax.set_ylabel("seconds")
        ax.set_xticks([j + 0.4 for j in range(len(oses))])
        ax.set_xticklabels(oses)
        ax.legend()
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out
```

- [ ] **Step 2: Write the synthetic fixture (all 60 cells, 5 reps each)**

Create `experiment/fixtures/synthetic_runs.json`. This is a list of tagged runs; each has `side`, `os`, `cache`, `run_id`, `total_seconds`, and a `jobs` list. Use plausible numbers (flox cold slower to build, flox warm faster; macOS slower than ubuntu). Minimum: 3 sides × 2 os × 2 cache × 5 reps = 60 entries. Generate it programmatically with this one-off (committed output, not the generator):

```python
# scratch generator (run once, paste output into the fixture; do NOT commit this snippet)
import json, itertools
sides = ["traditional", "flox-mirror", "flox-consolidated"]
oses = ["ubuntu-latest", "macos-latest"]
caches = ["cold", "warm"]
base = {"traditional": 200, "flox-mirror": 210, "flox-consolidated": 170}
cold_penalty = {"traditional": 40, "flox-mirror": 120, "flox-consolidated": 100}
os_mult = {"ubuntu-latest": 1.0, "macos-latest": 1.6}
runs = []
rid = 1000
for side, os_, cache in itertools.product(sides, oses, caches):
    for rep in range(5):
        total = (base[side] + (cold_penalty[side] if cache == "cold" else 0)) * os_mult[os_]
        total += (rep - 2) * 3  # mild jitter
        runs.append({
            "side": side, "os": os_, "cache": cache, "run_id": rid,
            "total_seconds": round(total, 1),
            "jobs": [
                {"name": "ruff-check", "seconds": round(total * 0.05, 1), "setup_seconds": round(total * 0.03, 1)},
                {"name": "pytest", "seconds": round(total * 0.4, 1), "setup_seconds": round(total * 0.05, 1)},
            ],
        })
        rid += 1
print(json.dumps(runs, indent=2))
```

The committed `experiment/fixtures/synthetic_runs.json` is the printed output (a JSON array of 60 objects).

- [ ] **Step 3: Commit**

```bash
git add experiment/bench/charts.py experiment/fixtures/synthetic_runs.json
git commit -m "feat: add chart rendering and synthetic fixture for ci harness"
```

---

### Task 7: `analyze.py` CLI + harness unit gate

**Files:**
- Create: `experiment/analyze.py`

- [ ] **Step 1: Write the CLI script**

Create `experiment/analyze.py`:

```python
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
```

- [ ] **Step 2: Run the harness unit gate (Validation Gate 1 — zero Actions minutes)**

Run:
```bash
chmod +x experiment/analyze.py
uv run --script experiment/analyze.py --fixture experiment/fixtures/synthetic_runs.json --out /tmp/exp-out
```
Expected: prints `wrote report + charts to /tmp/exp-out`; `/tmp/exp-out` contains `REPORT.md`, `results.json`, `results.csv`, `total_time.png`. Open `REPORT.md` — confirm the totals table has Δ% values and the per-job table is populated; confirm `total_time.png` renders grouped bars.

- [ ] **Step 3: Commit**

```bash
git add experiment/analyze.py
git commit -m "feat: add analyze.py cli with fixture and live modes"
```

---

## Phase 3 — Provisioning composite actions

### Task 8: `provision-flox` composite

**Files:**
- Create: `.github/actions/provision-flox/action.yml`

- [ ] **Step 1: Write the action**

Create `.github/actions/provision-flox/action.yml`:

```yaml
name: provision-flox
description: Install Flox and restore/save the Nix store cache.
inputs:
  cache:
    description: cold | warm
    required: true
runs:
  using: composite
  steps:
    - name: Install Flox
      uses: flox/install-flox-action@v2
    - name: Cache Nix store
      uses: actions/cache@v4
      with:
        path: |
          /nix
          ~/.cache/flox
        # cold -> unique key (guaranteed miss); warm -> stable key per lock+os
        key: >-
          flox-${{ inputs.cache }}-${{ runner.os }}-${{ hashFiles('.flox/env/manifest.lock') }}-${{
            inputs.cache == 'cold' && github.run_id || 'stable' }}
        restore-keys: |
          ${{ inputs.cache == 'warm' && format('flox-warm-{0}-{1}-stable', runner.os, hashFiles('.flox/env/manifest.lock')) || 'flox-never-restore' }}
    - name: Warm the flox env
      shell: bash
      run: flox activate -- true
```

- [ ] **Step 2: Lint the action**

Run: `bunx --bun actionlint .github/actions/provision-flox/action.yml || echo "actionlint not available locally; CI actionlint.yml will cover it"`
Expected: no errors (or the documented fallback note).

- [ ] **Step 3: Commit**

```bash
git add .github/actions/provision-flox/action.yml
git commit -m "feat: add provision-flox composite action"
```

---

### Task 9: `provision-traditional` composite

**Files:**
- Create: `.github/actions/provision-traditional/action.yml`

- [ ] **Step 1: Write the action**

Create `.github/actions/provision-traditional/action.yml`:

```yaml
name: provision-traditional
description: Install the traditional per-tool toolchain (uv / just / bun / gitleaks).
inputs:
  tools:
    description: space-separated subset of "uv just bun gitleaks"
    required: true
  cache:
    description: cold | warm
    required: true
runs:
  using: composite
  steps:
    - name: Setup uv
      if: contains(inputs.tools, 'uv')
      uses: astral-sh/setup-uv@v7
      with:
        enable-cache: ${{ inputs.cache == 'warm' }}
    - name: Setup just
      if: contains(inputs.tools, 'just')
      uses: extractions/setup-just@v4
    - name: Install taplo (when just present)
      if: contains(inputs.tools, 'just')
      shell: bash
      run: just install-taplo
    - name: Setup bun
      if: contains(inputs.tools, 'bun')
      uses: oven-sh/setup-bun@v2
    - name: Install gitleaks
      if: contains(inputs.tools, 'gitleaks')
      shell: bash
      run: bash scripts/install-gitleaks.sh
```

- [ ] **Step 2: Lint the action**

Run: `bunx --bun actionlint .github/actions/provision-traditional/action.yml || echo "actionlint not available locally; CI actionlint.yml will cover it"`
Expected: no errors (or fallback note).

- [ ] **Step 3: Commit**

```bash
git add .github/actions/provision-traditional/action.yml
git commit -m "feat: add provision-traditional composite action"
```

---

## Phase 4 — Measured workflows

### Task 10: Reusable `_checks.yml`

**Files:**
- Create: `.github/workflows/_checks.yml`

- [ ] **Step 1: Write the reusable workflow**

Create `.github/workflows/_checks.yml`. Each of the 11 jobs follows one template: checkout → provision (gated by `provisioner`) → run the check (flox vs traditional invocation chosen at runtime). The `RUN` env carries the flox-activate prefix when `provisioner == flox`. Full file:

```yaml
name: _checks
on:
  workflow_call:
    inputs:
      provisioner:
        type: string
        required: true   # traditional | flox
      os:
        type: string
        required: true
      cache:
        type: string
        required: true

permissions:
  contents: read

env:
  # flox runs the bare tool; traditional path embeds its own runner (uvx/bunx)
  RUN: ${{ inputs.provisioner == 'flox' && 'flox activate -- ' || '' }}

jobs:
  ruff-check:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: uv, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- ruff check .' || 'uvx ruff check .' }}

  ruff-format:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: uv, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- ruff format --check .' || 'uvx ruff format --check .' }}

  ty:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: uv, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: |
          if [ "${{ inputs.provisioner }}" = "flox" ]; then
            flox activate -- bash -c 'uv sync --group dev && ty check py_launch_blueprint/'
          else
            uv sync --group dev && uv run ty check py_launch_blueprint/
          fi

  pytest:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: uv, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: |
          if [ "${{ inputs.provisioner }}" = "flox" ]; then
            flox activate -- bash -c 'uv sync --group dev && pytest -m "" --cov=py_launch_blueprint --cov-report=xml'
          else
            uv sync --group dev && uv run pytest -m "" --cov=py_launch_blueprint --cov-report=xml
          fi

  taplo:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: just, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- taplo check ' || 'taplo check ' }}'**/*.toml'

  codespell:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: uv, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- codespell --toml pyproject.toml' || 'uvx codespell --toml pyproject.toml' }}

  yamllint:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: uv, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- yamllint -c .yamllint .' || 'uvx yamllint -c .yamllint .' }}

  editorconfig:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: bun, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- editorconfig-checker --config .editorconfig-checker.json' || 'bunx --bun editorconfig-checker --config .editorconfig-checker.json' }}

  bandit:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: uv, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- bandit -r py_launch_blueprint/ -c pyproject.toml' || 'uvx bandit -r py_launch_blueprint/ -c pyproject.toml' }}

  gitleaks:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
        with: {fetch-depth: 0}
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: gitleaks, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- gitleaks detect --source . --no-banner' || 'gitleaks detect --source . --no-banner' }}

  commitlint:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
        with: {fetch-depth: 0}
      - if: inputs.provisioner == 'traditional'
        uses: ./.github/actions/provision-traditional
        with: {tools: bun, cache: ${{ inputs.cache }}}
      - if: inputs.provisioner == 'flox'
        uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: run
        shell: bash
        run: ${{ inputs.provisioner == 'flox' && 'flox activate -- commitlint --from=HEAD~10 --to=HEAD' || 'bunx --bun commitlint --from=HEAD~10 --to=HEAD' }}
```

- [ ] **Step 2: Lint**

Run: `bunx --bun actionlint .github/workflows/_checks.yml || echo "actionlint not available locally; CI will cover it"`
Expected: no errors. Fix any shell-quoting issues actionlint flags (especially the `taplo` glob line) before committing.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/_checks.yml
git commit -m "feat: add reusable _checks workflow parameterized by provisioner"
```

---

### Task 11: Caller workflows `trad-suite.yml` + `flox-mirror-suite.yml`

**Files:**
- Create: `.github/workflows/trad-suite.yml`
- Create: `.github/workflows/flox-mirror-suite.yml`

- [ ] **Step 1: Write both callers**

Create `.github/workflows/trad-suite.yml`:

```yaml
name: trad-suite
on:
  workflow_dispatch:
    inputs:
      os:
        type: string
        required: true
      cache:
        type: string
        required: true

permissions:
  contents: read

jobs:
  checks:
    uses: ./.github/workflows/_checks.yml
    with:
      provisioner: traditional
      os: ${{ inputs.os }}
      cache: ${{ inputs.cache }}
```

Create `.github/workflows/flox-mirror-suite.yml` (identical but `provisioner: flox` and `name: flox-mirror-suite`):

```yaml
name: flox-mirror-suite
on:
  workflow_dispatch:
    inputs:
      os:
        type: string
        required: true
      cache:
        type: string
        required: true

permissions:
  contents: read

jobs:
  checks:
    uses: ./.github/workflows/_checks.yml
    with:
      provisioner: flox
      os: ${{ inputs.os }}
      cache: ${{ inputs.cache }}
```

- [ ] **Step 2: Lint both**

Run: `bunx --bun actionlint .github/workflows/trad-suite.yml .github/workflows/flox-mirror-suite.yml || echo "CI actionlint will cover it"`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/trad-suite.yml .github/workflows/flox-mirror-suite.yml
git commit -m "feat: add traditional and flox-mirror suite callers"
```

---

### Task 12: `flox-consolidated.yml`

**Files:**
- Create: `.github/workflows/flox-consolidated.yml`

- [ ] **Step 1: Write the consolidated workflow**

Create `.github/workflows/flox-consolidated.yml` (2 jobs: one activates the env once and runs all fast hygiene checks sequentially; `pytest` stays separate to preserve parallelism on the long pole):

```yaml
name: flox-consolidated
on:
  workflow_dispatch:
    inputs:
      os:
        type: string
        required: true
      cache:
        type: string
        required: true

permissions:
  contents: read

jobs:
  hygiene:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
        with: {fetch-depth: 0}
      - uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: all hygiene checks under one activation
        shell: bash
        run: |
          flox activate -- bash -euo pipefail -c '
            ruff check .
            ruff format --check .
            uv sync --group dev && ty check py_launch_blueprint/
            taplo check "**/*.toml"
            codespell --toml pyproject.toml
            yamllint -c .yamllint .
            editorconfig-checker --config .editorconfig-checker.json
            bandit -r py_launch_blueprint/ -c pyproject.toml
            gitleaks detect --source . --no-banner
            commitlint --from=HEAD~10 --to=HEAD
          '

  pytest:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - uses: ./.github/actions/provision-flox
        with: {cache: ${{ inputs.cache }}}
      - name: tests under one activation
        shell: bash
        run: flox activate -- bash -c 'uv sync --group dev && pytest -m "" --cov=py_launch_blueprint --cov-report=xml'
```

- [ ] **Step 2: Lint**

Run: `bunx --bun actionlint .github/workflows/flox-consolidated.yml || echo "CI actionlint will cover it"`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/flox-consolidated.yml
git commit -m "feat: add consolidated flox suite workflow"
```

---

## Phase 5 — Driver

### Task 13: `experiment-driver.yml`

**Files:**
- Create: `.github/workflows/experiment-driver.yml`

- [ ] **Step 1: Write the driver**

Create `.github/workflows/experiment-driver.yml`. It dispatches the target workflows serially via `gh`, waits for each, and records run IDs into `run-ids.json` (uploaded as an artifact for `analyze.py --live`). Scoped by inputs so one invocation stays well under the 6h job limit.

```yaml
name: experiment-driver
on:
  workflow_dispatch:
    inputs:
      sides:
        description: comma-separated subset of trad-suite,flox-mirror-suite,flox-consolidated
        type: string
        default: trad-suite,flox-mirror-suite,flox-consolidated
      oses:
        description: comma-separated subset of ubuntu-latest,macos-latest
        type: string
        default: ubuntu-latest
      caches:
        description: comma-separated subset of cold,warm
        type: string
        default: cold,warm
      reps:
        description: repetitions per cell
        type: string
        default: "5"

permissions:
  actions: write
  contents: read

jobs:
  drive:
    runs-on: ubuntu-latest
    timeout-minutes: 350
    steps:
      - uses: actions/checkout@v6
      - name: Dispatch, wait, collect run IDs
        env:
          GH_TOKEN: ${{ github.token }}
          REF: ${{ github.ref_name }}
        shell: bash
        run: |
          set -euo pipefail
          declare -A RUNIDS
          IFS=',' read -ra SIDES <<< "${{ inputs.sides }}"
          IFS=',' read -ra OSES <<< "${{ inputs.oses }}"
          IFS=',' read -ra CACHES <<< "${{ inputs.caches }}"
          REPS=${{ inputs.reps }}
          collect='{}'
          for side in "${SIDES[@]}"; do
            for os in "${OSES[@]}"; do
              for cache in "${CACHES[@]}"; do
                # warm: prime once (not measured) so the 5 measured runs hit cache
                if [ "$cache" = "warm" ]; then
                  gh workflow run "${side}.yml" --ref "$REF" -f os="$os" -f cache="warm" || true
                  sleep 20
                  gh run watch "$(gh run list --workflow="${side}.yml" --branch "$REF" --limit 1 --json databaseId -q '.[0].databaseId')" --exit-status || true
                fi
                ids=()
                for i in $(seq 1 "$REPS"); do
                  gh workflow run "${side}.yml" --ref "$REF" -f os="$os" -f cache="$cache"
                  sleep 20
                  rid=$(gh run list --workflow="${side}.yml" --branch "$REF" --limit 1 --json databaseId -q '.[0].databaseId')
                  gh run watch "$rid" --exit-status || true
                  ids+=("$rid")
                done
                tag="${side}|${os}|${cache}"
                joined=$(printf '%s\n' "${ids[@]}" | paste -sd, -)
                collect=$(echo "$collect" | jq --arg k "$tag" --arg v "$joined" '.[$k] = ($v|split(",")|map(tonumber))')
              done
            done
          done
          echo "$collect" > run-ids.json
          cat run-ids.json
      - uses: actions/upload-artifact@v4
        with:
          name: experiment-run-ids
          path: run-ids.json
```

> Note: `gh run list --limit 1` after dispatch is a best-effort correlation; if concurrent dispatches race, tighten by filtering on `--event workflow_dispatch` and a unique input echoed in the run name. For the serial driver above (one dispatch at a time, `sleep` + `watch`), the latest run is reliably the one just dispatched.

- [ ] **Step 2: Lint**

Run: `bunx --bun actionlint .github/workflows/experiment-driver.yml || echo "CI actionlint will cover it"`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/experiment-driver.yml
git commit -m "feat: add experiment driver workflow"
```

---

## Phase 6 — Runbook & live validation gates

### Task 14: Runbook + execute the gates

**Files:**
- Create: `experiment/README.md`

- [ ] **Step 1: Write the runbook**

Create `experiment/README.md`:

```markdown
# Flox vs Traditional CI timing experiment

## What this is
Measures CI provisioning time: traditional vs flox-mirror vs flox-consolidated,
across ubuntu/macOS, cold/warm cache, 5 reps. See
`docs/superpowers/specs/2026-05-30-flox-ci-timing-experiment-design.md`.

## Validation gates (run in order)

### Gate 1 — harness (no Actions minutes)
    uv run --script experiment/analyze.py \
      --fixture experiment/fixtures/synthetic_runs.json --out /tmp/exp-out
Confirm /tmp/exp-out has REPORT.md (populated tables) and total_time.png.

### Gate 2 — correctness smoke (6 runs)
Push the branch, then for each side × os, one cold run:
    gh workflow run trad-suite.yml --ref experiment/flox-ci-timing -f os=ubuntu-latest -f cache=cold
    gh workflow run flox-mirror-suite.yml --ref experiment/flox-ci-timing -f os=ubuntu-latest -f cache=cold
    gh workflow run flox-consolidated.yml --ref experiment/flox-ci-timing -f os=ubuntu-latest -f cache=cold
    # repeat with os=macos-latest
Confirm ALL jobs are green (equivalent checks pass) before timing.

### Gate 3 — full experiment
Run the driver per OS to stay under the job time limit:
    gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing -f oses=ubuntu-latest
    gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing -f oses=macos-latest
Download the run-ids artifact from each driver run, merge into run-ids.json, then:
    uv run --script experiment/analyze.py --live \
      --repo smorinlabs/py-launch-blueprint --run-ids run-ids.json \
      --out experiment/results
Commit experiment/results/ (REPORT.md, charts, raw data).
```

- [ ] **Step 2: Run Gate 1 to confirm the harness end-to-end**

Run: `uv run --script experiment/analyze.py --fixture experiment/fixtures/synthetic_runs.json --out experiment/results-sample`
Expected: `experiment/results-sample/REPORT.md` + `total_time.png` generated from synthetic data — this is the demonstrable markdown + visual artifact format, with zero Actions minutes.

- [ ] **Step 3: Commit runbook + sample output**

```bash
git add experiment/README.md experiment/results-sample/
git commit -m "docs: add experiment runbook and sample analysis output"
```

- [ ] **Step 4: Push branch and hand off to the user for live gates 2–3**

```bash
git push -u origin experiment/flox-ci-timing
```
Then the user runs Gate 2 (correctness) and Gate 3 (full 60-run experiment) per `experiment/README.md`, and `analyze.py --live` fills `experiment/results/` with the real report + charts artifact.

---

## Self-Review

**Spec coverage:**
- Additive branch / no deletions → Task 1 + plan intro ✓
- ~11 checks → Task 10 table ✓
- 3 sides → Tasks 11–12 ✓
- 2 OS dimension → all workflow `os` inputs + driver `oses` ✓
- cold/warm via cache keying → Tasks 8/9 + driver priming ✓
- 5 reps → driver `reps` ✓
- total + per-job + setup/work split → `collect.py` (setup/work), `aggregate.py` (totals + jobs) ✓
- min/max/avg/median/stddev → `stats.py` ✓
- markdown + charts artifact → `report.py`, `charts.py`, `analyze.py`, driver `upload-artifact` ✓
- dispatch-only, this branch → all workflows `workflow_dispatch` ✓
- build harness + user runs live → Phase 6 hand-off ✓
- validation gates / "testable" → Gates 1–3 ✓

**Placeholder scan:** No TBD/TODO; the scratch fixture generator in Task 6 is explicitly marked do-not-commit and its committed output is specified. The `[vars]`/`[profile]`/`[hook]` empty tables in the manifest are intentional (valid empty TOML sections), not placeholders.

**Type/name consistency:** `Cell`, `TaggedRun`, `RunTiming`, `JobTiming`, `Stats`, `summarize`, `delta_pct`, `aggregate_totals`, `aggregate_jobs`, `render_totals_table`, `grouped_total_bars`, `parse_run`, `parse_jobs`, `duration_seconds` — names are used identically across `stats.py`, `collect.py`, `aggregate.py`, `report.py`, `charts.py`, and `analyze.py`. Setup-step name `"provision (flox)"` matches between `_checks.yml` step naming intent and `collect.SETUP_STEP_NAMES` — NOTE during execution: `_checks.yml` step `name:` is currently `run`; rename the provision steps to `provision (flox)` / `provision (traditional)` so the setup/work split in `collect.py` matches. (Apply in Task 10.)

## Known follow-ups (out of scope for this plan)
- macOS rep count could drop to 3 via driver `reps` if minute cost bites.
- Box/strip and per-job small-multiple charts (specced) — `charts.py` ships `grouped_total_bars`; add `variance_box()` and `per_job_small_multiples()` as a fast follow once Gate 1 output is reviewed.
```
