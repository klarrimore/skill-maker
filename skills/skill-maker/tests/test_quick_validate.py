import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.package_skill import should_exclude
from scripts.quick_validate import _counts_as_skill_md, body_warnings, validate_skill


class TestValidateSkill(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)

    def _write_skill(self, dir_name, content):
        skill_dir = self.tmp_path / dir_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    def test_validate_skill_accepts_well_formed_frontmatter(self):
        skill_dir = self._write_skill(
            "my-skill",
            "---\nname: my-skill\ndescription: Does a thing.\n---\nBody.\n",
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_validate_skill_rejects_missing_opening_delimiter(self):
        skill_dir = self._write_skill("my-skill", "name: my-skill\ndescription: x\n")
        self.assertEqual(validate_skill(skill_dir), (False, "No YAML frontmatter found"))

    def test_validate_skill_rejects_missing_closing_delimiter(self):
        skill_dir = self._write_skill("my-skill", "---\nname: my-skill\ndescription: x\n")
        self.assertEqual(validate_skill(skill_dir), (False, "Invalid frontmatter format"))

    def test_validate_skill_rejects_invalid_yaml(self):
        skill_dir = self._write_skill("my-skill", "---\nname: [unclosed\n---\nBody.\n")
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertTrue(message.startswith("Invalid YAML in frontmatter"))

    def test_validate_skill_rejects_non_mapping_frontmatter(self):
        skill_dir = self._write_skill("my-skill", "---\n- a\n- b\n---\nBody.\n")
        self.assertEqual(
            validate_skill(skill_dir), (False, "Frontmatter must be a YAML dictionary")
        )

    def test_body_warnings_is_soft_on_malformed_frontmatter(self):
        skill_dir = self._write_skill("my-skill", "---\nname: my-skill\ndescription: x\n")
        self.assertEqual(body_warnings(skill_dir), [])

    def test_body_warnings_flags_description_near_the_limit(self):
        description = "x" * 1000
        skill_dir = self._write_skill(
            "my-skill", f"---\nname: my-skill\ndescription: {description}\n---\nBody.\n"
        )
        warnings = body_warnings(skill_dir)
        self.assertTrue(any("within 5% of the 1024 limit" in w for w in warnings))


class TestExclusionHelpers(unittest.TestCase):
    def test_counts_as_skill_md(self):
        cases = [
            (Path("SKILL.md"), True),
            (Path("references/SKILL.md"), True),
            (Path("evals/files/broken-skill/SKILL.md"), False),
            (Path("tests/fixtures/SKILL.md"), False),
            (Path("__pycache__/SKILL.md"), False),
            (Path(".pytest_cache/v/SKILL.md"), False),
        ]
        for rel_path, expected in cases:
            with self.subTest(rel_path=rel_path):
                self.assertIs(_counts_as_skill_md(rel_path), expected)

    def test_should_exclude(self):
        cases = [
            (Path("my-skill/SKILL.md"), False),
            (Path("my-skill/references/foo.md"), False),
            (Path("my-skill/evals/evals.json"), True),
            (Path("my-skill/tests/test_utils.py"), True),
            (Path("my-skill/.pytest_cache/v/cache"), True),
            (Path("my-skill/scripts/__pycache__/x.pyc"), True),
        ]
        for rel_path, expected in cases:
            with self.subTest(rel_path=rel_path):
                self.assertIs(should_exclude(rel_path), expected)


if __name__ == "__main__":
    unittest.main()
