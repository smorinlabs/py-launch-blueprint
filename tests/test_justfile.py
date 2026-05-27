from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_contributors_recipe_runs_contributors_please() -> None:
    result = subprocess.run(
        ["just", "--dry-run", "contributors"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    assert "npx @smorinlabs/contributors-please@1 init" in output
    assert "--config-file .contributors.yml" in output
