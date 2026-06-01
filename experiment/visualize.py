#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Render the final timing figure: traditional vs flox vs mise (committed results).

Aggregated means from experiment/results/REPORT.md
(5 sides x 2 OS x 2 cache x reps=5; 10 checks).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIDES = [
    "traditional",
    "mise-mirror",
    "mise-consolidated",
    "flox-mirror",
    "flox-consolidated",
]
COLORS = {
    "traditional": "#2f7ed8",
    "mise-mirror": "#5cb85c",
    "mise-consolidated": "#2ca089",
    "flox-mirror": "#d9534f",
    "flox-consolidated": "#f0ad4e",
}
# total run time (avg s): [ubuntu_cold, ubuntu_warm, macos_cold, macos_warm]
TOTAL = {
    "traditional": [17.2, 17.2, 36.4, 38.7],
    "mise-mirror": [33.0, 23.0, 63.0, 43.6],
    "mise-consolidated": [29.8, 23.2, 35.8, 30.6],
    "flox-mirror": [64.8, 64.6, 318.4, 303.6],
    "flox-consolidated": [64.8, 62.8, 181.6, 161.6],
}
# provisioning setup/job (avg s): [ubuntu_cold, ubuntu_warm, macos_cold, macos_warm]
SETUP = {
    "traditional": [3.0, 3.3, 4.1, 5.0],
    "mise-mirror": [11.9, 4.0, 13.7, 6.2],
    "mise-consolidated": [11.7, 4.6, 14.1, 7.3],
    "flox-mirror": [46.5, 47.6, 135.8, 129.0],
    "flox-consolidated": [49.3, 48.3, 150.6, 129.0],
}


def _grouped(ax, pairs, title, ylabel, logy=False):
    # pairs: dict side -> (values, labels)
    labels = pairs[SIDES[0]][1]
    w = 0.16
    for i, side in enumerate(SIDES):
        vals = pairs[side][0]
        xs = [j + i * w for j in range(len(vals))]
        bars = ax.bar(xs, vals, width=w, color=COLORS[side], label=side)
        for b, y in zip(bars, vals, strict=True):
            ax.text(
                b.get_x() + b.get_width() / 2,
                y,
                f"{y:.0f}",
                ha="center",
                va="bottom",
                fontsize=6.5,
            )
    ax.set_xticks([j + 2 * w for j in range(len(labels))])
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if logy:
        ax.set_yscale("log")
    ax.legend(fontsize=6.5, ncol=2)


def main(out: Path) -> int:
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(
        "CI provisioning: traditional vs mise vs flox — GitHub Actions (reps=5, 10 checks)",
        fontsize=15,
        fontweight="bold",
    )

    _grouped(
        axes[0][0],
        {s: ([TOTAL[s][0], TOTAL[s][1]], ["cold", "warm"]) for s in SIDES},
        "Total run time — ubuntu  (mise ~2x, flox ~3.8x traditional)",
        "seconds",
    )
    _grouped(
        axes[0][1],
        {s: ([TOTAL[s][2], TOTAL[s][3]], ["cold", "warm"]) for s in SIDES},
        "Total run time — macOS  (mise-consolidated <= traditional; flox 5-9x)",
        "seconds (log)",
        logy=True,
    )
    _grouped(
        axes[1][0],
        {s: ([SETUP[s][0], SETUP[s][2]], ["ubuntu cold", "macOS cold"]) for s in SIDES},
        "Provisioning per job (cold)  —  mise OS-insensitive, flox OS-sensitive",
        "seconds (log)",
        logy=True,
    )
    _grouped(
        axes[1][1],
        {s: ([SETUP[s][0], SETUP[s][1]], ["cold", "warm"]) for s in SIDES},
        "Provisioning per job, cold vs warm (ubuntu)  —  mise cache works, flox doesn't",
        "seconds",
    )

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    target = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("experiment/results/summary.png")
    )
    raise SystemExit(main(target))
