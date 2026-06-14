"""Pure decision-graph core for the template-press post-init interview.

No I/O, no TUI, no third-party deps — this is the part the frontends
(Textual TUI and CLI/JSON) share, per design docs 0004 §3 and 0005. The
Textual interview is a thin shell over `build_decisions`; agent mode would
call the same function. Keeping the logic here makes it testable without a
terminal (see test_decisions.py).

Encodes two fixes found in dogfood Run 1
(docs/research/0004-template-press-dogfood-log.md):

- PROBLEM-12: an absent answer (EOF / empty input) maps to ``deferred``
  ("ask me later"), never to a silently-committed default.
- PROBLEM-13: ``release_please`` is an INDEPENDENT decision, not a
  sub-decision of ``pypi`` — release-please (changelog + version PRs) is
  useful without publishing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Four-state lifecycle (design 0004 D9). ``removed`` is reached only behind a
# shown plan + confirm and is not an interview answer — the interview offers
# enabled / dormant(no) / deferred(later); removal happens later on the board.
ENABLED: str = "enabled"
DORMANT: str = "dormant"
DEFERRED: str = "deferred"
REMOVED: str = "removed"

# What a single keystroke means. Empty / EOF is deliberately absent here so it
# falls through to the default (deferred) — that IS the PROBLEM-12 fix.
ANSWER_TO_STATE: dict[str, str] = {
    "y": ENABLED,
    "yes": ENABLED,
    "n": DORMANT,
    "no": DORMANT,
    "l": DEFERRED,
    "later": DEFERRED,
}


@dataclass(frozen=True)
class Decision:
    """One question in the interview graph."""

    id: str
    question: str
    # id of the parent decision that must be ENABLED for this to be relevant;
    # None means top-level (always asked). Mirrors copier's relevant_when.
    relevant_when: str | None = None


# The real feature set from POST_INIT.md / Run 1 — no hypothetical features
# (design 0004 §8 guardrail: only as expressive as the real list demands).
DECISION_GRAPH: tuple[Decision, ...] = (
    Decision("pypi", "Publish releases to PyPI?"),
    Decision("testpypi", "Mirror to TestPyPI?", relevant_when="pypi"),
    # NOT relevant_when="pypi" — PROBLEM-13: independent of publishing.
    Decision("release_please", "Use release-please for version PRs?"),
    Decision("codecov", "Upload coverage to Codecov?"),
    Decision("readthedocs", "Host docs on ReadTheDocs?"),
)


@dataclass
class DecisionResult:
    """The outcome of resolving answers against the graph."""

    states: dict[str, str] = field(default_factory=dict)
    # decisions never asked because their parent was not enabled
    pruned: list[str] = field(default_factory=list)


def normalize(answer: str | None) -> str:
    """Map a raw interview answer to a lifecycle state.

    Anything unrecognized — including None (EOF) and whitespace — is
    ``deferred``, never a silent yes/no (PROBLEM-12).
    """
    if answer is None:
        return DEFERRED
    return ANSWER_TO_STATE.get(answer.strip().lower(), DEFERRED)


def build_decisions(answers: dict[str, str | None]) -> DecisionResult:
    """Resolve raw answers into per-decision states, pruning sub-trees.

    A decision whose ``relevant_when`` parent is not ENABLED is never
    recorded as a real choice — it is pruned (its tasks will never exist on
    the board). This is the "no prunes whole subtrees" rule from analysis
    0003.
    """
    result = DecisionResult()
    for decision in DECISION_GRAPH:
        parent = decision.relevant_when
        if parent is not None and result.states.get(parent) != ENABLED:
            result.pruned.append(decision.id)
            continue
        result.states[decision.id] = normalize(answers.get(decision.id))
    return result
