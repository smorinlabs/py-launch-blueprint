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
# Current cross-OS-cleaned Stage-3 run (reps up to 5; see REPORT.md for per-cell n).
TOTAL = {
    "traditional": [24.3, 23.0, 64.0, 49.0],
    "mise-mirror": [30.2, 44.6, 68.8, 55.8],
    "mise-consolidated": [24.5, 22.8, 39.4, 29.8],
    "flox-mirror": [70.0, 74.0, 405.7, 389.3],
    "flox-consolidated": [69.0, 64.4, 192.3, 193.5],
}
# provisioning setup/job (avg s): [ubuntu_cold, ubuntu_warm, macos_cold, macos_warm]
SETUP = {
    "traditional": [3.3, 3.4, 5.5, 5.2],
    "mise-mirror": [10.9, 4.9, 13.7, 6.2],
    "mise-consolidated": [9.5, 5.4, 13.9, 5.7],
    "flox-mirror": [47.6, 48.1, 163.8, 161.3],
    "flox-consolidated": [47.6, 47.3, 156.6, 165.5],
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
        "Total run time — ubuntu  (mise ~1.0-1.3x, flox ~2.8-3.2x traditional)",
        "seconds",
    )
    _grouped(
        axes[0][1],
        {s: ([TOTAL[s][2], TOTAL[s][3]], ["cold", "warm"]) for s in SIDES},
        "Total run time — macOS  (mise-consolidated <= traditional; flox ~3-8x)",
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
