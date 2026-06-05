#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib>=3.8"]
# ///
"""v2 figure: isolating *where* the flox provisioning cost lives.

Four flox install variants — same 10 checks, each changing one variable vs `flox`:
  flox          : flox/install-flox-action, use-cache=true   (baseline)
  flox-nocache  : flox/install-flox-action, use-cache=false  (no CLI-binary cache)
  flox-noaction : manual pinned .deb/.pkg install            (no GitHub Action)
  flox-baked    : whole env baked into a container image     (setup = image pull)

Setup/job means from experiment/results/REPORT.md (reps=5, consolidated rows).
flox-baked is ubuntu-only (container jobs are Linux-only). Shows every lever lands
on the same floor: setup is irreducibly the Nix-store realization.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIDES = ["flox", "flox-nocache", "flox-noaction", "flox-baked"]
COLORS = {
    "flox": "#f0ad4e",
    "flox-nocache": "#d9534f",
    "flox-noaction": "#9b59b6",
    "flox-baked": "#2ca089",
}
# setup/job (avg s), consolidated rows: [ubuntu_cold, ubuntu_warm, macos_cold, macos_warm]
# flox-noaction ubuntu-cold uses the 66s median run (n=3 had one 223s installer-retry outlier).
# flox-baked is ubuntu-only (None on macOS).
SETUP = {
    "flox": [47.6, 47.3, 156.6, 165.5],
    "flox-nocache": [47.9, 46.0, 166.0, 159.3],
    "flox-noaction": [50.5, 54.5, 150.6, 146.4],
    "flox-baked": [46.3, 46.3, None, None],
}


def _panel(ax, idx_pair, labels, title, ylabel):
    w = 0.2
    for i, side in enumerate(SIDES):
        vals = [SETUP[side][k] for k in idx_pair]
        xs = [j + i * w for j in range(len(vals))]
        plotted = [(x, v) for x, v in zip(xs, vals, strict=True) if v is not None]
        if not plotted:
            continue
        bx = [p[0] for p in plotted]
        bv = [p[1] for p in plotted]
        bars = ax.bar(bx, bv, width=w, color=COLORS[side], label=side)
        for b, y in zip(bars, bv, strict=True):
            ax.text(
                b.get_x() + b.get_width() / 2,
                y,
                f"{y:.0f}",
                ha="center",
                va="bottom",
                fontsize=7,
            )
    ax.set_xticks([j + 1.5 * w for j in range(len(labels))])
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=7)


def main(out: Path) -> int:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle(
        "Where the flox cost lives — every lever lands on the Nix-realization floor "
        "(setup/job, reps=5)",
        fontsize=13,
        fontweight="bold",
    )
    _panel(
        axes[0],
        [0, 1],
        ["ubuntu cold", "ubuntu warm"],
        "ubuntu — all variants ~47s (incl. flox-baked image pull)",
        "setup/job (s)",
    )
    _panel(
        axes[1],
        [2, 3],
        ["macOS cold", "macOS warm"],
        "macOS — all variants ~150-170s (flox-baked = linux-only, N/A)",
        "setup/job (s)",
    )
    fig.text(
        0.5,
        0.01,
        "flox-nocache (binary cache off) ≈ flox-noaction (no Action) ≈ flox-baked "
        "(image pull) ≈ flox.  net of every lever ≈ 0 — the cost is materializing "
        "the Nix closure.",
        ha="center",
        fontsize=8.5,
        style="italic",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    target = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("experiment/results/summary_v2.png")
    )
    raise SystemExit(main(target))
