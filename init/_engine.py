"""Migration engine — applies a Manifest given a set of Answers.

Owned by init.py; not run directly. Pure-stdlib (no questionary/rich) — keeps
the engine importable from tests that don't want to pay tomlkit's import cost
for code paths that don't need it. tomlkit is imported lazily inside the
structured-rewriter dispatcher.

Order of operations (per spec §4.3):  remove → replace → rename.

Why this order: remove shrinks the working set; replace runs while paths still
match the manifest's `files` lists; rename runs last so no other op sees a path
under its new name.

Failure mode: any op raising propagates; the CLI catches and tells the user to
`git checkout . && git clean -fd`. We do NOT attempt internal rollback —
git is the undo button.
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    BLUEPRINT_IDENTITY,
    REPO_ROOT,
    VALIDATORS,
    Manifest,
    RemoveOp,
    RenameOp,
    ResetOp,
)


@dataclass(frozen=True)
class Answers:
    """User-supplied answers — one per prompted field in BLUEPRINT_IDENTITY.

    ``app_name`` is the modern CLI's short name (blueprint: ``plbp``); its
    uppercase form (the env-var prefix) is derived, never asked.
    """

    package_name: str
    repo_name: str
    app_name: str
    author: str
    email: str
    owner: str

    def as_dict(self) -> dict[str, str]:
        return {
            "package_name": self.package_name,
            "repo_name": self.repo_name,
            "app_name": self.app_name,
            "app_name_upper": self.app_name.upper(),
            "author": self.author,
            "email": self.email,
            "owner": self.owner,
        }

    def validate(self) -> None:
        for k, v in self.as_dict().items():
            validator = VALIDATORS.get(k)
            if validator is None:
                continue
            validator(v)


@dataclass
class PlanItem:
    """One concrete edit/rename/remove to execute (and report to the user)."""

    kind: str  # "remove" | "replace" | "rename"
    path: str
    detail: str  # human-readable

    def render(self) -> str:
        return f"  [{self.kind:<7}] {self.path}  —  {self.detail}"


@dataclass
class Plan:
    items: list[PlanItem] = field(default_factory=list)

    def render(self) -> str:
        if not self.items:
            return "(plan is empty — nothing to do)"
        lines = ["Plan:"]
        for it in self.items:
            lines.append(it.render())
        return "\n".join(lines)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {"remove": 0, "replace": 0, "rename": 0}
        for it in self.items:
            out[it.kind] = out.get(it.kind, 0) + 1
        return out


def _resolve_renames(renames: Iterable[RenameOp], answers: Answers) -> list[RenameOp]:
    """Substitute {field} placeholders in rename destinations."""
    answer_map = answers.as_dict()
    resolved = []
    for r in renames:
        new_dst = r.dst
        for k, v in answer_map.items():
            new_dst = new_dst.replace("{" + k + "}", v)
        resolved.append(RenameOp(src=r.src, dst=new_dst))
    return resolved


def _replacement_map(answers: Answers) -> dict[str, str]:
    """Map blueprint identity value → user's answer.

    Sorted longest-first (caller may rely on this) to defuse substring collision
    between fields if any ever happens (none today, but cheap to ensure).
    """
    answer_map = answers.as_dict()
    pairs = [(BLUEPRINT_IDENTITY[k], answer_map[k]) for k in BLUEPRINT_IDENTITY]
    pairs.sort(key=lambda kv: -len(kv[0]))
    return dict(pairs)


def build_plan(manifest: Manifest, answers: Answers, root: Path = REPO_ROOT) -> Plan:
    """Resolve the manifest against answers; do NOT execute anything."""
    answers.validate()
    plan = Plan()

    for op in manifest.removes:
        target = root / op.path
        exists = "exists" if target.exists() else "missing — skip"
        plan.items.append(PlanItem("remove", op.path, f"{op.reason} ({exists})"))

    rep_map = _replacement_map(answers)
    for op in manifest.replaces:
        for f in op.files:
            target = root / f
            if not target.exists():
                plan.items.append(
                    PlanItem(
                        "replace",
                        f,
                        f"field={op.field} mode={op.mode} (missing — skip)",
                    )
                )
                continue
            plan.items.append(
                PlanItem(
                    "replace",
                    f,
                    f"field={op.field} mode={op.mode}  "
                    + ", ".join(
                        f"{cur!r}→{rep_map.get(cur, '?')!r}" for cur in op.current
                    ),
                )
            )

    for op in _resolve_renames(manifest.renames, answers):
        src = root / op.src
        if not src.exists():
            plan.items.append(
                PlanItem("rename", op.src, f"→ {op.dst} (missing — skip)")
            )
            continue
        plan.items.append(PlanItem("rename", op.src, f"→ {op.dst}"))

    for op in manifest.resets:
        target = root / op.path
        exists = "exists" if target.exists() else "missing — create"
        plan.items.append(PlanItem("reset", op.path, f"→ fresh stub ({exists})"))

    return plan


def apply_remove(op: RemoveOp, root: Path = REPO_ROOT) -> bool:
    target = root / op.path
    if not target.exists():
        return False
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return True


def apply_reset(op: ResetOp, root: Path = REPO_ROOT) -> bool:
    """Overwrite a file with its fresh stub. Returns True if it changed."""
    target = root / op.path
    if target.exists() and target.read_text(encoding="utf-8") == op.stub:
        return False
    target.write_text(op.stub, encoding="utf-8")
    return True


def apply_replace_text(
    path: Path, current_values: list[str], rep_map: dict[str, str]
) -> bool:
    """Longest-first string replacement. Returns True if file changed."""
    text = path.read_text(encoding="utf-8")
    new_text = text
    for cur in sorted(current_values, key=lambda s: -len(s)):
        repl = rep_map.get(cur)
        if repl is None or repl == cur:
            continue
        new_text = new_text.replace(cur, repl)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def apply_replace_structured(
    path: Path, current_values: list[str], rep_map: dict[str, str], field_name: str
) -> bool:
    """Dispatch to per-file structured rewriter (see _rewriters.py).

    Falls back to text replacement if no rewriter is registered — safe because
    the manifest's `current` enumeration is exact.
    """
    from _rewriters import STRUCTURED_REWRITERS

    rel = path.relative_to(REPO_ROOT) if path.is_absolute() else path
    rewriter = STRUCTURED_REWRITERS.get(str(rel))
    if rewriter is None:
        return apply_replace_text(path, current_values, rep_map)
    return rewriter(path, field_name, current_values, rep_map)


def apply_rename(op: RenameOp, root: Path = REPO_ROOT) -> bool:
    src = root / op.src
    dst = root / op.dst
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return True


@dataclass
class ApplyReport:
    removed: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str]] = field(default_factory=list)
    reset: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def render(self) -> str:
        return (
            f"Applied: "
            f"{len(self.removed)} removed, "
            f"{len(self.replaced)} replaced, "
            f"{len(self.renamed)} renamed, "
            f"{len(self.reset)} reset, "
            f"{len(self.skipped)} skipped."
        )


def apply(manifest: Manifest, answers: Answers, root: Path = REPO_ROOT) -> ApplyReport:
    """Execute the manifest in remove → replace → rename → reset order."""
    answers.validate()
    report = ApplyReport()
    rep_map = _replacement_map(answers)

    for op in manifest.removes:
        if apply_remove(op, root):
            report.removed.append(op.path)
        else:
            report.skipped.append(f"remove {op.path} (missing)")

    for op in manifest.replaces:
        for f in op.files:
            target = root / f
            if not target.exists():
                report.skipped.append(f"replace {f} (missing)")
                continue
            current_values = list(op.current)
            if op.mode == "structured":
                changed = apply_replace_structured(
                    target, current_values, rep_map, op.field
                )
            else:
                changed = apply_replace_text(target, current_values, rep_map)
            if changed:
                report.replaced.append(f)
            else:
                report.skipped.append(f"replace {f} (no change)")

    for op in _resolve_renames(manifest.renames, answers):
        if apply_rename(op, root):
            report.renamed.append((op.src, op.dst))
        else:
            report.skipped.append(f"rename {op.src} (missing)")

    for op in manifest.resets:
        if apply_reset(op, root):
            report.reset.append(op.path)
        else:
            report.skipped.append(f"reset {op.path} (no change)")

    return report
