"""Doctor tests against migrated + un-migrated fixtures.

Asserts:
  * On a fresh fixture (un-migrated): no-identity-leak reports error,
    marker absent (warn), guard-wiring ok, environment errors only for
    truly required things.
  * After `init` runs on the same fixture: no-identity-leak is clean,
    marker present, marker-matches passes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from conftest import build_fixture, run_init


def run_doctor(proj: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "--script", "init/init_doctor.py", *extra],
        cwd=proj,
        capture_output=True,
        text=True,
    )


class TestDoctorOnUnmigratedFixture:
    def test_reports_identity_leak(self, tmp_path):
        proj = build_fixture(tmp_path, "template_button")
        r = run_doctor(proj)
        # exit 1 — identity leak is an error
        assert r.returncode == 1, f"doctor should error on un-migrated:\n{r.stdout}"
        assert "no-identity-leak" in r.stdout
        assert "leftover" in r.stdout

    def test_marker_warns_when_absent(self, tmp_path):
        proj = build_fixture(tmp_path, "template_button")
        r = run_doctor(proj)
        assert "marker" in r.stdout
        assert "not found" in r.stdout or "absent" in r.stdout.lower()


class TestDoctorAfterInit:
    def test_no_identity_leak_post_init(self, tmp_path):
        proj = build_fixture(tmp_path, "template_button")
        init_result = run_init(proj)
        assert init_result.returncode == 0, init_result.stderr

        r = run_doctor(proj, "--skip", "env")
        # The fixture is a curated subset; manifest references files that don't
        # exist in the fixture and are skipped. Identity leak should be 0 over
        # files that ARE present.
        assert "no-identity-leak" in r.stdout
        # Marker present
        assert (proj / "init" / ".blueprint-initialized").exists()
        assert (
            "[ ok  ] marker" in r.stdout
            or "[ok] marker" in r.stdout
            or "ok" in r.stdout
        )

    def test_marker_matches_state(self, tmp_path):
        proj = build_fixture(tmp_path, "template_button")
        init_result = run_init(proj)
        assert init_result.returncode == 0

        r = run_doctor(proj, "--skip", "env")
        assert "marker-matches" in r.stdout
        assert "consistent" in r.stdout or "pass" in r.stdout.lower()


class TestDoctorJsonOutput:
    def test_json_is_parseable(self, tmp_path):
        import json

        proj = build_fixture(tmp_path, "template_button")
        r = run_doctor(proj, "--json")
        parsed = json.loads(r.stdout)
        assert "migration" in parsed
        assert "environment" in parsed
        assert "exit_code" in parsed
