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
