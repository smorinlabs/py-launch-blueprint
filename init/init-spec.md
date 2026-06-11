# py-launch-blueprint — Self-Setup System

**Analysis & implementation plan for `init`, `init-doctor`, and the `just` guard.**

---

## 1. Summary

When a developer creates a repo from the `py-launch-blueprint` GitHub template, the
project still carries the blueprint's identity (package name, repo name, CLI command,
copyright holder, URLs). This system makes the new project **guide the developer through
re-branding itself**, deterministically, and lets them verify setup state at any time.

Three components, all living in the `init/` directory so the entire system can be
removed in one step once it has done its job:

| Component | Type | Purpose |
|---|---|---|
| **Guard** | `init/guard.sh`, called two ways | Two-tier. Tier 1: a universal, non-fatal discovery warning on every recipe run. Tier 2: a hard block on the small subset of recipes that would do real harm un-migrated. |
| **`init`** | `just init` → `init/init.py` | Interactive (or file-driven) walkthrough that deterministically rewrites all blueprint identity into the new project's values. |
| **`init-doctor`** | `just init-doctor` → `init/init_doctor.py` | Audits migration completeness and environment setup; reports, and optionally `--fix`es the environment. |

---

## 2. Analysis — current state of the repo

Inventory of `github.com/smorinlabs/py-launch-blueprint` (fetched and verified):

- **Flat package layout.** The package is `py_launch_blueprint/` at the repo root (not
  `src/`), with `uv_build` configured as `module-root = ""`. Renaming the package means
  renaming a *root* directory.
- **Identity strings: 209 occurrences across 57 files** (rescan, post-URL-cleanup; the
  count is a live measurement and will shift as Phase-0 work proceeds). Per-value
  breakdown:

  | Value | Occurrences | Files |
  |---|---:|---:|
  | `py_launch_blueprint` (dist + import name) | 83 | 29 |
  | `py-launch-blueprint` (repo name) | 72 | 25 |
  | `Steve Morin` (author) | 25 | 23 |
  | `steve.morin@gmail.com` (author email) | 3 | 3 |
  | `smorinlabs` (GitHub owner) | 33 | 15 |

- **The Justfile already centralizes three of them** as variables at the top
  (`py_package_name`, `repo_name`, `app_name`) — but the other ~56 files hardcode the
  literal strings, so variable substitution alone is insufficient.
- **Pre-existing inconsistency in the blueprint itself** (exactly what `init-doctor`
  should catch): the copyright year is `2025` in `pyproject.toml` and `docs/source/conf.py`
  but `2026` in `LICENSE`. *(A separate URL inconsistency — `smorin` vs `smorinlabs` —
  existed earlier and was resolved on the `feat/init-script` branch; it is the kind of
  drift the doctor's owner-consistency check is designed to flag in downstream projects.)*
- **`CHANGELOG.md` accumulates the blueprint's own release history** (compare-URLs,
  `plbp`, `smorinlabs`), so `init` **resets it to a stub** via `[[reset]]` rather than
  identity-rewriting it — a fork starts its own changelog, repopulated by release-please.
- **`init/` already exists** with `setup-github-environments.sh` and
  `setup-pypi-publishing.sh`; the new system co-locates here.
- **Toolchain already present:** `rich`, `click` are project dependencies
  (`questionary` is provisioned by the init script's own PEP 723 metadata, not
  the project); `uv` is the package manager; `pyproject.toml` carries meaningful
  `ITM-`/`ADR-` annotation comments that must survive any rewrite.
- The Justfile is 710 lines with ~11 public recipes plus aliases.

**Constraints these impose:**

1. The blueprint must remain a **working, CI-green project** — it is also a live demo.
   This rules out converting it to `{{TOKEN}}` placeholders.
2. The guard runs on a **bare clone before `uv sync`** — the hot path cannot depend on
   the project's virtual environment.
3. Determinism must be a property of **inspectable data**, not buried replacement-order
   logic.

---

## 3. Locked design decisions

| # | Decision |
|---|---|
| **Detection** | A marker file `init/.blueprint-initialized` gates the guard. The guard **skips** (does not block) if any of: the marker exists; `origin` points at the original blueprint repo; or a local contribution sentinel `init/.blueprint-contributor` exists. |
| **Contribution sentinel** | `init/.blueprint-contributor` is **git-ignored** — local-only, so it never leaks into a contributor's PR or downstream. It unblocks people who forked the blueprint to contribute back. |
| **Guard — two tiers** | The guard does two distinct jobs, split: **discovery** (broad, gentle) and **safety** (narrow, hard). |
| **Tier 1 — discovery** | A non-fatal warning banner printed on **every recipe run**, via a single parse-time `shell()` variable in the `Justfile`. Zero per-recipe boilerplate; covers all current and future recipes automatically. |
| **Tier 2 — safety** | A **hard block** (`_guard` recipe as a dependency) on only the small risk-based subset — recipes that produce a wrong artifact, an external side effect, or an identity-bearing write (`build`, `pr-to-testrepo`, `clean-pr-to-testrepo`, future `publish`). `init` / `init-doctor` omit it so the escape hatch always works. |
| **Implementation (guard)** | `init/guard.sh` is **pure shell** (fast, dependency-free), called as `guard.sh warn` (Tier 1) or `guard.sh block` (Tier 2). Both modes share three skip conditions: marker exists, contribution sentinel exists, or `origin` matches the original blueprint repo. The warn mode **must always `exit 0`** — a non-zero exit from a `shell()` call aborts `just`. |
| **Substitution** | **Manifest-driven structured rewrite.** `init/manifest.toml` is the single source of truth — shared by `init` and `init-doctor`. |
| **`init` run model** | **Interactive walkthrough** (`questionary`) by default; **`--config answers.toml`** for non-interactive/CI. Every interactive run **persists the answers** it used. |
| **Idempotency** | **Strict one-shot** — refuses if the marker exists (`--force` overrides). |
| **Safety** | Requires a **clean git working tree** (`--allow-dirty` overrides) — git is the undo button *and* the partial-run guard. `--dry-run` prints the full plan without writing. No auto-commit (`--commit` optional). |
| **`init-doctor`** | **Report by default**; `--fix` handles only the safe **environment** class (installs). Migration/identity drift is reported but only ever *changed* by `init`. |
| **Implementation** | `init.py` / `init_doctor.py` are **Python PEP 723 inline-metadata scripts** run via `uv run` — `uv` provisions an ephemeral env, so they need no project venv. `tomlkit` preserves comments on structured edits. (Guard implementation: see the Tier rows above.) |
| **Exposure** | `just` recipes only — never subcommands of the project's own CLI (bootstrap + ownership reasons). |
| **Containment** | Everything lives in `init/`, including the markers. The only footprint outside `init/` is in the `Justfile` (the Tier-1 `_blueprint_notice` variable, the `_guard` recipe, the `_guard` dependency token on each subset recipe, and the `init` / `init-doctor` recipes), one CI workflow, and one `.gitignore` line — all removed by `init --prune`. Default is **keep** (the guard self-silences post-init, and `init-doctor`'s environment checks stay useful). |

---

## 4. Component architecture

### 4.1 `init/` directory layout

```
init/
  guard.sh                     # fast shell guard — warn (Tier 1) + block (Tier 2) modes
  init.py                      # PEP 723 — interactive setup engine
  init_doctor.py               # PEP 723 — migration + environment audit
  manifest.toml                # migration manifest: replace / rename / remove
  common.py                    # shared: identity detection, manifest loader, validation
  ci/
    check_guard_wiring.py      # CI check #1 logic (also imported by init_doctor)
    check_no_marker.sh         # CI check #2 logic (scoped by repo name)
    check_manifest_drift.py    # CI check #3 logic
  tests/
    test_init.py
    test_doctor.py
    test_manifest.py
  setup-github-environments.sh # (existing)
  setup-pypi-publishing.sh     # (existing)
  README.md                    # what the system is, and how to prune it
  .blueprint-initialized       # written by init on success — COMMITTED
  .blueprint-contributor       # local opt-out — GIT-IGNORED
```

Footprint **outside** `init/` (all removed by `init --prune`): in the `Justfile`, the
Tier-1 `_blueprint_notice` variable, the `_guard` recipe, the `init` / `init-doctor`
recipes, and the `_guard` dependency token on each Tier-2 subset recipe;
`.github/workflows/blueprint-guard.yml`; and one line in `.gitignore`.

### 4.2 The guard (two-tier)

The guard does two distinct jobs — *discovery* (nudge a developer to run `just init`) and
*safety* (stop an operation that produces a wrong result un-migrated). These are split
into two tiers backed by one shell script, `init/guard.sh`, which uses only `git` and
POSIX shell — no Python, no venv. Both tiers share three **skip conditions**: the marker
`init/.blueprint-initialized` exists, the contribution sentinel `init/.blueprint-contributor`
exists, or `git remote get-url origin` (normalized for SSH/HTTPS/`.git`) matches the
original `smorinlabs/py-launch-blueprint`.

**Tier 1 — universal discovery warning.** A single parse-time variable near the top of
the `Justfile`:

```just
# Blueprint setup guard — Tier 1 (universal discovery warning).
# Eagerly evaluated on every recipe run; guard.sh warn MUST exit 0.
_blueprint_notice := shell('bash init/guard.sh warn')
```

The variable is never referenced — `just` evaluates every top-level `:=` variable eagerly
whenever any recipe runs, so this fires on every recipe with **zero per-recipe
boilerplate** and covers all future recipes automatically. `guard.sh warn` prints a
one-line banner to **stderr** and **always exits 0** (a non-zero exit from a `shell()`
call aborts `just`). It is non-fatal: the recipe runs normally after the banner.

*Verified behavior (`just 1.51.0`):* running any recipe or bare `just` evaluates all
variables eagerly → Tier 1 fires. `just --list` / `--summary` do **not** evaluate
variables → Tier 1 is silent on pure introspection (acceptable — listing is read-only;
the first real recipe run warns).

**Tier 2 — hard block on the risk subset.** A private `_guard` recipe (`guard.sh block`)
declared as a dependency only on recipes that, run un-migrated, produce a wrong artifact,
an external side effect, or an identity-bearing write: `build`, `pr-to-testrepo`,
`clean-pr-to-testrepo`, and any future `publish`. `guard.sh block` prints the full
discovery message and `exit 1`. `init` / `init-doctor` omit the dependency so the escape
hatch always works; `just --list` / `--help` are builtins and unaffected.

**Selection criterion for the Tier-2 subset:** a recipe earns a hard block only if running
it before `init` is *wrong and externally consequential*. Everything else (`test`,
`lint`, `typecheck`, `format`, `check`, `install-*`, `hooks-run`, `debug-info`,
`verify-commits`, `dev`) operates on code that still works as `py_launch_blueprint` — it
is warned by Tier 1 but not blocked.

| Invocation | Tier 1 banner | Tier 2 block |
|---|---|---|
| `just test` / `lint` / `format` … | ✅ then runs | — |
| `just build` / `pr-to-testrepo` | ✅ | ✅ blocks |
| `just init` / `init-doctor` | ✅ (harmless) | — |
| bare `just` (runs default recipe) | ✅ | — |
| `just --list` / `--summary` / `--help` | ❌ silent | ❌ |
| after `init`, or blueprint contributor | silent | silent |

### 4.3 The migration manifest (`init/manifest.toml`)

Three operation tables, applied by `init` in a **fixed order: remove → replace → rename**
(remove first to shrink the working set; replace while paths are still original so file
scopes stay valid; rename last).

```toml
[[replace]]
field   = "package_name"
current = ["py_launch_blueprint"]          # all variants enumerated
files   = ["pyproject.toml", "py_launch_blueprint/__init__.py", ...]
mode    = "structured"                      # toml key edit  |  "text" for prose

[[replace]]
field   = "owner"
current = ["smorin", "smorinlabs"]          # absorbs the existing inconsistency
files   = ["pyproject.toml", "docs/source/conf.py", ...]
mode    = "structured"

[[rename]]
from = "py_launch_blueprint/"               # package directory
to   = "{package_name}/"

[[rename]]
from = "docs/source/_static/py_launch_blueprint_logo_100x100.png"
to   = "docs/source/_static/{package_name}_logo_100x100.png"

[[remove]]
path   = ".github/workflows/blueprint-guard.yml"   # blueprint-only (Q2a Option 2)
reason = "guard CI is blueprint-only"
```

`structured` edits use `tomlkit` (TOML) or targeted line edits (Justfile vars, Sphinx
`conf.py`) so comments and formatting survive. `text` mode does ordered, longest-first
string replacement for prose files (`README.md`, docs `.md`).

### 4.4 `init.py`

PEP 723 script (`dependencies = ["questionary", "rich", "tomlkit"]`), run via
`uv run init/init.py`. Flow:

1. **Preconditions** — refuse if marker exists (unless `--force`); refuse if the git tree
   is dirty (unless `--allow-dirty`); verify `uv`/`git` present.
2. **Collect answers** — interactive `questionary` walkthrough, or load `--config`.
   Defaults: repo + owner parsed from `origin`; author from `git config`; year = current;
   package/CLI names derived but **fully overridable** (CLI command name is its own
   first-class prompt). Each answer is validated (package name = valid Python identifier,
   etc.).
3. **Build the plan** — resolve the manifest against the answers into a concrete list of
   edits, renames, and removals.
4. **Preview** — print the full plan (interactive: ask to confirm; `--dry-run`: stop here).
5. **Apply** — execute remove → replace → rename. On failure, print
   `git checkout . && git clean -fd` and exit non-zero.
6. **Finalize** — run `uv lock` (and Bun's lock if `package.json` changed) so lockfiles
   regenerate rather than being hand-edited; write `init/.blueprint-initialized` as a TOML
   record containing `[meta]` (version, date) + `[answers]`. Do not auto-commit unless
   `--commit`; tell the user to review `git diff`.

Flags: `--config`, `--dry-run`, `--force`, `--allow-dirty`, `--commit`, `--prune`.

### 4.5 `init_doctor.py`

PEP 723 script. Each check reports **pass / warn / error**; the process exits non-zero on
any error (CI-usable).

**Migration checks** (audited against `manifest.toml`):
- No leftover blueprint identity values anywhere in the repo.
- Marker present and its recorded answers match actual file state.
- Guard wiring intact — the Tier-1 `_blueprint_notice` variable is present, and every
  recipe in the Tier-2 subset declares the `_guard` dependency (shares
  `ci/check_guard_wiring.py`).
- Internal consistency — Justfile `py_package_name` == `pyproject.toml [project].name`
  == package dir name; `[project.scripts]` command == Justfile `app_name`; copyright
  year and owner consistent across `LICENSE` / `pyproject.toml` / `conf.py`.

**Environment checks:**
- Required tools on PATH: `just`, `uv`, `git`, `bun`, `lefthook`, `gitleaks`, `cog`.
- Project installed (`uv sync` done / venv present / CLI importable).
- Git hooks installed (lefthook); `origin` configured; Python ≥ 3.12.

`--fix` runs only the safe environment remediations (`uv sync`, `scripts/install-*.sh`,
hook installation). It never touches identity/migration content.

### 4.6 CI (`.github/workflows/blueprint-guard.yml`)

One thin workflow calling `init/ci/` scripts:
- **Marker absence** — fails if `init/.blueprint-initialized` exists, **scoped to a repo
  named `py-launch-blueprint`** so it is a no-op on every downstream project (Q2a Option
  1). `init` also deletes this workflow during migration (Q2a Option 2) — layered defense.
- **Guard wiring lint** — the Tier-1 `_blueprint_notice` variable is present and every
  Tier-2 subset recipe declares `_guard` (same logic as `init-doctor`).
- **Tier-1 regression test** — runs a recipe in an un-migrated fixture and greps stderr
  for the banner. This pins the eager-evaluation behavior Tier 1 depends on, so a future
  `just` upgrade that changes variable-evaluation semantics fails CI loudly instead of
  silently killing discovery. (The repo also pins its `just` version.)
- **Manifest drift** — every occurrence of a known identity string falls inside a
  manifest-declared file, so the manifest cannot silently fall out of date.

### 4.7 Instantiation modes the script must handle

A new project can be derived from the blueprint five ways; each leaves the working tree
in a different state that `init` and the guard must handle correctly. §5 Phase 5
exercises one fixture per mode.

| # | Mode | `origin` after instantiation | `.git` state | Script handling |
|---|---|---|---|---|
| 1 | GitHub **"Use this template"** button | `<owner>/<new-repo>` (not the blueprint) | clean, single initial commit | Normal path — guard does **not** skip; `init` proceeds. |
| 2 | **`gh repo create --template`** | same as #1 | same as #1 | Indistinguishable from #1 to the script. |
| 3 | **Clone + `rm -rf .git` + `git init`** | **unset** until the user adds a remote | fresh single commit, no remotes | `init` proceeds with no origin; `init-doctor` reports `warn: origin not configured`; the guard's origin check returns empty and **does not skip**. |
| 4 | **Fork** | `<user>/py-launch-blueprint` — repo name collides, owner differs | full blueprint history preserved | Guard's skip-on-origin compares **owner + name**, not name alone — a fork must **not** skip. The contribution sentinel (`init/.blueprint-contributor`) is the documented escape hatch for contributors who fork to PR upstream. |
| 5 | **ZIP download** (no Git) | none | **no `.git` directory** | `init` refuses with an actionable message ("run `git init` first; git is the undo button"). `--allow-dirty` does **not** override the missing-`.git` precondition — the dirty-tree check presupposes a tree exists. |

**Why this matters for tests:** the skip-condition logic and the precondition checks
each have a state-space that is only fully covered when all five modes are exercised. A
name-only origin match would silently break mode #4; a missing `.git` handler that paths
through the dirty-tree check would crash on mode #5; a hard-failing origin lookup would
break mode #3.

---

## 5. Implementation plan (phased)

**Phase 0 — Scaffolding.** Create the `init/` skeleton and `init/common.py`. Build a
one-off discovery script that scans the 189 occurrences, groups them by file, and emits a
**draft `manifest.toml`** for review. *Populating and verifying the manifest is the
critical-path work item* — everything else depends on it being accurate.

**Phase 1 — Guard.** Write `init/guard.sh` (shared skip logic; `warn` and `block` modes).
Add the Tier-1 `_blueprint_notice` variable to the `Justfile`; add the `_guard` recipe and
declare it as a dependency on the ~3 Tier-2 subset recipes; write the warning banner and
the full discovery message; add `init/.blueprint-contributor` to `.gitignore`.

**Phase 2 — `init.py`.** Build precondition checks, the `questionary` walkthrough +
`--config` loader + validation, the manifest engine (remove → replace → rename), preview/
`--dry-run`, lockfile regeneration, marker write, and the remaining flags.

**Phase 3 — `init_doctor.py`.** Build the migration and environment check sets, `--fix`
for the environment class, and exit-code behavior. Factor guard-wiring logic into
`init/ci/check_guard_wiring.py` so CI and the doctor share it.

**Phase 4 — CI.** Add `.github/workflows/blueprint-guard.yml` with the three checks.

**Phase 5 — Tests & docs.** `init/tests/` exercising `init` headlessly via `--config`
(this is *why* the answers file exists), `init-doctor` against both migrated and
un-migrated fixtures, manifest round-tripping, and **one fixture per instantiation mode
in §4.7** (template-button, `gh` CLI template, clone-reinit, fork, ZIP) — each fixture
asserts the guard's skip decision and `init`'s precondition handling for that mode.
Write `init/README.md`.

---

## 6. Risks & open items

- **Manifest accuracy is the dominant risk** — 189 occurrences across 54 files. Mitigated
  by the Phase-0 discovery script and the manifest-drift CI check.
- **Tier 1 depends on `just`'s eager variable evaluation** — verified for `just 1.51.0`,
  but a future version could go lazy. Mitigated by pinning the `just` version and the
  Tier-1 regression test in CI.
- **Exact removal list** — confirm which docs pages are blueprint-only (e.g.
  `docs/source/github-templates.md`) when populating `[[remove]]`.
- **Lockfiles** — `uv.lock` and `bun.lock` embed the project name; `init` must regenerate
  them (`uv lock`), never hand-edit. Already in the Phase-2 finalize step.
- **`[project.scripts]` entry point** — `py_launch_blueprint.cli.main:cli`: the
  `py_launch_blueprint` segment changes with the package rename; `cli.main:cli` stays.
- **The "Py" pseudo-placeholder** in the description / `__init__.py` docstring is treated
  as the free-text *description* field, not a distinct token.
