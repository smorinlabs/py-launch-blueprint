"""Tests for the pure decision-graph core (no Textual, no terminal needed).

These lock in the two dogfood Run 1 fixes (PROBLEM-12, PROBLEM-13) at the
logic layer, so they hold regardless of which frontend drives them.
"""

from __future__ import annotations

from decisions import (
    DEFERRED,
    DORMANT,
    ENABLED,
    build_decisions,
    normalize,
)


def test_empty_or_eof_answer_is_deferred_not_default():
    # PROBLEM-12: an absent answer must NOT silently commit a yes/no.
    assert normalize("") == DEFERRED
    assert normalize(None) == DEFERRED
    assert normalize("   ") == DEFERRED
    assert normalize("garbage") == DEFERRED


def test_recognized_answers_map_to_states():
    assert normalize("y") == ENABLED
    assert normalize("Yes") == ENABLED
    assert normalize("n") == DORMANT
    assert normalize("later") == DEFERRED


def test_release_please_is_independent_of_pypi():
    # PROBLEM-13: release-please is useful without publishing — answering
    # "no" to pypi must NOT prune release_please.
    result = build_decisions({"pypi": "n", "release_please": "y"})
    assert result.states["release_please"] == ENABLED
    assert "release_please" not in result.pruned


def test_testpypi_pruned_when_pypi_not_enabled():
    # testpypi IS a real sub-decision of pypi — "no pypi" prunes it.
    result = build_decisions({"pypi": "n", "testpypi": "y"})
    assert "testpypi" in result.pruned
    assert "testpypi" not in result.states


def test_testpypi_relevant_when_pypi_enabled():
    result = build_decisions({"pypi": "y", "testpypi": "y"})
    assert result.states["testpypi"] == ENABLED
    assert "testpypi" not in result.pruned


def test_all_unanswered_defers_everything_relevant():
    # No answers at all: every top-level decision defers; testpypi prunes
    # (its parent pypi is not enabled). Nothing is silently enabled/disabled.
    result = build_decisions({})
    assert result.states["pypi"] == DEFERRED
    assert result.states["release_please"] == DEFERRED
    assert result.states["codecov"] == DEFERRED
    assert result.states["readthedocs"] == DEFERRED
    assert "testpypi" in result.pruned
