"""Shared utilities for init/, init_doctor/, and CI checks.

Holds the single source of truth for blueprint identity values, the migration-manifest
schema, and answer validation. Imported by init.py, init_doctor.py, the CI scripts in
init/ci/, and the test suite.

No third-party imports — runs under stdlib so the doctor's `check no-blueprint-leak`
path stays usable on a bare clone before `uv sync`.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INIT_DIR = Path(__file__).resolve().parent
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "new-python-project"
# Codex-side symlink to SKILL_DIR (Codex scans $REPO_ROOT/.agents/skills).
SKILL_LINK = REPO_ROOT / ".agents" / "skills" / "new-python-project"
MARKER_PATH = INIT_DIR / ".blueprint-initialized"
CONTRIBUTOR_SENTINEL_PATH = INIT_DIR / ".blueprint-contributor"
MANIFEST_PATH = INIT_DIR / "manifest.toml"

# Directories that hold bootstrap tooling — excluded from identity scans
# (manifest drift, doctor no-identity-leak) AND removed by `init --prune`.
# These are blueprint-only; downstream projects never need them.
BOOTSTRAP_DIRS: tuple[Path, ...] = (INIT_DIR, SKILL_DIR)


def is_bootstrap_path(path: Path) -> bool:
    """True if `path` lives inside one of the bootstrap tooling dirs."""
    resolved = path.resolve()
    for d in BOOTSTRAP_DIRS:
        try:
            resolved.relative_to(d)
            return True
        except ValueError:
            continue
    return False


BLUEPRINT_IDENTITY: dict[str, str] = {
    "package_name": "py_launch_blueprint",
    "repo_name": "py-launch-blueprint",
    "app_name": "plbp",
    "app_name_upper": "PLBP",
    "author": "Steve Morin",
    "email": "steve.morin@gmail.com",
    "owner": "smorinlabs",
}

# Fields computed from another answer rather than asked / required in answers
# files: app_name_upper = app_name.upper() (the PLBP_* env-var prefix and the
# _PLBP_COMPLETE completion var). Everything else is prompted.
DERIVED_IDENTITY_FIELDS: frozenset[str] = frozenset({"app_name_upper"})

# The fields a user actually supplies (interactively or via --config).
PROMPTED_IDENTITY_FIELDS: tuple[str, ...] = tuple(
    k for k in BLUEPRINT_IDENTITY if k not in DERIVED_IDENTITY_FIELDS
)

BLUEPRINT_ORIGIN_OWNER_REPO: tuple[tuple[str, str], ...] = (
    ("smorinlabs", "py-launch-blueprint"),
    ("smorin", "py-launch-blueprint"),
)

# The §4.7 instantiation modes. SSOT for Python consumers (conftest.py imports
# this). The shell runner (init/tests/integration/run-mode.sh) and the CI
# matrix in .github/workflows/init-integration.yml restate the list for
# cross-language reasons; a future init/modes.json could collapse those too.
MODES: tuple[str, ...] = (
    "template_button",
    "gh_template",
    "clone_reinit",
    "fork",
    "zip",
)

_ORIGIN_RE = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:)"
    r"(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)


def parse_origin(url: str) -> tuple[str, str] | None:
    """Normalize an origin URL to (owner, repo) or None on no match.

    Handles HTTPS + SSH forms, with or without trailing `.git`.
    """
    m = _ORIGIN_RE.match(url.strip())
    return (m["owner"], m["repo"]) if m else None


def origin_matches_blueprint(url: str) -> bool:
    parsed = parse_origin(url)
    return parsed in BLUEPRINT_ORIGIN_OWNER_REPO if parsed else False


PYTHON_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REPO_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
GITHUB_OWNER_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?$", re.IGNORECASE)
# Must start AND end with alphanumeric (GitHub rejects trailing hyphens).
# 1-39 chars total; the middle 0-37 chars may include hyphens.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    """Raised when a user-supplied answer fails its validator."""


def validate_package_name(name: str) -> str:
    if not PYTHON_IDENTIFIER_RE.fullmatch(name):
        raise ValidationError(
            f"package name must be a valid lowercase Python identifier "
            f"(matching {PYTHON_IDENTIFIER_RE.pattern}): {name!r}"
        )
    return name


def validate_repo_name(name: str) -> str:
    if not REPO_NAME_RE.fullmatch(name):
        raise ValidationError(
            f"repo name must be lowercase alphanumeric + hyphens "
            f"(matching {REPO_NAME_RE.pattern}): {name!r}"
        )
    return name


def validate_owner(name: str) -> str:
    if not GITHUB_OWNER_RE.fullmatch(name):
        raise ValidationError(
            f"GitHub owner must be 1-39 chars, alphanumeric + hyphens, "
            f"not starting/ending with hyphen: {name!r}"
        )
    return name


def validate_email(value: str) -> str:
    if not EMAIL_RE.fullmatch(value):
        raise ValidationError(f"email must look like local@domain.tld: {value!r}")
    return value


def validate_app_name(name: str) -> str:
    # The app short name becomes the CLI command, the XDG namespace, file
    # name prefixes (<app>_config.toml), and — uppercased — the env-var
    # prefix, so it must be identifier-safe (no hyphens: ACME-X is not a
    # valid env var).
    if not PYTHON_IDENTIFIER_RE.fullmatch(name):
        raise ValidationError(
            f"app name must be a valid lowercase Python identifier "
            f"(matching {PYTHON_IDENTIFIER_RE.pattern}): {name!r}"
        )
    return name


VALIDATORS = {
    "package_name": validate_package_name,
    "repo_name": validate_repo_name,
    "app_name": validate_app_name,
    "owner": validate_owner,
    "email": validate_email,
}


@dataclass(frozen=True)
class ReplaceOp:
    """One field's replacement scope under one rewrite mode.

    The spec writes `mode` as a block-level property; real files split (TOML wants
    structured edits, prose wants text), so the same field appears in multiple blocks
    when its files span both modes — one block per (field, mode).
    """

    field: str
    current: tuple[str, ...]
    files: tuple[str, ...]
    mode: str  # "structured" | "text"


@dataclass(frozen=True)
class RenameOp:
    src: str  # may contain {package_name} / {repo_name} templates
    dst: str


@dataclass(frozen=True)
class RemoveOp:
    path: str
    reason: str


@dataclass(frozen=True)
class RegenerateOp:
    """A file whose content embeds identity but must be regenerated, not edited.

    Lockfiles (`uv.lock`, `bun.lock`) — `init` invokes the regenerator after replaces
    and renames complete.
    """

    path: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class ResetOp:
    """A file reset to a fresh stub on init rather than identity-rewritten.

    For files that accumulate the *blueprint's own* history — `CHANGELOG.md`,
    whose release notes name the blueprint (`plbp`, `smorinlabs`, compare-URLs)
    — a fork must start its own. So `init` overwrites the file with a stub
    instead of rewriting the identity strings inside it (which would graft a
    fabricated history onto the fork). Reset runs in the main rewrite phase,
    so it is never skipped the way lockfile regeneration is.
    """

    path: str
    stub: str


@dataclass(frozen=True)
class Manifest:
    replaces: tuple[ReplaceOp, ...] = field(default_factory=tuple)
    renames: tuple[RenameOp, ...] = field(default_factory=tuple)
    removes: tuple[RemoveOp, ...] = field(default_factory=tuple)
    regenerates: tuple[RegenerateOp, ...] = field(default_factory=tuple)
    resets: tuple[ResetOp, ...] = field(default_factory=tuple)


def load_manifest(path: Path = MANIFEST_PATH) -> Manifest:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return Manifest(
        replaces=tuple(
            ReplaceOp(
                field=r["field"],
                current=tuple(r.get("current", ())),
                files=tuple(r.get("files", ())),
                mode=r.get("mode", "text"),
            )
            for r in raw.get("replace", [])
        ),
        renames=tuple(
            RenameOp(src=r["from"], dst=r["to"]) for r in raw.get("rename", [])
        ),
        removes=tuple(
            RemoveOp(path=r["path"], reason=r.get("reason", ""))
            for r in raw.get("remove", [])
        ),
        regenerates=tuple(
            RegenerateOp(path=r["path"], command=tuple(r["command"]))
            for r in raw.get("regenerate", [])
        ),
        resets=tuple(
            ResetOp(path=r["path"], stub=r.get("stub", "# Changelog\n"))
            for r in raw.get("reset", [])
        ),
    )


DEFAULT_EXCLUDE_DIRS = frozenset(
    {".git", "node_modules", ".venv", "dist", "build", "__pycache__", ".pytest_cache"}
)


def is_excluded(path: Path, root: Path = REPO_ROOT) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(p in DEFAULT_EXCLUDE_DIRS for p in parts)


def iter_repo_files(root: Path = REPO_ROOT) -> list[Path]:
    """All non-excluded files under `root`, sorted for deterministic output.

    Uses `git ls-files --cached --others --exclude-standard` so the scan
    respects `.gitignore`. Falls back to filesystem walk if git is unavailable
    (e.g. running on an unpacked tarball with no .git dir).
    """
    import subprocess

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to filesystem walk when git can't answer.
        out: list[Path] = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if is_excluded(p, root):
                continue
            out.append(p)
        return sorted(out)

    paths: list[Path] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        full = root / line
        if not full.is_file():
            continue  # `--others` can list symlinks to missing targets
        if is_excluded(full, root):
            continue  # belt-and-braces against tracked files in excluded dirs
        paths.append(full)
    return sorted(paths)
