#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Infographic: how the CI toolchain is provisioned — traditional vs flox.

Shows which installers set up which tools, the setup-vs-work split, and the
major differences between the two provisioning models.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

TRAD = "#2f7ed8"
FLOX = "#d9534f"
INK = "#222222"


def box(
    ax, x, y, w, h, text, fc, ec=INK, fs=9, tc="white", weight="normal", align="center"
):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.3,rounding_size=0.6",
            linewidth=1.2,
            edgecolor=ec,
            facecolor=fc,
        )
    )
    hx = x + (0.6 if align == "left" else w / 2)
    ax.text(
        hx,
        y + h / 2,
        text,
        ha="left" if align == "left" else "center",
        va="center",
        fontsize=fs,
        color=tc,
        weight=weight,
    )


def arrow(ax, x1, y1, x2, y2):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.4},
    )


def main(out: Path) -> int:
    fig, ax = plt.subplots(figsize=(16, 11.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    fig.text(
        0.5,
        0.965,
        "How the CI toolchain is provisioned:  Traditional  vs  Flox",
        ha="center",
        fontsize=18,
        weight="bold",
    )
    fig.text(
        0.5,
        0.935,
        "Same 10 checks run either way — only HOW the tools are installed & "
        "orchestrated differs.",
        ha="center",
        fontsize=11,
        color="#555",
    )

    # column headers
    box(
        ax,
        2,
        86,
        46,
        6,
        "TRADITIONAL  —  install only what each job needs",
        TRAD,
        fs=12,
        weight="bold",
    )
    box(
        ax,
        52,
        86,
        46,
        6,
        "FLOX  —  one manifest materializes the whole env",
        FLOX,
        fs=12,
        weight="bold",
    )

    # ---- TRADITIONAL: installer -> tools ----
    rows = [
        (
            "astral-sh/setup-uv  (action)",
            "uvx → ruff · ruff-format · codespell · yamllint · bandit\n"
            "uv run → ty · pytest        [PyPI, ephemeral]",
        ),
        (
            "extractions/setup-just  (action)",
            "just install-taplo → taplo        [curl GitHub release]",
        ),
        (
            "oven-sh/setup-bun  (action)",
            "bunx → commitlint        [npm download at runtime]",
        ),
        ("scripts/install-gitleaks.sh", "curl GitHub release + SHA verify → gitleaks"),
    ]
    y = 78
    for inst, tools in rows:
        box(ax, 3, y, 20, 6.4, inst, "#e8f0fb", ec=TRAD, fs=8.5, tc=INK, weight="bold")
        arrow(ax, 23, y + 3.2, 25, y + 3.2)
        ax.text(25.5, y + 3.2, tools, ha="left", va="center", fontsize=8, color=INK)
        y -= 8.4
    box(
        ax,
        3,
        y - 1,
        44,
        6,
        "4 heterogeneous installers · each job pulls only its tool · "
        "~3s/job · flaky runtime downloads",
        "#f4f4f4",
        ec=TRAD,
        fs=8.5,
        tc=INK,
    )

    # ---- FLOX: manifest -> activate -> whole env ----
    box(
        ax,
        53,
        78,
        44,
        6.4,
        ".flox/env/manifest.toml  +  manifest.lock   (15 packages, pinned)",
        "#fdeceb",
        ec=FLOX,
        fs=8.5,
        tc=INK,
        weight="bold",
    )
    arrow(ax, 75, 78, 75, 74.5)
    box(
        ax,
        53,
        68,
        44,
        6.4,
        "flox/install-flox-action  →  flox activate   (materialize from Nix store)",
        "#fdeceb",
        ec=FLOX,
        fs=8.5,
        tc=INK,
        weight="bold",
    )
    arrow(ax, 75, 68, 75, 64.5)
    env_tools = (
        "python312 · uv · ruff · taplo · gitleaks · bun · commitlint\n"
        "yamllint · codespell · bandit · just · lefthook · gh ·\n"
        "editorconfig-checker · gnumake     — ALL at once, every activation"
    )
    box(ax, 53, 53, 44, 11, env_tools, "#fff7f6", ec=FLOX, fs=9, tc=INK, weight="bold")
    ax.text(
        75,
        50,
        "then each check runs the bare tool:  ruff check · taplo check ·\n"
        "gitleaks detect · commitlint …   (* ty/pytest still via `uv run` —\n"
        "project deps, not flox-managed: the uv/flox boundary)",
        ha="center",
        va="center",
        fontsize=8,
        color=INK,
    )
    box(
        ax,
        53,
        40,
        44,
        6,
        "1 declarative manifest+lock · FULL env every activation · Nix store · "
        "~46s ubuntu / ~136s macOS provisioning/job · deterministic",
        "#f4f4f4",
        ec=FLOX,
        fs=8.5,
        tc=INK,
    )

    # ---- setup vs work (macOS, per job) ----
    ax.text(
        25,
        35,
        "Setup vs work  (macOS, per job)",
        ha="center",
        fontsize=11,
        weight="bold",
    )
    data = [
        ("traditional", 4.1, 7.8, TRAD),
        ("flox-mirror", 135.8, 9.0, FLOX),
        ("flox-consolidated", 150.6, 14.7, "#f0ad4e"),
    ]
    maxv = 175.0
    for i, (name, setup, work, _c) in enumerate(data):
        yy = 28 - i * 5.5
        ws = 42 * setup / maxv
        ww = 42 * work / maxv
        box(ax, 3 + 9, yy, ws, 3.6, "", "#d9534f", ec=None, fs=8, tc="white")
        ax.add_patch(plt.Rectangle((3 + 9 + ws, yy), ww, 3.6, color="#5cb85c"))
        ax.text(3, yy + 1.8, name, ha="left", va="center", fontsize=8.5, weight="bold")
        pct = 100 * setup / (setup + work)
        ax.text(
            3 + 9 + ws + ww + 1,
            yy + 1.8,
            f"setup {setup:.0f}s / work {work:.0f}s  ({pct:.0f}% setup)",
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.add_patch(plt.Rectangle((12, 9.5), 2.5, 2.2, color="#d9534f"))
    ax.text(15, 10.6, "setup (provision)", fontsize=8, va="center")
    ax.add_patch(plt.Rectangle((30, 9.5), 2.5, 2.2, color="#5cb85c"))
    ax.text(33, 10.6, "work (the check)", fontsize=8, va="center")

    # ---- major differences ----
    box(ax, 52, 6, 46, 28, "", "#fbfbfb", ec="#999", fs=8)
    ax.text(75, 31, "Major differences", ha="center", fontsize=12, weight="bold")
    diffs = [
        "Granularity: traditional installs ONLY the needed tool;",
        "   flox installs all 15 packages on every activation.",
        "Mechanism: 4 heterogeneous installers (3 actions + 1 curl",
        "   script) vs 1 declarative manifest + lockfile.",
        "Source: PyPI / npm / GitHub releases at runtime",
        "   vs content-addressed Nix store (cached).",
        "Cost: ~3s/job  vs  ~46s ubuntu to ~136s macOS per job.",
        "Reliability: runtime downloads flake (editorconfig pulled",
        "   ~45%); Nix store is deterministic (0 flox failures).",
        "Maintenance: 4 scripts + scattered version pins",
        "   vs one manifest.toml + manifest.lock.",
    ]
    yy = 28
    for d in diffs:
        lead = "•  " if not d.startswith("   ") else ""
        ax.text(
            53.5,
            yy,
            lead + d.strip() if lead else "   " + d.strip(),
            ha="left",
            va="center",
            fontsize=8.6,
            color=INK,
        )
        yy -= 2.3

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
