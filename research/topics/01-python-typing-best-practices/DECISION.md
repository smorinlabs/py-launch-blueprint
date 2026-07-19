# DECISION — Python typing best practices (ty-grounded)

- **Prompt:** `prompts/01-python-typing.prompt.md`
- **Raw output:** deep-research run `wf_0c1ce514-5dd` (104 agents, 22 sources,
  25 claims verified → 23 confirmed / 2 refuted)
- **Leaf (durable reference):** `../../reference/python-typing-ty-2026-07-18.md`
- **Baseline (this repo's current posture):** `baseline.md`

## The choice (actionable)

**`ty` owns type *correctness*; add `ruff ANN` for annotation *presence*; keep
boundary `Any` but narrow it within one hop.** ty is rule-based (no strict
mode) and already errors on its correctness core, so a strict posture is a small
`[tool.ty.rules]` promotion block + `python-version` pin + a `tests/**` override,
NOT a mode flip.

Confidence: **high** on mechanism/config surface (primary-source, live-verified
2026-07-18); **mixed** on exact rule-promotion list (pre-1.0 drift — re-verify
on ty upgrade).

## Why-nots (rejected framings)
- *"Turn on ty strict mode"* — no such thing; ty is rule-based.
- *"Tighten ty to match Pyright-strict"* — impossible: ty has no
  missing-annotation rule (gradual-typing guarantee). Only `ruff ANN` closes it.
- *"Purge all `Any`"* — over-churn; boundary `Any` (TOML/HTTP/structlog) is
  legitimate when narrowed inward.

## Ranked runner-up (if the recommended posture is too strict)
Minimal variant: only Tier-1 ty rules (`ambiguous-protocol-member`,
`blanket-ignore-comment`, ignore-comment hygiene) + `ruff TC`, defer `ANN`.
Zero expected churn; still closes the suppression-hygiene and Protocol gaps.

## Open (deferred to audit phase / follow-up)
- Exact per-file `Any` verdicts → Fable + Codex audit.
- Whether `error-on-warning` truly defaults `true` → confirm empirically (C1).
