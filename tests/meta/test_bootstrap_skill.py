"""Template-only bootstrap skill metadata check; removed in generated projects."""

from tests.meta.test_codex_astral_plugin import (
    REPO_ROOT,
    _frontmatter_description,
)


def test_repo_project_skill_description_stays_codex_compatible() -> None:
    skill_text = (
        REPO_ROOT / ".claude" / "skills" / "new-python-project" / "SKILL.md"
    ).read_text()

    assert len(_frontmatter_description(skill_text)) <= 1024
