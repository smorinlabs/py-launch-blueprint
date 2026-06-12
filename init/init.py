#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "questionary>=2.0",
#   "rich>=13.0",
# ]
# ///
"""init — interactive (or file-driven) blueprint setup.

Re-brands py-launch-blueprint into a new project by applying init/manifest.toml
against user-supplied answers. Strict one-shot: refuses to run if the marker
exists (unless --force). Requires a clean git tree (unless --allow-dirty).
Requires a .git directory (§4.7 mode #5: ZIP downloads must `git init` first).

Run via:
    just init                              # interactive walkthrough
    just init --config answers.toml        # headless / CI
    just init --dry-run                    # show plan, don't apply

Flags:
    --config PATH       Load answers from a TOML file (skips interactive).
    --dry-run           Print the plan; don't write anything.
    --force             Run even if init/.blueprint-initialized exists.
    --allow-dirty       Run even if git tree is dirty (NOT for missing .git).
    --commit            Stage and commit the changes after apply.
    --prune             Remove the init/ system itself (one-time, post-init).
    --no-lockfile       Skip [[regenerate]] commands — uv lock / bun install /
                        snapshot regeneration (tests use this).
    --yes               Skip the interactive confirmation prompt.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _engine import Answers, apply, build_plan
from common import (
    INIT_DIR,
    MARKER_PATH,
    PROMPTED_IDENTITY_FIELDS,
    REPO_ROOT,
    SKILL_DIR,
    SKILL_LINK,
    Manifest,
    ValidationError,
    load_manifest,
    origin_matches_blueprint,
    parse_origin,
)

VERSION = "0.1.0"


class PreconditionError(RuntimeError):
    pass


def _run(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    # Resolve cwd at call time — keeps test monkeypatching of REPO_ROOT effective.
    return subprocess.run(
        cmd, cwd=cwd or REPO_ROOT, check=check, capture_output=True, text=True
    )


def check_preconditions(args: argparse.Namespace) -> None:
    """All §4.7 mode handling + spec §4.4 step 1 lives here."""
    if not (REPO_ROOT / ".git").exists():
        raise PreconditionError(
            "no .git directory found — this looks like a ZIP download (§4.7 mode #5). "
            "Run `git init` first; git is the undo button this tool relies on. "
            "(--allow-dirty does NOT override this.)"
        )

    if MARKER_PATH.exists() and not args.force:
        raise PreconditionError(
            f"already initialized (marker: {MARKER_PATH.relative_to(REPO_ROOT)}). "
            "Pass --force to re-run."
        )

    for tool in ("git", "uv"):
        try:
            _run([tool, "--version"])
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            raise PreconditionError(
                f"required tool {tool!r} not available: {e}"
            ) from None

    if not args.allow_dirty:
        try:
            status = _run(["git", "status", "--porcelain"]).stdout
        except subprocess.CalledProcessError as e:
            raise PreconditionError(f"`git status` failed: {e}") from None
        if status.strip():
            raise PreconditionError(
                "git working tree is dirty. Commit or stash your changes, then re-run. "
                "(Pass --allow-dirty to override — but git is your undo button.)"
            )


def discover_origin_defaults() -> dict[str, str]:
    """Best-effort defaults from git config — owner, repo, author, email."""
    out: dict[str, str] = {}
    try:
        url = _run(["git", "remote", "get-url", "origin"], check=False).stdout.strip()
    except Exception:
        url = ""
    if url and not origin_matches_blueprint(url):
        parsed = parse_origin(url)
        if parsed:
            out["owner"], out["repo_name"] = parsed
    for git_key, ans_key in [("user.name", "author"), ("user.email", "email")]:
        try:
            v = _run(["git", "config", "--get", git_key], check=False).stdout.strip()
            if v:
                out[ans_key] = v
        except Exception:  # noqa: S110 - best-effort defaults; missing git config is normal
            pass
    return out


def derive_package_name(repo_name: str) -> str:
    return repo_name.replace("-", "_").lower()


def derive_app_name(package_name: str) -> str:
    # The app short name (the CLI command, env prefix, XDG namespace) defaults
    # to the package name; the user may override at the prompt.
    return package_name


def load_answers_from_file(path: Path) -> Answers:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    section = raw.get("answers", raw)
    missing = [k for k in PROMPTED_IDENTITY_FIELDS if k not in section]
    if missing:
        raise ValueError(f"--config file is missing answers for: {missing}")
    return Answers(
        package_name=section["package_name"],
        repo_name=section["repo_name"],
        app_name=section["app_name"],
        author=section["author"],
        email=section["email"],
        owner=section["owner"],
    )


def collect_answers_interactive() -> Answers:
    try:
        import questionary
    except ImportError:
        raise PreconditionError(
            "interactive mode requires `questionary` (not installed in this env). "
            "Use --config answers.toml for headless runs."
        ) from None
    defaults = discover_origin_defaults()

    def _ask(prompt: str, key: str, derive=None) -> str:
        default = defaults.get(key) or (derive() if derive else "")
        ans = questionary.text(prompt, default=default or "").ask()
        if ans is None:
            raise SystemExit("aborted at prompt")
        return ans.strip()

    print(
        "\nblueprint init — answer 6 questions to re-brand this project.\n"
        "(Defaults are inferred from origin + git config; press Enter to accept.)\n"
    )
    repo_name = _ask("repo name (kebab-case)", "repo_name")
    package_name = _ask(
        "Python package name (snake_case)",
        "package_name",
        derive=lambda: derive_package_name(repo_name),
    )
    app_name = _ask(
        "app short name (snake_case; CLI command + env prefix)",
        "app_name",
        derive=lambda: derive_app_name(package_name),
    )
    owner = _ask("GitHub owner (user or org)", "owner")
    author = _ask("author name", "author")
    email = _ask("author email", "email")
    return Answers(
        package_name=package_name,
        repo_name=repo_name,
        app_name=app_name,
        author=author,
        email=email,
        owner=owner,
    )


def write_marker(answers: Answers) -> None:
    """Marker is committed; it's the doctor's record of what answers were used."""
    today = _dt.date.today().isoformat()
    lines = [
        "# init/.blueprint-initialized — written by init.py on successful run.",
        "# Tracked by git; read by init/guard.sh and init_doctor.py.",
        "",
        "[meta]",
        f'version = "{VERSION}"',
        f'date    = "{today}"',
        "",
        "[answers]",
    ]
    for k, v in answers.as_dict().items():
        lines.append(f'{k} = "{v}"')
    MARKER_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_regenerates(manifest: Manifest) -> None:
    """Execute every ``[[regenerate]]`` command, in manifest order.

    These are files whose content embeds identity but cannot be rewritten by
    string replacement: lockfiles (hashes), and generated artifacts whose
    *layout* depends on the new identity — e.g. the CLI ``--help`` snapshots,
    which re-wrap at 80 columns for the renamed program name. Runs after
    replaces and renames so the regenerators see the renamed tree. Best
    effort: a missing tool or failing command warns instead of aborting init
    (git is still the undo button).
    """
    for op in manifest.regenerates:
        if not (REPO_ROOT / op.path).exists():
            continue
        try:
            result = _run(list(op.command), check=False)
        except FileNotFoundError:
            print(
                f"  (skipping {op.path} — {op.command[0]} not on PATH)",
                file=sys.stderr,
            )
            continue
        if result.returncode != 0:
            print(
                f"  WARNING: regenerating {op.path} failed "
                f"(`{' '.join(op.command)}` exited {result.returncode}) — "
                "regenerate it manually",
                file=sys.stderr,
            )


def prune_init_system() -> None:
    """Remove init/ tooling and Justfile/CI hooks once initialization is irreversible.

    Default policy per spec §3: keep (the guard self-silences post-init, and
    init-doctor's environment checks stay useful). --prune is opt-in.
    """
    targets = [
        INIT_DIR / "guard.sh",
        INIT_DIR / "init.py",
        INIT_DIR / "init_doctor.py",
        INIT_DIR / "manifest.toml",
        INIT_DIR / "discover.py",
        INIT_DIR / "_engine.py",
        INIT_DIR / "_rewriters.py",
        INIT_DIR / "common.py",
        INIT_DIR / "post_init.py",
        INIT_DIR / "init-spec.md",
        INIT_DIR / "README.md",
        INIT_DIR / "ci",
        INIT_DIR / "tests",
        SKILL_LINK,  # Codex-side symlink first, so it never dangles
        SKILL_DIR,  # agent skill is blueprint-only tooling
        REPO_ROOT / ".github" / "workflows" / "blueprint-guard.yml",
        REPO_ROOT / ".github" / "workflows" / "init-integration.yml",
    ]
    import shutil

    for t in targets:
        if t.is_symlink():
            t.unlink()  # never rmtree through a symlink
            continue
        if not t.exists():
            continue
        if t.is_dir():
            shutil.rmtree(t)
        else:
            t.unlink()
    # The skill dir/link live under .claude/skills/ and .agents/skills/;
    # drop those parents too when the skill was the only thing in them.
    for parent in (
        SKILL_LINK.parent,
        SKILL_LINK.parent.parent,
        SKILL_DIR.parent,
        SKILL_DIR.parent.parent,
    ):
        try:
            parent.rmdir()  # only succeeds when empty
        except OSError:
            # Parent still holds other entries (e.g. user-added skills) or
            # was already gone — best-effort cleanup, keep it.
            pass
    print(
        "pruned init/ system. Manually remove `_blueprint_notice`, `_guard`, "
        "`init`, `init-doctor` from Justfile and the .blueprint-contributor line "
        "from .gitignore — those are out of scope for automated removal.",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", type=Path, help="TOML file with [answers] table")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--prune", action="store_true")
    parser.add_argument("--no-lockfile", action="store_true")
    parser.add_argument(
        "--yes", action="store_true", help="skip interactive confirmation"
    )
    args = parser.parse_args(argv)

    if args.prune and not args.force:
        if not MARKER_PATH.exists():
            print(
                "--prune requires the marker to exist (run init first, or pass --force).",
                file=sys.stderr,
            )
            return 2

    try:
        check_preconditions(args)
    except PreconditionError as e:
        print(f"init: precondition failed — {e}", file=sys.stderr)
        return 1

    if args.prune:
        prune_init_system()
        return 0

    if args.config:
        try:
            answers = load_answers_from_file(args.config)
        except (FileNotFoundError, ValueError, tomllib.TOMLDecodeError) as e:
            print(f"init: --config error — {e}", file=sys.stderr)
            return 1
    else:
        try:
            answers = collect_answers_interactive()
        except PreconditionError as e:
            print(f"init: {e}", file=sys.stderr)
            return 1

    try:
        answers.validate()
    except ValidationError as e:
        print(f"init: invalid answer — {e}", file=sys.stderr)
        return 1

    manifest = load_manifest()
    plan = build_plan(manifest, answers)

    print(plan.render())
    counts = plan.counts()
    print(
        f"\nSummary: {counts['remove']} removes, {counts['replace']} replaces, {counts['rename']} renames."
    )

    if args.dry_run:
        print("\n(--dry-run: no changes written)")
        return 0

    if not args.yes and not args.config:
        try:
            confirm = input("\nApply these changes? [y/N] ").strip().lower()
        except EOFError:
            confirm = ""
        if confirm not in {"y", "yes"}:
            print("aborted.", file=sys.stderr)
            return 1

    try:
        report = apply(manifest, answers)
    except Exception as e:
        print(f"init: APPLY FAILED — {e}", file=sys.stderr)
        print("  recover with:  git checkout . && git clean -fd", file=sys.stderr)
        return 2

    print(report.render())

    if not args.no_lockfile:
        print("regenerating lockfiles and generated artifacts...", file=sys.stderr)
        run_regenerates(manifest)

    write_marker(answers)
    print(f"marker written: {MARKER_PATH.relative_to(REPO_ROOT)}")

    if args.commit:
        try:
            _run(["git", "add", "-A"])
            _run(
                ["git", "commit", "-m", f"chore: blueprint init → {answers.repo_name}"]
            )
        except subprocess.CalledProcessError as e:
            print(
                f"init: --commit failed (changes still on disk) — {e.stderr}",
                file=sys.stderr,
            )
            return 2

    print("\n✓ done. Review with `git diff HEAD~1` (or `git status` if not --commit).")

    # ── Auto-chain to post-init (only in interactive mode; CI uses --config and
    # should drive post-init separately). post_init.py detects remote availability
    # itself and runs partial-flow when GitHub isn't reachable yet.
    if not args.config and sys.stdin.isatty():
        try:
            do_post = (
                input("\nRun post-init now? (publishing, Codecov, RTD) [y/N] ")
                .strip()
                .lower()
            )
        except EOFError:
            do_post = ""
        if do_post in {"y", "yes"}:
            post_init_path = Path(__file__).resolve().parent / "post_init.py"
            subprocess.run(
                ["uv", "run", "--script", str(post_init_path)],
                cwd=REPO_ROOT,
                check=False,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
