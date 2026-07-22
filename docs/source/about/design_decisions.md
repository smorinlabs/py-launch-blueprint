# Design Decisions

This is the exhaustive, narrative map of **every deliberate tool, library, and
configuration choice** in Py Launch Blueprint — what each choice is, why it was
made, and what value it brings to the project and to anyone who builds on the
template.

## How to read this document

Py Launch Blueprint already keeps three kinds of authoritative engineering
records (see [`docs/README.md`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/README.md)):

- **ADRs** ([`docs/adr/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr)) —
  one significant decision each (context → choice → consequences), immutable
  once accepted.
- **Design specs** ([`docs/design/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design)) —
  normative "how it must behave" specifications, including the `WEB-xx` web-API
  catalog and the `HEX-xx` architecture rules.
- **Research notes** ([`docs/research/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/research)) —
  explorations that fed the decisions above.

**This page does not replace those records — it indexes them.** It walks every
decision thematically so a reader can understand the whole system in one pass,
and each entry links out to the artifact that *owns* the decision. Where a
decision is captured only in a config file, the entry links the config.

Each entry uses the same compact shape:

> **The decision (short title)**
> **What** — the concrete choice.
> **Why** — the rationale, and the alternative it displaced.
> **Value** — what it buys the project and its users.
> **Refs** — the in-repo artifact(s) that own or implement it.

**A note on the IDs.** Inline markers like `ADR-05`, `ITM-046`, `WL-001`,
`WEB-11`, and `HEX-30` are internal tracking IDs. `ADR-xx`, design docs, and the
`WEB-xx`/`HEX-xx` catalogs resolve to files in this repository (linked on first
use). `ITM-xx` (item) and `WL-xx` (wishlist) IDs are the maintainer's planning
identifiers; they are cited as provenance to show how granular the planning was,
but they are not standalone documents.

---

## 1. Language & runtime

### Python 3.12 minimum
**What** — `requires-python = ">=3.12"`; `.python-version` pins `3.12` for
pyenv/mise.
**Why** — 3.12 brings faster startup, better error messages, and modern typing
(`type` statement, `Self`, PEP 695 generics) without back-compat shims. A high
floor keeps the codebase free of version-gated branches.
**Value** — every example uses current idioms; contributors never debug
behaviour that only reproduces on an old interpreter.
**Refs** — `pyproject.toml [project]`, `.python-version`; ITM-033.

### Tested on 3.12 **and** 3.13
**What** — the CI test matrix runs both 3.12 and 3.13.
**Why** — a template is adopted across environments; proving the next minor
works prevents "works on my machine" upgrades.
**Value** — adopters can move to 3.13 with evidence, not hope.
**Refs** — `.github/workflows/ci.yml`; ITM-030.

---

## 2. Code structure & architecture

### `src/` layout
**What** — the package lives at `src/py_launch_blueprint/`, declared via
`[tool.uv.build-backend] module-root = "src"`.
**Why** — the `src/` layout forces tests to run against the *installed* package,
not the working tree, catching packaging mistakes (missing files, bad imports)
that a flat layout hides until release.
**Value** — "it imports in CI" means "it imports for users."
**Refs** — `pyproject.toml`; ITM-074.

### Hexagonal core (ports & adapters)
**What** — business logic lives in `core/`; `cli/` and `web/` are front-end
adapters; a `composition/` root wires them together. Dependencies point inward.
**Why** — a template should demonstrate an architecture that scales past a single
script. Isolating the core from frameworks keeps the domain testable and lets a
fork swap or add a front end (CLI today, web tomorrow) without rewriting logic.
**Value** — adopters inherit a structure that stays maintainable as the project
grows, instead of a god-module that has to be untangled later.
**Refs** — [ADR-0017](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0017-hexagonal-core-and-boundary-enforcement.md),
[design 0005](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0005-hexagonal-architecture-and-enforcement.md) (`HEX-xx`).

### Mechanical boundary enforcement with `import-linter`
**What** — `lint-imports` enforces five contracts: core never imports a
front-end; CLI and web are mutually independent; the composition root is never
imported by core; core layers run `models < services < adapters`; and core
imports no web/CLI frameworks (`fastapi`, `click`, `uvicorn`).
**Why** — architecture documented in prose erodes; architecture checked by a
tool does not. import-linter reads the actual import graph.
**Value** — the hexagonal boundaries above are *guaranteed*, not aspirational —
a violating import fails the pre-push hook and CI.
**Refs** — `pyproject.toml [tool.importlinter]`, `lefthook.yml`; HEX-30.

### Bounded-context isolation with `tach`
**What** — `tach.toml` declares each module's allowed dependencies
(`core → root`, `composition → core`, `cli/web → composition, core, root`).
**Why** — import-linter guards layering; tach guards *module ownership*, a
second, differently-shaped check on the same intent.
**Value** — defence in depth against accidental coupling between subsystems.
**Refs** — `tach.toml`; HEX-31.

### Framework-bleed guard via Ruff `TID251`
**What** — a fast Ruff rule blocks framework imports inside `core/` at
pre-commit time.
**Why** — import-linter and tach run at pre-push/CI; a Ruff rule gives the same
feedback in milliseconds while you type.
**Value** — the most common boundary mistake is caught at the earliest, cheapest
moment.
**Refs** — `pyproject.toml [tool.ruff]`; HEX-32.

### Pydantic result models with a rich-only row variant
**What** — command results are Pydantic models that serialize to JSON and also
expose a `.row()` variant for Rich-formatted terminal tables.
**Why** — one model serves both the machine contract (JSON) and the human view
(tables) without duplicating field definitions.
**Value** — JSON output and pretty output can never drift apart.
**Refs** — [ADR-0010](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0010-rich-row-variant-on-result-models.md).

---

## 3. Dependency management & build

### `uv` for dependencies and environments
**What** — `uv` manages the virtualenv, resolves dependencies, and writes
`uv.lock`. The canonical sync is `uv sync --group dev --extra web`.
**Why** — uv resolves and installs ~10–100× faster than pip/poetry and produces a
fully-pinned cross-platform lockfile, so local and CABA environments match.
**Value** — fresh-clone setup takes seconds; "dependency hell" is replaced by a
reproducible lock.
**Refs** — `pyproject.toml`, `uv.lock`, `Justfile`.

### `uv_build` as the build backend
**What** — `[build-system] build-backend = "uv_build"` (constrained
`>=0.5,<1.0`); `uv build` produces the wheel and sdist.
**Why** — using uv's own backend keeps build and dependency tooling in one
project, replacing the previous Hatchling + hatch-vcs stack.
**Value** — one tool, one mental model, fewer moving parts at release time.
**Refs** — [ADR-0006 (build backend)](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0006-stable-error-codes-hints-crash-log.md)
note in AGENTS.md (ADR-06); ITM-073.

### PEP 735 dependency-groups, not extras, for tooling
**What** — `dev` and `docs` are PEP 735 `[dependency-groups]`; only *runtime*
optionals (`web`, `otel`) are `[project.optional-dependencies]` extras.
**Why** — dev/doc tooling is not part of the published package's optional
feature set; PEP 735 groups model "local-only" dependencies correctly and are
installable with `uv sync --group`, never shipped to PyPI consumers.
**Value** — `pip install py-launch-blueprint[web]` pulls real features;
`pip install '.[dev]'` is intentionally *not* the path — dev deps stay out of the
distribution.
**Refs** — `pyproject.toml`; ITM-063.

### Static version, bumped by automation
**What** — `[project] version` is a literal string; release-please edits it.
**Why** — a static version makes package metadata predictable and removes the
runtime cost and failure modes of VCS-derived versions.
**Value** — what the file says is what PyPI ships; no surprises.
**Refs** — `pyproject.toml`, `release-please-config.json`; ADR-06.

### PEP 639 license expression
**What** — the license is declared as the SPDX expression `MIT`, not via
classifiers.
**Why** — PEP 639 is the modern, machine-readable way to express licensing;
classifiers are legacy and ambiguous.
**Value** — tooling reads the license deterministically.
**Refs** — `pyproject.toml`; ITM-070.

### Locked tool versions — never floating `uvx`
**What** — every hook/CI tool (ruff, bandit, codespell, …) runs via `uv run`
from the locked `dev` group, never `uvx`.
**Why** — `uvx` fetches the latest version at runtime, so a local hook and CI
can silently disagree. Running from `uv.lock` pins one version everywhere;
upgrades arrive as reviewable Dependabot PRs.
**Value** — reproducible checks: "passes locally" reliably means "passes in CI."
**Refs** — `lefthook.yml`, workflows, `uv.lock`; WL-001.

### Curated runtime dependencies
**What** — the runtime set is deliberately small: `click` (CLI), `pydantic`
(models), `structlog` (logging), `rich` (terminal), `requests` (HTTP),
`tomli-w` (TOML writes).
**Why** — each is the de-facto best-in-class for its job, and the list is kept
short so the install footprint stays light.
**Value** — adopters start from proven libraries, not a grab-bag.
**Refs** — `pyproject.toml [project.dependencies]`.

---

## 4. Linting & formatting

### Ruff for both linting and formatting
**What** — `ruff check` lints and `ruff format` formats, replacing
flake8 + isort + Black + pyupgrade. Selected rule families: `E`, `F`, `I`, `B`,
`C4`, `UP`, `N`, `RUF`, `W`, `YTT`, `S`.
**Why** — one Rust-based tool, one config table, 10–100× faster, and no
disagreements between separate linters/formatters.
**Value** — near-instant feedback in hooks and editor; fewer dev dependencies.
**Refs** — `pyproject.toml [tool.ruff]`; ITM-018.

### Line length 88
**What** — `line-length = 88` (the Black standard); `E501` is *ignored* by the
linter because the formatter owns wrapping.
**Why** — 88 is the widely-adopted default that balances density and
readability; letting the formatter (not the linter) own line length avoids
double-reporting the same issue.
**Value** — no style debates, no redundant lint noise.
**Refs** — `pyproject.toml [tool.ruff]`; ITM-018.

### Pragmatic per-file ignores
**What** — `__init__.py` ignores `F401` (re-export imports); `tests/**` ignore
`S101/S105/S106` (asserts and test credentials are expected in tests);
`init/**` ignores `S603/S607` (the rebrand engine intentionally shells out).
**Why** — blanket security/lint rules produce false positives in contexts where
the flagged pattern is correct; scoping the ignores keeps the rules strict
everywhere else.
**Value** — high signal: a lint failure almost always means a real problem.
**Refs** — `pyproject.toml [tool.ruff.lint.per-file-ignores]`.

### `flake8-bandit` (`S`) in the linter, plus standalone bandit
**What** — Ruff's `S` family flags insecure patterns inline; bandit runs the
deeper scan at pre-push and in CI.
**Why** — fast inline coverage during editing, thorough coverage before code
leaves the machine.
**Value** — security smells are caught early *and* comprehensively.
**Refs** — `pyproject.toml`; ITM-027.

### TOML formatting with `taplo`
**What** — `taplo` formats and validates TOML (`line-width 80`, aligned entries,
LF endings) via `.taplo.toml`; `just format-toml` and a CI `toml-format` job
enforce it.
**Why** — `pyproject.toml` is load-bearing config; a consistent, validated
layout prevents subtle syntax breakage.
**Value** — config files stay readable and never silently malformed.
**Refs** — `.taplo.toml`, `Justfile`, `.github/workflows/ci.yml`.

### YAML formatting (`yamlfmt`) and linting (`yamllint`)
**What** — `yamlfmt` formats YAML (2-space indent, `.yamlfmt`); `yamllint`
lints it (`.yamllint`, 88-char warning, GitHub-Actions-friendly truthy values).
**Why** — the repo is YAML-heavy (workflows, RTD, config); formatting plus
linting catches both style drift and the indentation bugs that break Actions.
**Value** — workflow YAML failures surface at commit time, not on push.
**Refs** — `.yamlfmt`, `.yamllint`; ITM-012/013/014.

### Spell-checking with `codespell`
**What** — `codespell` checks code, docs, and filenames; configured in
`pyproject.toml` with a curated skip list and a small `ignore-words` set
(including the *intentional* misspelling `porjects` used by a CLI typo
suggestion).
**Why** — typos in identifiers, comments, and docs erode polish and
searchability; an allow-list keeps deliberate misspellings from being "fixed."
**Value** — professional, typo-free output without fighting the tool.
**Refs** — `pyproject.toml [tool.codespell]`; ITM-015/016/017.

### Whitespace/encoding hygiene with EditorConfig + checker
**What** — `.editorconfig` sets UTF-8, LF, final newline, trimmed trailing
whitespace, and per-type indents (4 for Python, 2 for YAML/JSON/TOML, tabs for
`Makefile`); `editorconfig-checker` enforces it in hooks and CI. Markdown and
syrupy `.ambr` snapshots deliberately *preserve* trailing whitespace.
**Why** — consistent baseline formatting across every editor; indentation
checks are disabled where Ruff/taplo/yamlfmt already own them, avoiding
conflicts.
**Value** — no noisy whitespace diffs; `Makefile` tabs and Markdown hard-breaks
survive contributors' editors.
**Refs** — `.editorconfig`, `.editorconfig-checker.json`; ITM-008/009/010/011.

---

## 5. Type checking

### `ty` (Astral) in CI
**What** — `ty check src/py_launch_blueprint/` is the type gate; it runs with
`--extra web` so web imports resolve.
**Why** — `ty` is a fast Rust-based checker from the makers of Ruff/uv, keeping
the toolchain coherent and the gate quick. The `--extra web` flag is required so
the optional web package's imports type-check.
**Value** — a fast, single-vendor quality stack; type regressions block merges.
**Refs** — `Justfile`, `.github/workflows/ci.yml`; ADR-03 (per AGENTS.md), ITM-026.

### Pyright (strict) in the editor
**What** — `pyproject.toml` configures Pyright in strict mode for VS Code.
**Why** — the IDE benefits from Pyright's mature, real-time inference while CI
uses `ty`; strict mode surfaces the maximum signal while editing.
**Value** — type errors appear as you type, long before CI.
**Refs** — `pyproject.toml [tool.pyright]`.

### Strict typing as a project norm
**What** — all library functions are fully typed; test files may omit
annotations.
**Why** — types are documentation and a correctness check for the shipped code;
tests value brevity over ceremony.
**Value** — the public surface is self-documenting and refactor-safe.
**Refs** — AGENTS.md "Code style".

---

## 6. Testing

### `pytest` as the framework
**What** — `pytest` with `pytest-cov`; tests live in `tests/`.
**Why** — the de-facto standard: fixtures, parametrization, a vast plugin
ecosystem.
**Value** — contributors already know it; tests stay concise.
**Refs** — `pyproject.toml [tool.pytest.ini_options]`.

### `slow` / `live` marker taxonomy with default exclusion
**What** — two markers (`slow` = >1s, `live` = needs external services);
`addopts` excludes both by default (`-m "not live and not slow"`).
`strict_markers` is on, so unknown markers error.
**Why** — the default `pytest` run must be fast and offline so the inner loop and
hooks stay snappy; the heavy suites still run explicitly (`pytest -m ""`) and in
full CI.
**Value** — sub-second local test runs, with full coverage still gated before
merge.
**Refs** — `pyproject.toml`; ITM-046.

### Coverage gates via Codecov
**What** — `.codecov.yml` sets a project target of `auto` with a 1% threshold
and a patch target of 80% on changed lines; coverage uploads via OIDC from the
ubuntu/3.12 job only.
**Why** — comparing against the base branch (auto) with a small tolerance avoids
flaky failures from coverage noise, while the 80% patch gate holds *new* code to
a high bar. Uploading from one matrix cell prevents double-counting.
**Value** — coverage can't quietly rot, and PRs are judged on the lines they
touch.
**Refs** — `.codecov.yml`, `.github/workflows/ci.yml`; WL-005.

### Snapshot testing with `syrupy`
**What** — CLI output and the OpenAPI document are asserted against committed
`.ambr` snapshots.
**Why** — golden snapshots catch unintended output changes (formatting, field
order) that assertion-by-assertion tests miss.
**Value** — the human-facing output contract is locked and reviewed as a diff.
**Refs** — `pyproject.toml` (`syrupy` dev dep), `.editorconfig`; WL-023.

### Contract fuzzing with `schemathesis`
**What** — `schemathesis` fuzzes every documented web operation (marked `slow`),
currently asserting "no 5xx."
**Why** — generated test cases probe edge inputs no hand-written test would,
verifying the API matches its own schema.
**Value** — the web service is hardened against malformed input automatically.
**Refs** — `tests/web/`, `pyproject.toml`; WEB-50.

### Cross-platform, cross-version matrix
**What** — CI runs the suite on ubuntu/macOS/windows × Python 3.12/3.13.
**Why** — a template is cloned everywhere; path handling, line endings, and
interpreter quirks must be proven across OSes and versions.
**Value** — broad compatibility is evidence-backed.
**Refs** — `.github/workflows/ci.yml`; ITM-030.

---

## 7. Pre-commit / git hooks

### `lefthook` as the hook manager
**What** — `lefthook` (min version pinned) runs git hooks; `just setup` /
`just hooks-install` wires them.
**Why** — lefthook is fast, parallelizes tasks, and configures cleanly in one
YAML file — chosen over the Python `pre-commit` framework to avoid a second
Python env just for hooks.
**Value** — quality gates fire automatically with minimal overhead.
**Refs** — [ADR-0001-era hook decisions](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr) (ADR-01 per AGENTS.md),
`lefthook.yml`; ITM-021.

### Three hook stages, fastest-first
**What** — **commit-msg** runs commitlint; **pre-commit** (parallel) runs
gitleaks-staged, editorconfig-checker, yamllint, codespell, and ruff
check/format on staged files; **pre-push** (parallel) runs a gitleaks range
scan, bandit, import-linter, and the init-system integrity checks.
**Why** — cheap, high-frequency checks belong at commit time; slower, broader
checks (security scan, architecture, full secret range) run once per push.
**Value** — fast commits, with heavier guarantees before code ever leaves the
machine.
**Refs** — `lefthook.yml`; ITM-001/002/032/040/066.

### Hooks operate on staged files only
**What** — pre-commit tools receive `{staged_files}` and use `--force-exclude`.
**Why** — checking only what's staged keeps commits fast and avoids flagging
unrelated work-in-progress.
**Value** — the hook cost scales with your change, not the repo size.
**Refs** — `lefthook.yml`.

### Hooks are no-ops until installed — and the docs say so
**What** — a fresh clone has no wired hooks until `just setup` runs; AGENTS.md
flags this explicitly and lists the manual checks to run otherwise.
**Why** — git can't enforce hooks that aren't installed; silent no-ops are a
known footgun, so the workflow calls it out.
**Value** — contributors (and agents) know to run setup or check manually,
instead of assuming protection they don't have.
**Refs** — `lefthook.yml`, AGENTS.md.

---

## 8. Security

### Secret scanning at two depths: gitleaks (local) + TruffleHog (CI)
**What** — gitleaks scans the staged diff at commit and the push range at
pre-push (`.gitleaks.toml`, with allow-listed AWS *example* keys); TruffleHog
re-scans in CI in `--only-verified` mode.
**Why** — local scanning stops a secret before it's committed; verified CI
scanning catches anything that slipped past and confirms it's a *live*
credential, minimizing false alarms.
**Value** — layered protection against credential leaks with low noise.
**Refs** — `.gitleaks.toml`, `scripts/check-gitleaks.sh`,
`.github/workflows/secret-scan.yml`; ADR-02 (per AGENTS.md), ITM-001/002/031.

### Secrets never live in config files
**What** — the API token resolves only from `--token` or `$PLBP_TOKEN`;
`config set/get` operate on non-secret keys only.
**Why** — config files get committed, shared, and backed up; keeping secrets in
env/flags only removes the most common leak vector by design.
**Value** — users can't accidentally commit a token through normal config use.
**Refs** — [ADR-0002](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0002-no-secrets-in-config-file.md).

### `bandit` static security analysis
**What** — bandit scans `src/` at pre-push and in CI; configured in
`pyproject.toml` (tests/init excluded, no rule skips).
**Why** — bandit catches insecure Python patterns (shell injection, weak
crypto, unsafe deserialization) that linters don't; running it pre-push keeps
commits fast.
**Value** — a security regression is blocked before it can merge.
**Refs** — `pyproject.toml [tool.bandit]`, `lefthook.yml`,
`.github/workflows/lint.yml`; ITM-027/032.

### `CodeQL` semantic analysis
**What** — CodeQL runs the `security-extended` query suite on Python (push, PR,
and weekly schedule), config in `.github/codeql/codeql-config.yml`.
**Why** — CodeQL's taint-tracking finds data-flow vulnerabilities that
pattern-based tools miss; the scheduled run catches issues in code that isn't
changing.
**Value** — deep, continuous vulnerability detection.
**Refs** — `.github/workflows/codeql.yml`; ITM-034/035/036.

### Dependency CVE auditing
**What** — `dependency-review` comments on PRs that introduce vulnerable deps; a
weekly `pip-audit` job (`just audit`) audits the full locked set across all
extras/groups.
**Why** — vulnerabilities appear in dependencies you already shipped; scheduled
auditing catches newly-disclosed CVEs, and PR review stops new ones entering.
**Value** — known-vulnerable dependencies are caught both at introduction and
over time.
**Refs** — `.github/workflows/dependency-review.yml`,
`.github/workflows/dep-audit.yml`, `Justfile`; WL-014.

### Large-file guard
**What** — a workflow rejects new files >1 MB outside `docs/assets/`.
**Why** — accidental binary commits bloat history permanently and are painful to
excise.
**Value** — repo history stays lean and clone-fast.
**Refs** — `.github/workflows/large-file-guard.yml`; ITM-028.

### Least-privilege workflow permissions
**What** — workflows default to `permissions: {}` and grant the minimum per job
(`contents: read`, `id-token: write` only where OIDC is needed, etc.).
**Why** — the GitHub token is powerful by default; explicit, scoped grants limit
the blast radius if a workflow or action is compromised.
**Value** — supply-chain hardening with no functional cost.
**Refs** — `.github/workflows/*`.

---

## 9. CI/CD

### GitHub Actions as the CI platform
**What** — all automation runs in `.github/workflows/` — test/lint/typecheck,
security, contract, release, publish, and init-integration workflows.
**Why** — native to GitHub, no external service to configure, first-class OIDC
support for keyless publishing.
**Value** — zero-setup CI that adopters inherit working.
**Refs** — `.github/workflows/`.

### Docs-only change detection
**What** — a `changes` job classifies a diff as code vs docs and gates the heavy
jobs (typecheck, test matrix) so doc-only PRs skip them.
**Why** — running the full matrix for a typo fix wastes minutes and CI minutes.
**Value** — fast feedback on docs PRs; lower CI cost.
**Refs** — `.github/workflows/ci.yml`; WL-019.

### A single aggregate required check (`ci-ok`)
**What** — a `ci-ok` job depends on all CI jobs and is the one check required by
branch protection.
**Why** — required-check lists tied to individual matrix cells break whenever
the matrix changes; one aggregate gate is stable and still fails if any job
fails.
**Value** — branch protection that doesn't need editing every time CI evolves.
**Refs** — `.github/workflows/ci.yml`; WL-006.

### `build-smoke`: prove the package installs
**What** — CI runs `uv build`, `twine check`, then installs the wheel and sdist
and runs the CLI.
**Why** — a passing test suite doesn't prove the *distribution* is installable;
smoke-installing the artifacts does.
**Value** — broken packaging is caught before release, not by users.
**Refs** — `.github/workflows/ci.yml`; WL-004.

### Workflow linting with `actionlint`
**What** — `actionlint` (with shellcheck) lints the workflow files themselves,
skipped when no workflow changed.
**Why** — workflow YAML and its embedded shell are easy to get subtly wrong;
linting them catches errors before a broken run.
**Value** — CI that checks its own CI.
**Refs** — `.github/workflows/lint.yml`; ITM-029.

### Documentation build is a gate
**What** — CI builds the Sphinx docs with warnings-as-errors (using the `web`
extra so autodoc imports resolve); a weekly link-check validates external links.
**Why** — broken docs are a real regression; failing on warnings keeps the
published site clean, and scheduled link-checking catches link rot.
**Value** — the docs that ship always build and (mostly) link correctly.
**Refs** — `.github/workflows/ci.yml`, `.github/workflows/dep-audit.yml`; WL-021.

---

## 10. Commit conventions

### Conventional Commits, enforced
**What** — commit messages follow Conventional Commits with a lowercase subject;
commitlint enforces it at the commit-msg hook and in CI.
**Why** — a structured history is what lets release-please derive versions and
changelogs automatically; the convention is checked so it can be relied upon.
**Value** — the entire release pipeline (next section) becomes possible.
**Refs** — `commitlint.config.mjs`, `.github/workflows/commitlint.yml`,
`lefthook.yml`; ADR-04 (per AGENTS.md), ITM-037/038/039/040.

### Separate commitlint configs for humans and Dependabot
**What** — `commitlint.config.mjs` caps body/footer lines at 200 chars for
humans; `commitlint.dependabot.config.mjs` lifts the cap for Dependabot's
long URLs.
**Why** — human messages benefit from wrap discipline, but bot messages contain
unbreakable links that would otherwise fail the lint.
**Value** — strict standards for people, no false failures for bots.
**Refs** — `commitlint*.mjs`, `.github/workflows/commitlint.yml`.

### Grouped, scoped Dependabot updates
**What** — Dependabot updates pip/github-actions/npm weekly, grouped (runtime,
dev-tools, lint-and-format, test, …), committing as `chore(deps): …`.
**Why** — grouping reduces PR noise; the `chore(deps)` scope routes updates into
the changelog's dependency section automatically.
**Value** — dependency maintenance is steady, low-noise, and self-documenting.
**Refs** — `.github/dependabot.yml`; ITM-043/061/062.

---

## 11. Release management

### `release-please` drives versioning and changelog
**What** — on every push to `main`, release-please opens/updates a release PR
that bumps `[project] version`, updates the changelog, and tags `v*` on merge.
Sections show feat/fix/perf/refactor/revert/deps; chore/docs/etc. are hidden.
**Why** — automating version bumps and changelog from Conventional Commits
removes manual, error-prone release bookkeeping.
**Value** — releasing is "merge the PR"; the changelog is always accurate.
**Refs** — `release-please-config.json`, `.release-please-manifest.json`,
`.github/workflows/release-please.yml`; ADR-05 (per AGENTS.md), ITM-052/053/054.

### Lockfile stays in sync on the release PR
**What** — release-please's TOML updater changes the editable project entry in
`uv.lock` in the same generated commit that bumps `pyproject.toml`.
**Why** — a follow-up workflow commit left a window where CI and reviewers saw
stale locked metadata. Generating both version surfaces atomically removes that
race while `uv lock --check` remains the independent freshness gate.
**Value** — every revision of a release PR, including the first, has a matching
lockfile; no repair commit or force-push is required.
**Refs** — `release-please-config.json`, `.github/workflows/release-please.yml`;
ITM-054.

### Publishing via OIDC Trusted Publishing
**What** — on a `v*` tag, `publish.yml` verifies the tag is on `main` and that
the tag matches `pyproject.toml`, builds, and publishes to PyPI via OIDC (no
stored token), using a protected `pypi` environment.
**Why** — OIDC Trusted Publishing eliminates long-lived PyPI API tokens — the
single biggest credential-leak risk in a publish pipeline — and the tag/version
guard prevents mismatched releases.
**Value** — keyless, auditable publishing with no secret to leak.
**Refs** — `.github/workflows/publish.yml`; ITM-048/049/050/051.

### Simple `v*` tags
**What** — releases tag plain semver (`v2.2.0`), no component prefix.
**Why** — a single-package repo doesn't need monorepo-style prefixes; simpler
tags are easier to reason about and match release-please defaults.
**Value** — unambiguous, conventional release tags.
**Refs** — `release-please-config.json`.

---

## 12. Bootstrapping & toolchain provisioning

### Two-level, idempotent setup
**What** — `make bootstrap` (Level 1) installs the base toolchain (`just` + `uv`)
on a bare machine; `just setup` (Level 2) does everything else and is run every
fresh clone/container/session. Both are idempotent and `just setup` fails early
with a pointer to `make bootstrap` if the base toolchain is missing.
**Why** — you can't run a `just` recipe to install `just`; a tiny Make layer
bootstraps the bare minimum, then the rich `just` layer takes over. Idempotency
makes "run it again" always safe.
**Value** — one predictable path from bare machine to fully-wired dev env.
**Refs** — `Makefile`, `Justfile`, AGENTS.md.

### Three first-class toolchain provisioners, one tool set
**What** — native installers (`make`/`just` + `scripts/install-*.sh`),
`mise install` (`mise.toml`), and `flox activate` (`.flox/`) all declare the
*same* 10 tools (python, uv, ruff, taplo, gitleaks, just, bun, gh, lefthook,
make) and must stay in sync.
**Why** — developers have different machine-management preferences; offering
three equal paths to an identical environment meets people where they are.
**Value** — anyone can provision the canonical toolchain with the tool they
already use.
**Refs** — [ADR-0005](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0005-mise-flox-first-class-toolchains.md),
`mise.toml`, `.flox/`, `scripts/`.

### `just` as the command runner
**What** — every routine task is a `just` recipe (`check`, `format`, `test`,
`serve`, `audit`, `export-openapi`, `docs`, …).
**Why** — `just` is a modern, discoverable `make` alternative without make's
tab/phony-target sharp edges; one `just --list` shows the whole workflow.
**Value** — the project's full command surface is self-documenting and uniform.
**Refs** — `Justfile`.

### Prefer pre-built binaries for hook tools
**What** — `install-taplo`/`install-yamlfmt` fetch pinned pre-built binaries and
fall back to `cargo`/`go` only if needed.
**Why** — downloading a binary takes a second; compiling from source can take
minutes — a poor first-clone experience.
**Value** — fast, reliable setup on the common platforms.
**Refs** — `Justfile`, `scripts/install-*.sh`; ITM-042.

### Some tools deliberately run from their own lockfile, not the toolchain
**What** — yamllint, codespell, bandit, editorconfig-checker (locked `dev` group
via `uv run`) and commitlint (`bun ./node_modules/@commitlint/cli/cli.js`) are intentionally
*not* in `mise.toml`/`.flox`.
**Why** — these are pinned by `uv.lock`/`bun.lock` already (WL-001); duplicating
them in the toolchain creates a second, independently-drifting version source
that the hooks never consult. Invoking commitlint by its repo-local path also
keeps the hook working on every supported setup path without depending on a
global install being present.
**Value** — one source of truth per tool version; hooks that work on a fresh
clone without a global install.
**Refs** — AGENTS.md, `lefthook.yml`, `package.json`.

---

## 13. Documentation

### Sphinx + MyST + Furo
**What** — docs are built with Sphinx, authored in Markdown via MyST, themed
with Furo, with autodoc, napoleon, intersphinx, copybutton, and typehints
extensions.
**Why** — Sphinx is the Python documentation standard (autodoc, cross-refs);
MyST lets contributors write Markdown instead of reStructuredText, lowering the
barrier; Furo is a clean, modern theme.
**Value** — professional docs that contributors can actually write in.
**Refs** — `docs/source/conf.py`.

### ReadTheDocs with PEP 735 doc group
**What** — `.readthedocs.yaml` builds on ubuntu-22.04/Python 3.12, installs `uv`
and runs `uv sync --group docs`, and produces HTML, PDF, and ePub.
**Why** — RTD gives free hosted, versioned docs; using the PEP 735 `docs` group
keeps the doc dependencies consistent with local builds.
**Value** — docs publish automatically on every push, in multiple formats.
**Refs** — `.readthedocs.yaml`; ITM-063.

### Heading anchors for cross-references
**What** — MyST generates anchors for h1–h3 headings.
**Why** — without explicit anchors, cross-document links to sections silently
break.
**Value** — intra-doc links resolve reliably.
**Refs** — `docs/source/conf.py`; WL-021.

### Three engineering-doc buckets (ADR / design / research)
**What** — `docs/adr/`, `docs/design/`, and `docs/research/` separate decisions,
specs, and explorations, each with its own README and numbering.
**Why** — these three artifact types have different lifecycles (immutable vs.
normative vs. exploratory); separating them keeps each coherent.
**Value** — a clear filing system that this very page indexes.
**Refs** — [`docs/README.md`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/README.md).

### AGENTS.md / CLAUDE.md / CONTRIBUTING.md hierarchy
**What** — `AGENTS.md` is the single source of truth for the command surface;
`CLAUDE.md` imports it verbatim; `.github/CONTRIBUTING.md` mirrors it for humans.
**Why** — one canonical file prevents the three from drifting into three
different sets of instructions.
**Value** — humans and every AI agent read the same, current guidance.
**Refs** — `AGENTS.md`, `CLAUDE.md`, `.github/CONTRIBUTING.md`.

---

## 14. Web service (FastAPI)

The web service is optional (`--extra web`) and bakes in REST best practices.
The full normative catalog is
[design 0002 (`WEB-xx`)](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0002-web-api-conventions.md)
and [ADR-0013](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0013-web-service-best-practices.md);
the highlights:

### FastAPI behind an extra
**What** — FastAPI + uvicorn ship under `[project.optional-dependencies] web`,
not in the core install.
**Why** — CLI-only adopters shouldn't pay for web dependencies; gating them
behind an extra keeps the base install lean.
**Value** — opt-in web stack; the core stays minimal.
**Refs** — `pyproject.toml`; ADR-0013.

### RFC 9457 problem+json errors
**What** — every non-2xx response is `application/problem+json` with
`type/title/status/detail/instance`.
**Why** — a standardized error shape means clients parse failures uniformly
instead of guessing per-endpoint.
**Value** — predictable, machine-readable errors.
**Refs** — design 0002; WEB-01.

### Versioned business routes, unversioned ops
**What** — business endpoints live under `/v1`; `/healthz`, `/readyz`,
`/metrics` are unversioned.
**Why** — breaking changes get a `/v2` without disturbing operational endpoints
that monitoring depends on.
**Value** — a clean evolution path that doesn't break health checks.
**Refs** — design 0002; WEB-02.

### Pagination, idempotency, metrics, tracing, rate limiting, security headers
**What** — collections paginate via `fastapi-pagination` (WEB-03); unsafe methods
honor `Idempotency-Key` with replay marking (WEB-05); Prometheus RED metrics at
`/metrics` (WEB-11); opt-in OpenTelemetry tracing (WEB-10); `slowapi` rate
limiting off-by-default behind one env var (WEB-22); and `nosniff`/`DENY`/HSTS
security headers on every response with optional CORS (WEB-23).
**Why** — these are the cross-cutting concerns every production API needs; baking
them in (correctly, off-by-default where appropriate) saves every adopter from
reinventing them.
**Value** — a service that's production-shaped on day one.
**Refs** — design 0002; WEB-03/05/10/11/22/23.

### Typed settings, fail-fast at boot
**What** — `WebSettings` (pydantic-settings) reads `PLBP_WEB_*` env vars and
fails at startup on invalid config.
**Why** — configuration errors should crash immediately and loudly, not surface
as confusing runtime behaviour.
**Value** — misconfiguration is caught at deploy, not in production traffic.
**Refs** — design 0002; WEB-30.

### OpenAPI snapshot with breaking-change gate
**What** — the OpenAPI document is committed at `docs/api/openapi.json`;
`just export-openapi` regenerates it; a test fails when it's stale; and the
`api-contract` workflow runs `oasdiff` to fail PRs that introduce breaking API
changes. Typed clients are generated, never hand-written (WEB-60).
**Why** — the API contract is an asset; committing it makes changes reviewable as
a diff, and oasdiff turns "did we break clients?" into an automatic check.
**Value** — accidental breaking changes are caught in review; clients stay in
sync.
**Refs** — `.github/workflows/api-contract.yml`, `Justfile`; WEB-51/60.

### Production Dockerfile
**What** — a multi-stage uv Dockerfile installs locked deps, runs as non-root on
a slim base, healthchecks `/healthz` via stdlib `urllib`, and starts uvicorn with
graceful shutdown.
**Why** — a realistic, secure, minimal container image is what "production-ready"
actually requires.
**Value** — adopters get a deployable image, not a toy `Dockerfile`.
**Refs** — `Dockerfile`; WEB-31/32.

### One logging pipeline, two profiles
**What** — a single `structlog` pipeline serves a human-readable CLI profile and
a JSON-lines web profile, emitting one canonical `http_request` event per
request.
**Why** — sharing one pipeline avoids two divergent logging stacks while still
giving humans readable logs and machines parseable ones.
**Value** — consistent, structured logs across both front ends.
**Refs** — [ADR-0015](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0015-one-logging-pipeline-two-profiles.md),
[design 0003](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0003-logging-conventions.md); WEB-12.

---

## 15. CLI conventions

### Noun-verb command structure
**What** — the `plbp` CLI is noun-verb (`plbp projects list`), gh-style, with
text/JSON/Markdown output, stable exit codes, and layered TOML config.
**Why** — noun-verb scales to many resources cleanly and matches the mental model
users already have from `gh`, `kubectl`, etc.
**Value** — a discoverable, conventional CLI that grows without restructuring.
**Refs** — [design 0001](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0001-plbp-cli-conventions.md),
[EXAMPLECLI.md](https://github.com/smorinlabs/py-launch-blueprint/blob/main/EXAMPLECLI.md).

### Markdown as a third output format
**What** — alongside text and JSON, the CLI emits Markdown.
**Why** — Markdown output drops straight into issues, PRs, and docs — a common
real-world need the base spec omitted.
**Value** — copy-pasteable results for humans writing reports.
**Refs** — [ADR-0003](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0003-keep-markdown-output-mode.md).

### Stable error codes, hints, and a crash log
**What** — errors carry stable, append-only codes, actionable hints, and write a
reproducible crash log; the CLI exposes documented exit codes (0–5).
**Why** — stable codes let scripts and docs reference errors reliably; hints and
crash logs make failures self-service to debug.
**Value** — scriptable, debuggable failure behaviour.
**Refs** — [ADR-0006](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0006-stable-error-codes-hints-crash-log.md).

### Config degrades to warnings, never crashes
**What** — invalid config values warn and fall back to defaults rather than
aborting.
**Why** — one bad key shouldn't make the whole tool unusable; graceful
degradation keeps it working while flagging the problem.
**Value** — resilience to imperfect config.
**Refs** — [ADR-0004](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0004-config-errors-degrade-to-warnings.md).

### Quality-of-life touches
**What** — did-you-mean suggestions via stdlib `difflib` (ADR-0007), automatic
paging of long output (ADR-0008), a guided `config init` plus one-time first-run
hint (ADR-0009), Windows-native default paths with XDG overrides (ADR-0011), and
a redacting `doctor --bundle` that excludes log contents (ADR-0012).
**Why** — these small affordances are what separate a pleasant CLI from a
merely-functional one, and each was decided deliberately.
**Value** — a polished, secure, cross-platform user experience.
**Refs** — ADR-0007/0008/0009/0011/0012 (in
[`docs/adr/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr)).

---

## 16. Contributors & governance

### Contributing guide, code of conduct, security policy
**What** — `.github/CONTRIBUTING.md` (mirroring AGENTS.md), a Code of Conduct,
and a Security policy with a disclosure process.
**Why** — clear expectations lower the barrier for contributors and set
community norms; a stated disclosure path enables responsible reporting.
**Value** — a welcoming, well-governed project that contributors trust.
**Refs** — `.github/CONTRIBUTING.md`, `docs/source/contributing/`.

### Issue and PR templates
**What** — structured templates for feature/bug/docs issues and a PR template.
**Why** — templates gather the right information upfront, reducing review
round-trips.
**Value** — higher-quality submissions, faster triage.
**Refs** — `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`.

### CLA enforcement via CLA Assistant
**What** — CLA Assistant gates contributions on a signed individual/corporate
CLA.
**Why** — a CLA protects the project's ability to relicense and defend its code.
**Value** — legal clarity for a project meant to be widely adopted.
**Refs** — `docs/source/contributing/cla/`,
[CLA tool guide](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/source/tools/cla-assistant.md).

### Automated contributor recognition
**What** — a weekly workflow runs `contributors-please` to update the contributor
list.
**Why** — recognizing contributors manually is forgotten; automating it ensures
nobody is missed.
**Value** — every participant is acknowledged, automatically.
**Refs** — `.github/workflows/update-contributors.yml`.

---

## 17. Template / init system

### A rebrand engine, not a one-shot script
**What** — `init/` holds a manifest-driven engine (`init.py`) that renames the
template's identity (package, app short name, author) across the repo, with a
dry-run preview, plus an optional `post_init.py` for publishing/Codecov/RTD
setup.
**Why** — turning a template into your project by hand is error-prone; a
manifest-driven engine with a preview makes it reliable and reviewable.
**Value** — `gh repo create --template` → run init → working, rebranded project.
**Refs** — [design 0004](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0004-template-press-plan.md),
`init/manifest.toml`.

### Manifest-drift guard
**What** — any added/renamed file containing an identity value must be listed in
that value's `[[replace]]` block in `init/manifest.toml`; a CI check
(`check_manifest_drift.py`) enforces it.
**Why** — if a new file with the project name isn't in the manifest, a fork's
`init` ships half-renamed; the drift check makes that impossible to merge.
**Value** — the rebrand stays complete as the template evolves.
**Refs** — `init/ci/check_manifest_drift.py`, AGENTS.md; (blueprint-guard).

### Two-tier guard with a completion marker
**What** — `init/guard.sh` warns (Tier-1) on un-rebranded projects and blocks
(Tier-2) risky operations like publish; the `init/.blueprint-initialized` marker
records completion and gates blueprint-only maintenance checks in forks.
**Why** — it must be hard to accidentally publish the *template's* identity, and
forks shouldn't run the blueprint's self-maintenance checks.
**Value** — guardrails against shipping an un-rebranded project.
**Refs** — `init/guard.sh`, `Justfile` (`_guard`).

### Five instantiation modes, integration-tested
**What** — `init-integration.yml` tests all five ways a template is used
(template button, `gh ... --template`, clone-reinit, fork, zip) at both contract
(L1) and outcome (L2) levels, on a weekly schedule too.
**Why** — each instantiation path has different git/state characteristics; only
testing all of them proves the template works however it's adopted.
**Value** — confidence that adoption works for real users, not just the happy
path.
**Refs** — `.github/workflows/init-integration.yml`,
`.github/workflows/blueprint-guard.yml`.

---

## 18. AI agent tooling

### `AGENTS.md` as the canonical agent config
**What** — `AGENTS.md` is the one file every coding agent reads; `CLAUDE.md`
imports it via `@AGENTS.md`, and Cursor/Windsurf/Codex read it natively.
**Why** — maintaining separate `.cursor`/`.windsurf` rule files guarantees
drift; a single canonical file keeps every agent in sync.
**Value** — consistent, current AI guidance regardless of which assistant a
contributor uses.
**Refs** — `AGENTS.md`, `CLAUDE.md`.

### A project-bootstrap skill
**What** — a `new-python-project` skill (under `.claude/skills/`, symlinked for
Codex) encodes the full template-to-project runbook.
**Why** — bootstrapping has many steps (preconditions, identity collection, init,
post-init); a skill turns it into a guided, repeatable flow that's also a
copy-pasteable runbook for humans.
**Value** — agents (and people) scaffold new projects correctly and consistently.
**Refs** — `.claude/skills/new-python-project/SKILL.md`; ADR-0014.

---

## 19. IDE integration

### VS Code as the reference editor
**What** — committed VS Code settings, a DevContainer, and recommended Ruff,
Pyright, and EditorConfig extensions.
**Why** — shipping editor config means every contributor gets the same
format-on-save, type-check, and lint behaviour without manual setup.
**Value** — a zero-config, consistent editing experience out of the box.
**Refs** — `.vscode/`, `.devcontainer/`.

---

## 20. Decision records index

The authoritative records behind the decisions above. ADRs and design docs live
in [`docs/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs);
`WEB-xx` and `HEX-xx` are catalogued in their design specs.

| Record | Subject |
|---|---|
| [ADR-0001](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0001-app-short-name-plbp.md) | App short name `plbp` (superseded by 0016) |
| [ADR-0002](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0002-no-secrets-in-config-file.md) | Secrets never in the config file |
| [ADR-0003](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0003-keep-markdown-output-mode.md) | Markdown as a third output format |
| [ADR-0004](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0004-config-errors-degrade-to-warnings.md) | Invalid config degrades to warnings |
| [ADR-0005](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0005-mise-flox-first-class-toolchains.md) | mise & flox as first-class toolchains |
| [ADR-0006](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0006-stable-error-codes-hints-crash-log.md) | Stable error codes, hints, crash log |
| [ADR-0007](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0007-did-you-mean-stdlib-difflib.md) | Did-you-mean via stdlib `difflib` |
| [ADR-0008](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0008-pager-for-long-text-output.md) | Pager for long text output |
| [ADR-0009](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0009-config-init-and-first-run-hint.md) | Guided `config init` + first-run hint |
| [ADR-0010](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0010-rich-row-variant-on-result-models.md) | Rich-only row variant on result models |
| [ADR-0011](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0011-windows-native-paths-xdg-overrides.md) | Windows-native paths, XDG overrides |
| [ADR-0012](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0012-doctor-bundle-redact-at-collection.md) | `doctor --bundle` redacts at collection |
| [ADR-0013](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0013-web-service-best-practices.md) | Web service best practices (`WEB-xx`) |
| [ADR-0014](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0014-repo-simplification-batch.md) | Repo simplification batch |
| [ADR-0015](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0015-one-logging-pipeline-two-profiles.md) | One logging pipeline, two profiles |
| [ADR-0016](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0016-app-short-name-placeholder.md) | App short name as obvious placeholder |
| [ADR-0017](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0017-hexagonal-core-and-boundary-enforcement.md) | Hexagonal core + boundary enforcement |
| [Design 0001](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0001-plbp-cli-conventions.md) | CLI conventions |
| [Design 0002](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0002-web-api-conventions.md) | Web API conventions (`WEB-xx`) |
| [Design 0003](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0003-logging-conventions.md) | Logging conventions |
| [Design 0004](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0004-template-press-plan.md) | Template Press (init engine) |
| [Design 0005](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0005-hexagonal-architecture-and-enforcement.md) | Hexagonal architecture (`HEX-xx`) |

For the conventions the maintainer follows when writing new records, see the
READMEs in [`docs/adr/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr),
[`docs/design/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design),
and [`docs/research/`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/research).
