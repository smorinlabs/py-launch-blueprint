from __future__ import annotations

from pathlib import Path

from experiment.profiling.analyze import (
    Phase,
    dominant_phase,
    load_profile,
    total_seconds,
)

FIX = Path(__file__).parent.parent.parent / "experiment/profiling/fixtures"


def test_load_profile_reads_meta_and_phases():
    p = load_profile(FIX / "sample_phases.json")
    assert p.os == "macos"
    assert p.cache == "cold"
    assert len(p.phases) == 5
    assert p.phases[2] == Phase("realize", 90.0, 300.0, 250.0, 600.0)


def test_total_seconds_sums_phases():
    p = load_profile(FIX / "sample_phases.json")
    assert total_seconds(p) == 105.0


def test_dominant_phase_is_max_seconds():
    p = load_profile(FIX / "sample_phases.json")
    assert dominant_phase(p).name == "realize"
