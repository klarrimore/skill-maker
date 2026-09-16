import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.package_skill import should_exclude
from scripts.quick_validate import (
    BODY_LINE_BUDGET,
    _counts_as_skill_md,
    body_warnings,
    validate_skill,
)

# A minimal frontmatter body that is spec-valid on its own; individual tests
# override one field at a time so a single assertion pins a single branch.
GOOD = "---\nname: my-skill\ndescription: Does a thing.\n---\nBody.\n"


class TestValidateSkill(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)

    def _write_skill(self, dir_name, content):
        skill_dir = self.tmp_path / dir_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    # --- happy paths ------------------------------------------------------
    def test_accepts_well_formed_frontmatter(self):
        skill_dir = self._write_skill("my-skill", GOOD)
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_accepts_all_optional_fields(self):
        content = (
            "---\n"
            "name: my-skill\n"
            "description: Does a thing.\n"
            "license: MIT\n"
            "allowed-tools: Read, Write\n"
            "compatibility: Needs network access.\n"
            "metadata:\n"
            "  author: someone\n"
            "  version: '1.0'\n"
            "---\nBody.\n"
        )
        skill_dir = self._write_skill("my-skill", content)
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_accepts_digits_and_hyphens_in_name(self):
        skill_dir = self._write_skill(
            "pdf-2-docx", "---\nname: pdf-2-docx\ndescription: x\n---\nBody.\n"
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_accepts_unicode_name_cjk(self):
        skill_dir = self._write_skill(
            "技能", "---\nname: 技能\ndescription: x\n---\nBody.\n"
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_accepts_unicode_name_cyrillic(self):
        skill_dir = self._write_skill(
            "мой-навык", "---\nname: мой-навык\ndescription: x\n---\nBody.\n"
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_accepts_unicode_name_accented(self):
        skill_dir = self._write_skill(
            "café", "---\nname: café\ndescription: x\n---\nBody.\n"
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_empty_name_string_skips_name_checks(self):
        # Characterization: an empty name is present (not "missing") and the
        # `if name:` guard skips kebab/length/dir-match, so this validates.
        skill_dir = self._write_skill(
            "my-skill", "---\nname: ''\ndescription: x\n---\nBody.\n"
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    # --- structural / file-layout rejections ------------------------------
    def test_rejects_missing_skill_md(self):
        skill_dir = self.tmp_path / "my-skill"
        skill_dir.mkdir()
        self.assertEqual(validate_skill(skill_dir), (False, "SKILL.md not found"))

    def test_rejects_multiple_packaged_skill_md_files(self):
        skill_dir = self._write_skill("my-skill", GOOD)
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "SKILL.md").write_text(GOOD)
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("must contain exactly one", message)
        self.assertIn("references/SKILL.md", message)

    def test_nested_skill_md_under_excluded_dir_is_ignored(self):
        # A SKILL.md that would not be packaged (under evals/) must not trip the
        # single-SKILL.md check.
        skill_dir = self._write_skill("my-skill", GOOD)
        (skill_dir / "evals" / "files" / "fixture").mkdir(parents=True)
        (skill_dir / "evals" / "files" / "fixture" / "SKILL.md").write_text(GOOD)
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    # --- frontmatter parse errors surface through validate ---------------
    def test_rejects_missing_opening_delimiter(self):
        skill_dir = self._write_skill("my-skill", "name: my-skill\ndescription: x\n")
        self.assertEqual(validate_skill(skill_dir), (False, "No YAML frontmatter found"))

    def test_rejects_missing_closing_delimiter(self):
        skill_dir = self._write_skill("my-skill", "---\nname: my-skill\ndescription: x\n")
        self.assertEqual(validate_skill(skill_dir), (False, "Invalid frontmatter format"))

    def test_rejects_invalid_yaml(self):
        skill_dir = self._write_skill("my-skill", "---\nname: [unclosed\n---\nBody.\n")
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertTrue(message.startswith("Invalid YAML in frontmatter"))

    def test_rejects_non_mapping_frontmatter(self):
        skill_dir = self._write_skill("my-skill", "---\n- a\n- b\n---\nBody.\n")
        self.assertEqual(
            validate_skill(skill_dir), (False, "Frontmatter must be a YAML dictionary")
        )

    # --- unknown fields / required fields --------------------------------
    def test_rejects_unexpected_top_level_key(self):
        skill_dir = self._write_skill(
            "my-skill", "---\nname: my-skill\ndescription: x\nauthor: jo\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("Unexpected key(s)", message)
        self.assertIn("author", message)

    def test_rejects_missing_name(self):
        skill_dir = self._write_skill("my-skill", "---\ndescription: x\n---\nBody.\n")
        self.assertEqual(validate_skill(skill_dir), (False, "Missing 'name' in frontmatter"))

    def test_rejects_missing_description(self):
        skill_dir = self._write_skill("my-skill", "---\nname: my-skill\n---\nBody.\n")
        self.assertEqual(
            validate_skill(skill_dir), (False, "Missing 'description' in frontmatter")
        )

    # --- name validation --------------------------------------------------
    def test_rejects_non_string_name(self):
        skill_dir = self._write_skill("my-skill", "---\nname: 123\ndescription: x\n---\nBody.\n")
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("Name must be a string", message)
        self.assertIn("int", message)

    def test_rejects_non_kebab_name(self):
        skill_dir = self._write_skill(
            "My_Skill", "---\nname: My_Skill\ndescription: x\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("kebab-case", message)

    def test_rejects_uppercase_name(self):
        skill_dir = self._write_skill(
            "My-Skill", "---\nname: My-Skill\ndescription: x\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("kebab-case", message)

    def test_rejects_uppercase_unicode_name(self):
        skill_dir = self._write_skill(
            "Мой-Навык", "---\nname: Мой-Навык\ndescription: x\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("kebab-case", message)

    def test_rejects_leading_hyphen_name(self):
        skill_dir = self._write_skill(
            "-my-skill", "---\nname: -my-skill\ndescription: x\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("cannot start/end with hyphen", message)

    def test_rejects_consecutive_hyphens_name(self):
        skill_dir = self._write_skill(
            "my--skill", "---\nname: my--skill\ndescription: x\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("consecutive hyphens", message)

    def test_rejects_name_over_64_chars(self):
        long_name = "a" * 65
        skill_dir = self._write_skill(
            long_name, f"---\nname: {long_name}\ndescription: x\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("too long", message)
        self.assertIn("65", message)

    def test_accepts_name_at_64_chars(self):
        name = "a" * 64
        skill_dir = self._write_skill(
            name, f"---\nname: {name}\ndescription: x\n---\nBody.\n"
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    def test_rejects_name_directory_mismatch(self):
        skill_dir = self._write_skill(
            "other-dir", "---\nname: my-skill\ndescription: x\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("must match the parent directory name", message)

    # --- description validation ------------------------------------------
    def test_rejects_non_string_description(self):
        skill_dir = self._write_skill(
            "my-skill", "---\nname: my-skill\ndescription: 42\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("Description must be a string", message)

    def test_rejects_empty_description(self):
        skill_dir = self._write_skill(
            "my-skill", "---\nname: my-skill\ndescription: '   '\n---\nBody.\n"
        )
        self.assertEqual(
            validate_skill(skill_dir), (False, "Description must be non-empty.")
        )

    def test_rejects_angle_brackets_in_description(self):
        skill_dir = self._write_skill(
            "my-skill",
            "---\nname: my-skill\ndescription: Summarizes <error logs>.\n---\nBody.\n",
        )
        self.assertEqual(
            validate_skill(skill_dir),
            (False, "Description cannot contain angle brackets (< or >)"),
        )

    def test_rejects_description_over_1024_chars(self):
        desc = "x" * 1025
        skill_dir = self._write_skill(
            "my-skill", f"---\nname: my-skill\ndescription: {desc}\n---\nBody.\n"
        )
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("too long", message)
        self.assertIn("1025", message)

    def test_accepts_description_at_1024_chars(self):
        desc = "x" * 1024
        skill_dir = self._write_skill(
            "my-skill", f"---\nname: my-skill\ndescription: {desc}\n---\nBody.\n"
        )
        self.assertEqual(validate_skill(skill_dir), (True, "Skill is valid!"))

    # --- compatibility / metadata ----------------------------------------
    def test_rejects_non_string_compatibility(self):
        content = (
            "---\nname: my-skill\ndescription: x\ncompatibility:\n  - a\n  - b\n---\nBody.\n"
        )
        skill_dir = self._write_skill("my-skill", content)
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("Compatibility must be a string", message)

    def test_rejects_compatibility_over_500_chars(self):
        compat = "x" * 501
        content = f"---\nname: my-skill\ndescription: x\ncompatibility: {compat}\n---\nBody.\n"
        skill_dir = self._write_skill("my-skill", content)
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("Compatibility is too long", message)

    def test_rejects_non_mapping_metadata(self):
        content = "---\nname: my-skill\ndescription: x\nmetadata: just-a-string\n---\nBody.\n"
        skill_dir = self._write_skill("my-skill", content)
        valid, message = validate_skill(skill_dir)
        self.assertIs(valid, False)
        self.assertIn("Metadata must be a mapping", message)

    def test_accepts_path_given_as_string(self):
        # validate_skill accepts a str path as well as a Path.
        skill_dir = self._write_skill("my-skill", GOOD)
        self.assertEqual(validate_skill(str(skill_dir)), (True, "Skill is valid!"))


class TestBodyWarnings(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_path, ignore_errors=True)

    def _write(self, content):
        skill_dir = self.tmp_path / "my-skill"
        if not skill_dir.exists():
            skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    def test_no_warnings_under_budget(self):
        self.assertEqual(body_warnings(self._write(GOOD)), [])

    def test_missing_skill_md_returns_empty(self):
        empty = self.tmp_path / "empty"
        empty.mkdir()
        self.assertEqual(body_warnings(empty), [])

    def test_soft_on_malformed_frontmatter(self):
        self.assertEqual(body_warnings(self._write("---\nname: my-skill\ndescription: x\n")), [])

    def test_flags_body_over_line_budget(self):
        body = "\n".join(f"line {i}" for i in range(BODY_LINE_BUDGET + 2))
        skill_dir = self._write(f"---\nname: my-skill\ndescription: x\n---\n{body}\n")
        warnings = body_warnings(skill_dir)
        self.assertTrue(any("lines (recommended under" in w for w in warnings))

    def test_flags_body_over_token_budget(self):
        # One very long line: over the ~5000-token budget but under the line budget,
        # so only the token advisory fires.
        body = "x" * 20004
        skill_dir = self._write(f"---\nname: my-skill\ndescription: x\n---\n{body}\n")
        warnings = body_warnings(skill_dir)
        self.assertTrue(any("tokens (recommended under" in w for w in warnings))
        self.assertFalse(any("lines (recommended under" in w for w in warnings))

    def test_flags_description_near_limit_at_lower_bound(self):
        desc = "x" * 973
        skill_dir = self._write(f"---\nname: my-skill\ndescription: {desc}\n---\nBody.\n")
        self.assertTrue(any("within 5% of the 1024 limit" in w for w in body_warnings(skill_dir)))

    def test_no_description_warning_just_below_bound(self):
        desc = "x" * 972
        skill_dir = self._write(f"---\nname: my-skill\ndescription: {desc}\n---\nBody.\n")
        self.assertFalse(any("within 5% of the 1024 limit" in w for w in body_warnings(skill_dir)))


class TestExclusionHelpers(unittest.TestCase):
    def test_counts_as_skill_md(self):
        cases = [
            (Path("SKILL.md"), True),
            (Path("references/SKILL.md"), True),
            (Path("references/evals/SKILL.md"), True),  # 'evals' excluded only at root
            (Path("evals/files/broken-skill/SKILL.md"), False),
            (Path("tests/fixtures/SKILL.md"), False),
            (Path("__pycache__/SKILL.md"), False),
            (Path("scripts/__pycache__/SKILL.md"), False),
            (Path(".pytest_cache/v/SKILL.md"), False),
        ]
        for rel_path, expected in cases:
            with self.subTest(rel_path=rel_path):
                self.assertIs(_counts_as_skill_md(rel_path), expected)

    def test_should_exclude(self):
        cases = [
            (Path("my-skill/SKILL.md"), False),
            (Path("my-skill/references/foo.md"), False),
            (Path("my-skill/references/evals/foo.md"), False),  # evals only at root
            (Path("my-skill/evals/evals.json"), True),
            (Path("my-skill/tests/test_utils.py"), True),
            (Path("my-skill/.pytest_cache/v/cache"), True),
            (Path("my-skill/scripts/__pycache__/x.pyc"), True),
            (Path("my-skill/scripts/utils.pyc"), True),
            (Path("my-skill/.DS_Store"), True),
        ]
        for rel_path, expected in cases:
            with self.subTest(rel_path=rel_path):
                self.assertIs(should_exclude(rel_path), expected)


if __name__ == "__main__":
    unittest.main()
