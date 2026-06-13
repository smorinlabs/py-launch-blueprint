# press_tui — post-init TUI prototype (skeleton)

The bounded first deliverable from
[design 0005](../../docs/design/0005-template-press-tui-design.md): a
runnable interview that collects the four real post-init decisions and
emits the same JSON the agent (CLI/JSON) frontend consumes.

This is a **prototype** validating the frontend↔core seam before the
template-press engine is extracted (#423). It lives in the blueprint only
(`[[remove]]` in `init/manifest.toml`); it will move to the
`template_press/` package in phase 3.

## Files

| File | Responsibility | Deps |
|---|---|---|
| `decisions.py` | pure decision graph + `build_decisions()` — the shared core | none |
| `interview.py` | thin Textual interview shell over the core | textual (via PEP 723) |
| `test_decisions.py` | tests for the pure core (the two Run 1 fixes) | pytest |

## Run

```bash
# interactive interview (Textual)
uv run --script interview.py

# headless smoke (prints resolved decisions JSON, no TTY)
uv run --script interview.py --demo

# tests for the pure core (no Textual needed)
uv run --with pytest python -m pytest test_decisions.py -q
```

## What it proves

- **PROBLEM-12 fix**: an unanswered question resolves to `deferred`, never
  a silently-committed default.
- **PROBLEM-13 fix**: `release_please` is independent of `pypi` (answering
  "no" to publishing leaves release-please available).
- The frontend is a thin shell: all logic is in the dep-free, tested
  `decisions.py`, so the same core can back the agent frontend unchanged.
