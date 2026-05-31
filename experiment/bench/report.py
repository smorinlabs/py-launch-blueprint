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
