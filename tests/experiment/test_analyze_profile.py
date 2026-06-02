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


from experiment.profiling.analyze import phase_table, render_report  # noqa: E402


def test_phase_table_has_pct_of_total():
    p = load_profile(FIX / "sample_phases.json")
    md = phase_table(p)
    assert "| phase | seconds | % | max RSS (MB) | IO read (MB) | IO write (MB) |" in md
    assert "realize" in md
    # realize is 90 / 105 total = 85.7%
    assert "85.7%" in md


def test_render_report_names_dominant_and_has_sections():
    p = load_profile(FIX / "sample_phases.json")
    rep = render_report(p)
    assert "# Flox provisioning — root-cause report" in rep
    assert "Dominant phase: **realize**" in rep
    assert "## Resource attribution" in rep
    assert "## Ranked optimization candidates" in rep
    assert "realize.cpu.svg" in rep  # flamegraph referenced
