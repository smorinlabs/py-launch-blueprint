#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "textual>=0.80",
# ]
# ///
"""Thin Textual interview shell for the template-press post-init concierge.

This is the bounded "first deliverable" from design 0005: an interview that
collects the four real decisions and emits the same JSON the CLI/JSON
(agent) frontend would consume — proving the frontend↔core seam before the
dashboard/board and errand cards exist.

All decision logic lives in decisions.py (pure, dep-free, tested). This
file is only the terminal shell. Run interactively:

    ./interview.py            # or: uv run --script interview.py

Or smoke-test headlessly (no TTY, prints the resolved decisions as JSON):

    ./interview.py --demo
"""

from __future__ import annotations

import json
import sys

from decisions import DECISION_GRAPH, build_decisions


def _emit(answers: dict[str, str | None]) -> str:
    """Resolve answers and render the decisions JSON (the core's output)."""
    result = build_decisions(answers)
    return json.dumps(
        {"decisions": result.states, "pruned": result.pruned},
        indent=2,
    )


def _run_demo() -> None:
    # Canned answers exercising both fixes: pypi=no but release_please=yes
    # (PROBLEM-13 independence), codecov unanswered → deferred (PROBLEM-12).
    answers = {"pypi": "n", "release_please": "y", "readthedocs": "later"}
    print(_emit(answers))


def main() -> None:
    if "--demo" in sys.argv:
        _run_demo()
        return

    # Interactive Textual app. Imported lazily so --demo and the pure-logic
    # tests never need Textual installed.
    from textual.app import App, ComposeResult
    from textual.containers import VerticalScroll
    from textual.widgets import Button, Footer, Header, Label, RadioButton, RadioSet

    CHOICES = (("Yes", "y"), ("No", "n"), ("Later", "l"))

    class InterviewApp(App):
        CSS = "RadioSet { margin: 1 2; } #out { margin: 1 2; }"
        TITLE = "template-press · setup (first run)"

        def compose(self) -> ComposeResult:
            yield Header()
            with VerticalScroll():
                yield Label(
                    "Answer each, then Submit. Anything you skip is 'later' "
                    "— nothing is written until you confirm."
                )
                for decision in DECISION_GRAPH:
                    yield Label(decision.question)
                    rs = RadioSet(
                        *(RadioButton(text) for text, _ in CHOICES),
                        id=f"rs_{decision.id}",
                    )
                    yield rs
                yield Button("Submit", variant="primary", id="submit")
                yield Label("", id="out")
            yield Footer()

        def on_button_pressed(self, _event: Button.Pressed) -> None:
            answers: dict[str, str | None] = {}
            for decision in DECISION_GRAPH:
                rs = self.query_one(f"#rs_{decision.id}", RadioSet)
                idx = rs.pressed_index
                # PROBLEM-12: no selection (idx < 0) stays None → deferred.
                answers[decision.id] = CHOICES[idx][1] if idx >= 0 else None
            self.query_one("#out", Label).update(_emit(answers))

    InterviewApp().run()


if __name__ == "__main__":
    main()
