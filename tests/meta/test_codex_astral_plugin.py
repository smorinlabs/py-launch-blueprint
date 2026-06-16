from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "astral"


def _frontmatter(text: str) -> str:
    marker = "---\n"
    assert text.startswith(marker)
    _, metadata, _ = text.split(marker, 2)
    return metadata


def test_repo_marketplace_defaults_astral_plugin_on() -> None:
    marketplace = json.loads(
        (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text()
    )

    assert marketplace["name"] == "py-launch-blueprint"
    assert marketplace["interface"]["displayName"] == "py-launch-blueprint"
    assert marketplace["plugins"] == [
        {
            "name": "astral",
            "source": {"source": "local", "path": "./plugins/astral"},
            "policy": {
                "installation": "INSTALLED_BY_DEFAULT",
                "authentication": "ON_INSTALL",
            },
            "category": "Development",
        }
    ]


def test_astral_codex_plugin_manifest_adapts_official_astral_skills() -> None:
    manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text())

    assert manifest["name"] == "astral"
    assert manifest["author"] == {"name": "Astral", "url": "https://astral.sh"}
    assert manifest["repository"] == (
        "https://github.com/astral-sh/claude-code-plugins"
    )
    assert manifest["skills"] == "./skills/"
    assert manifest["license"] == "MIT"
    assert "mcpServers" not in manifest
    assert "apps" not in manifest
    assert "hooks" not in manifest
    assert manifest["interface"]["displayName"] == "Astral"
    assert manifest["interface"]["category"] == "Development"
    assert manifest["interface"]["capabilities"] == ["Code"]
    assert manifest["interface"]["defaultPrompt"] == [
        "Use uv for this Python project.",
        "Run ruff linting and formatting.",
        "Check Python types with ty.",
    ]


def test_astral_skills_are_plugin_scoped_without_agent_skill_duplicates() -> None:
    for skill_name in ("uv", "ruff", "ty"):
        skill_path = PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
        text = skill_path.read_text()

        assert f"name: {skill_name}\n" in _frontmatter(text)
        assert "docs.astral.sh" in text
        assert not (REPO_ROOT / ".agents" / "skills" / skill_name).exists()


def test_astral_adapter_carries_docs_and_upstream_licenses() -> None:
    assert (PLUGIN_ROOT / "README.md").is_file()
    assert (PLUGIN_ROOT / "LICENSE-APACHE").is_file()
    assert (PLUGIN_ROOT / "LICENSE-MIT").is_file()


def test_repo_project_skill_description_stays_codex_compatible() -> None:
    skill_text = (
        REPO_ROOT / ".claude" / "skills" / "new-python-project" / "SKILL.md"
    ).read_text()

    assert len(_frontmatter(skill_text)) <= 1024
