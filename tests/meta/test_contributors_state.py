import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NO_REPLY_RE = re.compile(
    r"^(?:(?P<id>\d+)\+)?(?P<login>[^@]+)@users\.noreply\.github\.com$"
)


def _identity_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    current_login: str | None = None
    in_identity_map = False

    for line in (ROOT / ".contributors.yml").read_text().splitlines():
        stripped = line.strip()
        if stripped == "identity_map:":
            in_identity_map = True
            continue
        if not in_identity_map:
            continue
        if stripped and not line.startswith(" "):
            break
        if stripped.startswith("- login: "):
            current_login = stripped.removeprefix("- login: ").strip("\"'")
            continue
        if current_login and stripped.startswith("- "):
            email = stripped.removeprefix("- ").strip("\"'").casefold()
            mapping[email] = current_login

    return mapping


def _login_for_email(email: str, mapping: dict[str, str]) -> str | None:
    mapped = mapping.get(email.casefold())
    if mapped:
        return mapped

    match = NO_REPLY_RE.match(email)
    if match:
        return match.group("login")

    return None


def _git() -> str:
    git = shutil.which("git")
    if git is None:
        msg = "git is required for contributor history checks"
        raise RuntimeError(msg)
    return git


def _ensure_full_history() -> str:
    git = _git()
    result = subprocess.run(  # noqa: S603
        [git, "rev-parse", "--is-shallow-repository"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() == "true":
        subprocess.run(  # noqa: S603
            [git, "fetch", "--unshallow", "--filter=blob:none"],
            cwd=ROOT,
            check=True,
        )
    return git


def _earliest_non_merge_commit_dates() -> dict[str, str]:
    git = _ensure_full_history()
    mapping = _identity_map()
    result = subprocess.run(  # noqa: S603
        [git, "log", "--no-merges", "--format=%ad%x09%ae", "--date=short"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    earliest: dict[str, str] = {}
    for line in result.stdout.splitlines():
        date, email = line.split("\t", maxsplit=1)
        login = _login_for_email(email, mapping)
        if login is None:
            continue
        existing = earliest.get(login)
        if existing is None or date < existing:
            earliest[login] = date

    return earliest


def test_commit_contributor_first_seen_matches_earliest_non_merge_commit() -> None:
    earliest = _earliest_non_merge_commit_dates()
    records = [
        json.loads(line)
        for line in (ROOT / ".contributors.jsonl").read_text().splitlines()
        if line.strip()
    ]
    commit_records = [record for record in records if record["source"] == "commit"]

    assert commit_records

    for record in commit_records:
        login = record["login"]
        assert login in earliest
        assert record["first_seen"] == earliest[login]
