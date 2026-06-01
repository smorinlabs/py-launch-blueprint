#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Infographic: three CI provisioning models compared — traditional, mise, flox.

Per-model card (mechanism + key metrics) + a verdict strip. Numbers from
experiment/results/REPORT.md (5 sides x 2 OS x 2 cache x reps=5; 10 checks).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK = "#222222"
CARDS = [
    {
        "name": "TRADITIONAL",
        "color": "#2f7ed8",
        "how": "4 separate installers — setup-uv, setup-just,\nsetup-bun, curl install-gitleaks.sh. Each job\ninstalls ONLY its tool, at runtime from\nPyPI / npm / GitHub releases.",
        "metrics": [
            ("provisioning/job", "~3s (both OS)"),
            ("total time", "ubuntu 17s · macOS 36s"),
            ("warm cache", "n/a (already minimal)"),
            ("reliability", "flaky runtime downloads"),
            ("maintenance", "4 scripts + scattered pins"),
        ],
    },
    {
        "name": "MISE",
        "color": "#2ca089",
        "how": "ONE mise.toml -> mise installs the WHOLE\ntoolchain from release binaries (aqua) +\npipx + npm, then `mise exec`. One source\nof truth, no build step.",
        "metrics": [
            ("provisioning/job", "~12s ubuntu / ~14s macOS  (OS-insensitive)"),
            ("total time", "ubuntu 23-33s · macOS 31-63s"),
            ("warm cache", "WORKS (~4-7s/job)"),
            ("reliability", "0 failures"),
            ("maintenance", "1 manifest + lock"),
        ],
    },
    {
        "name": "FLOX",
        "color": "#d9534f",
        "how": "ONE manifest.toml -> flox activate\nmaterializes the WHOLE toolchain from the\ncontent-addressed Nix store, every\nactivation (build on cold).",
        "metrics": [
            ("provisioning/job", "~47s ubuntu / ~136s macOS  (OS-sensitive)"),
            ("total time", "ubuntu 65s · macOS 182-318s"),
            ("warm cache", "ineffective (~47->48s)"),
            ("reliability", "0 failures"),
            ("maintenance", "1 manifest + lock"),
        ],
    },
]


def main(out: Path) -> int:
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.text(
        0.5,
        0.95,
        "Three CI provisioning models compared",
        ha="center",
        fontsize=19,
        weight="bold",
    )
    fig.text(
        0.5,
        0.915,
        "Same 10 checks, same repo — only HOW the toolchain is installed & "
        "orchestrated differs (GitHub Actions, reps=5).",
        ha="center",
        fontsize=11,
        color="#555",
    )

    xs = [2, 35, 68]
    for x, card in zip(xs, CARDS, strict=True):
        ax.add_patch(
            FancyBboxPatch(
                (x, 30),
                30,
                56,
                boxstyle="round,pad=0.4",
                lw=1.5,
                edgecolor=card["color"],
                facecolor="white",
            )
        )
        ax.add_patch(
            FancyBboxPatch(
                (x, 80), 30, 6, boxstyle="round,pad=0.4", lw=0, facecolor=card["color"]
            )
        )
        ax.text(
            x + 15,
            83,
            card["name"],
            ha="center",
            va="center",
            fontsize=14,
            weight="bold",
            color="white",
        )
        ax.text(x + 1.5, 73, card["how"], ha="left", va="top", fontsize=8.5, color=INK)
        yy = 58
        for label, val in card["metrics"]:
            ax.text(
                x + 1.5,
                yy,
                label,
                ha="left",
                va="top",
                fontsize=8,
                weight="bold",
                color=card["color"],
            )
            ax.text(x + 1.5, yy - 2.4, val, ha="left", va="top", fontsize=8, color=INK)
            yy -= 5.6

    # verdict strip
    ax.add_patch(
        FancyBboxPatch(
            (2, 4),
            96,
            22,
            boxstyle="round,pad=0.4",
            lw=1.2,
            edgecolor="#999",
            facecolor="#fbfbfb",
        )
    )
    ax.text(50, 23, "Verdict", ha="center", fontsize=13, weight="bold")
    lines = [
        "Speed (raw):  traditional  >  mise  >  flox.   On macOS, mise-consolidated MATCHES/BEATS traditional (-2% cold, -21% warm); flox is 5-9x slower.",
        "Cost is provisioning, not the checks — the actual checks run at the same speed on all three. flox is ~90% install; mise ~12s; traditional ~3s.",
        "Reliability:  flox = mise (0 failures)  >  traditional (flaky runtime downloads).      Simplicity:  flox = mise (1 manifest)  >  traditional (4 scripts).",
        "mise's provisioning is OS-insensitive (release binaries) and its warm cache works; flox's Nix build is OS-sensitive and warm barely helps.",
        "=> mise is the best balance for a single-source-of-truth CI toolchain: flox/mise simplicity + reliability, without flox's CI-speed tax.",
    ]
    yy = 19.5
    for ln in lines:
        ax.text(4, yy, ln, ha="left", va="center", fontsize=8.6, color=INK)
        yy -= 3.3

    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    target = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("experiment/results/provisioning_infographic.png")
    )
    raise SystemExit(main(target))
