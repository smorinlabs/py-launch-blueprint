#!/usr/bin/env bash
# init/tests/integration/run-mode.sh — L1 + L2 integration runner for one §4.7 mode.
#
# Usage:
#     MODE=template_button bash init/tests/integration/run-mode.sh
#     MODE=fork bash init/tests/integration/run-mode.sh
#     ...etc, any of: template_button | gh_template | clone_reinit | fork | zip
#
# L1 (contract) — guard + init exit codes + marker presence as §4.7 mandates.
# L2 (outcome)  — for modes 1-4: rebranded project actually builds + tests pass
#                 + CLI command works + post-migration doctor reports clean.
#                 Mode 5 has no L2 (init refuses).
#
# Exits non-zero on any contract or outcome failure. Designed to be the unit
# of work for the matrix in .github/workflows/init-integration.yml.

set -euo pipefail

MODE="${MODE:?usage: MODE=<mode> bash init/tests/integration/run-mode.sh}"
case "$MODE" in
    template_button|gh_template|clone_reinit|fork|zip) ;;
    *) printf >&2 'run-mode: unknown MODE=%s\n' "$MODE"; exit 2 ;;
esac

# Where the blueprint sources live (this script's repo root).
BLUEPRINT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
ANSWERS_SRC="$BLUEPRINT_ROOT/init/tests/integration/answers.toml"

FIXTURE="$(mktemp -d -t plbp-mode-XXXXXX)/proj"
mkdir -p "$FIXTURE"

# Forward git identity so commit ops work in CI runners without global config.
GIT_FLAGS=(
    -c user.email=ci@example.invalid
    -c user.name=Integration
    -c commit.gpgsign=false
    -c init.defaultBranch=main
)

log() { printf >&2 '\n\033[36m▸ [%s] %s\033[0m\n' "$MODE" "$*"; }
fail() { printf >&2 '\n\033[31m✗ [%s] FAIL: %s\033[0m\n' "$MODE" "$*"; exit 1; }
pass() { printf >&2 '\033[32m  ok: %s\033[0m\n' "$*"; }

# ──────────────────────────────────────────────────────────────
# 1. Build the fixture (full-repo copy, excluding ephemeral dirs).
# ──────────────────────────────────────────────────────────────
log "building fixture in $FIXTURE"
# rsync is available on every standard ubuntu/macos runner.
rsync -a \
    --exclude='.git/' \
    --exclude='.venv/' \
    --exclude='node_modules/' \
    --exclude='build/' \
    --exclude='dist/' \
    --exclude='__pycache__/' \
    --exclude='.pytest_cache/' \
    --exclude='.ruff_cache/' \
    --exclude='.mypy_cache/' \
    --exclude='.ty_cache/' \
    "$BLUEPRINT_ROOT/" "$FIXTURE/"
pass "rsync complete ($(find "$FIXTURE" -type f | wc -l | tr -d ' ') files)"

cp "$ANSWERS_SRC" "$FIXTURE/answers.toml"
cd "$FIXTURE"

# ──────────────────────────────────────────────────────────────
# 2. Mode-specific git state.
# ──────────────────────────────────────────────────────────────
log "configuring mode: $MODE"
case "$MODE" in
    zip)
        # Mode 5: no .git at all. Done.
        [ ! -d .git ] || fail "ZIP fixture must have no .git"
        pass "no .git directory (mode #5)"
        ;;
    template_button|gh_template|clone_reinit|fork)
        git "${GIT_FLAGS[@]}" init -q
        git "${GIT_FLAGS[@]}" add -A
        git "${GIT_FLAGS[@]}" commit -q -m "initial commit (fixture)"
        case "$MODE" in
            template_button|gh_template)
                git remote add origin git@github.com:newowner/my-project.git
                ;;
            clone_reinit)
                : # no origin
                ;;
            fork)
                # Same repo NAME, different OWNER — the §4.7 mode #4 regression case.
                git remote add origin git@github.com:alice/py-launch-blueprint.git
                ;;
        esac
        pass "git state ready ($(git remote get-url origin 2>/dev/null || echo 'no origin'))"
        ;;
esac

# ──────────────────────────────────────────────────────────────
# 3. L1 contract — guard behavior.
# ──────────────────────────────────────────────────────────────
log "L1: guard contract"
guard_warn_out="$(bash init/guard.sh warn 2>&1 >/dev/null || true)"
if printf '%s' "$guard_warn_out" | grep -q "blueprint un-initialized"; then
    pass "guard warn fires (un-migrated → banner shown)"
else
    fail "guard warn banner missing; got: $guard_warn_out"
fi

# ──────────────────────────────────────────────────────────────
# 4. Mode 5 (ZIP) — assert init refuses, then exit 0.
# ──────────────────────────────────────────────────────────────
if [ "$MODE" = "zip" ]; then
    log "L1: init must refuse without .git"
    set +e
    init_out="$(uv run --script init/init.py --config answers.toml --yes 2>&1)"
    init_rc=$?
    set -e
    [ "$init_rc" -ne 0 ] || fail "init must exit non-zero on missing .git"
    printf '%s' "$init_out" | grep -qiE 'no \.git|git init' \
        || fail "init refusal message must mention git init; got: $init_out"
    pass "init refused with actionable message"
    log "DONE — mode $MODE (no L2 for ZIP)"
    exit 0
fi

# ──────────────────────────────────────────────────────────────
# 5. Modes 1-4: run init, then L2 outcome checks.
# ──────────────────────────────────────────────────────────────
log "L1: running init --config answers.toml (includes lockfile regen)"
# Integration tests run the FULL pipeline — no --no-lockfile, no --allow-dirty.
# Stale lockfiles after init would leak identity (caught by the doctor below).
uv run --script init/init.py --config answers.toml --yes
[ -f init/.blueprint-initialized ] || fail "marker not written"
pass "marker written: init/.blueprint-initialized"

log "post-init: guard must self-silence"
guard_silent_out="$(bash init/guard.sh warn 2>&1 >/dev/null || true)"
if printf '%s' "$guard_silent_out" | grep -q "blueprint un-initialized"; then
    fail "guard still warning after init (marker should silence it)"
fi
pass "guard silent post-init"

# ──────────────────────────────────────────────────────────────
# 6. L2 outcome — uv sync, pytest, build, CLI smoke, doctor.
# ──────────────────────────────────────────────────────────────
log "L2: uv sync --group dev (rebuilds resolution against rebranded pyproject)"
uv sync --group dev

log "L2: project's own pytest"
uv run pytest --override-ini="addopts="

log "L2: uv build (produce a wheel for the rebranded project)"
uv build
wheel=$(find dist -name 'acme_widget-*.whl' -print -quit)
[ -n "${wheel:-}" ] || fail "no acme_widget wheel produced in dist/"
pass "built $wheel"

log "L2: CLI smoke (install wheel into ephemeral env, run --version)"
# uvx --from <wheel> <cli> runs the wheel's console_script in an isolated env.
cli_out="$(uvx --from "$wheel" widget --version 2>&1 || true)"
printf '%s\n' "$cli_out" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+' \
    || fail "CLI did not report a version; got: $cli_out"
pass "CLI works: $cli_out"

log "L2: init-doctor (--skip env; we want migration checks only)"
uv run --script init/init_doctor.py --skip env

# ──────────────────────────────────────────────────────────────
# 7. Mode 4 (fork) — contributor sentinel must silence the guard.
# ──────────────────────────────────────────────────────────────
if [ "$MODE" = "fork" ]; then
    log "mode #4 extra: contributor sentinel"
    rm init/.blueprint-initialized
    touch init/.blueprint-contributor
    sentinel_out="$(bash init/guard.sh warn 2>&1 >/dev/null || true)"
    if printf '%s' "$sentinel_out" | grep -q "blueprint un-initialized"; then
        fail "contributor sentinel did not silence the guard"
    fi
    pass "contributor sentinel silences guard"
fi

log "DONE — mode $MODE (L1 + L2 both passed)"
