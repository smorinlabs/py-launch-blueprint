# Internal engineering docs

Version-controlled engineering docs that are **not** part of the published
Sphinx site (`docs/source/`). Three buckets, by intent:

| Directory | Holds | Normative? |
|---|---|---|
| [`adr/`](adr/) | **Architecture Decision Records** — one significant decision each, with context + consequences. | Yes (a decision) |
| [`design/`](design/) | **Design / requirements specs** — proposals and conventions to implement. | Yes (a plan) |
| [`research/`](research/) | **Research** — investigations, comparisons, findings. | No (exploration) |

Rules of thumb:

- Exploring options, benchmarking, "what's out there" → **research**.
- Specifying what to build and how it must behave → **design**.
- Recording a single decision (and why) so it isn't re-litigated → **ADR**.

A research doc often feeds a design doc, which often crystallizes one or more
ADRs. Cross-link them. Each subdirectory has its own `README.md` with the file
naming + status conventions.

Two operational guides also live at this level (linked from the root README):

- [`POST_INIT.md`](POST_INIT.md) — the post-init decisions & configuration
  checklist for projects created from this template.
- [`RELEASE.md`](RELEASE.md) — the release/publish flow in detail.

> These docs are intentionally outside `docs/source/`, so they are reviewed in
> PRs and kept with the code without shipping to the rendered documentation
> site. Wire any into Sphinx later if you want them published.
