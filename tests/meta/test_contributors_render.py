import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
START_MARKER = "<!-- contributors-please:start -->"
END_MARKER = "<!-- contributors-please:end -->"


def _ignored_logins() -> set[str]:
    ignored: set[str] = set()
    in_ignore = False

    for line in (ROOT / ".contributors.yml").read_text().splitlines():
        stripped = line.strip()
        if stripped == "ignore:":
            in_ignore = True
            continue
        if not in_ignore:
            continue
        if stripped and not line.startswith(" "):
            break
        if stripped.startswith("- "):
            ignored.add(stripped.removeprefix("- ").strip("\"'"))

    return ignored


def _contributors_state() -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in (ROOT / ".contributors.jsonl").read_text().splitlines()
        if line.strip()
    ]


def _rendered_contributors_block() -> list[str]:
    content = (ROOT / "CONTRIBUTORS.md").read_text()
    before_start, marker, after_start = content.partition(START_MARKER)
    assert before_start
    assert marker

    block, marker, after_end = after_start.partition(END_MARKER)
    assert marker
    assert after_end

    return [line for line in block.splitlines() if line.strip()]


def test_rendered_contributors_block_matches_state_and_ignore_config() -> None:
    ignored = _ignored_logins()
    records = [
        record
        for record in _contributors_state()
        if str(record["login"]) not in ignored
    ]
    records.sort(key=lambda record: int(record["commits"]), reverse=True)

    expected = [
        f"- [{record['name']}]({record['profile']}) - "
        f"{record['title']} ({record['commits']} commits)"
        for record in records
    ]

    assert _rendered_contributors_block() == expected
