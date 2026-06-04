# PRD v6 — `flox-ci-base`: a Flox-preloaded GitHub Actions container image

**Status:** Draft / experiment — v6 (open questions resolved)
**Owner:** Steve Morin
**Repo home:** dedicated **`flox/flox-ci-base`**
**Image:** `ghcr.io/flox/flox-ci-base` (per-Python tags, e.g. `:py311`)
**Scope:** **Linux only; mirrors the single `test` job (§3, §4).**

### Changelog from v5
- **Q1 resolved → option (a), pure mirror.** Warm `uvx` tools *unpinned*, matching the existing `ci.yaml`. Drift (warmed = latest-at-build) is an accepted, noted caveat.
- **Q2 resolved → 4 images, validate on 1.** Target = 3.10/3.11 × amd64/arm64; P0 proves it on py311/amd64 first.
- **Q3 resolved → two base arms.** Build both `catthehacker/ubuntu:act-24.04` (runner-faithful) **and** `ubuntu:24.04`+git (minimal) and benchmark the spread. Rationale: the control pays no image-pull cost, so a heavier base only handicaps the treatment — the minimal arm isolates true pre-bake value.
- **Q4 resolved → scoped to the single `test` job.** Other CI jobs are explicitly out of scope; extension is a follow-up pending a real `.github/workflows/` enumeration.

---

## 1. Purpose & hypothesis

Move all of the `test` job's setup **to image-build time** so the running job executes only the project's real test commands.

```
Real ci.yaml today (per matrix arm)          This experiment (baked image)
───────────────────────────────────         ─────────────────────────────
astral-sh/setup-uv          ─┐               (uv baked in image)
actions/setup-python         ┊ setup         (python baked in image)
uv sync --all-extras --dev  ─┘               uv sync … (instant; warm cache)
uvx mypy / ruff / pytest     ← the work      uvx mypy / ruff / pytest  ← ~all that runs
```

**Hypothesis:** baking `setup-uv` + `setup-python` + dependency/tool resolution into the image makes the test job faster than installing at runtime — enough that saved setup time exceeds added image-pull time.

**Key measurement nuance (drives Q3):** the control runs on a pre-provisioned `ubuntu-latest` VM and pulls **nothing**; the treatment is a container job that **must pull the image**. Image-pull time is therefore a treatment-only cost, and base-image weight is a confound to measure, not assume away (§5.1, §7).

**Irreducible:** `checkout` always runs.

---

## 2. Background — footguns this design dodges

- **Missing `git` → checkout tarball fallback.** Handled by the base (system `git`; `uses:` steps need it — §5.3).
- **GHA-injected Node + FHS loader.** Ubuntu base = FHS/glibc intact, so injected Node runs. (Still why we layer Flox on Ubuntu, not `flox containerize` native.)
- **`--noprofile --norc` step shell.** Addressed by `flox activate` via a custom default shell (§5.3); `uses:` steps bypass it and use the base's system tools.
- **Root user required.** GHA container jobs run as root for `GITHUB_WORKSPACE`. **No `USER` instruction.**
- **Hidden tool install cost.** `uvx`/`uv sync` fetch on first use; both warmed at build (§5.4).

---

## 3. Goals / Non-goals

### Goals
- Two base arms (runner-faithful + minimal) + Flox with `python` + `uv` baked and realized at build.
- Warmed caches matching the real CI: `uv sync --all-extras --dev` and `uvx mypy/ruff/pytest`.
- Consumer job = `checkout` + the real `test`-job commands, inside `flox activate`.
- Per-Python images (3.10, 3.11) × amd64/arm64.
- GHCR publish pipeline, digest-pinnable.

### Non-goals
- **macOS coverage of any kind** (§4).
- **Other CI jobs** (lint, pre-commit, release/cog, docs) — this mirrors the single `test` job only. Extending would re-introduce `just`/pre-commit/taplo/etc. and is a follow-up.
- Not baking the `py_launch_blueprint` package itself.
- Not a production-supported product.

---

## 4. Why this is Linux-only (out-of-scope: macOS)

The premise "bake all setup into the image" can't hold on macOS, so a Mac run wouldn't test the hypothesis. Three walls: (1) **kernel** — containers share the Linux kernel; macOS is Darwin/XNU, no macOS container image format (Docker-OSX = macOS in a QEMU VM in a container, needs `/dev/kvm`); (2) **licensing** — Apple permits macOS only on Apple hardware; Docker's community license bars Docker Desktop for Mac on hosted services; (3) **virtualization + scope** — GitHub's macOS runners disable nested virtualization, and container jobs are Linux-only regardless. The native-Flox-on-Apple-hardware story is *runtime install on macOS* (what we measure against) — a separate effort.

---

## 5. Design

### 5.1 Base image — two arms
Build the image on **both** bases and compare:

| Arm | Base | Role | Size / pull cost |
|---|---|---|---|
| **Faithful** | `catthehacker/ubuntu:act-24.04` (pin by digest) | "Does it help under runner-equivalent conditions?" | medium (more pull) |
| **Minimal** | `ubuntu:24.04` + `git` only | "Best-case, does pre-baking help at all?" | small (least pull) |

The gap between the two arms = the base-weight tax. `catthehacker/ubuntu:full-*` is excluded (≈20 GB, amd64-only). For the faithful arm, `git` + runner toolchain are inherited; for the minimal arm, add `git` via apt. **No `USER`** in either.

> catthehacker is a community image — pin by digest, treat as a supply-chain dependency. Verify `act-24.04` publishes `linux/arm64` (the `full-*` line is amd64-only).

### 5.2 Flox environment — narrowed to real usage
Committed `.flox/env/manifest.toml`, **one per Python version** (`python310` / `python311`) — the `setup-python` + `setup-uv` replacement:

```toml
version = 1

[install]
python.pkg-path = "python311"   # python310 for the :py310 variant
uv.pkg-path     = "uv"

[vars]
UV_CACHE_DIR = "/opt/uv-cache"
UV_TOOL_DIR  = "/opt/uv-tools"
UV_LINK_MODE = "copy"

[options]
systems = ["x86_64-linux", "aarch64-linux"]
```

Flox installed from the **stable** channel; manifest locked. mypy/ruff/pytest are **not** Flox packages — they come via `uvx` (§5.4).

### 5.3 Activation strategy — use `flox activate`
Activated at run time, not flattened into `ENV`:

```yaml
defaults:
  run:
    shell: flox activate -d /opt/ci-env -- bash --noprofile --norc -eo pipefail {0}
```

- **`uses:` steps bypass this shell** → checkout uses the base's **system `git`** (don't remove it).
- **Per-step activation cost is intentional** (no downloads once baked); §7 measures it.

### 5.4 Cache warming — option (a), pure mirror
Warm exactly what the real CI runs, **unpinned** (matching `ci.yaml`):
1. **Dependencies:** `uv sync --all-extras --dev` → populate `UV_CACHE_DIR`, drop `.venv`.
2. **uvx tools:** warm `mypy`, `ruff`, `pytest` unpinned.

> **Accepted caveat (Q1, option a):** `uvx` resolves its own latest tool and ignores the project's dev-dep/pyproject version, so the warmed version is "latest at build time" and may differ at run time. This is what the existing CI already does. If determinism is ever needed, pin `uvx mypy@<ver>` from `uv.lock` (option b) in both the image and `ci.yaml`.

### 5.5 Dockerfile (sketch — `BASE` arg selects the arm)
```dockerfile
ARG BASE=ghcr.io/catthehacker/ubuntu:act-24.04   # or: ubuntu:24.04 (minimal arm)
FROM ${BASE}
# Faithful arm inherits git; minimal arm must add it:
RUN command -v git >/dev/null || ( apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates curl xz-utils && rm -rf /var/lib/apt/lists/* )
# NO `USER` instruction (root needed for GITHUB_WORKSPACE).

ARG TARGETARCH
RUN case "$TARGETARCH" in \
      amd64) FLOX_ARCH=x86_64-linux ;; \
      arm64) FLOX_ARCH=aarch64-linux ;; \
    esac \
 && curl -fsSL "https://downloads.flox.dev/by-env/stable/deb/flox.${FLOX_ARCH}.deb" -o /tmp/flox.deb \
 && apt-get update && apt-get install -y /tmp/flox.deb \
 && rm /tmp/flox.deb && rm -rf /var/lib/apt/lists/*

# Realize python+uv closure at build time.
COPY .flox /opt/ci-env/.flox
WORKDIR /opt/ci-env
RUN flox activate -- true

# Warm caches (option a, unpinned — mirrors ci.yaml).
ENV UV_CACHE_DIR=/opt/uv-cache UV_TOOL_DIR=/opt/uv-tools UV_LINK_MODE=copy
COPY pyproject.toml uv.lock /tmp/warm/
RUN cd /tmp/warm && flox activate -- sh -eux -c '\
      uv sync --all-extras --dev --no-install-project ; \
      uvx mypy --version ; uvx ruff --version ; uvx pytest --version ; \
    ' && rm -rf /tmp/warm/.venv /tmp/warm

WORKDIR /work
```

---

## 6. Consumer workflow (mirrors the `test` job, setup pre-baked)

```yaml
name: CI (baked)
on: [push, pull_request]
permissions: { contents: read, packages: read }

jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]            # mirrors real matrix
        runner: [ubuntu-latest, ubuntu-24.04-arm]   # amd64 + arm64
    runs-on: ${{ matrix.runner }}
    container:
      image: ghcr.io/flox/flox-ci-base:py${{ matrix.python-version }}@sha256:<digest>
    defaults:
      run:
        shell: flox activate -d /opt/ci-env -- bash --noprofile --norc -eo pipefail {0}
    steps:
      - uses: actions/checkout@v4                   # uses base system git
      - run: uv sync --all-extras --dev             # warm cache → near-instant
      - run: uvx mypy py_launch_blueprint/
      - run: uvx ruff check py_launch_blueprint/
      - run: uvx pytest
```

Only `astral-sh/setup-uv` and `actions/setup-python` are removed vs. the real `ci.yaml` (now baked); test commands are identical. Control arm = unmodified `ci.yaml`.

---

## 7. Benchmark & success criteria

Compare unmodified `ci.yaml` vs. the baked version, across **both base arms**, per Python version, on amd64 + arm64. Capture: total wall-clock; setup overhead (job start → first `uvx`); **image pull time** (treatment-only cost); per-step `flox activate` overhead; `uv sync` duration (warm vs cold).

Report the headline as a decomposition: `net = setup_saved − pull_added − activation_overhead`. The **minimal arm** gives best-case `net`; the **faithful arm** shows `net` under runner-equivalent weight; their difference is the base-weight tax.

**Success (informal):** minimal-arm `net` is clearly positive (pre-baking helps best-case); faithful-arm `net` tells you whether it survives a runner-faithful base.

---

## 8. Risks & footguns

- **Pull-time confound (central).** Treatment pays pull cost the control never does. Two base arms + the §7 decomposition exist to separate this from pre-bake value.
- **catthehacker supply chain.** Community image — pin by digest; reconsider beyond the experiment.
- **arm64 base availability.** Confirm `act-24.04` (and Flox aarch64 deb) publish arm64.
- **uvx drift (option a).** Unpinned = latest-at-build; accepted. Option (b) for determinism.
- **Activation-shell correctness.** Covers `run:` only. Guard: `command -v uv && uvx pytest --version && git rev-parse --is-inside-work-tree`.
- **Root requirement.** No `USER`.
- **Build fan-out.** Target = 2 Python × 2 arch (×2 base arms for the benchmark) — note the matrix size; P0 builds just one.
- **arm64 runner label churn.** No `-latest` alias; pin `ubuntu-24.04-arm`.
- **Flox-in-Docker semantics.** Smoke-test `flox activate -d /opt/ci-env` with cwd = workspace in P0.

---

## 9. Milestones

- **P0 — one image.** py311 / amd64 on the faithful base: Flox(python+uv) realized, activation verified by guard step, caches warmed. Push and run once.
- **P1 — full matrix.** py310 + py311 × amd64 + arm64; native arm64 build + manifest merge. Tag `v0.1.0`.
- **P2 — both base arms + benchmark.** Add the minimal-base build; run baked workflow beside unmodified `ci.yaml`; collect §7 decomposition; write up the finding.

---

## 10. Open questions — resolved

1. **uvx pins:** ✅ option (a), pure mirror (unpinned), matching `ci.yaml`. Caveat noted.
2. **Python matrix:** ✅ 4 images target; P0 validates on py311/amd64 first.
3. **Base image:** ✅ two arms — `catthehacker/ubuntu:act-24.04` (faithful) + `ubuntu:24.04`+git (minimal); benchmark the spread.
4. **Scope:** ✅ single `test` job only. Mirroring other jobs is a follow-up, pending a real `.github/workflows/` enumeration.

*Remaining input needed before scaffolding:* none blocking. Optional: confirm the full `.github/workflows/` set if/when extending beyond the `test` job (Q4 follow-up).
