from __future__ import annotations

import pytest

from experiment.bench.stats import Stats, delta_pct, summarize


def test_summarize_basic():
    s = summarize([10.0, 20.0, 30.0])
    assert s == Stats(
        n=3,
        min=10.0,
        max=30.0,
        avg=20.0,
        median=20.0,
        stddev=pytest.approx(8.16496, rel=1e-4),
    )


def test_summarize_single_sample_has_zero_stddev():
    s = summarize([42.0])
    assert s.n == 1
    assert s.stddev == 0.0


def test_summarize_empty_raises():
    with pytest.raises(ValueError):
        summarize([])


def test_delta_pct_sign():
    assert delta_pct(100.0, 80.0) == pytest.approx(-20.0)
    assert delta_pct(100.0, 130.0) == pytest.approx(30.0)


def test_delta_pct_zero_baseline_raises():
    with pytest.raises(ValueError):
        delta_pct(0.0, 5.0)
