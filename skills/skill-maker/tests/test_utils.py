import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.utils import parse_frontmatter, walk_skill


class TestParseFrontmatter(unittest.TestCase):
    def test_parses_frontmatter_and_body(self):
        content = "---\nname: my-skill\ndescription: Does a thing.\n---\nBody text.\n"
        frontmatter, body = parse_frontmatter(content)
        self.assertEqual(frontmatter, {"name": "my-skill", "description": "Does a thing."})
        self.assertEqual(body, "Body text.\n")

    def test_missing_opening_delimiter_raises(self):
        with self.assertRaisesRegex(ValueError, "No YAML frontmatter found"):
            parse_frontmatter("name: my-skill\ndescription: Does a thing.\n")

    def test_missing_closing_delimiter_raises(self):
        with self.assertRaisesRegex(ValueError, "Invalid frontmatter format"):
            parse_frontmatter("---\nname: my-skill\ndescription: Does a thing.\n")

    def test_invalid_yaml_raises(self):
        with self.assertRaisesRegex(ValueError, "Invalid YAML in frontmatter"):
            parse_frontmatter("---\nname: [unclosed\n---\nBody.\n")

    def test_non_mapping_frontmatter_raises(self):
        with self.assertRaisesRegex(ValueError, "Frontmatter must be a YAML dictionary"):
            parse_frontmatter("---\n- just\n- a\n- list\n---\nBody.\n")

    def test_empty_body_is_empty_string(self):
        frontmatter, body = parse_frontmatter("---\nname: my-skill\n---\n")
        self.assertEqual(frontmatter, {"name": "my-skill"})
        self.assertEqual(body, "")

    def test_empty_frontmatter_block_is_not_a_mapping(self):
        # `yaml.safe_load("")` returns None, which is not a dict.
        with self.assertRaisesRegex(ValueError, "Frontmatter must be a YAML dictionary"):
            parse_frontmatter("---\n\n---\nBody.\n")

    def test_body_may_itself_contain_a_triple_dash(self):
        # The DOTALL regex is non-greedy on the frontmatter, so a `---` in the
        # body is kept in the body rather than closing the block early.
        content = "---\nname: my-skill\n---\nIntro.\n\n---\n\nMore body.\n"
        frontmatter, body = parse_frontmatter(content)
        self.assertEqual(frontmatter, {"name": "my-skill"})
        self.assertIn("More body.", body)
        self.assertTrue(body.startswith("Intro."))

    def test_missing_trailing_newline_after_closing_delimiter(self):
        # The closing `\n?` after `---` is optional: no body, no trailing newline.
        frontmatter, body = parse_frontmatter("---\nname: my-skill\n---")
        self.assertEqual(frontmatter, {"name": "my-skill"})
        self.assertEqual(body, "")

    def test_multiline_scalar_body_preserved_verbatim(self):
        frontmatter, body = parse_frontmatter(
            "---\nname: my-skill\ndescription: Does a thing.\n---\nline1\nline2\n"
        )
        self.assertEqual(body, "line1\nline2\n")


class TestWalkSkill(unittest.TestCase):
    def _make_skill(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        skill = tmp / "my-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("x")
        (skill / "tests").mkdir()
        (skill / "tests" / "t.py").write_text("x")
        return skill

    def test_dot_path_keeps_skill_folder_prefix(self):
        # Regression: Path('.').parent is '.', so a relative `.` used to drop
        # the skill-folder prefix from arcnames.
        skill = self._make_skill()
        cwd = Path.cwd()
        os.chdir(skill)
        self.addCleanup(os.chdir, cwd)

        entries = {str(arc): excluded for _, arc, excluded in walk_skill(".")}

        self.assertIn("my-skill/SKILL.md", entries)
        self.assertFalse(entries["my-skill/SKILL.md"])
        self.assertTrue(entries["my-skill/tests/t.py"])

    def test_named_path_keeps_skill_folder_prefix(self):
        skill = self._make_skill()
        entries = {str(arc): excluded for _, arc, excluded in walk_skill(skill)}
        self.assertIn("my-skill/SKILL.md", entries)


if __name__ == "__main__":
    unittest.main()
