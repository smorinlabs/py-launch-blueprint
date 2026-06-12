#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "rich>=13.0",
# ]
# ///
"""init-doctor — audit migration completeness and environment readiness.

Two check classes:
  * MIGRATION — blueprint identity drift; only ever changed by `init`.
  * ENVIRONMENT — tools on PATH, lockfile sync, hooks installed; `--fix` may
                  remediate these (it never touches identity content).

Exit codes:
  0   all checks passed
  1   one or more checks reported error (CI-usable)
  2   doctor itself failed (missing manifest, IO error, ...)

Flags:
    --fix              Apply safe environment remediations (uv sync, install hooks).
    --json             Emit JSON instead of human-readable output.
    --skip env|mig     Skip a check class (run only the other).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "ci"))
from check_guard_wiring import check as check_guard_wiring
from common import (
    BLUEPRINT_IDENTITY,
    MARKER_PATH,
    REPO_ROOT,
    iter_repo_files,
    load_manifest,
)

Status = Literal["pass", "warn", "error"]


@dataclass
class Finding:
    name: str
    status: Status
    message: str

    def render(self, use_color: bool = True) -> str:
        colors = {"pass": "\033[32m", "warn": "\033[33m", "error": "\033[31m"}
        reset = "\033[0m"
        c = colors[self.status] if use_color else ""
        r = reset if use_color else ""
        tag = {"pass": " ok  ", "warn": "warn ", "error": "error"}[self.status]
        return f"  {c}[{tag}]{r} {self.name:<36} {self.message}"


@dataclass
class Report:
    migration: list[Finding] = field(default_factory=list)
    environment: list[Finding] = field(default_factory=list)
    post_init: list[Finding] = field(default_factory=list)

    def exit_code(self) -> int:
        all_findings = self.migration + self.environment + self.post_init
        return 1 if any(f.status == "error" for f in all_findings) else 0


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=check
    )


# ──────────────────────────────────────────────────────────────
# Migration checks
# ──────────────────────────────────────────────────────────────


def check_marker_present() -> Finding:
    if not MARKER_PATH.exists():
        return Finding(
            "marker",
            "warn",
            f"{MARKER_PATH.relative_to(REPO_ROOT)} not found — init not run yet",
        )
    return Finding("marker", "pass", f"{MARKER_PATH.relative_to(REPO_ROOT)} present")


def check_no_identity_leftover() -> Finding:
    """No blueprint identity value should remain anywhere outside init/.

    Excludes files declared in the manifest's `[[regenerate]]` list — those
    are generated artifacts (lockfiles) whose identity content is the
    responsibility of the generator (uv/bun), not the rewrite engine.
    """
    try:
        manifest = load_manifest()
        regenerate_paths = {
            (REPO_ROOT / r.path).resolve() for r in manifest.regenerates
        }
    except (FileNotFoundError, OSError):
        regenerate_paths = set()

    from common import is_bootstrap_path

    leftover: dict[str, list[Path]] = {}
    for value in BLUEPRINT_IDENTITY.values():
        for path in iter_repo_files():
            if is_bootstrap_path(path):
                continue  # bootstrap tooling (init/, the agent skill), not migration targets
            if path.resolve() in regenerate_paths:
                continue
            try:
                if value in path.read_text(encoding="utf-8"):
                    leftover.setdefault(value, []).append(path)
            except (OSError, UnicodeDecodeError):
                continue
    if not leftover:
        return Finding(
            "no-identity-leak", "pass", "no blueprint identity values remain"
        )
    sample = next(iter(leftover))
    n = sum(len(v) for v in leftover.values())
    return Finding(
        "no-identity-leak",
        "error",
        f"{n} leftover identity occurrences across {len(leftover)} values "
        f"(e.g., {sample!r} in {leftover[sample][0].relative_to(REPO_ROOT)})",
    )


def check_marker_matches_state() -> Finding:
    """The marker's recorded answers should match what's actually in the files."""
    if not MARKER_PATH.exists():
        return Finding("marker-matches", "warn", "marker missing — skip")
    try:
        recorded = tomllib.loads(MARKER_PATH.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return Finding("marker-matches", "error", f"marker is unreadable: {e}")
    answers = recorded.get("answers", {})
    if not answers:
        return Finding("marker-matches", "warn", "marker has no [answers] section")
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return Finding("marker-matches", "warn", "no pyproject.toml — skip")
    text = pyproject.read_text(encoding="utf-8")
    expected_pkg = answers.get("package_name")
    if expected_pkg and f'name = "{expected_pkg}"' not in text:
        return Finding(
            "marker-matches",
            "error",
            f"marker says package_name={expected_pkg!r} but pyproject.toml [project].name doesn't match",
        )
    return Finding(
        "marker-matches", "pass", "marker answers consistent with pyproject.toml"
    )


def _module_root(py_path: Path) -> str:
    """Read ``[tool.uv.build-backend].module-root`` from pyproject (default '').

    Lets the package-dir check honor a src/ layout (module-root = "src")
    without hardcoding the location.
    """
    if not py_path.exists():
        return ""
    try:
        data = tomllib.loads(py_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ""
    bb = data.get("tool", {}).get("uv", {}).get("build-backend", {})
    root = bb.get("module-root", "")
    return root if isinstance(root, str) else ""


def check_internal_consistency() -> list[Finding]:
    """Justfile/pyproject/conf.py/LICENSE all agree on package, command, year, owner."""
    findings: list[Finding] = []
    py_path = REPO_ROOT / "pyproject.toml"
    just_path = REPO_ROOT / "Justfile"
    license_path = REPO_ROOT / "LICENSE"
    conf_path = REPO_ROOT / "docs" / "source" / "conf.py"

    def _scrape(path: Path, pattern: str) -> str | None:
        import re

        if not path.exists():
            return None
        m = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
        return m.group(1) if m else None

    py_name = _scrape(py_path, r'^name\s*=\s*"([^"]+)"')
    just_pkg = _scrape(just_path, r'^py_package_name\s*:=\s*"([^"]+)"')
    just_cmd = _scrape(just_path, r'^app_name\s*:=\s*"([^"]+)"')

    if py_name and just_pkg and py_name != just_pkg:
        findings.append(
            Finding(
                "consistency/package-name",
                "error",
                f"pyproject.toml name={py_name!r} ≠ Justfile py_package_name={just_pkg!r}",
            )
        )
    elif py_name and just_pkg:
        findings.append(Finding("consistency/package-name", "pass", f"{py_name}"))

    if just_pkg:
        # Honor the build backend's module-root so src/ layout resolves
        # to src/<pkg>/ instead of <pkg>/ at the repo root.
        module_root = _module_root(py_path)
        rel = f"{module_root}/{just_pkg}" if module_root else just_pkg
        pkg_dir = REPO_ROOT / rel
        if not pkg_dir.is_dir():
            findings.append(
                Finding(
                    "consistency/package-dir",
                    "error",
                    f"package directory {rel}/ does not exist",
                )
            )
        else:
            findings.append(
                Finding("consistency/package-dir", "pass", f"{rel}/ exists")
            )

    if just_cmd:
        py_text = py_path.read_text(encoding="utf-8") if py_path.exists() else ""
        if f"{just_cmd} =" in py_text or f'"{just_cmd}"' in py_text:
            findings.append(Finding("consistency/cli-command", "pass", just_cmd))
        else:
            findings.append(
                Finding(
                    "consistency/cli-command",
                    "error",
                    f"Justfile app_name={just_cmd!r} not found in [project.scripts]",
                )
            )

    license_year = _scrape(license_path, r"Copyright \(c\) (\d{4})")
    py_year = _scrape(py_path, r"Copyright \(c\) (\d{4})")
    conf_year = _scrape(conf_path, r"copyright\s*=\s*['\"](\d{4})")
    years = {"LICENSE": license_year, "pyproject.toml": py_year, "conf.py": conf_year}
    distinct = {y for y in years.values() if y}
    if len(distinct) > 1:
        findings.append(
            Finding(
                "consistency/copyright-year",
                "warn",
                f"year mismatch: {years}",
            )
        )
    elif distinct:
        findings.append(
            Finding("consistency/copyright-year", "pass", next(iter(distinct)))
        )

    return findings


def run_migration_checks() -> list[Finding]:
    findings: list[Finding] = []
    findings.append(check_marker_present())
    findings.append(check_no_identity_leftover())
    findings.append(check_marker_matches_state())

    just = REPO_ROOT / "Justfile"
    if just.exists():
        gw = check_guard_wiring(just)
        findings.append(
            Finding(
                "guard-wiring", "pass" if gw.ok else "error", "; ".join(gw.messages)
            )
        )
    findings.extend(check_internal_consistency())
    return findings


# ──────────────────────────────────────────────────────────────
# Environment checks
# ──────────────────────────────────────────────────────────────

REQUIRED_TOOLS = ("just", "uv", "git", "bun", "lefthook", "gitleaks", "cog")


def check_tool(name: str) -> Finding:
    if shutil.which(name) is None:
        return Finding(
            f"tool/{name}", "warn", f"{name} not on PATH (some recipes won't work)"
        )
    return Finding(f"tool/{name}", "pass", f"{name} available")


def check_python_version() -> Finding:
    v = sys.version_info
    if (v.major, v.minor) < (3, 12):
        return Finding(
            "python-version",
            "error",
            f"Python {v.major}.{v.minor} < 3.12 required (ITM-033)",
        )
    return Finding("python-version", "pass", f"Python {v.major}.{v.minor}.{v.micro}")


def check_origin_configured() -> Finding:
    res = _run(["git", "remote", "get-url", "origin"])
    if res.returncode != 0 or not res.stdout.strip():
        return Finding(
            "git-origin",
            "warn",
            "no `origin` remote configured (mode #3 — clone-reinit)",
        )
    return Finding("git-origin", "pass", res.stdout.strip())


def check_venv_present(fix: bool = False) -> Finding:
    venv = REPO_ROOT / ".venv"
    if venv.exists():
        return Finding("venv", "pass", f"{venv.relative_to(REPO_ROOT)} present")
    if fix and shutil.which("uv"):
        res = _run(["uv", "sync"])
        if res.returncode == 0:
            return Finding("venv", "pass", "created via `uv sync --fix`")
        return Finding("venv", "error", f"`uv sync` failed: {res.stderr.strip()[:120]}")
    return Finding("venv", "warn", "no .venv — run `uv sync` (or `init-doctor --fix`)")


def check_lefthook_installed() -> Finding:
    if not (REPO_ROOT / ".git" / "hooks" / "pre-commit").exists():
        return Finding(
            "git-hooks", "warn", "lefthook not installed — run `just hooks-install`"
        )
    return Finding("git-hooks", "pass", "pre-commit hook present")


def run_environment_checks(fix: bool) -> list[Finding]:
    findings = [check_python_version(), check_origin_configured()]
    findings.extend(check_tool(t) for t in REQUIRED_TOOLS)
    findings.append(check_venv_present(fix=fix))
    findings.append(check_lefthook_installed())
    return findings


# ──────────────────────────────────────────────────────────────
# Post-init checks (consistency between marker [post_init] section
# and the actual workflow file locations + ci.yml gate state)
# ──────────────────────────────────────────────────────────────

POST_INIT_WORKFLOWS = (
    # (workflow filename, marker dotted-key, "enabled" expectation)
    ("publish.yml", "publishing.pypi"),
    ("release-please.yml", "publishing.release_please"),
)
_CODECOV_GATE_MARKER = "# post-init: codecov-gated"


def _read_post_init_section() -> dict | None:
    if not MARKER_PATH.exists():
        return None
    try:
        raw = tomllib.loads(MARKER_PATH.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return None
    return raw.get("post_init")


def _dotted_get(d: dict, path: str) -> str | None:
    cur: object = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur if isinstance(cur, str) else None


def check_post_init_marker_present() -> Finding:
    pi = _read_post_init_section()
    if pi is None:
        return Finding(
            "post_init/marker",
            "warn",
            "marker has no [post_init] section — run `just post-init` to configure publishing/Codecov/RTD",
        )
    date = pi.get("date", "unknown")
    mode = pi.get("mode", "unknown")
    return Finding("post_init/marker", "pass", f"present (date={date}, mode={mode})")


def check_post_init_workflows_match_state() -> list[Finding]:
    """For each tracked workflow, the file's location must match marker state."""
    pi = _read_post_init_section()
    if pi is None:
        return []  # nothing to check yet
    findings: list[Finding] = []
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    disabled_dir = REPO_ROOT / ".github" / "workflows.disabled"
    for wf_name, key in POST_INIT_WORKFLOWS:
        state = _dotted_get(pi, key)
        in_active = (workflows_dir / wf_name).exists()
        in_disabled = (disabled_dir / wf_name).exists()
        check_name = f"post_init/{key}"
        if state == "enabled":
            if in_active and not in_disabled:
                findings.append(
                    Finding(check_name, "pass", f"{wf_name} active (as marker says)")
                )
            elif in_disabled and not in_active:
                findings.append(
                    Finding(
                        check_name,
                        "error",
                        f"marker says enabled but {wf_name} is in workflows.disabled/ — "
                        f"run `just post-init` to reconcile",
                    )
                )
            elif not in_active and not in_disabled:
                findings.append(
                    Finding(
                        check_name,
                        "error",
                        f"marker says enabled but {wf_name} not found anywhere",
                    )
                )
            else:  # both — impossible-but-defensive
                findings.append(
                    Finding(
                        check_name,
                        "error",
                        f"{wf_name} exists in BOTH workflows/ and workflows.disabled/",
                    )
                )
        elif state == "disabled":
            if in_disabled and not in_active:
                findings.append(
                    Finding(check_name, "pass", f"{wf_name} disabled (as marker says)")
                )
            elif in_active and not in_disabled:
                findings.append(
                    Finding(
                        check_name,
                        "error",
                        f"marker says disabled but {wf_name} is in workflows/ — "
                        f"run `just post-init` to reconcile",
                    )
                )
            elif not in_active and not in_disabled:
                findings.append(
                    Finding(
                        check_name,
                        "warn",
                        f"marker says disabled and {wf_name} not found anywhere (may have been deleted)",
                    )
                )
            else:
                findings.append(
                    Finding(
                        check_name,
                        "error",
                        f"{wf_name} exists in BOTH workflows/ and workflows.disabled/",
                    )
                )
        # state == "deferred" or None — no expectation
    return findings


def check_post_init_codecov_gate() -> Finding:
    """If marker says codecov is enabled/disabled, ci.yml must carry the gate marker."""
    pi = _read_post_init_section()
    if pi is None:
        return Finding("post_init/codecov-gate", "pass", "n/a — post-init not run")
    codecov_status = pi.get("codecov", {}).get("status")
    if codecov_status in (None, "deferred"):
        return Finding(
            "post_init/codecov-gate",
            "pass",
            f"n/a — codecov status={codecov_status or 'unset'}",
        )
    ci_yml = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    if not ci_yml.exists():
        return Finding("post_init/codecov-gate", "warn", "ci.yml not found")
    has_marker = _CODECOV_GATE_MARKER in ci_yml.read_text(encoding="utf-8")
    if has_marker:
        return Finding(
            "post_init/codecov-gate", "pass", "ci.yml carries the codecov-gated marker"
        )
    return Finding(
        "post_init/codecov-gate",
        "error",
        f"marker says codecov={codecov_status} but ci.yml lacks the gate edit — "
        f"run `just post-init` to apply",
    )


def check_post_init_oidc_freshness() -> Finding:
    """Informational: surface OIDC verification timestamps if recorded."""
    pi = _read_post_init_section()
    if pi is None:
        return Finding("post_init/oidc", "pass", "n/a")
    oidc = pi.get("oidc", {})
    pypi_ts = oidc.get("pypi_trust_verified_at")
    testpypi_ts = oidc.get("testpypi_trust_verified_at")
    parts = []
    if pypi_ts:
        parts.append(f"pypi@{pypi_ts}")
    if testpypi_ts:
        parts.append(f"testpypi@{testpypi_ts}")
    if not parts:
        publishing = pi.get("publishing", {})
        if publishing.get("pypi") == "enabled":
            return Finding(
                "post_init/oidc",
                "warn",
                "publishing enabled but no OIDC verification recorded — "
                "re-run `just post-init` after your first release",
            )
        return Finding("post_init/oidc", "pass", "n/a — publishing not enabled")
    return Finding("post_init/oidc", "pass", "verified " + ", ".join(parts))


def run_post_init_checks() -> list[Finding]:
    findings: list[Finding] = [check_post_init_marker_present()]
    findings.extend(check_post_init_workflows_match_state())
    findings.append(check_post_init_codecov_gate())
    findings.append(check_post_init_oidc_freshness())
    return findings


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────


def render_report(report: Report, use_color: bool = True) -> str:
    lines: list[str] = []
    if report.migration:
        lines.append("\nMigration checks:")
        lines.extend(f.render(use_color) for f in report.migration)
    if report.post_init:
        lines.append("\nPost-init checks:")
        lines.extend(f.render(use_color) for f in report.post_init)
    if report.environment:
        lines.append("\nEnvironment checks:")
        lines.extend(f.render(use_color) for f in report.environment)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--skip",
        choices=["env", "mig", "pi"],
        default=None,
        help="skip a check class: env (environment), mig (migration), pi (post-init)",
    )
    args = parser.parse_args(argv)

    report = Report()
    try:
        if args.skip != "mig":
            report.migration = run_migration_checks()
        if args.skip != "pi":
            report.post_init = run_post_init_checks()
        if args.skip != "env":
            report.environment = run_environment_checks(fix=args.fix)
    except Exception as e:
        print(f"init-doctor: internal error — {e}", file=sys.stderr)
        return 2

    if args.json:
        out = {
            "migration": [asdict(f) for f in report.migration],
            "post_init": [asdict(f) for f in report.post_init],
            "environment": [asdict(f) for f in report.environment],
            "exit_code": report.exit_code(),
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_report(report, use_color=sys.stdout.isatty()))

    return report.exit_code()


if __name__ == "__main__":
    sys.exit(main())
