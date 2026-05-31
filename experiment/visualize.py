#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Render the final Flox-vs-Traditional CI timing figure (committed results).

Numbers are the aggregated means from experiment/results/REPORT.md
(3 sides x 2 OS x 2 cache x reps=5; 10 checks).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIDES = ["traditional", "flox-mirror", "flox-consolidated"]
COLORS = {
    "traditional": "#2f7ed8",
    "flox-mirror": "#d9534f",
    "flox-consolidated": "#f0ad4e",
}

# total run time (avg seconds) -> [ubuntu_cold, ubuntu_warm, macos_cold, macos_warm]
TOTAL = {
    "traditional": [17.2, 17.2, 36.4, 38.7],
    "flox-mirror": [64.8, 64.6, 318.4, 303.6],
    "flox-consolidated": [64.8, 62.8, 181.6, 161.6],
}
# per-job setup / work (macOS cold). setup includes BOTH provision pre-step AND
# the `Post provision` cache-SAVE post-step, so work is only the actual check.
SETUP_WORK_MAC = {  # side -> (setup, work)
    "traditional": (4.1, 7.8),
    "flox-mirror": (135.8, 9.0),
    "flox-consolidated": (150.6, 14.7),
}
# cumulative provisioning per run (seconds): [ubuntu_cold, macos_cold]
PROV_RUN = {
    "traditional": [30, 41],
    "flox-mirror": [465, 1358],
    "flox-consolidated": [99, 301],
}


def _bars_with_labels(ax, xs, ys, color, fmt="{:.0f}", rot=0):
    bars = ax.bar(xs, ys, color=color)
    for b, y in zip(bars, ys, strict=True):
        ax.text(
            b.get_x() + b.get_width() / 2,
            y,
            fmt.format(y),
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=rot,
        )
    return bars


def main(out: Path) -> int:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Flox vs. Traditional CI provisioning — GitHub Actions (reps=5, 10 checks)",
        fontsize=15,
        fontweight="bold",
    )

    # Panel A: total run time, grouped by OS x cache (cold), per side
    ax = axes[0][0]
    labels = ["ubuntu\ncold", "ubuntu\nwarm", "macOS\ncold", "macOS\nwarm"]
    x = range(len(labels))
    w = 0.26
    for i, side in enumerate(SIDES):
        xs = [j + i * w for j in x]
        _bars_with_labels(ax, xs, TOTAL[side], COLORS[side])
    ax.set_xticks([j + w for j in x])
    ax.set_xticklabels(labels)
    ax.set_ylabel("seconds (avg run wall-clock)")
    ax.set_title("Total CI run time  —  flox 3.8x (ubuntu) to ~8.7x (macOS) slower")
    ax.legend(SIDES, fontsize=8)

    # Panel B: per-job setup vs work (macOS cold) — stacked
    ax = axes[0][1]
    xs = list(range(len(SIDES)))
    setups = [SETUP_WORK_MAC[s][0] for s in SIDES]
    works = [SETUP_WORK_MAC[s][1] for s in SIDES]
    ax.bar(xs, setups, color="#d9534f", label="setup (provision step)")
    ax.bar(xs, works, bottom=setups, color="#5cb85c", label="work (the actual check)")
    for i in range(len(SIDES)):
        tot = setups[i] + works[i]
        pct = 100 * setups[i] / tot if tot else 0
        ax.text(i, tot, f"{pct:.0f}% setup", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(xs)
    ax.set_xticklabels(SIDES, fontsize=9)
    ax.set_ylabel("seconds per job")
    ax.set_title(
        "Where the time goes (macOS, per job)  —  flox is ~90-94% provisioning"
    )
    ax.legend(fontsize=8)

    # Panel C: cumulative provisioning per run (log scale), ubuntu vs macOS cold
    ax = axes[1][0]
    w = 0.36
    for k, (lbl, idx) in enumerate([("ubuntu cold", 0), ("macOS cold", 1)]):
        xs = [j + k * w for j in range(len(SIDES))]
        ys = [PROV_RUN[s][idx] for s in SIDES]
        bars = ax.bar(xs, ys, width=w, label=lbl)
        for b, y in zip(bars, ys, strict=True):
            ax.text(
                b.get_x() + b.get_width() / 2,
                y,
                f"{y}s",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    ax.set_yscale("log")
    ax.set_xticks([j + w / 2 for j in range(len(SIDES))])
    ax.set_xticklabels(SIDES, fontsize=9)
    ax.set_ylabel("seconds (log scale)")
    ax.set_title(
        "Cumulative provisioning per run  —  mirror pays it 10x, consolidated ~2x"
    )
    ax.legend(fontsize=8)

    # Panel D: cold vs warm total (macOS) — warm barely helps
    ax = axes[1][1]
    w = 0.36
    cold = [TOTAL[s][2] for s in SIDES]
    warm = [TOTAL[s][3] for s in SIDES]
    xs = list(range(len(SIDES)))
    _bars_with_labels(ax, [j - w / 2 for j in xs], cold, "#8e8e8e")
    _bars_with_labels(ax, [j + w / 2 for j in xs], warm, "#cfcfcf")
    ax.set_xticks(xs)
    ax.set_xticklabels(SIDES, fontsize=9)
    ax.set_ylabel("seconds (macOS total)")
    ax.set_title("Cold vs warm (macOS)  —  warm cache barely helps flox")
    ax.legend(["cold", "warm"], fontsize=8)

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
