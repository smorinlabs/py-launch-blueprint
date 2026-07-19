# Framing — Python typing best practices (ty-grounded)

**Trigger:** Domain best-practice (#2) — entering a project-wide type audit; the
class of problem ("what does excellent, precise Python typing look like, and how
do we make `ty` enforce it") has established, accumulating wisdom we want before
framing the audit.

**Mode:** By-hand — user explicitly requested the research. Run immediately.

**Value test:** Exploratory prior (new-to-repo strictness/tooling posture) × a
concrete decision point (ty config + rule selection + annotation conventions).
Clears the bar.

## Project constraints (relevance-filtered)

Stack (always in scope):
- Python **3.12+** (`requires-python = ">=3.12"`, ruff `target-version = py312`).
- **uv** for env/deps; **ruff** lint+format; **ty** (Astral) is the CI
  type-check authority per **ADR-03**, run as
  `uv run --extra web ty check src/py_launch_blueprint/`.
- **Pyright `strict`** is configured (`[tool.pyright]`) but drives the *IDE
  only*; CI does not gate on it.
- Frameworks: **FastAPI** (`web/`), a **CLI** (`cli/`), likely **Pydantic**
  (settings/models). Architecture is **hexagonal**: `core/ports.py` holds
  `Protocol` ports, `core/adapters/*` implement them, `core/services/*` use them.

Deliberately OUT of scope for the search (would be noise):
- Target platform — not specific.
- License posture — no declared requirement.
- Security posture — not this domain (type quality, not authz/payments).

## Known gaps this research must close

1. **No `[tool.ty]` config** exists — ty runs on defaults. What is ty's
   strictness model? Does it have a strict mode / rule catalog
   (`[tool.ty.rules]`, `[tool.ty.environment]`, `[[tool.ty.overrides]]`)? How do
   we make CI match the strict *intent* that Pyright-strict signals?
2. **Two type-checker voices** (ty defaults vs Pyright strict) — reconcile.
3. **No typing lint families in ruff** (no `ANN`, no `TC`). Should we add them,
   and which rules pull their weight vs. create noise?
4. What concretely counts as an **"overly general type"** and the precise
   replacement toolkit on 3.12+.

## Light framing searches run

(To be filled by the shaping pass / deep-research engine — capturing the field:
ty docs strictness & rules, PEP 695 adoption, typing best-practice guides
2024-2026, Pydantic+typing, Protocol vs ABC, TypedDict vs dataclass.)
