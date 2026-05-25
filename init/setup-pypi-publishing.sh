#!/usr/bin/env bash
set -euo pipefail

# Print the exact values you need to paste into the PyPI and TestPyPI
# "pending publisher" forms to set up Trusted Publishing (OIDC) for this repo.
# Also validates that .github/workflows/release.yml has the bits PyPI expects.
#
# Trusted Publishing means no API tokens — GitHub Actions auths to PyPI
# directly via OIDC. The provider config itself must be created in the PyPI
# web UI (there is no public API for it as of this writing), so this script
# stops just short of the browser step and hands you the inputs.
#
# Usage:
#   init/setup-pypi-publishing.sh [owner/repo]
#
# If owner/repo is omitted, the script auto-detects via `gh repo view`.

WORKFLOW_FILE=".github/workflows/publish.yml"
ENVIRONMENTS=(testpypi pypi)

cyan() { printf '\033[36m%s\033[0m' "$*"; }
bold() { printf '\033[1m%s\033[0m' "$*"; }
warn() { printf '\033[33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" \
    || die "run from inside the repo (git rev-parse failed)"
cd "$repo_root"

if [[ $# -ge 1 ]]; then
    repo="$1"
elif command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    repo="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)" \
        || die "could not detect repo via gh; pass owner/repo as the first arg"
else
    remote_url="$(git config --get remote.origin.url 2>/dev/null || true)"
    [[ -n "$remote_url" ]] || die "no origin remote; pass owner/repo as the first arg"
    repo="$(printf '%s' "$remote_url" \
        | sed -E 's#^(https?://[^/]+/|git@[^:]+:)##; s#\.git$##')"
fi

[[ "$repo" == */* ]] || die "repo must be in 'owner/repo' form, got: $repo"
owner="${repo%%/*}"
repo_name="${repo##*/}"

[[ -f pyproject.toml ]] || die "pyproject.toml not found at $repo_root"
project_name_raw="$(grep -E '^name[[:space:]]*=' pyproject.toml \
    | head -1 | sed -E 's/^name[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/')"
[[ -n "$project_name_raw" ]] || die "could not read project name from pyproject.toml"
# PyPI normalizes underscores to hyphens for display, but accepts both on input.
pypi_project_name="$(printf '%s' "$project_name_raw" | tr '_' '-')"

workflow_filename="$(basename "$WORKFLOW_FILE")"

# --- workflow sanity checks ----------------------------------------------------
if [[ ! -f "$WORKFLOW_FILE" ]]; then
    warn "$WORKFLOW_FILE not found — PyPI will reject the trusted-publisher config until this exists on the default branch."
else
    grep -q 'id-token:[[:space:]]*write' "$WORKFLOW_FILE" \
        || warn "$WORKFLOW_FILE has no 'id-token: write' permission — OIDC auth will fail."
    for env in "${ENVIRONMENTS[@]}"; do
        grep -qE "environment:[[:space:]]*${env}([[:space:]]|$)" "$WORKFLOW_FILE" \
            || warn "$WORKFLOW_FILE does not reference environment '$env'."
    done
    grep -qE 'pypa/gh-action-pypi-publish|uv publish.*--trusted-publishing|--trusted-publishing.*uv publish' "$WORKFLOW_FILE" \
        || warn "$WORKFLOW_FILE does not appear to invoke a trusted-publishing-capable publisher."
fi

# --- output --------------------------------------------------------------------
print_block() {
    local index_name="$1" url="$2" env="$3"
    echo
    bold "── $index_name ─────────────────────────────────────────────────"; echo
    echo
    echo "  1. Open: $(cyan "$url")"
    echo "     (sign in if needed; this is your account-level publishing page)"
    echo
    echo "  2. Under 'Add a new pending publisher', select the $(bold GitHub) tab."
    echo "     (Tabs/providers: GitHub | Google | ActiveState | GitLab — pick GitHub.)"
    echo
    echo "  3. Fill in these EXACT values:"
    printf "       %-22s %s\n" "PyPI Project Name:"  "$(bold "$pypi_project_name")"
    printf "       %-22s %s\n" "Owner:"              "$(bold "$owner")"
    printf "       %-22s %s\n" "Repository name:"    "$(bold "$repo_name")"
    printf "       %-22s %s\n" "Workflow name:"      "$(bold "$workflow_filename")"
    printf "       %-22s %s\n" "Environment name:"   "$(bold "$env")"
    echo
    echo "  4. Click 'Add'. The publisher stays 'pending' until the first"
    echo "     successful upload claims the project name."
    echo
}

echo
bold "Trusted Publisher setup for $repo"; echo
echo "Project (from pyproject.toml): $project_name_raw  →  PyPI name: $pypi_project_name"
echo "Workflow: $WORKFLOW_FILE"
echo "Environments: ${ENVIRONMENTS[*]}"

print_block "TestPyPI" "https://test.pypi.org/manage/account/publishing/" "testpypi"
print_block "PyPI"     "https://pypi.org/manage/account/publishing/"      "pypi"

echo "── After you've added BOTH publishers ──────────────────────────────"
echo
echo "  • No GitHub secrets are needed — the workflow uses OIDC."
echo "  • Tag a release (e.g. 'git tag v0.1.0 && git push --tags') to trigger"
echo "    the release.yml workflow, which will publish to TestPyPI first, then"
echo "    PyPI on success."
echo "  • If you ever rename the workflow file, the repo, or an environment,"
echo "    update the trusted-publisher entry on PyPI to match — it's an"
echo "    exact-match check."
echo
