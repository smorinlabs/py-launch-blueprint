# 0008. Long text output pages through the user's pager

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive + Copilot/CodeRabbit review), implemented in PR #400
- **Related:** `cli/output.py`; `EXAMPLECLI.md` §"Output contract"; design 0001 (R3/R4)

## Context

Interactive `text` output taller than the terminal scrolled away (git/gh
pipe through a pager). But paging must never break the output contract:
piped runs, `--output-file`, JSON/Markdown modes, and `--no-input` scripts
must behave exactly as before, and a missing pager binary must not lose
output.

## Decision

The text renderer pages **only when all of these hold**: text mode, no
`--output-file`, `paging` enabled (`--no-input` disables it — a script that
can't answer prompts can't quit `less` either), rich considers the console
a terminal, **and the underlying stream is a real TTY** (`isatty`; rich's
`force_terminal` from `color=always` is a styling decision, not an
interactivity one), and the rendered output is taller than the screen.

The pager command resolves `PLBP_PAGER` > `PAGER` > `less -FRX`, where a
variable that is **set but empty disables** paging (git convention).
Tokenization is platform-aware (`shlex` POSIX rules on Unix; `posix=False`
plus quote-stripping on Windows so `C:\…` paths survive). Any launch
failure falls back to printing the already-rendered text.

## Consequences

- Long listings stay readable interactively; pipelines and CI see
  byte-identical output to before.
- Output renders once into a capture buffer; the captured string is reused
  for the height check, the pager, and the fallback.
- An unquoted Windows pager path containing spaces still cannot be
  reconstructed; it fails to launch and falls back (quoting is the
  supported spelling).

## Alternatives considered

- **`click.echo_via_pager`** — rejected: no `PLBP_PAGER` precedence, no
  control over the default flags (`-FRX`), and it re-reads `PAGER` itself.
- **Always page on TTY (no height check)** — rejected: `less -F` would
  handle it, but non-less pagers would page one-line results.
- **Gate paging on rich's `is_terminal` alone** — rejected in review:
  `color=always` forces it true, which would page piped output.
