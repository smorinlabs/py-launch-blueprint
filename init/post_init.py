#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""post_init — guides through publishing / Codecov / ReadTheDocs setup.

Runs AFTER `init.py` has rebranded the project. Asks Yes/No/Defer per
service, applies the user's decisions (file moves, secret-set, YAML edits),
walks through anything that can only be done in a browser (OIDC trust at
PyPI, ReadTheDocs import), and records everything in
`init/.blueprint-initialized` under a `[post_init]` table for the doctor
and for re-runs.

Invocation:
    just post-init             # interactive walkthrough
    just post-init --status    # show current state, don't change anything
    just post-init --skip-remote  # only do local edits; defer gh/PyPI work

Re-run semantics:
    First run        — asks each decision fresh, defaults to "Defer".
    Subsequent runs  — shows current state as the default; pick a new
                       answer to flip a decision (file moves/edits applied
                       symmetrically).

What V1 owns:
    1. Publishing to PyPI (+ TestPyPI mirror, + release-please version PRs)
    2. Codecov coverage uploads
    3. ReadTheDocs docs publishing (informational walkthrough only)

What V1 explicitly does NOT own:
    branch protection, FUNDING.yml/Sponsors, dependabot tweaks, security
    workflow gating, container registries, --config headless mode.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    INIT_DIR,
    MARKER_PATH,
    REPO_ROOT,
    parse_origin,
)

POST_INIT_VERSION = "0.1.0"
DISABLED_WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows.disabled"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
CI_YML = WORKFLOWS_DIR / "ci.yml"

ENABLED, DISABLED, DEFERRED = "enabled", "disabled", "deferred"
STATES = (ENABLED, DISABLED, DEFERRED)


# ──────────────────────────────────────────────────────────────
# State (the [post_init] section of the marker)
# ──────────────────────────────────────────────────────────────


@dataclass
class PublishingConfig:
    pypi: str = DEFERRED
    testpypi: str = DEFERRED
    release_please: str = DEFERRED


@dataclass
class CodecovConfig:
    status: str = DEFERRED  # enabled | disabled | deferred
    token_set: bool = False


@dataclass
class RTDConfig:
    status: str = DEFERRED  # configured | declined | deferred


@dataclass
class PostInitConfig:
    version: str = POST_INIT_VERSION
    date: str = ""
    mode: str = "full"  # full | partial-no-remote | reconfigure
    publishing: PublishingConfig = field(default_factory=PublishingConfig)
    codecov: CodecovConfig = field(default_factory=CodecovConfig)
    readthedocs: RTDConfig = field(default_factory=RTDConfig)
    pypi_trust_verified_at: str | None = None
    testpypi_trust_verified_at: str | None = None


# ──────────────────────────────────────────────────────────────
# Printing helpers (no rich/questionary — kept stdlib for portability)
# ──────────────────────────────────────────────────────────────


def _c(code: str, s: str) -> str:
    if not sys.stdout.isatty():
        return s
    return f"\033[{code}m{s}\033[0m"


def header(s: str) -> None:
    print()
    print(_c("36;1", f"▸ {s}"))


def info(s: str) -> None:
    print(_c("36", f"  {s}"))


def ok(s: str) -> None:
    print(_c("32", f"  ✓ {s}"))


def warn(s: str) -> None:
    print(_c("33", f"  ⚠ {s}"))


def err(s: str) -> None:
    print(_c("31", f"  ✗ {s}"), file=sys.stderr)


# ──────────────────────────────────────────────────────────────
# Preconditions
# ──────────────────────────────────────────────────────────────


class PreconditionError(RuntimeError):
    pass


def _run(
    cmd: list[str], cwd: Path | None = None, check: bool = False
) -> subprocess.CompletedProcess:
    # Resolve cwd at call time, not def time — keeps test monkeypatching of
    # REPO_ROOT effective.
    return subprocess.run(
        cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True, check=check
    )


def check_preconditions() -> bool:
    """Returns True if remote is available (full flow), False otherwise (partial)."""
    if not MARKER_PATH.exists():
        raise PreconditionError(
            f"{MARKER_PATH.relative_to(REPO_ROOT)} not found — run `just init` first."
        )
    if shutil.which("gh") is None:
        raise PreconditionError("gh CLI not installed. See https://cli.github.com/")
    auth = _run(["gh", "auth", "status"])
    if auth.returncode != 0:
        raise PreconditionError("gh is not authenticated. Run: gh auth login")
    # Remote detection: parse origin → check the repo exists on GitHub.
    origin = _run(["git", "remote", "get-url", "origin"]).stdout.strip()
    if not origin:
        warn("no `origin` remote set — running in partial-no-remote mode.")
        return False
    parsed = parse_origin(origin)
    if not parsed:
        warn(f"could not parse origin URL ({origin!r}) — partial mode.")
        return False
    owner, repo = parsed
    rv = _run(["gh", "repo", "view", f"{owner}/{repo}", "--json", "name"])
    if rv.returncode != 0:
        warn(
            f"{owner}/{repo} not found via gh — push to GitHub then re-run for remote setup."
        )
        return False
    return True


def get_origin_owner_repo() -> tuple[str, str] | None:
    origin = _run(["git", "remote", "get-url", "origin"]).stdout.strip()
    return parse_origin(origin) if origin else None


# ──────────────────────────────────────────────────────────────
# Marker I/O (preserves existing [meta] + [answers]; manages [post_init])
# ──────────────────────────────────────────────────────────────


def read_existing_post_init() -> PostInitConfig | None:
    raw = tomllib.loads(MARKER_PATH.read_text(encoding="utf-8"))
    pi = raw.get("post_init")
    if not pi:
        return None
    cfg = PostInitConfig(
        version=pi.get("version", POST_INIT_VERSION),
        date=pi.get("date", ""),
        mode=pi.get("mode", "full"),
        publishing=PublishingConfig(**pi.get("publishing", {})),
        codecov=CodecovConfig(**pi.get("codecov", {})),
        readthedocs=RTDConfig(**pi.get("readthedocs", {})),
        pypi_trust_verified_at=pi.get("oidc", {}).get("pypi_trust_verified_at"),
        testpypi_trust_verified_at=pi.get("oidc", {}).get("testpypi_trust_verified_at"),
    )
    return cfg


def _render_post_init_toml(cfg: PostInitConfig) -> str:
    lines = [
        "",
        "[post_init]",
        f'version = "{cfg.version}"',
        f'date    = "{cfg.date}"',
        f'mode    = "{cfg.mode}"',
        "",
        "[post_init.publishing]",
        f'pypi           = "{cfg.publishing.pypi}"',
        f'testpypi       = "{cfg.publishing.testpypi}"',
        f'release_please = "{cfg.publishing.release_please}"',
        "",
        "[post_init.codecov]",
        f'status    = "{cfg.codecov.status}"',
        f"token_set = {str(cfg.codecov.token_set).lower()}",
        "",
        "[post_init.readthedocs]",
        f'status = "{cfg.readthedocs.status}"',
        "",
        "[post_init.oidc]",
    ]
    if cfg.pypi_trust_verified_at:
        lines.append(f'pypi_trust_verified_at     = "{cfg.pypi_trust_verified_at}"')
    if cfg.testpypi_trust_verified_at:
        lines.append(f'testpypi_trust_verified_at = "{cfg.testpypi_trust_verified_at}"')
    return "\n".join(lines) + "\n"


def write_marker_with_post_init(cfg: PostInitConfig) -> None:
    text = MARKER_PATH.read_text(encoding="utf-8")
    # Strip any existing [post_init...] section to the end.
    idx = text.find("[post_init]")
    base = text[:idx].rstrip() + "\n" if idx != -1 else text.rstrip() + "\n"
    cfg.date = _dt.date.today().isoformat()
    MARKER_PATH.write_text(base + _render_post_init_toml(cfg), encoding="utf-8")


# ──────────────────────────────────────────────────────────────
# Interactive prompts (stdlib `input` — keep deps to zero)
# ──────────────────────────────────────────────────────────────


def ask_choice(prompt: str, choices: tuple[str, ...], default: str) -> str:
    options = "/".join(c.upper() if c == default else c for c in choices)
    while True:
        try:
            raw = input(f"  {prompt} [{options}]: ").strip().lower()
        except EOFError:
            return default
        if not raw:
            return default
        # accept first-letter shortcuts too
        for c in choices:
            if raw == c or raw == c[0]:
                return c
        warn(f"choose one of: {', '.join(choices)}")


def ask_yes_no_defer(prompt: str, current: str | None) -> str:
    """Returns 'enabled', 'disabled', or 'deferred'."""
    current_default = current or DEFERRED
    short_to_state = {"y": ENABLED, "n": DISABLED, "d": DEFERRED}
    default_short = next(k for k, v in short_to_state.items() if v == current_default)
    if current:
        prompt = f"{prompt} (currently: {current})"
    ans = ask_choice(prompt, ("y", "n", "d"), default_short)
    return short_to_state[ans]


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    ans = ask_choice(prompt, ("y", "n"), "y" if default else "n")
    return ans == "y"


# ──────────────────────────────────────────────────────────────
# Decision flow
# ──────────────────────────────────────────────────────────────


def ask_publishing(current: PublishingConfig | None) -> PublishingConfig:
    header("Publishing — release artifacts to PyPI")
    cur = current or PublishingConfig()
    pypi = ask_yes_no_defer("Publish to PyPI?", cur.pypi)
    new = PublishingConfig(pypi=pypi)
    if pypi == ENABLED:
        new.testpypi = (
            ENABLED
            if ask_yes_no(
                "Mirror to TestPyPI for pre-release validation? (recommended)",
                default=cur.testpypi != DISABLED,
            )
            else DISABLED
        )
        new.release_please = (
            ENABLED
            if ask_yes_no(
                "Use release-please to auto-generate version-bump PRs? (recommended)",
                default=cur.release_please != DISABLED,
            )
            else DISABLED
        )
    elif pypi == DISABLED:
        new.testpypi = DISABLED
        new.release_please = (
            DISABLED
            if ask_yes_no(
                "Also disable release-please version-bump PRs? (recommended when not publishing)",
                default=True,
            )
            else ENABLED
        )
    else:  # DEFERRED
        new.testpypi = cur.testpypi
        new.release_please = cur.release_please
    return new


def ask_codecov(current: CodecovConfig | None) -> CodecovConfig:
    header("Codecov — upload coverage reports")
    cur = current or CodecovConfig()
    status_choice = ask_yes_no_defer("Upload coverage to Codecov?", cur.status)
    new = CodecovConfig(status=status_choice, token_set=cur.token_set)
    return new


def ask_readthedocs(current: RTDConfig | None) -> RTDConfig:
    header("ReadTheDocs — publish docs at readthedocs.org")
    cur = current or RTDConfig()
    # RTDConfig uses configured/declined/deferred instead of enabled/disabled.
    cur_for_prompt = {
        "configured": ENABLED,
        "declined": DISABLED,
        "deferred": DEFERRED,
    }.get(cur.status, DEFERRED)
    pick = ask_yes_no_defer("Publish docs to ReadTheDocs?", cur_for_prompt)
    rev = {ENABLED: "configured", DISABLED: "declined", DEFERRED: "deferred"}
    return RTDConfig(status=rev[pick])


# ──────────────────────────────────────────────────────────────
# Apply: local file operations
# ──────────────────────────────────────────────────────────────


def _git_mv(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Try git mv (clean diff); fall back to shutil if file is untracked.
    r = _run(["git", "mv", str(src), str(dst)])
    if r.returncode != 0:
        shutil.move(str(src), str(dst))


def disable_workflow(name: str) -> bool:
    """Move .github/workflows/<name> → workflows.disabled/<name>. Idempotent."""
    src = WORKFLOWS_DIR / name
    dst = DISABLED_WORKFLOWS_DIR / name
    if dst.exists() and not src.exists():
        return False  # already disabled
    if not src.exists():
        warn(f"{name} not found in workflows/ — skipping")
        return False
    _git_mv(src, dst)
    ok(f"disabled workflow: moved {name} → workflows.disabled/")
    return True


def enable_workflow(name: str) -> bool:
    """Reverse of disable_workflow."""
    src = DISABLED_WORKFLOWS_DIR / name
    dst = WORKFLOWS_DIR / name
    if dst.exists() and not src.exists():
        return False  # already enabled
    if not src.exists():
        warn(f"{name} not found in workflows.disabled/ — skipping")
        return False
    _git_mv(src, dst)
    ok(f"enabled workflow: moved workflows.disabled/{name} → workflows/")
    return True


_CODECOV_GATE_MARKER = "# post-init: codecov-gated"


def edit_ci_yml_codecov_gate() -> bool:
    """Add `&& secrets.CODECOV_TOKEN != ''` to the codecov step's `if:`, and
    append a warning step that runs when the token is unset.

    Idempotent — does nothing if the gate marker already exists.
    """
    if not CI_YML.exists():
        warn(f"{CI_YML.relative_to(REPO_ROOT)} not found — skipping codecov gate")
        return False
    text = CI_YML.read_text(encoding="utf-8")
    if _CODECOV_GATE_MARKER in text:
        info("ci.yml codecov gate already present — no edit needed")
        return False

    # Find the codecov step's `if:` line and append the secret check.
    lines = text.splitlines()
    new_lines: list[str] = []
    gated = False
    warning_step_added = False
    for i, ln in enumerate(lines):
        # The codecov step's `if:` precedes `uses: codecov/codecov-action`.
        # Detect the pattern: gate the existing `if:` on this step.
        if (
            not gated
            and ln.lstrip().startswith("if:")
            and i + 1 < len(lines)
            and "codecov/codecov-action" in lines[i + 1]
        ):
            new_lines.append(ln + " && secrets.CODECOV_TOKEN != ''")
            gated = True
            continue
        new_lines.append(ln)

    # Append the warning step right after the codecov step. Find the end of
    # the codecov step (next sibling or end of job) and inject.
    if gated and not warning_step_added:
        # Find the line with the codecov `uses:` and walk to the end of its block.
        codecov_idx = next(
            (i for i, ln in enumerate(new_lines) if "codecov/codecov-action" in ln),
            None,
        )
        if codecov_idx is not None:
            # The step ends when we hit a line with less indent than the step's
            # body, or a `- name:` / `- uses:` at the step indent. Find indent
            # of the codecov step's `-` (look backwards).
            step_indent = None
            for j in range(codecov_idx - 1, -1, -1):
                if new_lines[j].lstrip().startswith("- "):
                    step_indent = len(new_lines[j]) - len(new_lines[j].lstrip())
                    break
            if step_indent is not None:
                # Walk forward to find where the step body ends.
                end_idx = codecov_idx + 1
                while end_idx < len(new_lines):
                    ln = new_lines[end_idx]
                    if not ln.strip():
                        end_idx += 1
                        continue
                    cur_indent = len(ln) - len(ln.lstrip())
                    if cur_indent <= step_indent and ln.lstrip().startswith("- "):
                        break
                    if cur_indent <= step_indent and ln.strip():
                        break
                    end_idx += 1
                # Insert the warning step at end_idx (before the next step / job end).
                pad = " " * step_indent
                snippet = [
                    "",
                    f"{pad}- name: Codecov upload dormant warning  {_CODECOV_GATE_MARKER}",
                    f"{pad}  if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12' && secrets.CODECOV_TOKEN == ''",
                    f"{pad}  run: |",
                    f'{pad}    echo "::warning::Codecov uploads dormant — set CODECOV_TOKEN repo secret to enable."',
                ]
                new_lines = new_lines[:end_idx] + snippet + new_lines[end_idx:]
                warning_step_added = True

    if not gated:
        warn("could not locate codecov step in ci.yml — manual edit required")
        return False

    CI_YML.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    ok("ci.yml: codecov step gated on CODECOV_TOKEN + warning step appended")
    return True


# ──────────────────────────────────────────────────────────────
# Apply: remote operations (skipped in partial mode)
# ──────────────────────────────────────────────────────────────


def run_setup_github_environments(repo_slug: str, envs: list[str]) -> bool:
    """Wraps init/setup-github-environments.sh for the chosen envs."""
    script = INIT_DIR / "setup-github-environments.sh"
    if not script.exists():
        warn(f"{script.relative_to(REPO_ROOT)} not found — skip env creation")
        return False
    # The existing script creates BOTH pypi and testpypi. We let it do that
    # (idempotent; downstream PyPI trust setup just won't be done for envs
    # the user doesn't intend to use).
    r = _run(["bash", str(script), repo_slug])
    if r.returncode != 0:
        err(f"setup-github-environments.sh failed: {r.stderr.strip()[:200]}")
        return False
    ok(f"GitHub environments ready for {repo_slug}")
    return True


def set_codecov_token_via_gh(repo_slug: str, token: str) -> bool:
    r = subprocess.run(
        ["gh", "secret", "set", "CODECOV_TOKEN", "--repo", repo_slug, "--body", token],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        err(f"gh secret set failed: {r.stderr.strip()[:200]}")
        return False
    ok(f"CODECOV_TOKEN secret set on {repo_slug}")
    return True


# ──────────────────────────────────────────────────────────────
# OIDC walkthrough (assisted manual + verification polling)
# ──────────────────────────────────────────────────────────────


def _open_url(url: str) -> bool:
    for cmd in (["open", url], ["xdg-open", url]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                return True
        except FileNotFoundError:
            continue
    return False


def print_oidc_form_values(
    project_name: str,
    owner: str,
    repo: str,
    target: str,
) -> str:
    """Returns the URL the user must visit."""
    env_name = "pypi" if target == "pypi" else "testpypi"
    base = "https://pypi.org" if target == "pypi" else "https://test.pypi.org"
    url = f"{base}/manage/account/publishing/"
    print()
    info("Paste these values into the Pending Publisher form at:")
    info(_c("36;4", url))
    print()
    print(f"    PyPI Project Name:       {_c('1', project_name)}")
    print(f"    Owner:                   {_c('1', owner)}")
    print(f"    Repository name:         {_c('1', repo)}")
    print(f"    Workflow name:           {_c('1', 'publish.yml')}")
    print(f"    Environment name:        {_c('1', env_name)}")
    print()
    return url


def poll_pypi_trust(
    project_name: str,
    target: str,
    timeout_s: int = 300,
) -> bool:
    """Polls the public PyPI JSON until the project exists. Crude but reliable.

    The project page only appears once a Trusted Publisher has produced an
    actual release (PyPI's UI doesn't expose 'pending publishers' publicly).
    For first-time setup we can only verify the project listing — once a
    real release happens, the trust contract is implied.
    """
    base = "https://pypi.org" if target == "pypi" else "https://test.pypi.org"
    url = f"{base}/pypi/{project_name}/json"
    import time

    deadline = time.time() + timeout_s
    info(f"polling {url} (timeout {timeout_s}s; Ctrl-C to skip)")
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 - hardcoded PyPI/TestPyPI URL, not user input
                if resp.status == 200:
                    return True
        except urllib.error.HTTPError as e:
            if e.code != 404:
                warn(f"PyPI returned {e.code}; continuing to poll")
        except (urllib.error.URLError, TimeoutError):
            pass
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            return False
    return False


def oidc_walkthrough(
    project_name: str,
    owner: str,
    repo: str,
    target: str,
) -> str | None:
    """Returns ISO timestamp on verified, None if user skipped."""
    url = print_oidc_form_values(project_name, owner, repo, target)
    if ask_yes_no("Open the URL in your browser now?", default=True):
        if _open_url(url):
            ok("opened in browser")
        else:
            warn("could not auto-open; please open the URL manually")
    if not ask_yes_no(
        "Poll for verification? (waits up to 5 min for a first release)",
        default=False,
    ):
        info("skipped — re-run `just post-init` after your first release to verify")
        return None
    if poll_pypi_trust(project_name, target):
        ts = _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")
        ok(f"verified {target}/{project_name} at {ts}")
        return ts
    warn(f"timed out waiting for {target}/{project_name}; verify manually later")
    return None


# ──────────────────────────────────────────────────────────────
# Status / summary
# ──────────────────────────────────────────────────────────────


def print_status(cfg: PostInitConfig | None) -> None:
    if cfg is None:
        print("post-init has not been run on this project yet.")
        return
    print(f"post-init last ran:  {cfg.date} (mode: {cfg.mode}, v{cfg.version})")
    print()
    print(f"  publishing.pypi           = {cfg.publishing.pypi}")
    print(f"  publishing.testpypi       = {cfg.publishing.testpypi}")
    print(f"  publishing.release_please = {cfg.publishing.release_please}")
    print(
        f"  codecov.status            = {cfg.codecov.status}  (token_set={cfg.codecov.token_set})"
    )
    print(f"  readthedocs.status        = {cfg.readthedocs.status}")
    if cfg.pypi_trust_verified_at:
        print(f"  oidc.pypi_verified_at     = {cfg.pypi_trust_verified_at}")
    if cfg.testpypi_trust_verified_at:
        print(f"  oidc.testpypi_verified_at = {cfg.testpypi_trust_verified_at}")


def print_summary(cfg: PostInitConfig, remote_available: bool) -> None:
    print()
    header("Summary")
    print_status(cfg)
    print()
    if not remote_available:
        warn("partial mode — remote-side setup deferred")
        print("    push to GitHub then re-run `just post-init` to finish")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--status", action="store_true", help="print current state and exit"
    )
    parser.add_argument(
        "--skip-remote", action="store_true", help="skip gh/PyPI ops (local edits only)"
    )
    args = parser.parse_args(argv)

    existing = read_existing_post_init() if MARKER_PATH.exists() else None

    if args.status:
        print_status(existing)
        return 0

    if args.skip_remote:
        # --skip-remote bypasses gh/auth/remote checks entirely; only the
        # marker-existence precondition still applies.
        if not MARKER_PATH.exists():
            err(
                f"{MARKER_PATH.relative_to(REPO_ROOT)} not found — run `just init` first."
            )
            return 1
        remote_available = False
    else:
        try:
            remote_available = check_preconditions()
        except PreconditionError as e:
            err(str(e))
            return 1

    if existing:
        header(f"post-init has already run on this project ({existing.date})")
        print_status(existing)
        if not ask_yes_no(
            "Reconfigure? (current values shown as defaults below)", default=False
        ):
            info("no changes; exiting")
            return 0

    cfg = PostInitConfig(
        mode="full" if remote_available else "partial-no-remote",
        publishing=ask_publishing(existing.publishing if existing else None),
        codecov=ask_codecov(existing.codecov if existing else None),
        readthedocs=ask_readthedocs(existing.readthedocs if existing else None),
        pypi_trust_verified_at=existing.pypi_trust_verified_at if existing else None,
        testpypi_trust_verified_at=existing.testpypi_trust_verified_at
        if existing
        else None,
    )

    # ── Apply local: workflow file moves
    header("Applying local changes")
    publish_state = cfg.publishing.pypi
    if publish_state == ENABLED:
        enable_workflow("publish.yml")
    elif publish_state == DISABLED:
        disable_workflow("publish.yml")

    rp_state = cfg.publishing.release_please
    if rp_state == ENABLED:
        enable_workflow("release-please.yml")
    elif rp_state == DISABLED:
        disable_workflow("release-please.yml")

    # ── Apply local: ci.yml codecov gate (always — gate is conservative, runs whether enabled or not)
    if cfg.codecov.status in (ENABLED, DISABLED):
        edit_ci_yml_codecov_gate()

    # ── Apply remote (skipped in partial flow)
    if remote_available and cfg.publishing.pypi == ENABLED:
        header("Configuring remote (GitHub environments)")
        owner_repo = get_origin_owner_repo()
        if owner_repo:
            slug = f"{owner_repo[0]}/{owner_repo[1]}"
            run_setup_github_environments(slug, ["pypi", "testpypi"])

    # ── Codecov token (only if user said enabled and remote available)
    if remote_available and cfg.codecov.status == ENABLED and not cfg.codecov.token_set:
        if ask_yes_no(
            "Paste your Codecov token now? (else set later via `gh secret set CODECOV_TOKEN`)",
            default=False,
        ):
            try:
                token = input("  CODECOV_TOKEN: ").strip()
            except EOFError:
                token = ""
            if token:
                owner_repo = get_origin_owner_repo()
                if owner_repo:
                    slug = f"{owner_repo[0]}/{owner_repo[1]}"
                    if set_codecov_token_via_gh(slug, token):
                        cfg.codecov.token_set = True

    # ── OIDC walkthrough
    if remote_available and cfg.publishing.pypi == ENABLED:
        header("OIDC trusted-publisher walkthrough")
        # Derive project name from rebranded pyproject [project].name.
        project_name = _derive_project_name()
        owner_repo = get_origin_owner_repo()
        if project_name and owner_repo:
            owner, repo = owner_repo
            if cfg.publishing.pypi == ENABLED:
                ts = oidc_walkthrough(project_name, owner, repo, "pypi")
                if ts:
                    cfg.pypi_trust_verified_at = ts
            if cfg.publishing.testpypi == ENABLED:
                ts = oidc_walkthrough(project_name, owner, repo, "testpypi")
                if ts:
                    cfg.testpypi_trust_verified_at = ts

    # ── RTD informational walkthrough
    if cfg.readthedocs.status == "configured":
        header("ReadTheDocs setup walkthrough")
        owner_repo = get_origin_owner_repo()
        if owner_repo:
            owner, repo = owner_repo
            info("Open: https://readthedocs.org/dashboard/import/")
            info("  1. Sign in with your GitHub account")
            info(f"  2. Find and import: {owner}/{repo}")
            info("  3. Confirm project slug + default branch (usually `main`)")
            info("  4. RTD auto-detects `.readthedocs.yaml` and starts a build")
            if ask_yes_no("Open the import page now?", default=True):
                _open_url("https://readthedocs.org/dashboard/import/")
            ask_yes_no("Press Enter when import is done (or skip)", default=True)

    # ── Write marker
    header("Recording state in marker")
    write_marker_with_post_init(cfg)
    ok(f"wrote [post_init] section to {MARKER_PATH.relative_to(REPO_ROOT)}")

    print_summary(cfg, remote_available)
    return 0


def _derive_project_name() -> str | None:
    pj = REPO_ROOT / "pyproject.toml"
    if not pj.exists():
        return None
    raw = pj.read_text(encoding="utf-8")
    import re

    m = re.search(r'^name\s*=\s*"([^"]+)"', raw, re.MULTILINE)
    return m.group(1) if m else None


if __name__ == "__main__":
    sys.exit(main())
