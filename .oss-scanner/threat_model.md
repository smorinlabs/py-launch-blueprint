# Threat model

py-launch-blueprint is a Python project template. Projects generated from it
inherit its code, CI workflows, and release pipeline, so a flaw here
propagates to every generated project. Report flaws in this repository's own
code, not in its dependencies.

## What this project does and where untrusted input enters

- **Web service** (`src/py_launch_blueprint/web/`, FastAPI). Assume it is
  deployed on the public internet to anonymous clients, as the published
  GHCR image allows. All HTTP input is untrusted: path parameters (notably
  `project_id` on `GET /projects/{project_id}`), query strings, and headers,
  including `Idempotency-Key` (`web/idempotency.py`).
- **Server-held credential.** The web service reads `PLBP_TOKEN` from its
  own environment and calls the upstream API on behalf of anonymous clients.
  Any way a client can steer that token, such as path manipulation reaching
  other upstream endpoints, is in scope.
- **Upstream API client** (`src/py_launch_blueprint/core/adapters/py_api.py`).
  It builds request URLs from caller-supplied path parts
  (`f"{self.BASE_URL}/{path.lstrip('/')}"`) and parses the JSON responses.
  Treat upstream responses as untrusted.
- **CLI** (`plbp`, `src/py_launch_blueprint/cli/`). Inputs: layered TOML
  config files (`core/config.py`, `core/paths.py`), `--token` or
  `$PLBP_TOKEN`, and the `--log-file` and crash-file paths.
- **Log redaction** (`src/py_launch_blueprint/core/logging.py`). It masks
  values whose keys contain `token`, `secret`, `authorization`, or
  `api_key`. A bypass that writes credentials to logs is in scope.
- **GitHub Actions workflows** (`.github/workflows/`). Outsiders can trigger
  three workflows that hold credentials:
  - `claude.yml`: `issues`, `issue_comment`, and
    `pull_request_review_comment`; holds `CLAUDE_CODE_OAUTH_TOKEN`.
  - `audit-triage.yml`: `workflow_run`; holds `META_MUSE_CI_API_KEY`.
  - `difftree-pr-comment.yml`: `pull_request_target`, with a write-scoped
    `GITHUB_TOKEN`.

## Components that matter most / least

High priority:
- The web service, the upstream API client, and the server-held token.
- The CI workflows: workflow injection through untrusted event fields,
  prompt injection into the Claude and Muse jobs, secret exposure, and
  over-broad `GITHUB_TOKEN` permissions.
- The release pipeline: `release-please.yml`, `publish.yml`,
  `publish-container.yml`, and `scripts/release_commits.cjs`. Anything that
  could tamper with PyPI or GHCR artifacts.

Normal priority:
- The CLI and its config and path handling.
- The `press/` configuration that rebrands generated projects.
- Documentation sources under `docs/`.

## How to exercise it

- The image has the full dev environment on `PATH`: run `pytest`, `plbp`,
  `bun`, and `just` directly. The default test set excludes `slow` and
  `live` markers; `pytest -m "not live"` adds the slow tests and still runs
  offline. One test,
  `tests/meta/test_contributors_state.py::test_commit_contributor_first_seen_matches_earliest_non_merge_commit`,
  fails here because the image has no git history; ignore it.
- The upstream API is unreachable offline. Tests stub it: see
  `tests/core/test_py_api_repository.py` and `tests/web/test_app.py`, and
  `core/adapters/in_memory.py` for a network-free repository.
- Run the web service with `python -m py_launch_blueprint.web`, or drive it
  in-process with FastAPI's `TestClient` as `tests/web/` does.
- Workflow tests live in `tests/meta/`; release-generation tests live in
  `tests/release/` and `tests/meta/test_release_generation.py`.

## How you rate severity

- **Critical:** remote code execution; exfiltration of CI secrets or of the
  server's `PLBP_TOKEN`; tampering with PyPI or GHCR releases or with
  generated projects.
- **High:** misuse of the server-held token through path manipulation;
  workflow injection; authentication bypass.
- **Medium:** denial of service; secrets written to logs.
- **Low:** CLI issues that require control of the user's own config files
  or environment.

## Anything to leave alone

- `prototypes/` and `research/`: experimental material, not shipped in the
  package or the image.
