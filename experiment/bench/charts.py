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
    fig, axes = plt.subplots(
        1, len(caches), figsize=(6 * len(caches), 4), squeeze=False
    )
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
