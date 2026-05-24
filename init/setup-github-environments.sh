#!/usr/bin/env bash
set -euo pipefail

# Create the GitHub Actions environments referenced by .github/workflows/release.yml
# (testpypi, pypi) on a target repository, restricting deployments to `main` and
# any `release/*` branch.
#
# Usage:
#   init/setup-github-environments.sh [owner/repo]
#
# If owner/repo is omitted, the script uses the repo of the current working
# directory (as resolved by `gh repo view`).
#
# Requires: gh CLI, authenticated with a token that has `repo` scope (or a
# fine-grained PAT / GitHub App with `Administration: write` on the target).
#
# Re-running is safe: environments are upserted and branch policies are
# reconciled to match ALLOWED_BRANCHES.

ENVIRONMENTS=(testpypi pypi)
ALLOWED_BRANCHES=(main "release/*")

die() { echo "error: $*" >&2; exit 1; }

command -v gh >/dev/null 2>&1 || die "gh CLI not found. Install: https://cli.github.com/"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated. Run: gh auth login"

if [[ $# -ge 1 ]]; then
    repo="$1"
else
    repo="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)" \
        || die "could not detect repo; pass owner/repo as the first argument"
fi

[[ "$repo" == */* ]] || die "repo must be in 'owner/repo' form, got: $repo"

gh api "repos/$repo" >/dev/null 2>&1 \
    || die "cannot access repo '$repo' (not found, or token lacks Administration:write)"

echo "Target repo: $repo"
echo "Environments: ${ENVIRONMENTS[*]}"
echo "Allowed branch patterns: ${ALLOWED_BRANCHES[*]}"
echo

upsert_environment() {
    local env="$1"
    echo "==> $env: upsert environment"
    # PUT is idempotent. custom_branch_policies=true means the allowed list is
    # managed via the deployment-branch-policies subresource (set below).
    gh api --method PUT "repos/$repo/environments/$env" \
        -F "wait_timer=0" \
        -F "prevent_self_review=false" \
        -F "reviewers=[]" \
        -F "deployment_branch_policy[protected_branches]=false" \
        -F "deployment_branch_policy[custom_branch_policies]=true" \
        >/dev/null
}

reconcile_branch_policies() {
    local env="$1"
    local existing_ids
    existing_ids="$(gh api \
        "repos/$repo/environments/$env/deployment-branch-policies" \
        -q '.branch_policies[].id' 2>/dev/null || true)"

    if [[ -n "$existing_ids" ]]; then
        echo "    clearing existing branch policies"
        while read -r id; do
            [[ -z "$id" ]] && continue
            gh api --method DELETE \
                "repos/$repo/environments/$env/deployment-branch-policies/$id" \
                >/dev/null
        done <<< "$existing_ids"
    fi

    for pattern in "${ALLOWED_BRANCHES[@]}"; do
        echo "    allow branch: $pattern"
        gh api --method POST \
            "repos/$repo/environments/$env/deployment-branch-policies" \
            -f "name=$pattern" \
            -f "type=branch" \
            >/dev/null
    done
}

for env in "${ENVIRONMENTS[@]}"; do
    upsert_environment "$env"
    reconcile_branch_policies "$env"
done

echo
echo "Done. Review at: https://github.com/$repo/settings/environments"
