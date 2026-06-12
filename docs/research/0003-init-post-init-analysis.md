# Init &amp; Post-Init Systems — Asset Report &amp; Design Exploration

> A consolidated record of (1) everything found in the repository as existing
> assets, (2) the first design analysis (formalizing init/post-init into
> config-driven sub-systems), and (3) the second design analysis (mental
> models, ASCII diagrams, and architectural alternatives).
>
> Nothing from the working sessions has been dropped; this file is the
> durable artifact.

---

# Table of Contents

1. [Part 0 — Asset Report: What Exists Today](#part-0--asset-report-what-exists-today)
2. [Part 1 — First Analysis: Formalizing Init &amp; Post-Init](#part-1--first-analysis-formalizing-init--post-init)
3. [Part 2 — Second Analysis: Mental Models, Diagrams &amp; Alternatives](#part-2--second-analysis-mental-models-diagrams--alternatives)
4. [Part 3 — Synthesis &amp; Recommendations](#part-3--synthesis--recommendations)

---

# Part 0 — Asset Report: What Exists Today

A thorough exploration of the `py-launch-blueprint` repository produced the
following complete picture of both systems.

## Overall Shape of the Template

The template provides a comprehensive Python project scaffold with:

- **Package**: `src/py_launch_blueprint/` (PEP 420 layout with uv)
- **CLI**: `plbp` (Click-based, example in `src/py_launch_blueprint/cli/`)
- **Tooling**: ruff (lint/format), mypy, pytest, lefthook (git hooks), commitlint
- **CI/CD**: 16+ GitHub Actions workflows (test, lint, CodeQL, release-please, publish, etc.)
- **Publishing**: OIDC trusted publishing to PyPI + TestPyPI, release-please version automation
- **Docs**: Sphinx + MyST, ReadTheDocs integration, ADRs, design docs
- **Features**: Codecov integration, secret scanning, dependency review, contributors automation

---

## 1. INIT SYSTEM — Rebranding: Identity Transformation

### What It Does

The `init` system guides developers through **rebranding a template instance
into a new project** by transforming all blueprint identity strings into
project-specific values.

### Entry Points &amp; Flow

| Component | Type | File Path | Entry | Flow |
|---|---|---|---|---|
| **Guard (Tier 1)** | POSIX shell | `init/guard.sh` | `just` recipe evaluation | Prints non-fatal warning banner on every `just` command when un-migrated. Uses parse-time `_blueprint_notice := shell('bash init/guard.sh warn')` in Justfile to fire eagerly. Always exits 0. |
| **Guard (Tier 2)** | POSIX shell | `init/guard.sh` | `_guard` recipe dependency | Hard block (exit 1) on risky recipes (`build`, `pr-to-testrepo`, `publish`) that produce external side effects or identity-bearing artifacts. |
| **`init.py`** | PEP 723 script | `init/init.py` (399 lines) | `just init [--config/--dry-run/--force/--allow-dirty/--commit/--prune]` | Interactive questionary walkthrough (or headless via `--config answers.toml`) that rewrites identity across the repo and writes the initialization marker. |
| **`init_doctor.py`** | PEP 723 script | `init/init_doctor.py` (597 lines) | `just init-doctor [--fix]` | Audits migration completeness (no leftover blueprint strings, marker consistency, guard wiring) and environment readiness (tools on PATH, uv sync done, hooks installed). `--fix` remediates environment issues only. |
| **Manifest** | TOML (declarative) | `init/manifest.toml` (14KB) | Loaded by init.py &amp; init_doctor.py | Single source of truth: lists all identity replacements, renames, removals, and resets across 60+ files. |

### Core Components &amp; Design

#### 1. Guard (Two-Tier Architecture)

**Tier 1 — Discovery Warning (non-fatal, universal)**

```bash
# In Justfile (line 17):
_blueprint_notice := shell('bash init/guard.sh warn')
# Fires on EVERY recipe run unless:
#   1. init/.blueprint-initialized exists (migration done)
#   2. init/.blueprint-contributor exists (contributor opting out)
#   3. git origin matches the blueprint repo
```

- **Output**: One-line stderr banner: `⚠  blueprint un-initialized — run 'just init'`
- **Exit Code**: Always 0 (must never block a `just` recipe)
- **Purpose**: Nudge developers to run init before doing real work

**Tier 2 — Safety Block (hard block, selective)**

```bash
# Declared as _guard recipe dependency on only risky recipes:
#   build, pr-to-testrepo, clean-pr-to-testrepo, publish (future)
```

- **Output**: Full discovery message with escape hatches
- **Exit Code**: 1 (blocks the recipe)
- **Purpose**: Prevent un-migrated projects from shipping wrong artifacts or making external side effects

**Skip Conditions** (shared by both tiers):

- Marker `init/.blueprint-initialized` exists
- Contributor sentinel `init/.blueprint-contributor` exists (git-ignored)
- Origin URL matches blueprint repo (for contributors forking upstream)

**File**: `init/guard.sh` (93 lines)

#### 2. Identity Manifest

**File**: `init/manifest.toml` (14KB)

**Structure**: TOML with four operation types, applied in fixed order:
**remove → replace → rename → reset**

**Example (Identity Values)**:

```toml
[[replace]]
field = "package_name"
current = ["py_launch_blueprint"]
files = ["pyproject.toml", "src/py_launch_blueprint/__init__.py", ...]
mode = "structured"  # or "text"

[[replace]]
field = "app_name"
current = ["plbp"]
files = ["Justfile", "pyproject.toml", "docs/", "src/", ...]
mode = "text"

[[rename]]
from = "src/py_launch_blueprint/"
to   = "src/{package_name}/"

[[remove]]
path = ".github/workflows/blueprint-guard.yml"
reason = "blueprint-only CI"

[[reset]]
path = "CHANGELOG.md"
stub = "# Changelog\n"
```

**Coverage** (per spec §2):

- 6 identity fields: `package_name`, `repo_name`, `app_name`, `app_name_upper`, `author`, `owner`, `email`
- ~209 occurrences across 57 files
- Modes: `structured` (TOML edits via tomlkit, targeted line edits) vs `text` (naive longest-first replacement)

**Discovery**: `init/discover.py` (one-off Phase 0 tool) scans the repo and
emits a draft manifest for review.

#### 3. `init.py` — Interactive/Headless Rebrand

**File**: `init/init.py` (399 lines)

**Flow**:

1. **Preconditions** (§4.4 step 1):
   - `.git` directory must exist (mode #5 — ZIP downloads must `git init` first)
   - Marker must not exist (unless `--force`)
   - Git tree must be clean (unless `--allow-dirty`)
   - `git` and `uv` must be available

2. **Collect Answers** (interactive or `--config`):

   ```python
   class Answers:
       package_name: str  # derived from repo_name if not set
       repo_name: str     # parsed from git origin
       app_name: str      # derived from package_name if not set
       author: str        # from git config or prompt
       email: str
       owner: str         # parsed from git origin
   ```

   - Validated per BLUEPRINT_IDENTITY constraints (Python identifier, valid email, etc.)
   - Defaults inferred from git config &amp; origin URL

3. **Build Plan** (via `_engine.py`):

   ```python
   plan = build_plan(manifest, answers)  # resolve manifest against answers
   ```

   - Non-destructive: shows user what will happen
   - Supports `--dry-run` (print plan, exit)

4. **Apply** (remove → replace → rename):
   - **Remove**: Delete files listed in `[[remove]]` (e.g., blueprint-only CI)
   - **Replace**: Rewrite identity strings in `[[replace]]` files (text or structured mode)
   - **Rename**: Move files/dirs (e.g., `src/py_launch_blueprint/` → `src/{new_name}/`)
   - **Reset**: Overwrite with fresh stubs (e.g., CHANGELOG.md)

5. **Finalize**:
   - Regenerate lockfiles: `uv lock`, `bun install` (identity embedded in lockfiles)
   - Write marker: `init/.blueprint-initialized` (TOML with `[meta]` + `[answers]`)
   - Optional `--commit` (auto-stage &amp; commit changes)

**Flags**:

- `--config PATH`: Headless mode (TOML file with `[answers]` table)
- `--dry-run`: Print plan, don't write
- `--force`: Run even if marker exists
- `--allow-dirty`: Run even if git tree is dirty
- `--commit`: Auto-commit changes
- `--prune`: Remove init/ system entirely (post-init cleanup)
- `--no-lockfile`: Skip lock regeneration (tests use this)

**Auto-Chain**: After interactive init, prompts to run `just post-init` if stdin is a TTY.

#### 4. Marker (`init/.blueprint-initialized`)

**Written by**: `init.py` on success, `post_init.py` on each run

**Purpose**:

- Gate the guard (once written, guard skips)
- Record answers for doctor's verification
- Record post-init decisions (publishing, Codecov, RTD state)

**Format** (TOML):

```toml
[meta]
version = "0.1.0"
date    = "2026-05-25"

[answers]
package_name = "my_project"
repo_name = "my-project"
app_name = "mp"
author = "Your Name"
email = "you@example.com"
owner = "yourgithub"

[post_init]
version = "0.1.0"
date    = "2026-05-25"
mode    = "full"

[post_init.publishing]
pypi           = "enabled"
testpypi       = "enabled"
release_please = "enabled"

[post_init.codecov]
status    = "enabled"
token_set = false

[post_init.readthedocs]
status = "configured"

[post_init.oidc]
pypi_trust_verified_at     = "2026-05-26T14:30:00+00:00"
testpypi_trust_verified_at = "2026-05-26T14:31:00+00:00"
```

#### 5. `init_doctor.py` — Audit &amp; Verification

**File**: `init/init_doctor.py` (597 lines)

**Two/Three Check Classes**:

| Class | Checks | Remediation |
|---|---|---|
| **MIGRATION** | No leftover blueprint identity, marker consistency, guard wiring, internal consistency (Justfile vars match pyproject, copyright year aligned) | None (read-only, except reporting) |
| **ENVIRONMENT** | Tools on PATH (just, uv, git, bun, lefthook, gitleaks, cog), venv present, hooks installed, Python ≥3.12 | `--fix` runs safe remediations (uv sync, script installs, lefthook install) |
| **POST_INIT** (new) | Marker post_init section validity, workflow files match recorded state (if publishing enabled, publish.yml exists, not in .disabled/) | None (validation only) |

**Exit Codes**:

- 0: All checks passed
- 1: One or more checks reported error
- 2: Doctor itself failed (missing manifest, IO error)

#### 6. Engine (`_engine.py`)

**File**: `init/_engine.py` (304 lines)

**Classes**:

```python
class Answers: identity answers from user
class Plan: concrete list of edits to apply
class PlanItem: one edit (kind, path, detail)
class ApplyReport: summary of what was applied

def build_plan(manifest, answers) -> Plan:
    # Non-destructive; shows user what will happen

def apply(manifest, answers) -> ApplyReport:
    # Execute in order: remove → replace → rename → reset
    # On failure: user gets `git checkout . && git clean -fd` recovery advice
```

**Replace Modes**:

- **`text`**: Longest-first string replacement (prose files, docs, etc.)
- **`structured`**: Calls `_rewriters.py` dispatch for TOML/YAML/Sphinx conf files
  - Uses `tomlkit` to preserve comments &amp; formatting
  - Targeted line edits for Justfile vars, Sphinx `conf.py`

#### 7. Testing (Five Instantiation Modes, §4.7)

**Files**: `init/tests/` (9 test files)

The five modes represent different ways a developer can instantiate the template:

| # | Mode | Origin State | `.git` | Init Behavior | Test Coverage |
|---|---|---|---|---|---|
| 1 | **GitHub "Use this template" button** | `<owner>/<new-repo>` (not blueprint) | Clean, single commit | Normal path — guard does NOT skip | L1 + L2 |
| 2 | **`gh repo create --template`** | Same as #1 | Same as #1 | Same as #1 | L1 + L2 |
| 3 | **Clone + `rm -rf .git` + `git init`** | Unset until user adds remote | Fresh single commit | Guard passes (no origin), init proceeds | L1 + L2 |
| 4 | **Fork** | `<user>/py-launch-blueprint` (name collides, owner differs) | Full blueprint history | Guard's skip-on-origin checks owner + name (must NOT skip forks; contributor sentinel is escape hatch) | L1 + L2 + contrib sentinel test |
| 5 | **ZIP download** | None | **No `.git` directory** | Init refuses with "run `git init` first"; `--allow-dirty` does NOT override | L1 only (no L2) |

**Test Assertion Layers**:

- **L1 — Contract** (all 5 modes): Guard fires, init exit code correct, marker present/absent as mandated
- **L2 — Outcome** (modes 1-4): After init: `uv sync --group dev`, tests pass, `uv build` works, CLI runs, `init-doctor` clean

**Integration Runner**: `init/tests/integration/run-mode.sh` (bash) +
`answers.toml` (static fixture answers)

**CI Integration**: `.github/workflows/init-integration.yml` runs all 5 modes
as a matrix, triggered on PR/push/cron (Mon 09:00 UTC).

### Identity Values Tracked

From `init/common.py`:

```python
BLUEPRINT_IDENTITY = {
    "package_name": "py_launch_blueprint",
    "repo_name": "py-launch-blueprint",
    "app_name": "plbp",
    "app_name_upper": "PLBP",  # derived, not prompted
    "author": "Steve Morin",
    "email": "steve.morin@gmail.com",
    "owner": "smorinlabs",
}

PROMPTED_IDENTITY_FIELDS = (
    "package_name", "repo_name", "app_name", "author", "email", "owner"
)
```

### Documentation

| File | Purpose |
|---|---|
| `init/README.md` | Quick reference: components, usage, how to remove system |
| `init/init-spec.md` | Full spec: rationale, locked design decisions, architecture (§1–§6), risks, phased plan |
| `init/tests/integration/README.md` | Integration test runner explanation, modes, CI usage |

---

## 2. POST-INIT SYSTEM — Feature Selection &amp; Remote Setup

### What It Does

The `post-init` system guides developers through **configurable feature
decisions** and **remote service setup** (PyPI publishing, Codecov,
ReadTheDocs) that run **after `init` rebrand is complete**.

### Entry Point

| Component | Type | File Path | Entry | Flow |
|---|---|---|---|---|
| **`post_init.py`** | PEP 723 script | `init/post_init.py` (804 lines) | `just post-init [--status/--skip-remote]` | Interactive prompts for publishing (PyPI/TestPyPI/release-please), Codecov, ReadTheDocs decisions. Applies file moves, edits ci.yml, walks through OIDC/RTD browser steps, records decisions in marker. |

### What Post-Init Owns (V1 Scope)

1. **Publishing to PyPI** (OIDC trusted publishing)
   - Enable/disable PyPI publish
   - Enable/disable TestPyPI mirror
   - Enable/disable release-please version bumps

2. **Codecov Coverage Uploads**
   - Enable/disable Codecov integration
   - Optionally set Codecov token

3. **ReadTheDocs Docs Hosting**
   - Configure/decline/defer RTD import
   - Guided walkthrough (informational; user clicks links)

### What Post-Init Does NOT Own

- Branch protection, FUNDING.yml/Sponsors, dependabot tweaks
- Security workflow gating, container registries
- Headless `--config` mode (CLI only; CI must drive separately)

### Flow &amp; Components

#### 1. Preconditions &amp; Remote Detection

**File**: `init/post_init.py` lines 152–179 (function `check_preconditions()`)

```python
def check_preconditions() -> bool:
    """Returns True if remote available (full flow), False otherwise (partial mode)."""
    if not MARKER_PATH.exists():
        raise PreconditionError("run `just init` first")
    if shutil.which("gh") is None:
        raise PreconditionError("gh CLI not installed")
    auth = _run(["gh", "auth", "status"])  # must be authenticated
    if auth.returncode != 0:
        raise PreconditionError("gh is not authenticated")

    # Try to parse origin & verify repo exists
    origin = _run(["git", "remote", "get-url", "origin"]).stdout.strip()
    if not origin:
        warn("no `origin` remote set — partial-no-remote mode")
        return False
    parsed = parse_origin(origin)
    if not parsed:
        warn("could not parse origin URL — partial mode")
        return False
    owner, repo = parsed
    rv = _run(["gh", "repo", "view", f"{owner}/{repo}"])
    if rv.returncode != 0:
        warn("repo not found; push to GitHub then re-run for remote setup")
        return False
    return True
```

**Two Modes**:

- **Full**: Remote available, all walkthroughs + remote ops (gh/PyPI)
- **Partial (`--skip-remote`)**: Local edits only; defers gh/PyPI work

#### 2. Decision Dataclasses

**File**: `init/post_init.py` lines 71–98

```python
@dataclass
class PublishingConfig:
    pypi: str = DEFERRED          # "enabled" | "disabled" | "deferred"
    testpypi: str = DEFERRED
    release_please: str = DEFERRED

@dataclass
class CodecovConfig:
    status: str = DEFERRED         # "enabled" | "disabled" | "deferred"
    token_set: bool = False

@dataclass
class RTDConfig:
    status: str = DEFERRED         # "configured" | "declined" | "deferred"

@dataclass
class PostInitConfig:
    version: str = POST_INIT_VERSION
    date: str = ""
    mode: str = "full"             # "full" | "partial-no-remote" | "reconfigure"
    publishing: PublishingConfig
    codecov: CodecovConfig
    readthedocs: RTDConfig
    pypi_trust_verified_at: str | None = None
    testpypi_trust_verified_at: str | None = None
```

#### 3. Interactive Prompts

**Functions**:

- `ask_yes_no_defer()` → returns `("enabled", "disabled", "deferred")`
- `ask_yes_no()` → returns `bool`
- `ask_choice()` → generic choice picker

**Examples**:

```python
def ask_publishing(current: PublishingConfig | None) -> PublishingConfig:
    header("Publishing — release artifacts to PyPI")
    pypi = ask_yes_no_defer("Publish to PyPI?", current.pypi if current else DEFERRED)
    if pypi == ENABLED:
        testpypi = ask_yes_no("Mirror to TestPyPI?", default=True)
        release_please = ask_yes_no("Use release-please for version bumps?", default=True)
    # ...
    return PublishingConfig(pypi=pypi, testpypi=testpypi, release_please=release_please)
```

#### 4. Local File Operations

**Workflow File Moves** (lines 363–388):

```python
def disable_workflow(name: str) -> bool:
    """Move .github/workflows/<name> → workflows.disabled/<name>. Idempotent."""

def enable_workflow(name: str) -> bool:
    """Reverse of disable_workflow."""
```

- If `publish.yml` enabled, move from `.disabled/` to `workflows/`
- If publish disabled, move from `workflows/` to `.disabled/`
- If release-please disabled, move its workflow to `.disabled/`

**CI.yml Codecov Gate Edit** (lines 394–476):

```python
def edit_ci_yml_codecov_gate() -> bool:
    """Add `&& secrets.CODECOV_TOKEN != ''` to codecov step's `if:` condition."""
    # Marks with: # post-init: codecov-gated
    # Appends warning step that runs when token is unset
    # Idempotent — does nothing if marker already present
```

#### 5. Remote Operations (Full Mode Only)

**GitHub Environments**:

```python
def run_setup_github_environments(repo_slug: str, envs: list[str]) -> bool:
    """Wraps init/setup-github-environments.sh for chosen envs."""
    # Calls: bash init/setup-github-environments.sh <owner>/<repo>
```

**Codecov Token**:

```python
def set_codecov_token_via_gh(repo_slug: str, token: str) -> bool:
    # gh secret set CODECOV_TOKEN --repo <slug>
```

**OIDC Walkthrough** (lines 588–612):

```python
def oidc_walkthrough(
    project_name: str,
    owner: str,
    repo: str,
    target: str,  # "pypi" | "testpypi"
) -> str | None:  # returns ISO timestamp on verified, None if skipped
    """
    1. Prints PyPI form values (project name, owner, repo, workflow, env)
    2. Optionally opens browser to https://pypi.org/manage/account/publishing/
    3. Polls PyPI JSON API for project existence (timeout 5 min)
    4. Returns verification timestamp on success
    """
```

**ReadTheDocs Walkthrough** (lines 769–781):

```python
# Informational only — user clicks links at readthedocs.org/dashboard/import/
# Lists steps: sign in, find & import repo, confirm slug, wait for build
```

#### 6. Marker I/O (Post-Init Section)

**Read Existing**:

```python
def read_existing_post_init() -> PostInitConfig | None:
    raw = tomllib.loads(MARKER_PATH.read_text())
    pi = raw.get("post_init")
    if not pi:
        return None
    # Reconstruct dataclasses from TOML [post_init.*] sections
```

**Write with Existing Preserved**:

```python
def write_marker_with_post_init(cfg: PostInitConfig) -> None:
    text = MARKER_PATH.read_text()
    idx = text.find("[post_init]")
    base = text[:idx].rstrip() + "\n" if idx != -1 else text.rstrip() + "\n"
    # Preserves [meta] + [answers]; appends/replaces [post_init.*] sections
    MARKER_PATH.write_text(base + _render_post_init_toml(cfg))
```

#### 7. Re-Run Semantics

**First Run**: Asks each decision fresh, defaults to "Defer"

**Subsequent Runs**:

- Shows current state as default
- User can pick a new answer to flip a decision
- File moves/edits applied symmetrically (if was disabled, enable it; if enabled, disable it)
- Example: disable publish.yml → subsequent run shows "currently: disabled" → user can switch to "enabled" to re-enable it

**Status Output** (lines 620–636):

```python
def print_status(cfg: PostInitConfig | None) -> None:
    # Prints all post-init decisions + OIDC verification timestamps
    # Called by --status flag (no changes, just report)
```

### Testing

**Files**:

- `init/tests/test_post_init.py` (149 lines) — Unit tests: marker I/O, workflow moves, ci.yml gate edits, idempotency
- `init/tests/test_doctor_post_init.py` (200+ lines) — Doctor's post_init check class validation

**Coverage**:

- Marker round-trip (read/write, preserve sections)
- Workflow disable/enable idempotency
- ci.yml codecov gate insertion + idempotency
- Status output
- NOT tested: gh CLI, PyPI polling, browser ops (integration concerns)

### Integration with Marker

The `init/.blueprint-initialized` marker now has three sections:

```toml
[meta]                          # version, date (read-only)
[answers]                       # init answers (read-only after init)
[post_init]                     # post-init decisions (mutable)
  [post_init.publishing]        # pypi, testpypi, release_please
  [post_init.codecov]           # status, token_set
  [post_init.readthedocs]       # status
  [post_init.oidc]              # pypi_trust_verified_at, testpypi_trust_verified_at
```

---

## 3. Feature Selection &amp; Decision Pattern

### How Post-Init Drives Behavior

**Workflow File Placement Strategy**:

- **Default**: `.github/workflows/` (enabled)
- **Disabled Decision**: Move to `.github/workflows.disabled/` (stays in git, not run)
- **Motivation**: Offline-friendly, reversible, CI can verify consistency

**Features Configurable via Post-Init** (from `POST_INIT.md`):

| Feature | Decision | Outcome |
|---|---|---|
| **Publish to PyPI** | Yes/No/Defer | `publish.yml` enabled/disabled/.disabled |
| **Mirror to TestPyPI** | Yes/No/Defer | `publish.yml` job commented/uncommented |
| **release-please version bumps** | Yes/No/Defer | `release-please.yml` enabled/disabled/.disabled |
| **Codecov uploads** | Yes/No/Defer | `ci.yml` codecov step gated + warning appended |
| **ReadTheDocs hosting** | Configure/Decline/Defer | Informational walkthrough |

**Features NOT in Post-Init (Manual in POST_INIT.md Checklist)**:

- CodeQL advanced setup (§3.1)
- Branch protection (§3.6)
- Dependabot (§3.5)
- CLA assistant (§3.7)
- Funding/Sponsors (§3.8)
- Secret setup (§3.3)

### Existing Config-Driven Approach

**POST_INIT.md** (`POST_INIT.md`, 297 lines): A comprehensive **post-init
checklist** organized by feature category:

| Category | Type | Approach |
|---|---|---|
| **§1: Feature Decisions** | Dropdown checklist | Keep/Remove per feature (with files to delete) |
| **§2: Configuration Checklist** | Reference table | Secrets, environments, external services, repo settings |
| **§3: Per-Feature Setups** | Step-by-step | Concrete instructions for each feature (gh commands, UI paths) |
| **Quick Start** | Abbreviated flow | Typical public OSS project setup order |

This is **not automated** (manual checklist-driven); post-init.py **automates a
subset** (publishing, Codecov, RTD).

---

## 4. Existing Specs, ADRs &amp; Project Tracking

### Project Tracking

**File**: `PROJECTS.md` + `projects/`

**Current Project**:

- **P01**: "Init app-name rebrand robustness" (COMPLETED) — Fixed per-field drift coverage + derived non-contract internals (env vars, logging markers)
  - **File**: `projects/P01-init-rebrand-robustness.md`
  - **Status**: `[x]` completed
  - **Scope**: init rebrand system, CLI internals
  - **Key Finding**: Drift guard was using flat-union coverage (missing per-value scope); fixed to verify per field + stopped blanket-skipping `[[rename]]` files

### Architecture Decision Records (ADRs)

**Location**: `docs/adr/` (not in superpowers/specs yet). Likely includes
decisions about app_name (plbp), config handling, etc.

### Superpowers/Specs

**Location**: `docs/superpowers/specs/` — Currently has only a `.gitkeep`
(empty). Reserved for future specs but not yet populated; could host post-init
design specs if formalized.

---

## 5. File Structure Reference

### Init System Files

```
init/
  guard.sh                       # (93 lines) Tier 1+2 guard, skip logic
  init.py                        # (399 lines) Interactive/headless rebrand
  init_doctor.py                 # (597 lines) Audit + verification
  post_init.py                   # (804 lines) Feature selection + remote setup
  manifest.toml                  # (14KB) Declarative replacement scope
  common.py                      # (319 lines) Identity SSOT, validators, manifest loader
  _engine.py                     # (304 lines) Rewrite engine: build plan, apply edits
  _rewriters.py                  # (29 lines) Structured rewriter dispatch (empty today)
  discover.py                    # (273 lines) One-off: scan repo, emit manifest draft
  init-spec.md                   # (343 lines) Full design rationale + architecture
  README.md                      # (61 lines) Quick reference
  ci/
    check_guard_wiring.py        # Verify Tier 1+2 wiring in Justfile + recipes
    check_no_marker.sh           # CI: fail if marker exists (blueprint-only check)
    check_manifest_drift.py      # Verify manifest covers all identity occurrences
    check_path_filter.py         # Enforce strict init-integration paths
  tests/
    test_init.py                 # Headless rebrand tests
    test_doctor.py               # Doctor checks tests
    test_doctor_post_init.py     # Post-init decision state tests
    test_post_init.py            # Marker I/O, workflow moves, ci.yml edits
    test_manifest.py             # Manifest loading, schema validation
    test_modes.py                # Five §4.7 instantiation mode coverage
    test_drift_per_field.py      # Per-field drift coverage (P01 fix)
    test_cross_language_drift.py # Check_manifest_drift regression
    test_reset.py                # Reset operation (CHANGELOG stub)
    test_conftest_guard.py       # Guard eager-eval behavior (Tier 1 regression)
    integration/
      run-mode.sh                # L1+L2 integration runner (bash)
      answers.toml               # Static fixture answers
      README.md                  # Integration test explanation
  .blueprint-initialized         # Marker (TOML, committed)
  .blueprint-contributor         # Sentinel (local, git-ignored)
  setup-github-environments.sh   # (existing) GitHub env creation
  setup-pypi-publishing.sh       # (existing) PyPI publishing setup
```

### Related Files Outside `init/`

```
.github/workflows/
  blueprint-guard.yml            # CI: checks marker absence, guard wiring, drift
  init-integration.yml           # CI: L1+L2 matrix for 5 modes (15 min)

.gitignore                       # Includes: init/.blueprint-contributor

Justfile                         # Lines 17 (_blueprint_notice), 237 (_guard), 243–256 (recipes)

POST_INIT.md                     # Manual post-init checklist (§1 decisions, §2 setup, §3 steps)

PROJECTS.md                      # P01 project tracking

projects/P01-init-rebrand-robustness.md  # Completed project: per-field drift coverage

docs/superpowers/specs/          # Currently empty (.gitkeep)

docs/adr/                        # ADRs (app_name, config handling, etc.)
```

---

## Summary Table: Init vs Post-Init (as built)

| Aspect | Init | Post-Init |
|---|---|---|
| **Purpose** | Rebrand identity (one-shot) | Feature selection + remote setup (re-runnable) |
| **Trigger** | User or CI (headless) | User interactive (or `--skip-remote`) |
| **Guard** | Yes (Tier 1+2) | No (precondition check instead) |
| **Idempotency** | Strict one-shot (`--force` override) | Re-runnable (shows current, lets user flip) |
| **Marker** | Writes `[meta]` + `[answers]` | Appends/rewrites `[post_init.*]` sections |
| **File Changes** | Replace 60+ files (text+structured), rename dirs, remove blueprint-only | Move workflows (.disabled/), edit ci.yml |
| **Remote Ops** | None | GitHub envs, codecov token, OIDC walkthrough, RTD import |
| **Config** | `--config answers.toml` (headless) | `--status` (no-op), `--skip-remote` (local-only) |
| **Automation Level** | Full (manifest-driven) | Partial (workflow files only; secrets/settings manual) |
| **Offline-Friendly** | Yes (no remote needed) | Partial (`--skip-remote` for local-only) |

---

# Part 1 — First Analysis: Formalizing Init &amp; Post-Init

> The headline: **init already implements the proposed config-generator +
> config-runner model almost exactly, and post-init is where the model doesn't
> exist yet.** That asymmetry should shape the whole plan.

## What you already have

Init is already split into config-generator + runner, just not named that way:

- **Schema/scope**: `init/manifest.toml` declares every replace/rename/remove/reset across ~57 files
- **Config**: `answers.toml` (the `--config` headless path) — the interactive questionary flow is just one *generator* of that config
- **Runner**: `init/_engine.py` — `build_plan(manifest, answers)` → `apply()`, with `--dry-run` showing the plan
- **State**: `init/.blueprint-initialized` marker records what was applied
- **Verifier**: `init_doctor.py` audits completeness

Post-init (`init/post_init.py`, 804 lines) is the opposite: prompts, decision
dataclasses, file ops, and remote walkthroughs are all interleaved in one
script. There is no `--config` mode, no plan stage, and decisions only exist as
marker output after the fact. `POST_INIT.md` covers a much larger feature
surface (CodeQL, branch protection, dependabot, funding…) that's entirely
manual.

## The refined model: four artifacts, not two

The "config generator + config runner" split is right, but each pipe really has
**four** artifacts, and naming them separately resolves most of the design
questions:

| Artifact | Init | Post-init |
|---|---|---|
| **Schema** (what's decidable, what's valid, what depends on what) | manifest.toml + identity fields | a *feature/decision graph* — doesn't exist yet |
| **Config** (the answers — desired state) | answers.toml | decisions.toml — doesn't exist yet |
| **Plan** (concrete diff the runner will make) | `build_plan()` output | doesn't exist yet |
| **State** (what was actually applied) | marker `[answers]` | marker `[post_init.*]` |

The generator's job is *schema → config* (interactively, by flags, or
hand-written). The runner's job is *config + current state → plan → apply →
updated state*. Keeping **config (intent)** separate from **state (record)**
matters most for post-init, because they diverge — "deferred" lives in config,
"OIDC verified at timestamp X" lives in state.

## Why the two pipes are different kinds of programs

**Init is a one-shot function**: template → project. Run once, deterministic,
then it prunes itself. The plan/apply model it has is correct and basically
done.

**Post-init is a reconciler**, and this is the key design decision. It's
Terraform-shaped, not script-shaped: config declares *desired* feature state,
the runner diffs desired vs actual (files in `workflows/` vs `.disabled/`,
marker contents, remote checks) and converges. This gives you the iterative
behavior, the checks, and the "alternate cleanup path" for free:

- **Decision graph with sub-decisions**: each decision in the schema carries a `relevant_when` condition (e.g., `testpypi` and `release_please` only when `pypi = enabled`). The generator skips irrelevant questions; the runner records them as `not_applicable`. When a parent flips, dependents automatically become relevant or collapse.
- **Feature modules, each declaring both directions**: every feature defines its `enabled` materialization and its `disabled` one. Cleanup isn't a special path — it's just the runner converging to the disabled state. Make disabled two-valued, because the current system conflates two things:
  - `dormant` — reversible (today's move-to-`workflows.disabled/`)
  - `removed` — destructive delete of the feature's files (today's manual POST_INIT.md §1 checklist), declared like init's `[[remove]]` blocks, always shown in a plan and confirmed before apply, one-way (state records it; sub-decisions become `not_applicable` permanently)
- **Action capability classes**: every action is tagged `local` (file edits — always automatable), `remote` (gh/PyPI API — automatable when credentials exist), or `manual` (browser walkthroughs — runner emits instructions and optionally polls for verification, like the existing OIDC flow). This is what makes one codebase serve both agents and humans: an agent runs `apply` and gets back machine-readable "manual steps remaining"; a human gets the walkthrough.

So the post-init verb set becomes: `decide` (generator) → `plan` (diff,
`--json` for agents) → `apply` → `verify`/`status` (doctor-style), all
idempotent and re-runnable.

## Packaging: one tool, two commands — extract after the seam is proven

Two separate Python projects were floated. Recommend against that as the
starting point. The two pipes share a lot of kernel: config/marker I/O,
plan/apply engine pattern, repo-root discovery, prompt layer, doctor framework,
and the `--json`/exit-code contract for agents. Two projects means a third
shared library and three-way version coordination, for exactly one consumer
(this template).

Instead:

1. **One package, two entry points** (e.g., `plb init` and `plb setup`, or `blueprint-init`/`blueprint-setup`), with a strict internal layering: pure core (schema → questions, config+state → plan, plan → effects) and two thin frontends (TUI via questionary, CLI/JSON). The TUI is just a config generator over the same core the CLI uses.
2. **Data stays in the template, engine moves to the tool.** `manifest.toml` and the feature definitions are template-specific content; the engine, prompts, state machine, and doctor framework are generic. The template's Justfile recipes become `uvx plb@<pinned-version> ...` wrappers, and the config schema version is the contract between them.
3. **Split into two projects later only if release cadences actually diverge.** The extraction seam (declarative manifest/feature files in, plans out) is the thing to get right; the repo boundary is cheap to add afterwards.

One caution on the extracted-init-engine direction: a generic "manifest-driven
repo rewriter" drifts toward reimplementing **copier** (templates + answers
file + conditional questions + update story). This approach is deliberately
different — the blueprint is a *working repo*, not a Jinja skeleton, which is
why the CI can test the template itself. Keep that property; but copier's
`copier.yml` is worth borrowing from for the decision-graph schema (it has
conditional questions and answer-file conventions already worked out).

## Suggested phasing

1. **Formalize post-init in place** (biggest gap, zero extraction risk): split `post_init.py` into schema/generator/engine modules mirroring init's structure; add `--config decisions.toml` headless mode and a real `plan` stage. This alone makes it agent-drivable.
2. **Define the feature-module interface** and migrate the existing three features (publishing, codecov, RTD) onto it; then absorb 2–3 manual POST_INIT.md items (dependabot, funding, CodeQL) as new modules to prove the interface generalizes — including a `removed` path.
3. **Extract the shared engine** into its own package once the interface survives step 2; template keeps manifest + feature definitions; the five-mode integration matrix becomes the tool's test fixture (this test suite is the most valuable asset here — the extraction must keep it intact, including the manifest-drift CI checks, which become "template CI invokes the tool's drift checker").

The main risk to watch: over-generalizing the engine before a second consumer
exists. The feature-module interface should be exactly as expressive as
POST_INIT.md's real feature list requires, no more.

---

# Part 2 — Second Analysis: Mental Models, Diagrams &amp; Alternatives

> Emphasis: clarity and easy consumption, without skipping the details that
> drive the design choices. The stated goal is **results** — something simple,
> easy, but that works well.
>
> - **Init**: take the template and update all the references. Not making
>   choices — just deterministically updating references into place,
>   maintainable, kept in sync, with checks.
> - **Post-init**: the harder piece. A bunch of choices that may change files,
>   remove files, and have supporting actions (run things to make life easy —
>   set up GitHub variables/secrets, help open and log in to services, give
>   instructions for creating accounts or getting tokens). People don't know
>   what's there and it's hard to set up; there's a lot of mental fatigue. Make
>   both easy. Post-init may even warrant a TUI mode and an agent mode.

## The two systems at a glance

They're different *shapes* of program, and that's the most important thing to
internalize:

```
              ┌──────────────────────────────────────────────┐
              │       py-launch-blueprint (a working repo)   │
              └──────────────────────────────────────────────┘
                     │                            │
        no choices,  │                            │  all choices,
        run once     ▼                            ▼  run many times
          ┌────────────────────┐      ┌────────────────────────┐
          │        INIT        │      │       POST-INIT        │
          │   "make it yours"  │      │      "set it up"       │
          │                    │      │                        │
          │  rewrite every     │      │  pick features, wire   │
          │  reference, exactly│      │  services, run errands,│
          │  once, verifiably  │      │  remove what you skip  │
          └────────────────────┘      └────────────────────────┘
             compiler-shaped              concierge-shaped
```

**Init is a compiler**: same inputs always produce the same output, and a
checker proves nothing was missed. **Post-init is a concierge**: it knows
everything that *could* be set up, asks what you want, does what a machine can
do, and hands you precise errand cards for the rest.

---

## Part 2A — INIT: the compiler

### Mental model: a pure function with a receipt

```
   identity answers              manifest ("what to touch")
   ┌───────────────┐           ┌──────────────────────────────┐
   │ package_name  │           │ [[replace]]  ~209 hits/57 f  │
   │ repo_name     │           │ [[rename]]   src/ directory  │
   │ app_name      │     +     │ [[remove]]   blueprint-only  │
   │ author, email │           │ [[reset]]    CHANGELOG stub  │
   │ owner         │           └──────────────────────────────┘
   └───────────────┘                        │
          └───────────────┬─────────────────┘
                          ▼
                   ┌─────────────┐   deterministic:
                   │ build plan  │   same inputs → same plan,
                   └──────┬──────┘   every time (--dry-run shows it)
                          ▼
                   ┌─────────────┐
                   │    apply    │   remove → replace → rename → reset
                   └──────┬──────┘
                          ▼
              marker file = the receipt
              (records exactly what answers were applied)
```

This already exists in the repo (`init/manifest.toml` + `_engine.py`). The
design question for init isn't the pipeline — it's **how the manifest stays
true as the template evolves**. That's the "keep it in sync and have checks"
part, and it's the loop below:

```
   template evolves                    manifest
   (new doc mentions "plbp")           (doesn't know yet)
        │                                   │
        ▼                                   ▼
   ┌─────────────────────────────────────────────────────┐
   │ CI DRIFT CHECK (every PR):                          │
   │   scan whole repo for each identity string;         │
   │   every occurrence must be claimed by the manifest, │
   │   per field — unclaimed hit  →  CI fails            │
   └─────────────────────────────────────────────────────┘

   ⇒ the manifest can never silently rot.
     Reality is re-derived on every change.
```

This is the load-bearing invariant. Everything else about init is replaceable;
this check is what makes it *maintainable*.

### Four alternative mental models for init

```
A) WORKING REPO + MANIFEST (current)   B) PLACEHOLDER TEMPLATE (cookiecutter/copier)
   ───────────────────────────            ──────────────────────────────
   repo contains real strings:            repo contains jinja:
     "py_launch_blueprint"                  "{{ package_name }}"
   manifest records where they live       placeholders ARE the manifest
   ✓ template runs/tests itself           ✗ template can't run itself —
   ✓ contributors work on real code         every CI check needs a
   − needs the drift check                  render-then-test pipeline

C) INDIRECTION (single source)         D) BLIND SEARCH-AND-REPLACE
   ───────────────────────────            ──────────────────────────────
   identity defined in ONE file;          sed -i 's/old/new/' across repo
   code reads it at run/build time;       ✓ trivially simple
   init edits one file                    ✗ no scoping: rewrites prose,
   ✓ almost nothing to keep in sync         upstream URLs, things that
   ✗ can't reach places where               should stay; no way to know
     literals are required:                 what it missed
     pyproject name, dir names,
     workflow YAML, badges, docs
```

The honest framing: **A is just D plus a memory and a conscience.** It does the
same string surgery, but the manifest scopes it (no false positives) and the
drift check proves completeness (no false negatives). B is the
industry-standard answer, and it forfeits the template's defining property —
that it's a permanently green, runnable project. C is worth using
*opportunistically* (P01 already did this: derive internals like env-var
prefixes from one constant, so the manifest shrinks) but can never cover the
whole surface.

**Verdict on init**: the model in place is the right one, and it's essentially
finished. The remaining work is making it *boringly* solid — shrink the
manifest via C-style derivation where possible, keep the drift check strict,
and optionally extract the engine later. Results-wise, init should be invisible:
run once, doctor says clean, done.

---

## Part 2B — POST-INIT: the concierge

### What a "feature" really is

Every feature in POST_INIT.md decomposes the same way. This anatomy is the core
unit of the whole design:

```
   ┌─ FEATURE: Codecov ─────────────────────────────────────────┐
   │                                                            │
   │  decision:   use it?   yes / no / later                    │
   │                                                            │
   │  if yes ──►  LOCAL    gate the upload step in ci.yml       │
   │              MANUAL   create account, copy token   ◄── the │
   │              REMOTE   gh secret set CODECOV_TOKEN     pain │
   │              CHECK    secret set? upload step green?       │
   │                                                            │
   │  if no  ──►  LOCAL    strip upload step, badge, config     │
   │              (sub-questions never asked: token? flags?)    │
   │                                                            │
   │  if later ─► nothing touched; stays on the board as open   │
   └────────────────────────────────────────────────────────────┘
```

Three kinds of work fall out of every decision, and they have fundamentally
different automation properties:

```
   LOCAL    edit / move / delete repo files     machine, always
   REMOTE   gh API: secrets, environments,      machine, when authed
            repo settings
   MANUAL   create the account, click the       human errand —
            consent screen, copy the token      a machine can only
            from a dashboard                    INSTRUCT and VERIFY
```

That last line is the crucial insight for "mental fatigue": **manual steps
can't be automated, but they can all be *checked*.** PyPI's API can confirm the
project exists; `gh` can confirm the secret is set; a CI run confirms the
upload worked. So if every task carries a check, the system never asks a human
to remember where they left off — status is recomputed from reality every time
you open it.

### The decision graph (why choices have shape)

Decisions aren't a flat list — they're a shallow tree, and "no" prunes branches:

```
  publish to PyPI? ──yes─┬─ mirror to TestPyPI?        (sub-decision)
                         ├─ release-please bumps?      (sub-decision)
                         └─ OIDC trust on pypi.org     [manual errand]
                  └─no──►  remove publish.yml + release-please
                           ▲ sub-questions never asked; their
                             tasks never exist on the board

  coverage? ───────yes─┬─ Codecov account              [manual errand]
                       └─ CODECOV_TOKEN secret         [remote]
            └──no────►   strip upload step + badge

  docs hosting? ──RTD──► import walkthrough            [manual errand]
               └─no───►  keep local docs build only
```

And the answer to any decision lands the feature in a small state machine:

```
                  ┌──────────┐
          ┌──────►│ deferred │   default: "ask me later" —
          │       └────┬─────┘   zero cost to postpone
          │            │ decide
          │      ┌─────┴──────┐
          │      ▼            ▼
     ┌────┴─────────┐   ┌─────────────┐
     │   enabled    │◄─►│   dormant   │   reversible: workflow
     │ (wired, on)  │   │ (.disabled/)│   files moved, not deleted
     └──────┬───────┘   └──────┬──────┘
            └────────┬─────────┘
                     ▼
            ┌─────────────────┐    one-way: files deleted,
            │     removed     │    always behind a shown plan
            │ (confirm gate)  │    + confirmation; sub-decisions
            └─────────────────┘    collapse to n/a forever
```

Today's system has `enabled / dormant / deferred` but conflates "no" with
"dormant." Splitting **dormant** (reversible, cheap) from **removed**
(destructive, deliberate) is what makes the cleanup path safe instead of scary.

### Four architectures for post-init — the real alternatives

```
1) WIZARD (what you have today)
   ───────────────────────────
   Q → act → Q → act → Q → act → done
   ✓ dead simple, low fatigue on first run
   ✗ asking and doing are interleaved — quit halfway, you're nowhere
   ✗ re-run = replay the interview
   ✗ agents can't drive it (no config in, no machine status out)

2) CHECKLIST / TASK RUNNER (POST_INIT.md, formalized)
   ──────────────────────────────────────────────────
   flat list of tasks, each with a status; tick them off
   ✓ great visibility — you can SEE the whole setup surface
   ✗ no decision layer: tasks for features you'll never use
     still clutter the board
   ✗ status is whatever was stored — drifts from reality

3) RECONCILER (terraform-shaped)
   ─────────────────────────────
   decisions.toml = desired state; engine diffs vs reality, converges
   ✓ perfect for LOCAL + REMOTE work; idempotent; agent-native
   ✗ awkward for MANUAL work — you cannot "converge" a human
     creating a Codecov account; the model has no place for errands

4) HYBRID: decide → derive board → work the board   ★ recommended
   ────────────────────────────────────────────────
   decisions (declarative)  +  per-feature task defs (with checks)
   engine derives the task board; checks compute status from
   reality; machine tasks auto-apply; manual tasks become
   errand cards
```

The hybrid in one picture:

```
   decisions.toml             feature definitions
   (your choices —            (ship with the template:
    yes/no/later/remove)       actions + checks per feature)
        │                          │
        └────────────┬─────────────┘
                     ▼
          ① derive the task board      ← "no" prunes tasks entirely
                     │
                     ▼
          ② run every check against reality
             (repo files · gh api · pypi api)
                     │
                     ▼
        ┌────────────────────────────────┐
        │           THE BOARD            │
        │  ✓ done   ◌ todo   ⊘ n/a       │
        │  ⚠ needs-human   ✗ broken      │
        └───────────┬──────────┬─────────┘
                    │          │
                    ▼          ▼
          ③ apply machine   ④ present errand
             tasks             cards (manual)
             (local+remote)
                    │          │
                    └────┬─────┘
                         ▼
            re-check → board updates → repeat until ✓
```

Why hybrid beats pure reconciler *for this problem*: roughly half the real pain
(accounts, tokens, consent screens) is human-paced. A reconciler pretends that
work doesn't exist; a checklist pretends decisions don't exist. The hybrid
keeps the reconciler's best property — **status is always computed, never
remembered** — while giving manual work a first-class home.

### What the TUI could be

The shape of the TUI follows from the model. First run is an **interview**
(lowest fatigue: linear questions, sensible defaults, "later" always
available). Every run after that is a **dashboard** — because the
second-session question is never "ask me everything again," it's "where was I?":

```
 ┌─ my-project · setup board ──────────────────── checks: 4s ago ─┐
 │                                                                │
 │  Publishing            ● enabled        2 of 4 done            │
 │    ├ publish.yml wired           ✓                             │
 │    ├ release-please wired        ✓                             │
 │    ├ PyPI OIDC trust             ⚠ needs you      [enter]      │
 │    └ TestPyPI trust              ◌ blocked by ↑                │
 │                                                                │
 │  Coverage · Codecov    ◐ deferred        [enter] to decide     │
 │  Docs · ReadTheDocs    ○ dormant         re-enable anytime     │
 │  Branch protection     ◌ not asked       [enter] to decide     │
 │  Funding / sponsors    ⊘ removed                               │
 │                                                                │
 │  [a]pply machine tasks   [r]efresh checks   [q]uit             │
 └────────────────────────────────────────────────────────────────┘
```

Pressing enter on a ⚠ opens an **errand card** — the direct attack on "people
don't know what's there and it's hard to set up":

```
 ┌─ PyPI trusted publishing (manual, ~3 min) ──────────────────┐
 │                                                             │
 │  1. open  https://pypi.org/manage/account/publishing/      │
 │  2. fill the form with EXACTLY these values:                │
 │       project   my-project                                  │
 │       owner     myorg        repo      my-project           │
 │       workflow  publish.yml  env       pypi                 │
 │  3. submit                                                  │
 │                                                             │
 │  verify: polling pypi.org for the publisher… ⠋              │
 │  (this card closes itself when it sees it)                  │
 └─────────────────────────────────────────────────────────────┘
```

Notice what the card does: opens the page for you, pre-computes every value
you'd otherwise hunt for, and verifies completion itself. That's the concierge
promise — the human only does the parts that genuinely require a human.

### Agent mode: same engine, second face

```
              ┌────────────── core engine ───────────────┐
              │  decisions · board · checks · apply      │
              └───────┬──────────────────────┬───────────┘
                      │                      │
               TUI frontend            CLI / JSON frontend
               (human)                 (agent)
               interview, dashboard,   setup status  --json
               errand cards            setup decide  --set codecov=yes
                                       setup apply   --json
                                       setup check   (exit code = board state)
```

An agent's session: read `status --json`, set or confirm decisions, run `apply`
(all local + remote tasks), then report back the remaining ⚠ errands as a short
human checklist with the pre-computed values inlined. The agent becomes the
concierge's clerk — it does everything automatable and writes you a perfect
errand list for the rest. No TUI scraping, no parallel logic.

---

## Side by side (the two shapes)

| | INIT | POST-INIT |
|---|---|---|
| Shape | compiler | concierge |
| Choices | none — just your identity | all of them, with sub-decisions |
| Runs | once, then prunes itself | open-ended, until board is ✓ |
| Hard part | staying in sync with the template (→ drift check) | manual errands + decision pruning (→ checks + board) |
| State | receipt of what was applied | computed live from reality |
| "Done" looks like | doctor clean, zero blueprint strings | board all ✓/⊘, no ⚠ left |

## What "simple, easy, works well" means concretely

Ranked by how much each choice buys you:

1. **Every task has a check; status is computed, never stored.** This single rule eliminates the "where was I / what's left" fatigue and is what makes re-runs and agent mode trivial.
2. **Decisions are separate from actions.** The choices live in one small declarative file; the consequences are derived. "No" prunes whole subtrees so you never see questions or tasks that can't matter.
3. **Local / remote / manual are honestly different.** Don't pretend errands are automatable — give them cards with pre-computed values and self-closing verification instead.
4. **Dormant ≠ removed.** Cheap reversible "off" by default; destructive cleanup only behind a shown plan and confirmation.
5. **Init stays exactly the compiler it is.** Its model is already right; invest there only in shrinking the manifest and keeping the drift check ruthless.

---

# Part 3 — Synthesis &amp; Recommendations

> **Status update (2026-06-12):** these recommendations were reviewed and
> accepted. The concrete decision record — engine name (**template-press**),
> the `press/` directory and config-file contracts, the core/TUI/CLI-JSON
> architecture, and the phased migration map — lives in
> [design doc 0004 — Template Press plan](../design/0004-template-press-plan.md).

## The one-sentence model

**Init is a compiler** (deterministic template→project rewrite, kept honest by
a drift check) and **post-init is a concierge** (decisions → a live task board
where machines do machine-work and humans get pre-filled, self-verifying errand
cards).

## Four artifacts per pipe

| Artifact | Init (status) | Post-init (status) |
|---|---|---|
| **Schema** | `manifest.toml` ✅ exists | feature/decision graph ⛔ to build |
| **Config** | `answers.toml` ✅ exists | `decisions.toml` ⛔ to build |
| **Plan** | `build_plan()` ✅ exists | plan stage ⛔ to build |
| **State** | marker `[answers]` ✅ exists | marker `[post_init.*]` ◐ partial |

## Recommended architecture

- **One package, two entry points** (`init` + `setup`/`post-init`), strict layering: a pure core (schema→questions, config+state→plan, plan→effects) under two thin frontends (TUI for humans, CLI/JSON for agents).
- **Post-init = hybrid model** (decide → derive board → work the board), not pure wizard, checklist, or reconciler.
- **Three action classes** — `local` (always automatable), `remote` (automatable when authed), `manual` (instruct + verify only).
- **Four-state feature lifecycle** — `deferred → enabled ⇄ dormant → removed`, with `removed` one-way behind a confirm gate.
- **Status is computed from reality**, never just stored — every task carries a check.

## Suggested phasing

1. **Formalize post-init in place** — split `post_init.py` into schema/generator/engine modules mirroring init; add `--config decisions.toml` headless mode and a real plan stage. Makes it agent-drivable with zero extraction risk.
2. **Define the feature-module interface** — migrate the existing three features (publishing, codecov, RTD) onto it; then absorb 2–3 manual POST_INIT.md items (dependabot, funding, CodeQL) — including a `removed` path — to prove it generalizes.
3. **Extract the shared engine** into its own package once the interface survives step 2; template keeps `manifest.toml` + feature definitions; the five-mode integration matrix + manifest-drift checks become the tool's test fixtures (and must be preserved intact).

## Risks to watch

- **Over-generalizing the engine** before a second consumer exists — keep the feature-module interface exactly as expressive as POST_INIT.md's real feature list demands, no more.
- **Drifting toward copier** — a generic "manifest-driven repo rewriter" reinvents copier; the deliberate difference is that the blueprint is a *working, testable repo*, not a Jinja skeleton. Preserve that property. Borrow copier's `copier.yml` conditional-question conventions for the decision-graph schema only.
- **Two-projects-too-early** — the extraction *seam* (declarative files in, plans out) is what matters; the repo boundary is cheap to add later and expensive to coordinate prematurely.
