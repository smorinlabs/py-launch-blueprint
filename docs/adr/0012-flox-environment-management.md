# ADR-12: Flox for developer-environment provisioning

- Status: proposed
- Date: 2026-05-30
- Deciders: Steve Morin

## Context

The repo provisions its developer toolchain three different ways:

- **Install scripts** — `scripts/install-bun.sh`, `install-gitleaks.sh`,
  `install-lefthook.sh`: curl-pipe-bash installers with hand-pinned versions,
  per-platform detection (`detect_platform()`), SHA256 verification, and manual
  `PATH`/`.zshenv` munging. Each carries a "review pin every 6 months" cadence.
- **Makefile** — `make check` / `make hook-check`: *audit* whether `just`, `uv`,
  `lefthook`, `gitleaks`, `bun`, `editorconfig-checker`, `yamllint`, `codespell`
  are present, plus `install-uv*`/`install-just*`/`set-path` targets that print
  install commands and append to `.zshenv`. The Makefile can detect a missing
  tool but cannot reproducibly *provide* it.
- **Devcontainer** (ADR-11) — re-runs the same install scripts in
  `postCreateCommand` and hand-sets `PATH`/`BUN_INSTALL` in `remoteEnv`.

This is three overlapping sources of truth for "which binaries does a contributor
need, at which versions, on which platform." [Flox](https://flox.dev) is a
Nix-backed environment manager that declares the toolchain once in
`.flox/env/manifest.toml`, locks it cross-platform in `manifest.lock`, and puts
it all on `PATH` via `flox activate`.

A catalog check (`flox search`, Flox 1.12.1) confirmed **every** tool in the
current toolchain is available in the Flox/nixpkgs catalog — including the
brand-new `ty`, `commitlint`, and `cogapp`. So the question is not whether Flox
*can* manage the toolchain, but **which parts it should own** versus leave to the
lockfile-based managers (`uv.lock`, `bun.lock`) already in place.

## Decision drivers

- One declarative, cross-platform, lockfile-reproducible source for the binary
  toolchain (replacing 3 install scripts + the Makefile audit targets).
- Avoid duplicating dependency ownership: `uv.lock` (the app + dev closures) and
  `bun.lock` (commitlint) must remain the single source of truth for the package
  graphs they already pin.
- Keep local dev and the devcontainer (ADR-11) on one definition.
- Weigh against the Makefile's founding rationale — "make it easy ... because
  almost everyone has `make`" — which is the philosophical opposite of requiring
  a new prerequisite (Flox) on every contributor.

## Governing principle

**Flox provides binaries and runtimes; `uv.lock` and `bun.lock` keep owning the
locked dependency closures.** Flox installs the `uv` executable, the Python 3.12
interpreter, and the `bun` runtime — and `uv sync` / `bun install` still resolve
the project's actual package graphs underneath.

## Item-by-item inventory

### Bucket 1 — Flox owns (replaces install scripts + Makefile audit)

System binaries and language runtimes. All verified in catalog.

| Item | Today | Under Flox (`[install]`) |
| --- | --- | --- |
| Python 3.12 | `.python-version` + uv | `python312` |
| `uv` | `install-uv-force` (curl) | `flox/uv` |
| `just` | `install-just-force` (curl) | `just` |
| `bun` | `scripts/install-bun.sh` (pin 1.3.5) | `bun` |
| `lefthook` | `scripts/install-lefthook.sh` (via bun) | `lefthook` |
| `gitleaks` | `scripts/install-gitleaks.sh` (tarball+SHA) | `gitleaks` |
| `gh` | assumed pre-installed | `gh` |
| `make` | assumed pre-installed | `gnumake` |
| `taplo` | `just install-taplo` | `taplo` |
| `node` (if needed) | via bun | `nodejs` |

Direct casualties: all three `scripts/install-*.sh`; the
`install-uv*`/`install-just*`/`set-path` Makefile targets; and the entire reason
`make check` / `make hook-check` exist (Flox guarantees presence rather than
auditing it).

### Bucket 2 — Flox provides the runner, lockfile keeps ownership

Do **not** move these into `[install]` — that would create two sources of truth.

| Item | Stays in | Why |
| --- | --- | --- |
| App deps (click, rich, requests, thefuzz…) | `uv.lock` | Application closure |
| `pytest`, `pytest-cov` | dev group (uv) | Test runner pinned with app |
| `mypy`, `ty` | dev group (uv) | `ty>=0.0.1a16` is a pre-release pin uv tracks exactly |
| `bandit` | dev group (uv) | Pinned with its `pyproject.toml` config |
| `cogapp` | docs/dev group (uv) | Python lib, not a standalone binary |

### Bucket 3 — judgment call (general-purpose, currently `uvx`/`bunx`-invoked)

Catalog-available and runtime-agnostic, so movable — but presently version-pinned
through uv/bun.

| Item | Today | Recommendation |
| --- | --- | --- |
| `ruff` | `uvx ruff` (also dev group) | **Move** — standalone Rust binary, no Python-env coupling |
| `editorconfig-checker` | `bunx editorconfig-checker` | **Move** — drops a bun dependency |
| `yamllint` | `uvx yamllint` | Optional — small win |
| `codespell` | `uvx codespell` | Optional — small win |
| `commitlint` | `bunx commitlint` (bun.lock) | **Keep in bun** — config lives in `commitlint.config.mjs`; moving splits config from binary |

Once moved, the lefthook hooks simplify (`uvx yamllint` → `yamllint`).

### Bucket 4 — Flox cannot manage (out of scope)

| Item | Why not |
| --- | --- |
| ReadTheDocs build | External CI with its own environment |
| `release-please` | Runs in GitHub Actions, not locally |
| Tool *configs* / app *code* | Configuration & source, not provisioning |
| Pinned graphs in `uv.lock` / `bun.lock` | Owned by the uv/bun resolvers |

## Migration delta (if adopted)

1. `flox init` → commit `.flox/env/manifest.toml` + `manifest.lock`.
2. Populate `[install]` with Bucket 1 (+ chosen Bucket 3 items), pinned & locked.
3. `[hook] on-activate` runs the old provisioning: `uv sync --group dev` then
   `lefthook install`.
4. `[vars]`/`[profile]` replace the devcontainer `remoteEnv` and the Makefile
   `.zshenv` `PATH` logic — Flox sets `PATH` on `flox activate`.
5. `[options].systems = ["aarch64-darwin", "x86_64-linux"]` — what the install
   scripts' `detect_platform()` did by hand.
6. Repoint the devcontainer (ADR-11): `flox activate` in `postCreateCommand`, or
   replace it with `flox containerize` (OCI image from the same manifest).
7. CI: swap ad-hoc tool installs for `flox/install-flox-action` +
   `flox activate -- just check`.
8. Retire `scripts/install-{bun,gitleaks,lefthook}.sh`; gut the Makefile
   `check`/`hook-check`/`install-*`/`set-path` targets; replace the "review pin
   every 6 months" cadence with `flox upgrade`.

Sketch:

```toml
[install]
python.pkg-path = "python312"
uv.pkg-path = "uv"
just.pkg-path = "just"
bun.pkg-path = "bun"
lefthook.pkg-path = "lefthook"
gitleaks.pkg-path = "gitleaks"
gh.pkg-path = "gh"
taplo.pkg-path = "taplo"
ruff.pkg-path = "ruff"                                  # Bucket 3 (recommended)
editorconfig-checker.pkg-path = "editorconfig-checker"  # Bucket 3 (recommended)

[hook]
on-activate = '''
  uv sync --group dev
  lefthook install
'''

[options]
systems = ["aarch64-darwin", "x86_64-linux"]
```

## Consequences

**Positive**

- One declarative, cross-platform, lockfile-reproducible toolchain definition.
- Deletes ~3 shell scripts and most of the Makefile; local dev and devcontainer
  share one definition.
- Version drift becomes `flox upgrade` + commit instead of editing pins in shell.

**Negative / trade-offs**

- Adds Flox (and thus Nix) as a contributor prerequisite — contradicting the
  Makefile's "almost everyone has `make`" premise. This is the central tension.
- Two activation models coexist during transition (`flox activate` vs. bare
  shell) until the scripts/Makefile are retired.

**Neutral**

- `uv.lock` and `bun.lock` are unchanged — Flox layers *under* them, not over.
- Keep `ty` (pre-release pin) and `commitlint` (config-next-to-binary) in their
  current managers even though both are catalog-available.

## Status note

`proposed` — this ADR records the analysis and decision space. Adoption is a
separate step (the migration delta above) and should land behind its own ITM.
```
