# Test & Tooling Analysis — Dev-Tooling Wishlist

Analysis complete — no changes made in this document, this is the planning
deliverable. **TL;DR:** this repo is already in the top tier of Python project
tooling (most of the classic "wish list" is *done* here), so the highest-value
items left fall into three themes: **(1) making the existing tooling
reproducible and gated** (pinned tool versions, locked installs, coverage
floors, a CI summary gate), **(2) closing the scheduled/supply-chain gaps**
(continuous vuln audits, attestations, zizmor), and **(3) a small set of CLI-
and FastAPI-specific contract tests** (help-output snapshots, OpenAPI drift
check). Below is the inventory, then the wishlist with IDs, and finally the
subset that was implemented on PR #406.

## Part 1 — Inventory of what's already in place

**Local hooks (lefthook):** commitlint (commit-msg); gitleaks,
editorconfig-checker, yamllint, codespell, ruff check + format on staged files
(pre-commit); gitleaks range scan, bandit, init-system guards + init tests
(pre-push).

**CI (16 workflows):** core CI (ruff lint, ty typecheck, pytest matrix
ubuntu+macos × py3.12/3.13 with Codecov OIDC upload, taplo TOML check), plus
dedicated workflows for actionlint, bandit, codespell, commitlint, yamllint,
editorconfig, CodeQL (PR + weekly), TruffleHog secret scan, dependency-review,
large-file guard, blueprint/init integrity guards, manual Safety scan,
contributors automation. All workflows use least-privilege `permissions: {}` +
per-job grants and concurrency groups — genuinely well-hardened.

**Release & deps:** release-please → tag → OIDC trusted publishing with
tag-on-main and version-matches-tag verification (TestPyPI stage scaffolded but
currently disabled); Dependabot for pip/actions/npm with grouping, cooldowns,
and commitlint-conforming messages.

**DX & docs:** rich Justfile (~40 recipes incl. `dev`, `check`, `coverage`,
docs), devcontainer, .editorconfig, VS Code extensions/launch, `py.typed`,
Sphinx + ReadTheDocs, ADRs/design docs, full community file set (CONTRIBUTING,
SECURITY, CoC, issue/PR templates), pytest marker taxonomy (`slow`/`live`).

Already done that's usually on wish lists: uv, conventional commits, secret
scanning ×2, CodeQL, trusted publishing, devcontainer, coverage upload, grouped
Dependabot, spell/TOML/YAML/editorconfig linting. So the tables below
deliberately exclude all of that.

## Part 2 — Wish list

IDs use `WL-` to avoid colliding with the repo's `ITM-`/`ADR-` numbering.

### Category A — Harden what already exists (reproducibility & gating)

These are improvements to existing tooling, not new tools — highest
value-to-effort ratio in the repo.

| ID | Item | Best practice / what it is | What the developer gets | Applicability |
|---|---|---|---|---|
| WL-001 | Pin tool versions in hooks + CI | Hooks and the CI lint job run floating `uvx ruff`, `uvx codespell`, `uvx bandit` (latest-at-runtime) while ruff/ty are *also* pinned in `uv.lock`. Best practice: one pinned version everywhere — `uv run ruff` from the locked dev group, or `uvx ruff@==X`. | CI never breaks overnight because a linter released new rules; local hook results always match CI; tool upgrades become reviewable Dependabot PRs instead of surprises. | Universal |
| WL-002 | Locked installs in CI (`uv sync --locked`) | CI jobs run plain `uv sync`, which silently re-resolves if `uv.lock` drifted from `pyproject.toml`. `--locked` fails instead. | Guarantees CI tests exactly what's committed; catches "edited pyproject, forgot to re-lock" at PR time instead of at a confusing future failure. | Universal |
| WL-003 | SHA-pin GitHub Actions | Actions are tag-pinned (`actions/checkout@v6`). OpenSSF best practice is full commit-SHA pins with a version comment; Dependabot keeps them fresh. | Immunity to tag-rewrite supply-chain attacks (the tj-actions incident class); exact reproducibility of CI behavior. | Universal |
| WL-004 | Build + install smoke test in CI | The package is first built at tag time. Best practice: every PR runs `uv build` + `twine check` / `check-wheel-contents` + install the wheel and run `plbp --version`. | Packaging breakage (missing files, broken entry point, bad metadata) caught in PR review, not during a release that then needs a hotfix tag. | Universal |
| WL-005 | Coverage gates | Codecov uploads exist but `.codecov.yml` sets no status targets and pytest has no `--cov-fail-under`. Best practice: project coverage can't drop > X% and patch coverage ≥ Y%. | Coverage stops silently eroding; reviewers get a red check instead of needing to remember to look at the Codecov comment. | Universal |
| WL-006 | CI summary "gate" job | A single `ci-ok` job with `needs:` on all required jobs (and `if: always()` failure logic). Branch protection requires only that one check. | Required-checks config never drifts when jobs are renamed/added across 16 workflows; also the enabler for path-filtering (WL-019) without breaking required checks. | Universal |
| WL-007 | Re-enable the TestPyPI stage | The publish workflow has a complete TestPyPI smoke-test job that's commented out. | A real install-from-index rehearsal before every PyPI publish; bad releases die in staging. | Universal (already 90% built) |

### Category B — Testing & quality

| ID | Item | Best practice / what it is | What the developer gets | Applicability |
|---|---|---|---|---|
| WL-008 | Parallel tests (`pytest-xdist`) | `pytest -n auto` locally and in CI. | The single biggest perceived-speed win as the suite grows; keeps `just dev` loop fast. | Universal |
| WL-009 | Test timeouts (`pytest-timeout`) | Global per-test timeout (e.g. 60s). | A hung test fails loudly instead of burning a 6-hour CI slot; especially relevant with `live` marker tests. | Universal |
| WL-010 | Test-order randomization (`pytest-randomly`) | Shuffle test order each run with a reproducible seed. | Flushes out hidden inter-test state coupling early, when it's cheap to fix. | Common |
| WL-011 | Windows in the test matrix | Matrix is ubuntu + macOS. Add at least one `windows-latest` × py3.12 combo. | Catches path-separator, encoding, and console-color bugs — disproportionately important for a *CLI* tool users will run on Windows. | Common; high value for CLI |
| WL-012 | Scheduled "canary" CI run | Weekly cron job: full suite including `slow`/`live` markers against freshly-resolved latest deps (`uv lock --upgrade` in a throwaway env). | Ecosystem breakage (new pydantic/click release) surfaces in a scheduled run you can triage calmly, not inside an unrelated feature PR. | Common |
| WL-013 | Property-based tests (Hypothesis) | Apply to parsing/serialization boundaries (config round-trip, pydantic models). | Finds edge cases example-based tests never enumerate; the canonical "always wished for" testing upgrade. | Common, apply selectively |

### Category C — Security & supply chain

| ID | Item | Best practice / what it is | What the developer gets | Applicability |
|---|---|---|---|---|
| WL-014 | Continuous dependency vuln audit | `pip-audit` or `osv-scanner` on a weekly schedule + PR. Today, dependency-review only fires on PRs that *change* manifests, and the Safety scan is manual + needs an API key. | Alerts when a CVE lands in an *already-pinned* dependency — the gap none of the current three scanners covers. | Universal |
| WL-015 | zizmor (workflow security linter) | Astral's static analyzer for GitHub Actions (template injection, excessive permissions, unpinned actions). Complements existing actionlint (which checks syntax, not security). | With 16 workflows, an automated reviewer for the CI itself; also enforces WL-003 going forward. | Common, fast-rising standard |
| WL-016 | Build provenance attestations | PEP 740 attestations / `actions/attest-build-provenance` on published artifacts (pairs with existing trusted publishing). | Users can cryptographically verify the PyPI artifact came from this repo's CI; "verified" badge on PyPI. | Common, rising |
| WL-017 | OpenSSF Scorecard | Scheduled scorecard workflow + README badge. | Continuous grading of repo security posture, and a strong signal for a *blueprint* repo that others fork as a reference. | Common (OSS-facing) |
| WL-018 | SBOM on release | Generate CycloneDX/SPDX SBOM as a release artifact (syft or cyclonedx-py). | Compliance-readiness and dependency transparency for downstream users. | Moderate — leaning enterprise; lower priority |

### Category D — Automation & CI ergonomics

| ID | Item | Best practice / what it is | What the developer gets | Applicability |
|---|---|---|---|---|
| WL-019 | Path-filtered heavy jobs | Skip the 4-way test matrix on docs-only changes, via path filters + the WL-006 gate job (so required checks still pass). | Faster feedback on docs/config PRs, lower CI spend; matters since *every* PR currently runs ~16 workflows. | Universal |
| WL-020 | Dependabot auto-merge | Workflow that enables auto-merge for patch/minor *dev-tool* group PRs once all checks pass. | Eliminates the Monday ritual of rubber-stamping 5 dependency PRs; humans only review majors and runtime deps. | Common |
| WL-021 | Docs build + linkcheck in CI | PR job running `sphinx-build -W` (warnings-as-errors) and `-b linkcheck`. Today docs failures only surface on ReadTheDocs after merge. | Broken cross-references and dead links blocked at PR time; docs get the same gate code has. | Universal |
| WL-022 | Public-API docstring enforcement | Enable ruff `D` rules scoped to `src/` public modules (or `interrogate` with a % floor). | Docstring coverage stops regressing; Sphinx autodoc output stays complete. | Common; start scoped to avoid noise |

### Category E — CLI-specific (plbp)

| ID | Item | Best practice / what it is | What the developer gets | Applicability |
|---|---|---|---|---|
| WL-023 | Golden/snapshot tests for CLI output | Snapshot `--help` for every command and key command outputs (syrupy or pytest-regressions), reviewed as diffs. | UX regressions (renamed flag, garbled help text) become visible red diffs in PR review; doubles as living CLI documentation. | CLI-specific, broadly loved |
| WL-024 | Shell completions | Generate bash/zsh/fish completions from click, document install, smoke-test generation in CI. | Table-stakes polish users expect from a modern CLI (`gh`, `uv` both ship it); near-free with click. | CLI-specific |
| WL-025 | Documented zero-install run path | First-class `uv tool install` / `uvx plbp` and pipx docs in README, verified by the WL-004 smoke test. (Standalone PyInstaller binaries: defer — maintenance-heavy.) | Users try the CLI in one command; lowers adoption friction for the template's forks too. | CLI-specific, low effort |

### Category F — FastAPI-specific (web extra)

| ID | Item | Best practice / what it is | What the developer gets | Applicability |
|---|---|---|---|---|
| WL-026 | OpenAPI schema drift check | Export `app.openapi()` to a committed `openapi.json`; CI fails if the generated schema differs from the committed one. | API contract changes become explicit, reviewable diffs — the web-service equivalent of a lockfile; enables client-codegen later. | FastAPI-specific, the standout item in this category |
| WL-027 | Schema-based API fuzzing (schemathesis) | Run schemathesis against the app's OpenAPI schema in CI (or the weekly canary, WL-012). | Free negative-testing of every endpoint (wrong types, missing fields, edge values) with zero per-endpoint test code. | FastAPI-specific; semi-specialty, do after WL-026 |
| WL-028 | Container image for the web service | Dockerfile (uv multi-stage) + hadolint + GHCR publish on release with a healthcheck. | The standard deploy artifact for a service; also gives forks a working reference Dockerfile. | Service-specific; common once the web extra is real |

### Considered and deliberately left off (too niche per the constraint)

Mutation testing (mutmut/cosmic-ray — high noise-to-signal), continuous
benchmarking (codspeed/pytest-benchmark — no perf-sensitive code yet), a second
type checker alongside ty, stale-issue bots (community-hostile), Renovate
migration (Dependabot is well-tuned here), CITATION.cff, and enforced commit
signing (GitHub's verified-merge flow covers most of the value).

### Starting shortlist

Highest value-per-effort, in order: **WL-001/WL-002** (pin everything — pure
correctness, near-zero cost), **WL-006 + WL-019** (gate job + path filters,
they're one piece of work), **WL-004** (build smoke test), **WL-005** (coverage
gates), **WL-014** (the one real security gap), **WL-021** (docs CI), and
**WL-023/WL-026** as the two flagship domain-specific items.

## Part 3 — What was implemented (PR #406)

The shortlist above was implemented on
`claude/dev-tooling-wishlist-review-brsm2v` (PR #406).

| ID | Delivered |
|---|---|
| WL-001 | All hook/CI tools (ruff, bandit, codespell, yamllint, editorconfig-checker) run from the locked dev group via `uv run` — lefthook, Justfile, and every workflow now use identical `uv.lock` versions; dependabot groups extended; `--force-exclude` added so ruff hooks honor the config excludes |
| WL-002 | Every CI sync is `uv sync --locked` — lockfile drift fails at PR time |
| WL-004 | `build-smoke` job, uv end-to-end: `uv build` → `twine` metadata check → install wheel *and* sdist into fresh envs → `plbp --version` |
| WL-005 | Codecov gates: project can't drop > 1% vs base, patch target 80% (baseline measured at 89%) |
| WL-006 / WL-019 | `ci-ok` aggregate gate job (the one check to require in branch protection) + shell-based `changes` filter that skips typecheck/test-matrix/build-smoke on docs-only PRs |
| WL-014 | Weekly `dep-audit` workflow (pip-audit over the hashed locked export, all extras + groups) + `just audit` running the identical pipeline |
| WL-021 | `sphinx-build -W` docs job per PR (fixed the 21-warning baseline: toctree typo, broken xrefs, heading levels, missing anchors); flaky external `linkcheck` runs weekly instead |
| WL-023 | Syrupy golden snapshots of all `plbp` commands' `--help`, width pinned to 80 for determinism |
| WL-026 | `docs/api/openapi.json` committed API contract + drift test (see post-merge note below) |

### Post-merge status notes

- **WL-026 superseded by main's WEB-51.** While this branch was open, `main`
  independently shipped a more complete OpenAPI contract system (WEB-51:
  `scripts/export_openapi.py`, `tests/web/test_openapi_snapshot.py`,
  `just export-openapi`, and an `api-contract` workflow running oasdiff for
  breaking-change detection, plus client codegen). On merge, this branch's
  WL-026 implementation (`web/openapi.py`, its drift test, and the duplicate
  Justfile recipe) was dropped in favor of main's. The WL-026 *intent* — a
  committed, drift-checked OpenAPI contract — is satisfied by WEB-51.
- **WL-011 (Windows matrix) arrived via main.** The test matrix is now
  ubuntu + macOS + `windows-latest` × py3.12/3.13 (main's REC-24 work), so the
  CLI-on-Windows coverage this wishlist called for is in place even though it
  wasn't part of this branch's shortlist.
- **Not in this PR (remaining wishlist):** WL-003, WL-007, WL-008–WL-010,
  WL-012, WL-013, WL-015–WL-018, WL-020, WL-022, WL-024, WL-025, WL-027,
  WL-028. These map naturally onto the repo's project-harness flow
  (`project-add` to reserve ITM-style IDs) when prioritized.
