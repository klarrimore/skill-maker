from pathlib import Path

import pytest

from scripts.package_skill import should_exclude
from scripts.quick_validate import _counts_as_skill_md, body_warnings, validate_skill


def _write_skill(tmp_path, dir_name, content):
    skill_dir = tmp_path / dir_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


def test_validate_skill_accepts_well_formed_frontmatter(tmp_path):
    skill_dir = _write_skill(
        tmp_path,
        "my-skill",
        "---\nname: my-skill\ndescription: Does a thing.\n---\nBody.\n",
    )
    assert validate_skill(skill_dir) == (True, "Skill is valid!")


def test_validate_skill_rejects_missing_opening_delimiter(tmp_path):
    skill_dir = _write_skill(tmp_path, "my-skill", "name: my-skill\ndescription: x\n")
    assert validate_skill(skill_dir) == (False, "No YAML frontmatter found")


def test_validate_skill_rejects_missing_closing_delimiter(tmp_path):
    skill_dir = _write_skill(tmp_path, "my-skill", "---\nname: my-skill\ndescription: x\n")
    assert validate_skill(skill_dir) == (False, "Invalid frontmatter format")


def test_validate_skill_rejects_invalid_yaml(tmp_path):
    skill_dir = _write_skill(tmp_path, "my-skill", "---\nname: [unclosed\n---\nBody.\n")
    valid, message = validate_skill(skill_dir)
    assert valid is False
    assert message.startswith("Invalid YAML in frontmatter")


def test_validate_skill_rejects_non_mapping_frontmatter(tmp_path):
    skill_dir = _write_skill(tmp_path, "my-skill", "---\n- a\n- b\n---\nBody.\n")
    assert validate_skill(skill_dir) == (False, "Frontmatter must be a YAML dictionary")


def test_body_warnings_is_soft_on_malformed_frontmatter(tmp_path):
    skill_dir = _write_skill(tmp_path, "my-skill", "---\nname: my-skill\ndescription: x\n")
    assert body_warnings(skill_dir) == []


def test_body_warnings_flags_description_near_the_limit(tmp_path):
    description = "x" * 1000
    skill_dir = _write_skill(
        tmp_path, "my-skill", f"---\nname: my-skill\ndescription: {description}\n---\nBody.\n"
    )
    warnings = body_warnings(skill_dir)
    assert any("within 5% of the 1024 limit" in w for w in warnings)


@pytest.mark.parametrize(
    "rel_path, expected",
    [
        (Path("SKILL.md"), True),
        (Path("references/SKILL.md"), True),
        (Path("evals/files/broken-skill/SKILL.md"), False),
        (Path("tests/fixtures/SKILL.md"), False),
        (Path("__pycache__/SKILL.md"), False),
        (Path(".pytest_cache/v/SKILL.md"), False),
    ],
)
def test_counts_as_skill_md(rel_path, expected):
    assert _counts_as_skill_md(rel_path) is expected


@pytest.mark.parametrize(
    "rel_path, expected",
    [
        (Path("my-skill/SKILL.md"), False),
        (Path("my-skill/references/foo.md"), False),
        (Path("my-skill/evals/evals.json"), True),
        (Path("my-skill/tests/test_utils.py"), True),
        (Path("my-skill/.pytest_cache/v/cache"), True),
        (Path("my-skill/scripts/__pycache__/x.pyc"), True),
    ],
)
def test_should_exclude(rel_path, expected):
    assert should_exclude(rel_path) is expected
